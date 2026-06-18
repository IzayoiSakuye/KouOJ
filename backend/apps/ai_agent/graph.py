from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterable, TypedDict

from langgraph.graph import END, START, StateGraph

from apps.ai_agent.models import AgentRun
from apps.ai_agent.tools.model_client import call_chat_completion
from apps.ai_agent.tools.web_search import format_web_sources_for_agent, search_web_for_solutions
from apps.solutions.models import Solution
from apps.submissions.models import Submission


MAX_LOCAL_SOLUTIONS = 8


class DiagnosticAgentState(TypedDict, total=False):
    """
    LangGraph 图里的共享状态。

    LangGraph 会把每个节点返回的字段合并回这个 state，后续节点再继续读取。
    这样 agent 的流程、数据流和终止点都交给框架管理，而不是在 service 里手写一长串
    if/else 调度逻辑。
    """

    run_id: int
    submission_id: int
    hint_level: str
    problem_title: str
    problem_context: str
    submission_code: str
    submission_status: str
    judge_summary: str
    judge_detail_summary: str
    problem_type: str
    local_solution_summaries: list[dict[str, Any]]
    selected_solution_id: int | None
    selected_solution_title: str
    web_search_result: dict[str, Any]
    final_message: str
    confidence: int
    steps: list[dict[str, Any]]


@dataclass
class SolutionCandidate:
    """本地题解候选。这里只存 agent 需要的最小信息，避免把 ORM 对象放进 LangGraph state。"""

    solution_id: int
    title: str
    score: int
    summary: str


def _clean_text(value: object, max_length: int = 500) -> str:
    """把数据库字段整理成短文本，避免步骤日志和 agent state 过大。"""
    if value is None:
        return ""
    text = re.sub(r"\s+", " ", str(value)).strip()
    if len(text) <= max_length:
        return text
    return text[:max_length].rstrip()


def _tokenize(value: str) -> set[str]:
    """
    拆出用于本地题解粗匹配的 token。

    这是“资料选择工具”的内部实现，不是 agent 编排框架。LangGraph 负责决定流程；
    这个函数只负责给“本地题解节点”一个稳定、可测试的排序依据。
    """
    return set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*|[\u4e00-\u9fff]{2,}", value.lower()))


def _append_step(
    state: DiagnosticAgentState,
    step_type: str,
    input_summary: str,
    output_summary: str,
    success: bool = True,
) -> list[dict[str, Any]]:
    """在 LangGraph state 中追加一步日志，最终由 service 统一写入数据库。"""
    steps = list(state.get("steps", []))
    steps.append(
        {
            "step_type": step_type,
            "input_summary": _clean_text(input_summary, max_length=1000),
            "output_summary": _clean_text(output_summary, max_length=1500),
            "success": success,
        }
    )
    return steps


def _summarize_judge_results(submission: Submission) -> str:
    """把测试点结果压缩成诊断摘要；这里不输出隐藏测试点原始输入输出。"""
    results = list(submission.results.all())
    if not results:
        return "暂无测试点明细。"

    failed_results = [result for result in results if result.status != Submission.Status.ACCEPTED]
    if not failed_results:
        return f"共有 {len(results)} 个测试点，当前未发现失败测试点。"

    first_failed = failed_results[0]
    return (
        f"共有 {len(results)} 个测试点，失败 {len(failed_results)} 个；"
        f"首个失败状态为 {first_failed.status}，耗时 {first_failed.time_used} ms。"
    )


def _build_problem_context(submission: Submission) -> str:
    """
    组织给模型看的题面上下文。

    这里只放公开题面和样例测试点。隐藏测试点可以用于后端判题和内部统计，但不应该把
    原始输入输出放进模型提示或最终返回，避免学生通过复盘功能反推出隐藏数据。
    """
    problem = submission.problem
    sample_cases = problem.test_cases.filter(is_sample=True).order_by("order", "id")[:3]
    sample_lines = []
    for index, sample in enumerate(sample_cases, start=1):
        sample_lines.append(
            "\n".join(
                [
                    f"样例 {index}",
                    f"输入：{_clean_text(sample.input_data, 500)}",
                    f"输出：{_clean_text(sample.output_data, 500)}",
                ]
            )
        )

    return "\n".join(
        [
            f"题目标题：{problem.title}",
            f"题目描述：{_clean_text(problem.description, 1200)}",
            f"输入描述：{_clean_text(problem.input_description, 600)}",
            f"输出描述：{_clean_text(problem.output_description, 600)}",
            f"时间限制：{problem.time_limit} ms",
            f"内存限制：{problem.memory_limit} MB",
            "样例：",
            "\n\n".join(sample_lines) if sample_lines else "暂无样例。",
        ]
    )


def _build_judge_detail_summary(submission: Submission) -> str:
    """
    组织判题细节摘要。

    这里可以给模型看运行状态、用户程序输出和错误信息，但不展示隐藏测试点的原始输入
    或标准输出。这样模型能理解“错在哪里”，又不会泄露题库数据。
    """
    lines = []
    for index, result in enumerate(submission.results.all()[:5], start=1):
        lines.append(
            "\n".join(
                [
                    f"测试点 {index} 状态：{result.status}",
                    f"耗时：{result.time_used} ms，内存：{result.memory_used} KB",
                    f"程序输出摘要：{_clean_text(result.output, 500)}",
                    f"错误信息摘要：{_clean_text(result.error_message, 500)}",
                ]
            )
        )
    return "\n\n".join(lines) if lines else "暂无测试点明细。"


def _extract_expected_output_text(problem_context: str) -> str:
    """从题面上下文中提取一个很短的输出目标，用于模型不可用时做直接差异提示。"""
    patterns = [
        r"题目标题：输出[\"“](.*?)[\"”]",
        r"题目描述：输出[\"“](.*?)[\"”]",
        r"输出描述：([^\n]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, problem_context)
        if match:
            value = match.group(1).strip()
            if value and value.lower() != "null":
                return value
    return ""


def _extract_simple_print_value(code: str) -> str:
    """识别最常见的 print(...) 提交，给兜底复盘提供具体证据。"""
    match = re.search(r"print\s*\(\s*([\"']?)(.*?)\1\s*\)", code.strip(), re.S)
    if not match:
        return ""
    return match.group(2).strip()


def _build_direct_observation(state: DiagnosticAgentState) -> str:
    """
    在模型不可用时，尽量从题面和代码里直接提炼一个有用观察。

    这不是替代模型，而是避免兜底输出变成“状态复读机”。比如题目要求输出字符串
    1+1，而代码写 print(2)，这个差异后端可以直接看出来。
    """
    problem_context = state.get("problem_context", "")
    code = state.get("submission_code", "")
    expected_output = _extract_expected_output_text(problem_context)
    printed_value = _extract_simple_print_value(code)

    if expected_output and printed_value and expected_output != printed_value:
        return f"题面要求输出 `{expected_output}`，但你的代码实际输出 `{printed_value}`。这两者不是同一个输出。"

    if "输出" in problem_context and printed_value:
        return f"你的代码只输出了 `{printed_value}`，先确认它是否和题面要求的输出内容逐字符一致。"

    return "先从题面要求和代码实际输出是否一致开始检查。"


def _infer_problem_type(status: str) -> str:
    """根据判题状态生成初步问题假设，作为 agent 诊断主线。"""
    if status == Submission.Status.ACCEPTED:
        return "代码已经通过，可以关注复杂度、可读性和是否有更稳的写法。"
    if status == Submission.Status.WRONG_ANSWER:
        return "更像是算法思路、边界条件或输出格式存在偏差。"
    if status == Submission.Status.TIME_LIMIT_EXCEEDED:
        return "更像是复杂度过高、循环无法收敛或输入规模下算法不合适。"
    if status == Submission.Status.RUNTIME_ERROR:
        return "更像是数组越界、空输入处理、类型转换或运行时异常。"
    if status == Submission.Status.COMPILE_ERROR:
        return "更像是语法、类型、头文件或编译选项问题。"
    if status in (Submission.Status.PENDING, Submission.Status.JUDGING):
        return "提交还没有完成判题，当前只能做静态方向判断。"
    return "需要结合错误信息和测试点结果继续缩小问题范围。"


def _list_local_solution_candidates(submission: Submission) -> list[SolutionCandidate]:
    """读取公开本地题解，并根据学生代码和题解内容的关键词重合度排序。"""
    solutions = (
        Solution.objects.select_related("author", "problem")
        .filter(problem=submission.problem, is_public=True)
        .order_by("-created_at")[:MAX_LOCAL_SOLUTIONS]
    )
    code_tokens = _tokenize(submission.code)
    candidates: list[SolutionCandidate] = []

    for solution in solutions:
        solution_text = f"{solution.title} {solution.language} {solution.content}"
        overlap = code_tokens.intersection(_tokenize(solution_text))
        language_bonus = 2 if solution.language and solution.language == submission.language else 0
        score = len(overlap) + language_bonus
        candidates.append(
            SolutionCandidate(
                solution_id=solution.id,
                title=solution.title,
                score=score,
                summary=f"{solution.title} / 语言：{solution.language or '未标注'} / 摘要：{_clean_text(solution.content, 180)}",
            )
        )

    return sorted(candidates, key=lambda item: item.score, reverse=True)


def _render_solution_summary(candidates: Iterable[SolutionCandidate]) -> str:
    """把候选题解渲染成日志文本，方便查看 agent 选择依据。"""
    lines = []
    for index, candidate in enumerate(candidates, start=1):
        lines.append(f"{index}. #{candidate.solution_id} 分数 {candidate.score}：{candidate.summary}")
    return "\n".join(lines) if lines else "该题暂无公开本地题解。"


def read_context_node(state: DiagnosticAgentState) -> DiagnosticAgentState:
    """LangGraph 节点：读取题目、提交和判题摘要。"""
    submission = (
        Submission.objects.select_related("problem", "user")
        .prefetch_related("results", "problem__tags", "problem__test_cases")
        .get(id=state["submission_id"])
    )
    judge_summary = _summarize_judge_results(submission)
    judge_detail_summary = _build_judge_detail_summary(submission)
    problem_type = _infer_problem_type(submission.status)
    output_summary = f"题目：{submission.problem.title}；状态：{submission.status}；{judge_summary}"

    return {
        "problem_title": submission.problem.title,
        "problem_context": _build_problem_context(submission),
        "submission_code": _clean_text(submission.code, 6000),
        "submission_status": submission.status,
        "judge_summary": judge_summary,
        "judge_detail_summary": judge_detail_summary,
        "problem_type": problem_type,
        "steps": _append_step(state, "read_context", f"submission_id={submission.id}", output_summary),
    }


def select_local_solution_node(state: DiagnosticAgentState) -> DiagnosticAgentState:
    """LangGraph 节点：先在本地公开题解里选择最接近学生代码的一条。"""
    submission = Submission.objects.select_related("problem").get(id=state["submission_id"])
    candidates = _list_local_solution_candidates(submission)
    selected = candidates[0] if candidates else None
    summaries = [
        {
            "solution_id": candidate.solution_id,
            "title": candidate.title,
            "score": candidate.score,
            "summary": candidate.summary,
        }
        for candidate in candidates
    ]

    return {
        "local_solution_summaries": summaries,
        "selected_solution_id": selected.solution_id if selected else None,
        "selected_solution_title": selected.title if selected else "",
        "steps": _append_step(
            state,
            "select_local_solution",
            "读取该题所有公开本地题解，并按学生代码与题解内容的关键词重合度排序。",
            _render_solution_summary(candidates),
        ),
    }


def web_search_node(state: DiagnosticAgentState) -> DiagnosticAgentState:
    """LangGraph 节点：调用 Tavily 搜索外部题解资料。"""
    submission = Submission.objects.select_related("problem").prefetch_related("problem__tags").get(
        id=state["submission_id"]
    )
    search_result = search_web_for_solutions(
        submission.problem,
        submission=submission,
        query_hint=state.get("problem_type", ""),
    )
    output_summary = search_result.get("reason") or format_web_sources_for_agent(
        search_result.get("results", [])
    )

    return {
        "web_search_result": search_result,
        "steps": _append_step(
            state,
            "web_search",
            search_result.get("query", ""),
            output_summary,
            success=bool(search_result.get("available")),
        ),
    }


def render_hint_node(state: DiagnosticAgentState) -> DiagnosticAgentState:
    """LangGraph 节点：根据档位把 agent 收集到的证据渲染成学生可读提示。"""
    final_message = _render_rule_based_hint(state)
    model_result = call_chat_completion(_build_review_messages(state))
    success = bool(model_result.get("available"))
    if success:
        final_message = model_result["content"]

    confidence = 90 if success else _fallback_confidence(state)
    output_summary = model_result.get("reason") or final_message
    return {
        "final_message": final_message,
        "confidence": confidence,
        "steps": _append_step(
            state,
            "render_hint",
            f"hint_level={state.get('hint_level', AgentRun.HintLevel.DIRECTION)}",
            output_summary,
            success=success,
        ),
    }


def _fallback_confidence(state: DiagnosticAgentState) -> int:
    """模型不可用时，根据是否有题解/外部资料给一个保守置信度。"""
    web_search_result = state.get("web_search_result", {})
    return 80 if state.get("selected_solution_id") or web_search_result.get("results") else 60


def _render_rule_based_hint(state: DiagnosticAgentState) -> str:
    """模型不可用时使用的兜底提示，内容必须比空泛模板更贴近题面和代码。"""
    hint_level = state.get("hint_level", AgentRun.HintLevel.DIRECTION)
    code = state.get("submission_code", "")
    observation = _build_direct_observation(state)
    code_line = f"当前代码：`{_clean_text(code, 220)}`"

    if hint_level == AgentRun.HintLevel.DIRECTION:
        return "\n".join(
            [
                "方向提示：",
                observation,
                "先不要想复杂算法，优先检查“输出内容是否逐字符符合题面”。",
            ]
        )

    if hint_level == AgentRun.HintLevel.LOCATE:
        return "\n".join(
            [
                "定位提示：",
                observation,
                code_line,
                "可疑点在最终输出这一行。OJ 比对的是标准输出文本，不会把数学表达式 `1+1` 自动等价成数字 `2`。",
            ]
        )

    return "\n".join(
        [
            "详细解释：",
            observation,
            code_line,
            "这类题通常要求输出固定字符串。`print(2)` 输出的是数字字符 `2`，而不是字符串 `1+1`。",
            "把输出改成题面要求的文本即可。注意引号只用于 Python 字符串本身，最终输出里不一定包含引号，要以题目输出描述为准。",
        ]
    )


def _build_review_messages(state: DiagnosticAgentState) -> list[dict[str, str]]:
    """
    构造给模型的复盘提示。

    这里明确告诉模型：它已经拿到题面和学生代码，必须引用具体代码/题面信息来分析；
    同时要求不要泄露隐藏测试点、不要直接给完整 AC 代码。
    """
    hint_level = state.get("hint_level", AgentRun.HintLevel.DIRECTION)
    level_instruction = {
        AgentRun.HintLevel.DIRECTION: "只给方向性提示，必须结合题面和代码指出最值得检查的一两个方向，不给关键代码。",
        AgentRun.HintLevel.LOCATE: "定位可疑代码或逻辑分支，说明为什么可能错，允许给小反例思路，不给完整答案。",
        AgentRun.HintLevel.EXPLAIN: "给出较完整的修正路径和局部关键写法，但不要输出完整可提交代码。",
    }.get(hint_level, "给出适度的单次提交复盘。")

    local_solutions = state.get("local_solution_summaries", [])
    web_search_result = state.get("web_search_result", {})
    web_sources = format_web_sources_for_agent(web_search_result.get("results", []))
    local_summary = "\n".join(
        f"- #{item.get('solution_id')} {item.get('title')}：{item.get('summary')}"
        for item in local_solutions[:3]
    ) or "暂无本地公开题解。"

    user_content = "\n\n".join(
        [
            "请复盘这一次 OJ 提交，输出中文。",
            f"提示档位要求：{level_instruction}",
            f"题面信息：\n{state.get('problem_context', '')}",
            f"学生代码：\n```{state.get('submission_code', '')}\n```",
            f"提交状态：{state.get('submission_status', '')}",
            f"判题摘要：{state.get('judge_summary', '')}",
            f"判题细节摘要：\n{state.get('judge_detail_summary', '')}",
            f"初步问题类型：{state.get('problem_type', '')}",
            f"本地题解候选摘要：\n{local_summary}",
            f"外部搜索资料摘要：\n{web_sources}",
        ]
    )

    return [
        {
            "role": "system",
            "content": (
                "你是 KouOJ 的单次提交复盘 Agent。你必须基于题面、学生代码和判题结果给出具体反馈。"
                "不要泛泛而谈；不要泄露隐藏测试点原始数据；不要复制外部题解全文；不要输出完整可提交答案。"
            ),
        },
        {"role": "user", "content": user_content},
    ]


def build_diagnostic_agent_graph():
    """
    构建诊断型 agent 的 LangGraph 图。

    目前图是线性的，但它已经由框架承接状态流和节点连接；下一步要做“验证不通过就继续”
    时，只需要在这里加条件边，而不是重写 service。
    """
    graph = StateGraph(DiagnosticAgentState)
    graph.add_node("read_context", read_context_node)
    graph.add_node("select_local_solution", select_local_solution_node)
    graph.add_node("web_search", web_search_node)
    graph.add_node("render_hint", render_hint_node)

    graph.add_edge(START, "read_context")
    graph.add_edge("read_context", "select_local_solution")
    graph.add_edge("select_local_solution", "web_search")
    graph.add_edge("web_search", "render_hint")
    graph.add_edge("render_hint", END)
    return graph.compile()


diagnostic_agent_graph = build_diagnostic_agent_graph()

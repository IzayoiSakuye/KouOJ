from __future__ import annotations

import re
from typing import Any

from django.conf import settings


SOURCE_TYPE_EXTERNAL_SOLUTION = "external_solution"
ALLOWED_SEARCH_DEPTHS = {"basic", "advanced", "fast", "ultra-fast"}


def _clean_text(value: Any, max_length: int = 300) -> str:
    """把模型、数据库字段或 Tavily 返回值整理成适合放进搜索词/上下文的短文本。"""
    if value is None:
        return ""
    text = str(value)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_length:
        return text
    return text[:max_length].rstrip()


def _collect_tag_names(problem: Any) -> list[str]:
    """从 Problem.tags 中提取标签名，兼容 Django ManyRelatedManager 和测试里的普通列表。"""
    tags = getattr(problem, "tags", None)
    if not tags:
        return []

    try:
        tag_items = tags.all()
    except AttributeError:
        tag_items = tags

    names: list[str] = []
    for tag in tag_items:
        name = _clean_text(getattr(tag, "name", tag), max_length=40)
        if name:
            names.append(name)
    return names


def _safe_int(value: Any, default: int, min_value: int, max_value: int) -> int:
    """把 settings 中的字符串配置转成安全整数，避免环境变量写错导致运行时报错。"""
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return max(min_value, min(number, max_value))


def _get_tavily_search_depth() -> str:
    """只允许 Tavily 官方支持的 search_depth，防止环境变量传入不可预期的值。"""
    depth = getattr(settings, "KOUOJ_TAVILY_SEARCH_DEPTH", "basic")
    if depth in ALLOWED_SEARCH_DEPTHS:
        return depth
    return "basic"


def _create_tavily_client(api_key: str):
    """
    延迟导入 Tavily SDK。

    这样做有两个好处：
    1. 未配置 API Key 时不会强制导入外部依赖，开发环境可以先跑通其它功能。
    2. 单元测试可以直接 patch 这个函数，稳定模拟 Tavily 成功、失败和异常。
    """
    from tavily import TavilyClient

    return TavilyClient(api_key=api_key)


def build_solution_search_query(problem: Any, submission: Any | None = None, query_hint: str = "") -> str:
    """
    为“寻找外部题解”构造 Tavily 查询词。

    这里刻意不读取 submission.code，也不读取隐藏测试点。网页搜索只需要题目标题、
    题意摘要、标签和判题状态等非敏感信息；学生完整代码和隐藏数据只应该留在后端
    agent 的内部诊断流程里，不能发给第三方搜索服务。
    """
    title = _clean_text(getattr(problem, "title", ""), max_length=120)
    description = _clean_text(getattr(problem, "description", ""), max_length=160)
    tags = _collect_tag_names(problem)

    query_parts = [title, "题解", "算法思路"]
    if tags:
        query_parts.append(" ".join(tags))
    if description:
        query_parts.append(description)
    if submission is not None:
        language = _clean_text(getattr(submission, "language", ""), max_length=30)
        status = _clean_text(getattr(submission, "status", ""), max_length=40)
        if language:
            query_parts.append(language)
        if status:
            query_parts.append(status)
    if query_hint:
        query_parts.append(_clean_text(query_hint, max_length=120))

    return " ".join(part for part in query_parts if part)


def normalize_tavily_results(response: dict[str, Any] | None) -> list[dict[str, Any]]:
    """
    把 Tavily 原始响应收敛成 agent 能稳定消费的结构。

    Tavily 会返回很多字段，例如图片、favicon、raw_content 等；当前 v1 只保留标题、
    链接、摘要和相关度，避免把大段外部题解正文直接塞进 agent 上下文。
    """
    if not response:
        return []

    normalized_results: list[dict[str, Any]] = []
    for item in response.get("results", []):
        url = _clean_text(item.get("url"), max_length=500)
        if not url:
            continue

        normalized_results.append(
            {
                "title": _clean_text(item.get("title") or url, max_length=180),
                "url": url,
                "content": _clean_text(item.get("content"), max_length=800),
                "score": item.get("score"),
                "source_type": SOURCE_TYPE_EXTERNAL_SOLUTION,
            }
        )
    return normalized_results


def search_external_solutions(query: str) -> dict[str, Any]:
    """
    调用 Tavily 搜索外部题解，并把所有失败都转成可降级的返回值。

    agent runner 调这个函数时，不需要自己处理“没配 key、SDK 未安装、网络失败、
    Tavily 限流”等细节；它只要看 available 和 results，就能决定继续使用本地题解
    还是把外部搜索结果加入推理上下文。
    """
    cleaned_query = _clean_text(query, max_length=500)
    if not cleaned_query:
        return {
            "available": False,
            "reason": "搜索关键词为空，已跳过 Tavily 搜索。",
            "query": "",
            "results": [],
        }

    api_key = getattr(settings, "KOUOJ_TAVILY_API_KEY", "")
    if not api_key:
        return {
            "available": False,
            "reason": "未配置 KOUOJ_TAVILY_API_KEY，已跳过 Tavily 搜索。",
            "query": cleaned_query,
            "results": [],
        }

    max_results = _safe_int(
        getattr(settings, "KOUOJ_TAVILY_MAX_RESULTS", 5),
        default=5,
        min_value=1,
        max_value=20,
    )

    try:
        client = _create_tavily_client(api_key)
        response = client.search(
            cleaned_query,
            search_depth=_get_tavily_search_depth(),
            max_results=max_results,
            include_answer=False,
            include_raw_content=False,
            timeout=10,
        )
    except Exception as exc:
        return {
            "available": False,
            "reason": f"Tavily 搜索失败，已降级为不使用外部搜索：{exc}",
            "query": cleaned_query,
            "results": [],
        }

    return {
        "available": True,
        "reason": "",
        "query": cleaned_query,
        "results": normalize_tavily_results(response),
        "response_time": response.get("response_time") if isinstance(response, dict) else None,
    }


def format_web_sources_for_agent(results: list[dict[str, Any]]) -> str:
    """
    把归一化后的搜索结果转成 agent prompt 中的一段资料摘要。

    注意：这里输出的是“给 agent 看”的资料摘要，不是直接给学生看的最终答案。
    最终回答仍应由 agent 根据提示档位重新组织，避免原样搬运外部题解。
    """
    if not results:
        return "没有找到可用的外部搜索结果。"

    lines: list[str] = []
    for index, result in enumerate(results, start=1):
        score = result.get("score")
        score_text = f"相关度：{score}" if score is not None else "相关度：未知"
        lines.append(
            "\n".join(
                [
                    f"[{index}] {result.get('title', '未命名资料')}",
                    f"来源：{result.get('url', '')}",
                    score_text,
                    f"摘要：{result.get('content', '')}",
                ]
            )
        )
    return "\n\n".join(lines)


def search_web_for_solutions(
    problem: Any,
    submission: Any | None = None,
    query_hint: str = "",
) -> dict[str, Any]:
    """
    agent 的网页搜索入口：先根据题目和提交状态生成查询词，再调用 Tavily。

    后续 agent runner 可以在“先读本地公开题解”之后调用这个函数，把外部题解作为
    辅助证据。函数不会暴露为前端 API，也不会把学生代码发给 Tavily。
    """
    query = build_solution_search_query(problem, submission=submission, query_hint=query_hint)
    return search_external_solutions(query)

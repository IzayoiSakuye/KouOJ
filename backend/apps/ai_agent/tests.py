from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase, override_settings
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.ai_agent.models import AgentRun
from apps.ai_agent.services import run_diagnostic_agent
from apps.ai_agent.tools.model_client import call_chat_completion
from apps.ai_agent.tools.web_search import (
    build_solution_search_query,
    format_web_sources_for_agent,
    normalize_tavily_results,
    search_external_solutions,
)
from apps.problems.models import Problem
from apps.solutions.models import Solution
from apps.submissions.models import JudgeResult, Submission


class FakeModelResponse:
    def __init__(self, status_code, data):
        self.status_code = status_code
        self._data = data

    def json(self):
        return self._data


class WebSearchToolTests(SimpleTestCase):
    def test_build_query_does_not_include_student_code(self):
        problem = SimpleNamespace(
            title="两数之和",
            description="给定一个整数数组和一个目标值，返回两个数的下标。",
            tags=[SimpleNamespace(name="哈希表")],
        )
        submission = SimpleNamespace(
            language="python3",
            status="WRONG_ANSWER",
            code="SECRET_STUDENT_CODE_SHOULD_NOT_LEAK",
        )

        query = build_solution_search_query(problem, submission=submission)

        self.assertIn("两数之和", query)
        self.assertIn("哈希表", query)
        self.assertIn("WRONG_ANSWER", query)
        self.assertNotIn("SECRET_STUDENT_CODE_SHOULD_NOT_LEAK", query)

    def test_normalize_tavily_results_keeps_only_agent_safe_fields(self):
        response = {
            "results": [
                {
                    "title": "题解标题",
                    "url": "https://example.com/solution",
                    "content": "这是一段外部题解摘要。",
                    "score": 0.91,
                    "raw_content": "这里模拟很长的原文，当前工具不应该保留它。",
                },
                {"title": "缺少 URL 的结果", "content": "应该被跳过。"},
            ]
        }

        results = normalize_tavily_results(response)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["source_type"], "external_solution")
        self.assertNotIn("raw_content", results[0])

    @override_settings(KOUOJ_TAVILY_API_KEY="")
    def test_search_external_solutions_degrades_without_api_key(self):
        result = search_external_solutions("A+B Problem 题解")

        self.assertFalse(result["available"])
        self.assertEqual(result["results"], [])
        self.assertIn("未配置", result["reason"])

    @override_settings(KOUOJ_TAVILY_API_KEY="tvly-test-key")
    def test_search_external_solutions_degrades_when_tavily_raises(self):
        with patch(
            "apps.ai_agent.tools.web_search._create_tavily_client",
            side_effect=RuntimeError("network error"),
        ):
            result = search_external_solutions("A+B Problem 题解")

        self.assertFalse(result["available"])
        self.assertEqual(result["results"], [])
        self.assertIn("Tavily 搜索失败", result["reason"])

    @override_settings(
        KOUOJ_TAVILY_API_KEY="tvly-test-key",
        KOUOJ_TAVILY_MAX_RESULTS="3",
        KOUOJ_TAVILY_SEARCH_DEPTH="basic",
    )
    def test_search_external_solutions_calls_tavily_with_safe_defaults(self):
        class FakeClient:
            def __init__(self):
                self.call_kwargs = None

            def search(self, query, **kwargs):
                self.call_kwargs = {"query": query, **kwargs}
                return {
                    "response_time": "0.1",
                    "results": [
                        {
                            "title": "外部题解",
                            "url": "https://example.com/solution",
                            "content": "外部资料摘要。",
                            "score": 0.7,
                        }
                    ],
                }

        fake_client = FakeClient()
        with patch(
            "apps.ai_agent.tools.web_search._create_tavily_client",
            return_value=fake_client,
        ):
            result = search_external_solutions("A+B Problem 题解")

        self.assertTrue(result["available"])
        self.assertEqual(result["results"][0]["title"], "外部题解")
        self.assertEqual(fake_client.call_kwargs["max_results"], 3)
        self.assertEqual(fake_client.call_kwargs["search_depth"], "basic")
        self.assertFalse(fake_client.call_kwargs["include_answer"])
        self.assertFalse(fake_client.call_kwargs["include_raw_content"])
        self.assertEqual(fake_client.call_kwargs["timeout"], 10)

    def test_format_web_sources_for_agent(self):
        text = format_web_sources_for_agent(
            [
                {
                    "title": "资料一",
                    "url": "https://example.com/a",
                    "content": "摘要一",
                    "score": 0.8,
                }
            ]
        )

        self.assertIn("资料一", text)
        self.assertIn("https://example.com/a", text)
        self.assertIn("摘要一", text)


class ModelClientTests(SimpleTestCase):
    @override_settings(
        KOUOJ_AI_MODEL_BASE_URL="https://example.com/v1",
        KOUOJ_AI_MODEL_API_KEY="test-key",
        KOUOJ_AI_MODEL_NAME="test-model",
        KOUOJ_AI_MODEL_TIMEOUT="5",
    )
    def test_call_chat_completion_retries_temporary_service_error(self):
        responses = [
            FakeModelResponse(503, {"error": {"message": "temporary unavailable"}}),
            FakeModelResponse(503, {"error": {"message": "temporary unavailable"}}),
            FakeModelResponse(
                200,
                {
                    "model": "test-model",
                    "choices": [
                        {"message": {"content": "模型复盘结果"}},
                    ],
                },
            ),
        ]

        with (
            patch("apps.ai_agent.tools.model_client.requests.post", side_effect=responses) as post,
            patch("apps.ai_agent.tools.model_client.time.sleep"),
        ):
            result = call_chat_completion([{"role": "user", "content": "hello"}])

        self.assertTrue(result["available"])
        self.assertEqual(result["content"], "模型复盘结果")
        self.assertEqual(post.call_count, 3)


class DiagnosticAgentGraphTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="student", password="pass")
        self.problem = Problem.objects.create(
            title="A+B Problem",
            description="输入两个整数，输出它们的和。",
            input_description="两个整数",
            output_description="和",
        )
        self.submission = Submission.objects.create(
            user=self.user,
            problem=self.problem,
            language=Submission.Language.PYTHON3,
            code="a, b = map(int, input().split())\nprint(a - b)",
            status=Submission.Status.WRONG_ANSWER,
            score=0,
        )
        self.solution = Solution.objects.create(
            author=self.user,
            problem=self.problem,
            title="使用加法直接求和",
            content="读取两个整数后使用加法输出结果。",
            language=Submission.Language.PYTHON3,
            is_public=True,
        )
        JudgeResult.objects.create(
            submission=self.submission,
            testcase=self.problem.test_cases.create(
                input_data="1 2",
                output_data="3",
                is_sample=True,
                score=100,
            ),
            status=Submission.Status.WRONG_ANSWER,
            time_used=10,
            output="-1",
        )

    def test_run_diagnostic_agent_uses_langgraph_and_records_steps(self):
        fake_web_result = {
            "available": True,
            "reason": "",
            "query": "A+B Problem 题解",
            "results": [
                {
                    "title": "外部 A+B 题解",
                    "url": "https://example.com/ab",
                    "content": "外部资料摘要。",
                    "score": 0.8,
                }
            ],
        }

        with (
            patch("apps.ai_agent.graph.search_web_for_solutions", return_value=fake_web_result),
            patch(
                "apps.ai_agent.graph.call_chat_completion",
                return_value={
                    "available": True,
                    "reason": "",
                    "content": "定位提示：代码里使用了减法，题面要求输出两个整数的和。",
                },
            ),
        ):
            run = run_diagnostic_agent(self.user, self.submission.id, AgentRun.HintLevel.LOCATE)

        self.assertEqual(run.status, AgentRun.Status.COMPLETED)
        self.assertEqual(run.selected_solution, self.solution)
        self.assertIn("定位提示", run.final_message)
        self.assertIn("减法", run.final_message)
        self.assertEqual(run.steps_count, 4)
        self.assertEqual(
            list(run.steps.values_list("step_type", flat=True)),
            ["read_context", "select_local_solution", "web_search", "render_hint"],
        )

    def test_agent_run_api_creates_diagnostic_run(self):
        client = APIClient()
        client.force_authenticate(self.user)

        with (
            patch(
                "apps.ai_agent.graph.search_web_for_solutions",
                return_value={
                    "available": False,
                    "reason": "未配置 KOUOJ_TAVILY_API_KEY，已跳过 Tavily 搜索。",
                    "query": "A+B Problem 题解",
                    "results": [],
                },
            ),
            patch(
                "apps.ai_agent.graph.call_chat_completion",
                return_value={
                    "available": True,
                    "reason": "",
                    "content": "方向提示：题目要求求和，但代码输出的是 a - b。",
                },
            ),
        ):
            response = client.post(
                "/api/ai-agent/runs/",
                {"submission_id": self.submission.id, "hint_level": AgentRun.HintLevel.DIRECTION},
                format="json",
            )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["status"], AgentRun.Status.COMPLETED)
        self.assertIn("方向提示", response.data["final_message"])
        self.assertEqual(response.data["steps_count"], 4)

    def test_fallback_hint_points_out_fixed_output_mismatch(self):
        fixed_problem = Problem.objects.create(
            title='输出"1+1"',
            description='输出"1+1"字符串',
            input_description="null",
            output_description="1+1",
        )
        fixed_submission = Submission.objects.create(
            user=self.user,
            problem=fixed_problem,
            language=Submission.Language.PYTHON3,
            code="print(2)",
            status=Submission.Status.WRONG_ANSWER,
            score=0,
        )
        JudgeResult.objects.create(
            submission=fixed_submission,
            testcase=fixed_problem.test_cases.create(
                input_data="",
                output_data="1+1",
                is_sample=True,
                score=100,
            ),
            status=Submission.Status.WRONG_ANSWER,
            time_used=10,
            output="2",
        )

        with (
            patch(
                "apps.ai_agent.graph.search_web_for_solutions",
                return_value={"available": False, "reason": "skip", "query": "", "results": []},
            ),
            patch(
                "apps.ai_agent.graph.call_chat_completion",
                return_value={"available": False, "reason": "模型不可用", "content": ""},
            ),
        ):
            run = run_diagnostic_agent(self.user, fixed_submission.id, AgentRun.HintLevel.EXPLAIN)

        self.assertIn("题面要求输出 `1+1`", run.final_message)
        self.assertIn("实际输出 `2`", run.final_message)
        self.assertNotIn("没有匹配到本地公开题解", run.final_message)
        self.assertNotIn("外部搜索", run.final_message)

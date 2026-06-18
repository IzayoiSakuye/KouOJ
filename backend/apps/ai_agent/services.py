from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.ai_agent.models import AgentRun, AgentStep
from apps.ai_agent.graph import diagnostic_agent_graph
from apps.submissions.models import Submission


def _get_submission_for_user(user, submission_id: int) -> Submission:
    """读取提交并做权限校验：普通学生只能诊断自己的提交，管理员可以诊断所有提交。"""
    try:
        submission = (
            Submission.objects.select_related("user", "problem")
            .prefetch_related("results", "problem__tags", "problem__test_cases")
            .get(id=submission_id)
        )
    except Submission.DoesNotExist as exc:
        raise ValidationError({"submission_id": "提交不存在。"}) from exc

    if submission.user_id != user.id and not getattr(user, "is_admin", False):
        raise PermissionDenied("你只能诊断自己的提交。")
    return submission


def _save_graph_steps(run: AgentRun, steps: list[dict]):
    """把 LangGraph state 中收集到的步骤统一落库。"""
    AgentStep.objects.bulk_create(
        [
            AgentStep(
                run=run,
                step_type=step.get("step_type", ""),
                input_summary=step.get("input_summary", ""),
                output_summary=step.get("output_summary", ""),
                success=step.get("success", True),
            )
            for step in steps
        ]
    )
    run.steps_count = len(steps)
    run.save(update_fields=["steps_count", "updated_at"])


@transaction.atomic
def run_diagnostic_agent(user, submission_id: int, hint_level: str) -> AgentRun:
    """
    创建并执行一次诊断型 agent。

    v1 为了保持课程设计项目简单，先使用同步执行：接口收到请求后立刻跑完整个流程并
    返回结果。流程已经拆成步骤记录，后续如果要改成异步任务，也可以复用这些模型。
    """
    if hint_level not in AgentRun.HintLevel.values:
        raise ValidationError({"hint_level": "不支持的提示档位。"})

    submission = _get_submission_for_user(user, submission_id)
    run = AgentRun.objects.create(
        user=user,
        submission=submission,
        hint_level=hint_level,
        status=AgentRun.Status.RUNNING,
    )

    try:
        graph_result = diagnostic_agent_graph.invoke(
            {
                "run_id": run.id,
                "submission_id": submission.id,
                "hint_level": hint_level,
                "steps": [],
            }
        )
        selected_solution_id = graph_result.get("selected_solution_id")
        run.selected_solution_id = selected_solution_id
        run.final_message = graph_result.get("final_message", "")
        run.confidence = graph_result.get("confidence", 0)
        run.status = AgentRun.Status.COMPLETED
        run.updated_at = timezone.now()
        run.save(
            update_fields=[
                "selected_solution",
                "final_message",
                "confidence",
                "status",
                "updated_at",
            ]
        )
        _save_graph_steps(run, graph_result.get("steps", []))
    except Exception as exc:
        run.status = AgentRun.Status.FAILED
        run.error_message = str(exc)
        run.updated_at = timezone.now()
        run.save(update_fields=["status", "error_message", "updated_at"])
        AgentStep.objects.create(
            run=run,
            step_type="failed",
            input_summary="agent 运行异常",
            output_summary=str(exc),
            success=False,
        )
        raise

    return run

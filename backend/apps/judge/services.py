import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.submissions.models import JudgeResult, Submission


@dataclass
class RunResult:
    status: str
    output: str = ""
    error_message: str = ""
    time_used: int = 0


def normalize_output(value):
    return value.replace("\r\n", "\n").strip()


def run_python_code(code, input_data, timeout_seconds):
    with tempfile.TemporaryDirectory() as temp_dir:
        code_path = Path(temp_dir) / "main.py"
        code_path.write_text(code, encoding="utf-8")

        started_at = time.perf_counter()
        try:
            completed = subprocess.run(
                [settings.JUDGE_PYTHON_COMMAND, str(code_path)],
                input=input_data,
                text=True,
                capture_output=True,
                timeout=timeout_seconds,
                cwd=temp_dir,
            )
        except subprocess.TimeoutExpired:
            time_used = int((time.perf_counter() - started_at) * 1000)
            return RunResult(status=Submission.Status.TIME_LIMIT_EXCEEDED, time_used=time_used)

        time_used = int((time.perf_counter() - started_at) * 1000)
        if completed.returncode != 0:
            return RunResult(
                status=Submission.Status.RUNTIME_ERROR,
                output=completed.stdout,
                error_message=completed.stderr[-2000:],
                time_used=time_used,
            )
        return RunResult(
            status=Submission.Status.ACCEPTED,
            output=completed.stdout,
            time_used=time_used,
        )


def acquire_pending_submission():
    with transaction.atomic():
        submission = (
            Submission.objects.select_for_update(skip_locked=True)
            .filter(status=Submission.Status.PENDING)
            .order_by("id")
            .first()
        )
        if submission is None:
            return None
        submission.status = Submission.Status.JUDGING
        submission.save(update_fields=["status"])
        return submission


def judge_submission(submission):
    test_cases = list(submission.problem.test_cases.all())
    if not test_cases:
        submission.status = Submission.Status.SYSTEM_ERROR
        submission.error_message = "该题目没有测试点。"
        submission.judged_at = timezone.now()
        submission.save(update_fields=["status", "error_message", "judged_at"])
        return submission

    timeout_seconds = max(1, submission.problem.time_limit / 1000)
    total_score = 0
    max_time = 0
    final_status = Submission.Status.ACCEPTED
    final_error = ""

    JudgeResult.objects.filter(submission=submission).delete()

    for test_case in test_cases:
        run_result = run_python_code(submission.code, test_case.input_data, timeout_seconds)
        status = run_result.status

        if status == Submission.Status.ACCEPTED:
            if normalize_output(run_result.output) == normalize_output(test_case.output_data):
                total_score += test_case.score
            else:
                status = Submission.Status.WRONG_ANSWER

        JudgeResult.objects.create(
            submission=submission,
            testcase=test_case,
            status=status,
            time_used=run_result.time_used,
            memory_used=0,
            output=run_result.output[-2000:],
            error_message=run_result.error_message,
        )

        max_time = max(max_time, run_result.time_used)
        if status != Submission.Status.ACCEPTED:
            final_status = status
            final_error = run_result.error_message
            # break

    submission.status = final_status
    submission.score = 100 if final_status == Submission.Status.ACCEPTED else total_score
    submission.time_used = max_time
    submission.error_message = final_error
    submission.judged_at = timezone.now()
    submission.save(
        update_fields=["status", "score", "time_used", "error_message", "judged_at"]
    )
    return submission


def process_next_submission():
    submission = acquire_pending_submission()
    if submission is None:
        return None
    return judge_submission(submission)

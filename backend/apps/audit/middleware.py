import time

from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import OperationLog


class OperationLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        started_at = time.perf_counter()

        response = self.get_response(request)

        duration_ms = int(
            (time.perf_counter() - started_at) * 1000
        )

        if self.should_record(request, response):
            self.create_log(request, response, duration_ms)

        return response
    # 记录需要的
    def should_record(self, request, response):
        if not request.path.startswith("/api/"):
            return False

        if request.path.startswith("/api/audit/"):
            return False

        write_methods = {"POST", "PUT", "PATCH", "DELETE"}

        return (
            request.method in write_methods
            or response.status_code >= 400
        )
    # 获得JWT用户
    def get_user(self, request):
        if request.user.is_authenticated:
            return request.user

        try:
            authentication = JWTAuthentication()
            result = authentication.authenticate(request)

            if result is not None:
                user, token = result
                return user
        except Exception:
            pass

        return None
    # 获取ip
    def get_ip_address(self, request):
        forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        return request.META.get("REMOTE_ADDR")
    # 生成操作名称
    def get_action(self, request):
        action_map = {
            "POST": "CREATE",
            "PUT": "UPDATE",
            "PATCH": "UPDATE",
            "DELETE": "DELETE",
        }

        if request.path == "/api/auth/login/":
            return "LOGIN"

        if request.path == "/api/auth/register/":
            return "REGISTER"

        if request.path == "/api/auth/change-password/":
            return "CHANGE_PASSWORD"

        if request.path == "/api/submissions/":
            return "CREATE_SUBMISSION"

        return action_map.get(request.method, "REQUEST_ERROR")
    # 创建日志
    def create_log(self, request, response, duration_ms):
        try:
            OperationLog.objects.create(
                user=self.get_user(request),
                action=self.get_action(request),
                method=request.method,
                path=request.path[:255],
                status_code=response.status_code,
                ip_address=self.get_ip_address(request),
                user_agent=request.META.get(
                    "HTTP_USER_AGENT",
                    "",
                )[:500],
                duration_ms=duration_ms,
                detail={
                    "query": request.GET.dict(),
                },
            )
        except Exception:
            # 日志失败不能影响正常业务请求
            pass
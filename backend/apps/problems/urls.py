from rest_framework.routers import DefaultRouter

from .views import ProblemViewSet, TagViewSet, TestCaseViewSet

router = DefaultRouter()
router.register("problems", ProblemViewSet, basename="problem")
router.register("tags", TagViewSet, basename="tag")
router.register("test-cases", TestCaseViewSet, basename="test-case")

urlpatterns = router.urls

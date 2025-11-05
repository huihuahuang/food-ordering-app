from rest_framework.routers import DefaultRouter
from .views import StaffOrderViewSet

router = DefaultRouter()
router.register(r"orders", StaffOrderViewSet, basename="staff-order")

urlpatterns = router.urls
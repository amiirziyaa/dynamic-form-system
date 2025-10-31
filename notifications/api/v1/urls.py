from rest_framework.routers import DefaultRouter
from notifications.views import WebhookViewSet, ReportAdminViewSet

router = DefaultRouter()

# /api/v1/admin/webhooks/
router.register(r'webhooks', WebhookViewSet, basename='webhook')

# /api/v1/admin/reports/
router.register(r'reports', ReportAdminViewSet, basename='report-admin')

urlpatterns = router.urls
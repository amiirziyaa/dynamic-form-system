from rest_framework.routers import DefaultRouter
from analytics.views import FormAnalyticsViewSet

router = DefaultRouter()
router.register(
    r'analytics',
    FormAnalyticsViewSet, 
    basename='form-analytics'
)

urlpatterns = router.urls

# /analytics/{form_slug}/overview/
# /analytics/{form_slug}/views/
# /analytics/{form_slug}/submissions/
# /analytics/{form_slug}/completion-rate/
# /analytics/{form_slug}/drop-off/
# /analytics/{form_slug}/reports/summary/
# /analytics/{form_slug}/reports/field/{field_id}/
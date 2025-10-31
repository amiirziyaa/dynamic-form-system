from django.urls import path, include
from rest_framework.routers import DefaultRouter
from processes.views import ProcessViewSet, ProcessStepViewSet

app_name = 'processes'


router = DefaultRouter()
router.register(r'processes', ProcessViewSet, basename='process')


urlpatterns = [
    # List and create step
    path(
        'processes/<slug:process_slug>/steps/',
        ProcessStepViewSet.as_view({
            'get': 'list',
            'post': 'create'
        }),
        name='step-list'
    ),

    path(
        'processes/<slug:process_slug>/steps/reorder/',
        ProcessStepViewSet.as_view({
            'post': 'reorder'
        }),
        name='step-reorder'
    ),

    # Step details, update, and delete
    path(
        'processes/<slug:process_slug>/steps/<uuid:id>/',
        ProcessStepViewSet.as_view({
            'get': 'retrieve',
            'patch': 'partial_update',
            'put': 'update',
            'delete': 'destroy'
        }),
        name='step-detail'
    ),
]

urlpatterns = router.urls + urlpatterns


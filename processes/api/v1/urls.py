from django.urls import path, include
from rest_framework.routers import DefaultRouter
from processes.views import ProcessViewSet, ProcessStepViewSet
from processes.public_views import PublicProcessViewSet
from processes.analytics_views import ProcessAnalyticsViewSet

app_name = 'processes'


router = DefaultRouter()
router.register(r'processes', ProcessViewSet, basename='process')


urlpatterns = [
    path(
        'public/processes/<slug:slug>/',
        PublicProcessViewSet.as_view({
            'get': 'retrieve'
        }),
        name='public-process-detail'
    ),
    
    path(
        'public/processes/<slug:slug>/verify-password/',
        PublicProcessViewSet.as_view({
            'post': 'verify_password'
        }),
        name='public-process-verify-password'
    ),
    
    path(
        'public/processes/<slug:slug>/view/',
        PublicProcessViewSet.as_view({
            'post': 'track_view'
        }),
        name='public-process-track-view'
    ),
    
    path(
        'public/processes/<slug:slug>/start/',
        PublicProcessViewSet.as_view({
            'post': 'start'
        }),
        name='public-process-start'
    ),
    
    path(
        'public/processes/<slug:slug>/progress/<str:session_id>/',
        PublicProcessViewSet.as_view({
            'get': 'get_progress'
        }),
        name='public-process-progress'
    ),
    
    path(
        'public/processes/<slug:slug>/progress/<str:session_id>/current-step/',
        PublicProcessViewSet.as_view({
            'get': 'get_current_step'
        }),
        name='public-process-current-step'
    ),
    
    path(
        'public/processes/<slug:slug>/progress/<str:session_id>/next/',
        PublicProcessViewSet.as_view({
            'post': 'move_next'
        }),
        name='public-process-next-step'
    ),
    
    path(
        'public/processes/<slug:slug>/progress/<str:session_id>/previous/',
        PublicProcessViewSet.as_view({
            'post': 'move_previous'
        }),
        name='public-process-previous-step'
    ),
    
    path(
        'public/processes/<slug:slug>/steps/<str:step_id>/form/',
        PublicProcessViewSet.as_view({
            'get': 'get_step_form'
        }),
        name='public-process-step-form'
    ),
    
    path(
        'public/processes/<slug:slug>/steps/<str:step_id>/complete/',
        PublicProcessViewSet.as_view({
            'post': 'complete_step'
        }),
        name='public-process-complete-step'
    ),
    
    path(
        'public/processes/<slug:slug>/complete/',
        PublicProcessViewSet.as_view({
            'post': 'complete_process'
        }),
        name='public-process-complete'
    ),
    
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
    
    path(
        'processes/<slug:slug>/analytics/',
        ProcessAnalyticsViewSet.as_view({
            'get': 'analytics_overview'
        }),
        name='process-analytics-overview'
    ),
    
    path(
        'processes/<slug:slug>/analytics/views/',
        ProcessAnalyticsViewSet.as_view({
            'get': 'analytics_views'
        }),
        name='process-analytics-views'
    ),
    
    path(
        'processes/<slug:slug>/analytics/completions/',
        ProcessAnalyticsViewSet.as_view({
            'get': 'analytics_completions'
        }),
        name='process-analytics-completions'
    ),
    
    path(
        'processes/<slug:slug>/analytics/completion-rate/',
        ProcessAnalyticsViewSet.as_view({
            'get': 'analytics_completion_rate'
        }),
        name='process-analytics-completion-rate'
    ),
    
    path(
        'processes/<slug:slug>/analytics/step-drop-off/',
        ProcessAnalyticsViewSet.as_view({
            'get': 'analytics_step_drop_off'
        }),
        name='process-analytics-step-drop-off'
    ),
    
    path(
        'processes/<slug:slug>/analytics/average-time/',
        ProcessAnalyticsViewSet.as_view({
            'get': 'analytics_average_time'
        }),
        name='process-analytics-average-time'
    ),
    
    path(
        'processes/<slug:slug>/progress/',
        ProcessAnalyticsViewSet.as_view({
            'get': 'list_progress'
        }),
        name='process-progress-list'
    ),
    
    path(
        'processes/<slug:slug>/progress/<uuid:progress_id>/',
        ProcessAnalyticsViewSet.as_view({
            'get': 'get_progress'
        }),
        name='process-progress-detail'
    ),
    
    path(
        'processes/<slug:slug>/progress/abandoned/',
        ProcessAnalyticsViewSet.as_view({
            'get': 'list_abandoned'
        }),
        name='process-progress-abandoned'
    ),
]

urlpatterns = router.urls + urlpatterns


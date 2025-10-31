from django.urls import re_path
from . import consumers

# WS /ws/v1/forms/{slug}/reports/live/
websocket_urlpatterns = [
    re_path(
        r'ws/v1/forms/(?P<form_slug>[\w-]+)/reports/live/$', 
        consumers.AnalyticsConsumer.as_asgi()
    ),
]
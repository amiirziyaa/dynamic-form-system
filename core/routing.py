from django.urls import path, include
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import analytics.routing

application = ProtocolTypeRouter({    
    "websocket": AuthMiddlewareStack(
        URLRouter(
            analytics.routing.websocket_urlpatterns
        )
    ),
})
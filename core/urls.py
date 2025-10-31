"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView
)
import core.system_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # System endpoints
    path('api/v1/health/', core.system_views.health_check, name='health-check'),
    path('api/v1/version/', core.system_views.version_info, name='version-info'),
    
    # OpenAPI Schema (drf-spectacular)
    path('api/v1/schema/', SpectacularAPIView.as_view(), name='schema'),
    
    # Swagger UI
    path('api/v1/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    
    # ReDoc
    path('api/v1/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # API v1 endpoints
    path('api/v1/', include('forms.api.v1.urls')),
    path('api/v1/', include('categories.api.v1.urls')),
    path('api/v1/auth/', include('accounts.api.v1.urls')),
    path('api/v1/users/', include('accounts.api.v1.user_urls')),
    path('api/v1/', include('submissions.api.v1.urls')),
    path('api/v1/', include('processes.api.v1.urls')),
]

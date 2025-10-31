from django.urls import path
from accounts.views import (
    UserProfileView,
    ResendVerificationEmailView,
    EmailVerificationView,
)

app_name = 'users'

urlpatterns = [
    # User profile endpoints - matches api-endpoints-list.md
    path('me/', UserProfileView.as_view(), name='user-profile'),  # GET, PATCH
    path('me/verify-email/', ResendVerificationEmailView.as_view(), name='user-verify-email-send'),  # POST
    path('me/verify-email/<str:token>/', EmailVerificationView.as_view(), name='user-verify-email'),  # GET
]


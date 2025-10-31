from django.urls import path
from submissions.views import PublicFormViewSet
from submissions.owner_views import SubmissionManagementViewSet

app_name = 'submissions'

urlpatterns = [
    # ============================================
    # Public Form Access (No Authentication!)
    # ============================================

    # Get form structure
    path(
        'public/forms/<slug:slug>/',
        PublicFormViewSet.as_view({
            'get': 'retrieve'
        }),
        name='public-form-detail'
    ),

    # Verify password for private forms
    path(
        'public/forms/<slug:slug>/verify-password/',
        PublicFormViewSet.as_view({
            'post': 'verify_password'
        }),
        name='public-form-verify-password'
    ),

    # Track form view (analytics)
    path(
        'public/forms/<slug:slug>/view/',
        PublicFormViewSet.as_view({
            'post': 'track_view'
        }),
        name='public-form-track-view'
    ),

    # Submit form (final)
    path(
        'public/forms/<slug:slug>/submit/',
        PublicFormViewSet.as_view({
            'post': 'submit_form'
        }),
        name='public-form-submit'
    ),

    # Save draft
    path(
        'public/forms/<slug:slug>/submissions/draft/',
        PublicFormViewSet.as_view({
            'post': 'save_draft'
        }),
        name='public-form-draft-create'
    ),

    # Get/Update draft
    path(
        'public/forms/<slug:slug>/submissions/draft/<str:session_id>/',
        PublicFormViewSet.as_view({
            'get': 'get_draft',
            'patch': 'update_draft'
        }),
        name='public-form-draft-detail'
    ),

    # ============================================
    # Owner Submission Management (Authentication Required!)
    # ============================================

    # List submissions
    path(
        'forms/<slug:slug>/submissions/',
        SubmissionManagementViewSet.as_view({
            'get': 'list'
        }),
        name='submission-list'
    ),

    # Get submission statistics
    path(
        'forms/<slug:slug>/submissions/stats/',
        SubmissionManagementViewSet.as_view({
            'get': 'statistics'
        }),
        name='submission-stats'
    ),

    # Export submissions
    path(
        'forms/<slug:slug>/submissions/export/',
        SubmissionManagementViewSet.as_view({
            'post': 'export_submissions'
        }),
        name='submission-export'
    ),

    # Bulk delete
    path(
        'forms/<slug:slug>/submissions/bulk-delete/',
        SubmissionManagementViewSet.as_view({
            'post': 'bulk_delete'
        }),
        name='submission-bulk-delete'
    ),

    # Bulk export
    path(
        'forms/<slug:slug>/submissions/bulk-export/',
        SubmissionManagementViewSet.as_view({
            'post': 'bulk_export'
        }),
        name='submission-bulk-export'
    ),

    # Get/Delete single submission
    path(
        'forms/<slug:slug>/submissions/<uuid:id>/',
        SubmissionManagementViewSet.as_view({
            'get': 'retrieve',
            'delete': 'destroy'
        }),
        name='submission-detail'
    ),
]

# ============================================
# Usage in main urls.py:
# ============================================
"""
# In your main project urls.py:

from django.urls import path, include

urlpatterns = [
    path('api/v1/', include('submissions.api.v1.urls')),
]

This will create URLs like:
/api/v1/public/forms/{slug}/
/api/v1/public/forms/{slug}/submit/
etc.
"""

# ============================================
# Final URL examples:
# ============================================
"""
✅ Public Form Access:
GET    /api/v1/public/forms/my-survey/
POST   /api/v1/public/forms/my-survey/verify-password/
POST   /api/v1/public/forms/my-survey/view/
POST   /api/v1/public/forms/my-survey/submit/
POST   /api/v1/public/forms/my-survey/submissions/draft/
GET    /api/v1/public/forms/my-survey/submissions/draft/{session_id}/
PATCH  /api/v1/public/forms/my-survey/submissions/draft/{session_id}/
"""
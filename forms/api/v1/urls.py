from django.urls import path
from forms.views import FormFieldViewSet, FieldOptionViewSet

app_name = 'forms'

# POST /api/v1/forms/{slug}/fields/reorder/
# POST /api/v1/forms/{slug}/fields/{field_id}/options/reorder/
# ❌❌❌ this 2 api are not working for now!!!❌❌❌
# need to be fixed


urlpatterns = [
    # ============================================
    # Form Fields Management
    # ============================================

    # List and create field
    path(
        'forms/<slug:form_slug>/fields/',
        FormFieldViewSet.as_view({
            'get': 'list',  # List fields
            'post': 'create'  # Create new field
        }),
        name='field-list'
    ),

    # Reorder fields
    path(
        'forms/<slug:form_slug>/fields/reorder/',
        FormFieldViewSet.as_view({
            'post': 'reorder'
        }),
        name='field-reorder'
    ),

    # Field details, update, and delete
    path(
        'forms/<slug:form_slug>/fields/<uuid:id>/',
        FormFieldViewSet.as_view({
            'get': 'retrieve',  # Get field details
            'patch': 'partial_update',  # Partial update
            'put': 'update',  # Full update
            'delete': 'destroy'  # Delete field
        }),
        name='field-detail'
    ),

    # ============================================
    # Field Options Management (Select/Radio/Checkbox)
    # ============================================

    # List and create option
    path(
        'forms/<slug:form_slug>/fields/<uuid:field_id>/options/',
        FieldOptionViewSet.as_view({
            'get': 'list',  # List options
            'post': 'create'  # Create new option
        }),
        name='option-list'
    ),

    # Reorder options
    path(
        'forms/<slug:form_slug>/fields/<uuid:field_id>/options/reorder/',
        FieldOptionViewSet.as_view({
            'post': 'reorder'
        }),
        name='option-reorder'
    ),

    # Update and delete option
    path(
        'forms/<slug:form_slug>/fields/<uuid:field_id>/options/<uuid:id>/',
        FieldOptionViewSet.as_view({
            'get': 'retrieve',  # Get option details
            'patch': 'partial_update',  # Update option
            'delete': 'destroy'  # Delete option
        }),
        name='option-detail'
    ),
]



# ============================================
# Usage in main urls.py:
# ============================================
"""
# In your main project urls.py or api/v1/urls.py:

from django.urls import path, include

urlpatterns = [
    path('api/v1/', include('forms.urls')),
    # This will create URLs like:
    # /api/v1/forms/{slug}/fields/
    # /api/v1/forms/{slug}/fields/{id}/
    # etc.
]
"""

# ============================================
# Final URL examples:
# ============================================
"""
✅ Form Fields:
GET    /api/v1/forms/my-survey/fields/
POST   /api/v1/forms/my-survey/fields/
GET    /api/v1/forms/my-survey/fields/{uuid}/
PATCH  /api/v1/forms/my-survey/fields/{uuid}/
PUT    /api/v1/forms/my-survey/fields/{uuid}/
DELETE /api/v1/forms/my-survey/fields/{uuid}/

✅ Field Options:
GET    /api/v1/forms/my-survey/fields/{field_uuid}/options/
POST   /api/v1/forms/my-survey/fields/{field_uuid}/options/
GET    /api/v1/forms/my-survey/fields/{field_uuid}/options/{uuid}/
PATCH  /api/v1/forms/my-survey/fields/{field_uuid}/options/{uuid}/
DELETE /api/v1/forms/my-survey/fields/{field_uuid}/options/{uuid}/
POST   /api/v1/forms/my-survey/fields/{field_uuid}/options/reorder/
"""
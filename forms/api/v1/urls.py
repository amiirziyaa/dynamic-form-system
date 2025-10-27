from django.urls import path, include
from rest_framework.routers import DefaultRouter
from forms.views import FormViewSet, FormFieldViewSet, FieldOptionViewSet

app_name = 'forms'


router = DefaultRouter()
router.register(r'forms', FormViewSet, basename='form')


urlpatterns = [

    # List and create field
    path(
        'forms/<slug:form_slug>/fields/',
        FormFieldViewSet.as_view({
            'get': 'list',
            'post': 'create'
        }),
        name='field-list'
    ),

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
            'get': 'retrieve',
            'patch': 'partial_update',
            'put': 'update',
            'delete': 'destroy'
        }),
        name='field-detail'
    ),

    # List and create option
    path(
        'forms/<slug:form_slug>/fields/<uuid:field_id>/options/',
        FieldOptionViewSet.as_view({
            'get': 'list',
            'post': 'create'
        }),
        name='option-list'
    ),

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
            'get': 'retrieve',
            'patch': 'partial_update',
            'delete': 'destroy'
        }),
        name='option-detail'
    ),
]

urlpatterns = router.urls + urlpatterns
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import models

from .models import FormField, FieldOption, Form
from .serializers import (
    FormFieldSerializer,
    FormFieldListSerializer,
    FormFieldReorderSerializer,
    FieldOptionSerializer,
    FieldOptionReorderSerializer
)
from .permissions import IsFormOwner, CanManageFieldOptions


class FormFieldViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing form fields

    Endpoints:
    - GET    /api/v1/forms/{slug}/fields/
    - POST   /api/v1/forms/{slug}/fields/
    - GET    /api/v1/forms/{slug}/fields/{id}/
    - PATCH  /api/v1/forms/{slug}/fields/{id}/
    - DELETE /api/v1/forms/{slug}/fields/{id}/
    - POST   /api/v1/forms/{slug}/fields/reorder/
    """
    # permission_classes = [IsAuthenticated, IsFormOwner]
    lookup_field = 'id'

    def get_queryset(self):
        """Get fields for the specified form in URL"""
        form_slug = self.kwargs.get('form_slug')
        form = get_object_or_404(
            Form,
            unique_slug=form_slug,
            # user=self.request.user
        )
        return FormField.objects.filter(form=form).prefetch_related('options')

    def get_serializer_class(self):
        """Select serializer based on action"""
        if self.action == 'list':
            return FormFieldListSerializer
        elif self.action == 'reorder':
            return FormFieldReorderSerializer
        return FormFieldSerializer

    def get_form(self):
        """Get form from URL"""
        form_slug = self.kwargs.get('form_slug')
        return get_object_or_404(
            Form,
            unique_slug=form_slug,
            # user=self.request.user
        )

    def list(self, request, *args, **kwargs):
        """
        List all fields in a form
        GET /api/v1/forms/{slug}/fields/
        """
        queryset = self.get_queryset().order_by('order_index')
        serializer = self.get_serializer(queryset, many=True)

        return Response({
            'count': queryset.count(),
            'results': serializer.data
        })

    def create(self, request, *args, **kwargs):
        """
        Create new field
        POST /api/v1/forms/{slug}/fields/
        """
        form = self.get_form()

        # Add form to data
        data = request.data.copy()
        data['form'] = str(form.id)

        # If order_index not provided, assign last position
        if 'order_index' not in data:
            last_order = FormField.objects.filter(form=form).count()
            data['order_index'] = last_order

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    def retrieve(self, request, *args, **kwargs):
        """
        Get field details
        GET /api/v1/forms/{slug}/fields/{id}/
        """
        instance = self.get_object()
        serializer = FormFieldSerializer(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """
        Full field update
        PUT /api/v1/forms/{slug}/fields/{id}/
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        data = request.data.copy()
        data['form'] = str(instance.form.id)

        serializer = self.get_serializer(
            instance,
            data=data,
            partial=partial
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        """
        Partial field update
        PATCH /api/v1/forms/{slug}/fields/{id}/
        """
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        Delete field
        DELETE /api/v1/forms/{slug}/fields/{id}/
        """
        instance = self.get_object()
        form = instance.form
        order_index = instance.order_index

        # Delete field
        instance.delete()

        # Update order_index of subsequent fields
        FormField.objects.filter(
            form=form,
            order_index__gt=order_index
        ).update(order_index=models.F('order_index') - 1)

        return Response(
            {'message': 'Field deleted successfully'},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(detail=False, methods=['post'], url_path='reorder')
    def reorder(self, request, *args, **kwargs):
        """
        Reorder fields
        POST /api/v1/forms/{slug}/fields/reorder/

        Body: {
            "fields": [
                {"id": "uuid1", "order_index": 0},
                {"id": "uuid2", "order_index": 1}
            ]
        }
        """
        form = self.get_form()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        fields = serializer.save(form=form)

        return Response({
            'message': 'Fields reordered successfully',
            'fields': FormFieldListSerializer(fields, many=True).data
        })


class FieldOptionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing field options

    Endpoints:
    - GET    /api/v1/forms/{slug}/fields/{field_id}/options/
    - POST   /api/v1/forms/{slug}/fields/{field_id}/options/
    - PATCH  /api/v1/forms/{slug}/fields/{field_id}/options/{id}/
    - DELETE /api/v1/forms/{slug}/fields/{field_id}/options/{id}/
    - POST   /api/v1/forms/{slug}/fields/{field_id}/options/reorder/
    """
    serializer_class = FieldOptionSerializer
    # permission_classes = [IsAuthenticated, IsFormOwner]
    lookup_field = 'id'

    def get_queryset(self):
        """Get options for the specified field"""
        field = self.get_field()
        return FieldOption.objects.filter(field=field)

    def get_field(self):
        """Get field from URL"""
        form_slug = self.kwargs.get('form_slug')
        field_id = self.kwargs.get('field_id')

        form = get_object_or_404(
            Form,
            unique_slug=form_slug,
            # user=self.request.user
        )

        return get_object_or_404(
            FormField,
            id=field_id,
            form=form
        )

    def get_serializer_class(self):
        """Select serializer based on action"""
        if self.action == 'reorder':
            return FieldOptionReorderSerializer
        return FieldOptionSerializer

    def list(self, request, *args, **kwargs):
        """
        List all options for a field
        GET /api/v1/forms/{slug}/fields/{field_id}/options/
        """
        field = self.get_field()

        # Check field type
        if field.field_type not in ['select', 'radio', 'checkbox']:
            return Response(
                {'error': 'This field type cannot have options'},
                status=status.HTTP_400_BAD_REQUEST
            )

        queryset = self.get_queryset().order_by('order_index')
        serializer = self.get_serializer(queryset, many=True)

        return Response({
            'count': queryset.count(),
            'results': serializer.data
        })

    def create(self, request, *args, **kwargs):
        """
        Create new option
        POST /api/v1/forms/{slug}/fields/{field_id}/options/
        """
        field = self.get_field()

        # Check field type
        if field.field_type not in ['select', 'radio', 'checkbox']:
            return Response(
                {'error': 'This field type cannot have options'},
                status=status.HTTP_400_BAD_REQUEST
            )

        data = request.data.copy()

        # If order_index not provided
        if 'order_index' not in data:
            last_order = FieldOption.objects.filter(field=field).count()
            data['order_index'] = last_order

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(field=field)

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    def partial_update(self, request, *args, **kwargs):
        """
        Update option
        PATCH /api/v1/forms/{slug}/fields/{field_id}/options/{id}/
        """
        instance = self.get_object()
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """
        Delete option
        DELETE /api/v1/forms/{slug}/fields/{field_id}/options/{id}/
        """
        instance = self.get_object()
        field = instance.field
        order_index = instance.order_index

        # Delete option
        instance.delete()

        # Update order_index of subsequent options
        FieldOption.objects.filter(
            field=field,
            order_index__gt=order_index
        ).update(order_index=models.F('order_index') - 1)

        return Response(
            {'message': 'Option deleted successfully'},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(detail=False, methods=['post'], url_path='reorder')
    def reorder(self, request, *args, **kwargs):
        """
        Reorder options
        POST /api/v1/forms/{slug}/fields/{field_id}/options/reorder/

        Body: {
            "options": [
                {"id": "uuid1", "order_index": 0},
                {"id": "uuid2", "order_index": 1}
            ]
        }
        """
        field = self.get_field()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        options = serializer.save(field=field)

        return Response({
            'message': 'Options reordered successfully',
            'options': FieldOptionSerializer(options, many=True).data
        })
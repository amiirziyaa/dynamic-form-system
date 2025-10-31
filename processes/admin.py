from django.contrib import admin
from .models import Process, ProcessStep


@admin.register(Process)
class ProcessAdmin(admin.ModelAdmin):
    list_display = ['title', 'unique_slug', 'user', 'category', 'process_type', 'visibility', 'is_active', 'published_at', 'created_at']
    list_filter = ['process_type', 'visibility', 'is_active', 'created_at']
    search_fields = ['title', 'unique_slug', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at', 'published_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'user', 'category', 'title', 'description', 'unique_slug')
        }),
        ('Settings', {
            'fields': ('visibility', 'access_password', 'process_type', 'is_active', 'settings')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'published_at')
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user', 'category')


@admin.register(ProcessStep)
class ProcessStepAdmin(admin.ModelAdmin):
    list_display = ['title', 'process', 'form', 'order_index', 'is_required', 'created_at']
    list_filter = ['is_required', 'created_at']
    search_fields = ['title', 'description', 'process__title', 'form__title']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'process', 'form', 'title', 'description')
        }),
        ('Ordering', {
            'fields': ('order_index', 'is_required')
        }),
        ('Advanced', {
            'fields': ('conditions',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('process', 'form')

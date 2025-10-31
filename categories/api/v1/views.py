from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers

from categories.models import Category
from categories.services import CategoryService
from categories.serializers import (
    CategorySerializer,
    CategoryCreateSerializer,
    CategoryUpdateSerializer,
    CategoryListSerializer,
    CategoryWithStatsSerializer,
    CategoryStatsSerializer,
    CategoryBulkDeleteSerializer,
    CategorySearchSerializer,
    PaginatedCategorySerializer,
    PaginatedCategoryWithStatsSerializer
)
from categories.permissions import CategoryPermission


class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Category management.
    
    Provides CRUD operations for categories with proper authentication
    and ownership validation.
    """
    
    permission_classes = [CategoryPermission]
    lookup_field = 'id'
    
    def get_queryset(self):
        """Return categories for the authenticated user."""
        return Category.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return CategoryCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return CategoryUpdateSerializer
        elif self.action == 'list':
            return CategoryListSerializer
        elif self.action in ['retrieve', 'destroy']:
            return CategorySerializer
        elif self.action == 'stats':
            return CategoryStatsSerializer
        elif self.action == 'bulk_delete':
            return CategoryBulkDeleteSerializer
        elif self.action == 'search':
            return CategorySearchSerializer
        return CategorySerializer
    
    def get_service(self):
        """Get category service instance."""
        return CategoryService()
    
    def list(self, request):
        """
        List all categories for the authenticated user.
        
        Query Parameters:
        - page: Page number (default: 1)
        - page_size: Items per page (default: 20, max: 100)
        - search: Search query for name/description
        - include_stats: Include form/process counts (default: false)
        """
        serializer = CategorySearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        
        service = self.get_service()
        params = serializer.validated_data
        
        try:
            result = service.list_categories(
                user=request.user,
                page=params.get('page', 1),
                page_size=params.get('page_size', 20),
                search=params.get('search'),
                include_stats=params.get('include_stats', False)
            )
            
            if params.get('include_stats', False):
                response_serializer = PaginatedCategoryWithStatsSerializer(result)
            else:
                response_serializer = PaginatedCategorySerializer(result)
            
            return Response(response_serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def create(self, request):
        """
        Create a new category.
        
        Required fields:
        - name: Category name (2-255 characters)
        
        Optional fields:
        - description: Category description (max 1000 characters)
        - color: Hex color code (e.g., #FF5733)
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        service = self.get_service()
        
        try:
            category = service.create_category(
                user=request.user,
                name=serializer.validated_data['name'],
                description=serializer.validated_data.get('description'),
                color=serializer.validated_data.get('color')
            )
            
            response_serializer = CategorySerializer(category)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def retrieve(self, request, id=None):
        """
        Retrieve a specific category by ID.
        """
        service = self.get_service()
        
        try:
            category = service.get_category(request.user, id)
            serializer = CategorySerializer(category)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def update(self, request, id=None):
        """
        Update a category (full update).
        """
        service = self.get_service()
        
        try:
            category = service.update_category(
                user=request.user,
                category_id=id,
                name=request.data.get('name'),
                description=request.data.get('description'),
                color=request.data.get('color')
            )
            
            serializer = CategorySerializer(category)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def partial_update(self, request, id=None):
        """
        Partially update a category.
        """
        service = self.get_service()
        
        try:
            category = service.update_category(
                user=request.user,
                category_id=id,
                name=request.data.get('name'),
                description=request.data.get('description'),
                color=request.data.get('color')
            )
            
            serializer = CategorySerializer(category)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            if "not found" in str(e).lower():
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_404_NOT_FOUND
                )
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def destroy(self, request, id=None):
        """
        Delete a category.
        """
        service = self.get_service()
        
        try:
            success = service.delete_category(request.user, id)
            if success:
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response(
                    {'error': 'Failed to delete category'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['get'])
    def stats(self, request, id=None):
        """
        Get statistics for a specific category.
        """
        service = self.get_service()
        
        try:
            stats = service.get_category_stats(request.user, id)
            serializer = CategoryStatsSerializer(stats)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['post'])
    def bulk_delete(self, request):
        """
        Delete multiple categories at once.
        
        Required fields:
        - category_ids: List of category IDs to delete (max 50)
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        service = self.get_service()
        
        try:
            result = service.bulk_delete_categories(
                user=request.user,
                category_ids=serializer.validated_data['category_ids']
            )
            
            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def most_used(self, request):
        """
        Get most used categories by form/process count.
        
        Query Parameters:
        - limit: Maximum number of categories to return (default: 5, max: 20)
        """
        limit = min(int(request.query_params.get('limit', 5)), 20)
        
        service = self.get_service()
        
        try:
            categories = service.get_most_used_categories(request.user, limit)
            serializer = CategoryWithStatsSerializer(categories, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def forms(self, request, id=None):
        """
        List all forms in a specific category.
        
        This endpoint will be implemented when forms are ready.
        """
        return Response(
            {'message': 'Forms endpoint will be implemented when forms are ready'},
            status=status.HTTP_501_NOT_IMPLEMENTED
        )
    
    @action(detail=True, methods=['get'])
    def processes(self, request, id=None):
        """
        List all processes in a specific category.
        
        This endpoint will be implemented when processes are ready.
        """
        return Response(
            {'message': 'Processes endpoint will be implemented when processes are ready'},
            status=status.HTTP_501_NOT_IMPLEMENTED
        )

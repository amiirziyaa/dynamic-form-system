from rest_framework import serializers
from categories.models import Category


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for Category model.
    Used for basic CRUD operations.
    """
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'color', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_name(self, value):
        """Validate category name."""
        if not value or not value.strip():
            raise serializers.ValidationError("Category name is required")
        
        if len(value.strip()) > 255:
            raise serializers.ValidationError("Category name cannot exceed 255 characters")
        
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Category name must be at least 2 characters long")
        
        return value.strip()

    def validate_description(self, value):
        """Validate category description."""
        if value and len(value) > 1000:
            raise serializers.ValidationError("Category description cannot exceed 1000 characters")
        return value

    def validate_color(self, value):
        """Validate hex color code."""
        if not value:
            return value
        
        # Remove # if present
        color = value.strip().lstrip('#')
        
        # Validate hex color format
        if len(color) not in [3, 6]:
            raise serializers.ValidationError("Color must be a valid hex code (3 or 6 characters)")
        
        try:
            int(color, 16)
        except ValueError:
            raise serializers.ValidationError("Color must be a valid hex code")
        
        return f"#{color.upper()}"


class CategoryCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new categories.
    """
    
    class Meta:
        model = Category
        fields = ['name', 'description', 'color']

    def validate_name(self, value):
        """Validate category name."""
        if not value or not value.strip():
            raise serializers.ValidationError("Category name is required")
        
        if len(value.strip()) > 255:
            raise serializers.ValidationError("Category name cannot exceed 255 characters")
        
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Category name must be at least 2 characters long")
        
        return value.strip()

    def validate_description(self, value):
        """Validate category description."""
        if value and len(value) > 1000:
            raise serializers.ValidationError("Category description cannot exceed 1000 characters")
        return value

    def validate_color(self, value):
        """Validate hex color code."""
        if not value:
            return value
        
        # Remove # if present
        color = value.strip().lstrip('#')
        
        # Validate hex color format
        if len(color) not in [3, 6]:
            raise serializers.ValidationError("Color must be a valid hex code (3 or 6 characters)")
        
        try:
            int(color, 16)
        except ValueError:
            raise serializers.ValidationError("Color must be a valid hex code")
        
        return f"#{color.upper()}"


class CategoryUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating existing categories.
    All fields are optional for partial updates.
    """
    
    class Meta:
        model = Category
        fields = ['name', 'description', 'color']

    def validate_name(self, value):
        """Validate category name."""
        if value is not None:
            if not value or not value.strip():
                raise serializers.ValidationError("Category name cannot be empty")
            
            if len(value.strip()) > 255:
                raise serializers.ValidationError("Category name cannot exceed 255 characters")
            
            if len(value.strip()) < 2:
                raise serializers.ValidationError("Category name must be at least 2 characters long")
            
            return value.strip()
        return value

    def validate_description(self, value):
        """Validate category description."""
        if value is not None and len(value) > 1000:
            raise serializers.ValidationError("Category description cannot exceed 1000 characters")
        return value

    def validate_color(self, value):
        """Validate hex color code."""
        if value is not None:
            if not value:
                return None
            
            # Remove # if present
            color = value.strip().lstrip('#')
            
            # Validate hex color format
            if len(color) not in [3, 6]:
                raise serializers.ValidationError("Color must be a valid hex code (3 or 6 characters)")
            
            try:
                int(color, 16)
            except ValueError:
                raise serializers.ValidationError("Color must be a valid hex code")
            
            return f"#{color.upper()}"
        return value


class CategoryListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing categories.
    Includes basic information without sensitive data.
    """
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'color', 'created_at', 'updated_at']


class CategoryWithStatsSerializer(serializers.ModelSerializer):
    """
    Serializer for categories with statistics.
    Includes form and process counts.
    """
    forms_count = serializers.IntegerField(read_only=True, default=0)
    processes_count = serializers.IntegerField(read_only=True, default=0)
    total_items = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'color', 'forms_count', 
                 'processes_count', 'total_items', 'created_at', 'updated_at']
    
    def get_total_items(self, obj):
        """Calculate total items (forms + processes)."""
        return getattr(obj, 'forms_count', 0) + getattr(obj, 'processes_count', 0)


class CategoryStatsSerializer(serializers.Serializer):
    """
    Serializer for category statistics.
    """
    category_id = serializers.UUIDField()
    name = serializers.CharField()
    forms_count = serializers.IntegerField()
    processes_count = serializers.IntegerField()
    total_items = serializers.IntegerField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


class CategoryBulkDeleteSerializer(serializers.Serializer):
    """
    Serializer for bulk delete operations.
    """
    category_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=50,
        help_text="List of category IDs to delete (max 50)"
    )

    def validate_category_ids(self, value):
        """Validate category IDs list."""
        if not value:
            raise serializers.ValidationError("At least one category ID is required")
        
        if len(value) != len(set(value)):
            raise serializers.ValidationError("Duplicate category IDs are not allowed")
        
        return value


class CategorySearchSerializer(serializers.Serializer):
    """
    Serializer for category search parameters.
    """
    search = serializers.CharField(
        max_length=255,
        required=False,
        help_text="Search query for category name or description"
    )
    page = serializers.IntegerField(
        default=1,
        help_text="Page number (1-based)"
    )
    page_size = serializers.IntegerField(
        min_value=1,
        max_value=100,
        default=20,
        help_text="Number of items per page"
    )
    include_stats = serializers.BooleanField(
        default=False,
        help_text="Include form and process counts"
    )


class PaginatedCategorySerializer(serializers.Serializer):
    """
    Serializer for paginated category responses.
    """
    results = CategorySerializer(many=True)
    pagination = serializers.DictField()


class PaginatedCategoryWithStatsSerializer(serializers.Serializer):
    """
    Serializer for paginated category responses with statistics.
    """
    results = CategoryWithStatsSerializer(many=True)
    pagination = serializers.DictField()

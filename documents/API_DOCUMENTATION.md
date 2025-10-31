# Category Management API Documentation

## Overview

The Category Management API provides endpoints for managing organizational containers that group forms and processes. Categories help users organize their content and improve workflow management.

## Base URL

All category endpoints are prefixed with `/api/v1/categories/`

## Authentication

All endpoints require authentication via JWT token in the Authorization header:
```
Authorization: Bearer <your-jwt-token>
```

## Endpoints

### 1. List Categories

**GET** `/api/v1/categories/`

Retrieve all categories for the authenticated user.

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Page number (1-based) |
| `page_size` | integer | 20 | Items per page (max: 100) |
| `search` | string | - | Search query for name/description |
| `include_stats` | boolean | false | Include form/process counts |

#### Example Request
```bash
GET /api/v1/categories/?page=1&page_size=10&include_stats=true
```

#### Example Response
```json
{
  "results": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "HR Forms",
      "description": "Human resources related forms",
      "color": "#FF5733",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "pages": 1,
    "total": 1,
    "has_next": false,
    "has_previous": false,
    "next_page": null,
    "previous_page": null
  }
}
```

### 2. Create Category

**POST** `/api/v1/categories/`

Create a new category.

#### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Category name (2-255 characters) |
| `description` | string | No | Category description (max 1000 characters) |
| `color` | string | No | Hex color code (e.g., #FF5733) |

#### Example Request
```json
{
  "name": "Marketing Campaigns",
  "description": "Forms and processes for marketing campaigns",
  "color": "#3498DB"
}
```

#### Example Response
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "Marketing Campaigns",
  "description": "Forms and processes for marketing campaigns",
  "color": "#3498DB",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### 3. Retrieve Category

**GET** `/api/v1/categories/{id}/`

Get a specific category by ID.

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | UUID | Category ID |

#### Example Response
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "Marketing Campaigns",
  "description": "Forms and processes for marketing campaigns",
  "color": "#3498DB",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### 4. Update Category

**PUT** `/api/v1/categories/{id}/` (Full update)
**PATCH** `/api/v1/categories/{id}/` (Partial update)

Update an existing category.

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | UUID | Category ID |

#### Request Body (PUT - Full Update)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Category name (2-255 characters) |
| `description` | string | No | Category description (max 1000 characters) |
| `color` | string | No | Hex color code |

#### Request Body (PATCH - Partial Update)

All fields are optional for partial updates.

#### Example Request (PATCH)
```json
{
  "name": "Updated Marketing Campaigns",
  "color": "#E74C3C"
}
```

#### Example Response
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "Updated Marketing Campaigns",
  "description": "Forms and processes for marketing campaigns",
  "color": "#E74C3C",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T11:45:00Z"
}
```

### 5. Delete Category

**DELETE** `/api/v1/categories/{id}/`

Delete a category.

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | UUID | Category ID |

#### Response
- **204 No Content** - Category deleted successfully

### 6. Get Category Statistics

**GET** `/api/v1/categories/{id}/stats/`

Get statistics for a specific category.

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | UUID | Category ID |

#### Example Response
```json
{
  "category_id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "Marketing Campaigns",
  "forms_count": 5,
  "processes_count": 3,
  "total_items": 8,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T11:45:00Z"
}
```

### 7. Bulk Delete Categories

**POST** `/api/v1/categories/bulk_delete/`

Delete multiple categories at once.

#### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `category_ids` | array | Yes | List of category IDs (max 50) |

#### Example Request
```json
{
  "category_ids": [
    "123e4567-e89b-12d3-a456-426614174000",
    "987fcdeb-51a2-43d1-b456-426614174000"
  ]
}
```

#### Example Response
```json
{
  "deleted_count": 2,
  "requested_count": 2,
  "success": true
}
```

### 8. Get Most Used Categories

**GET** `/api/v1/categories/most_used/`

Get most used categories by form/process count.

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 5 | Maximum number of categories (max: 20) |

#### Example Request
```bash
GET /api/v1/categories/most_used/?limit=10
```

#### Example Response
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "HR Forms",
    "description": "Human resources related forms",
    "color": "#FF5733",
    "forms_count": 15,
    "processes_count": 8,
    "total_items": 23,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
]
```

### 9. List Forms in Category

**GET** `/api/v1/categories/{id}/forms/`

List all forms in a specific category.

**Note**: This endpoint will be implemented when forms are ready.

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | UUID | Category ID |

#### Response
- **501 Not Implemented** - Endpoint not yet available

### 10. List Processes in Category

**GET** `/api/v1/categories/{id}/processes/`

List all processes in a specific category.

**Note**: This endpoint will be implemented when processes are ready.

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | UUID | Category ID |

#### Response
- **501 Not Implemented** - Endpoint not yet available

## Error Responses

### 400 Bad Request
```json
{
  "error": "Category name is required"
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 404 Not Found
```json
{
  "error": "Category not found"
}
```

### 500 Internal Server Error
```json
{
  "error": "Failed to create category: Database error"
}
```

## Validation Rules

### Category Name
- Required field
- Minimum length: 2 characters
- Maximum length: 255 characters
- Must be unique per user
- Case-insensitive uniqueness check

### Category Description
- Optional field
- Maximum length: 1000 characters
- Can be empty or null

### Category Color
- Optional field
- Must be valid hex color code
- Format: #RRGGBB or #RGB
- Automatically converted to uppercase
- Examples: #FF5733, #3498DB, #2ECC71

## Business Rules

1. **Ownership**: Users can only access their own categories
2. **Uniqueness**: Category names must be unique per user (case-insensitive)
3. **Bulk Operations**: Maximum 50 categories can be deleted at once
4. **Search**: Search works on both name and description fields
5. **Pagination**: Default page size is 20, maximum is 100
6. **Statistics**: Form and process counts are calculated in real-time

## Rate Limiting

- No specific rate limits implemented
- Standard API rate limiting applies

## Caching

- Category lists are cached for 5 minutes
- Individual category details are cached for 30 minutes
- Statistics are cached for 5 minutes

## Examples

### Complete Workflow Example

1. **Create a category**:
```bash
curl -X POST /api/v1/categories/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Customer Feedback", "description": "Forms for collecting customer feedback", "color": "#E74C3C"}'
```

2. **List categories with statistics**:
```bash
curl -X GET "/api/v1/categories/?include_stats=true" \
  -H "Authorization: Bearer <token>"
```

3. **Update category**:
```bash
curl -X PATCH /api/v1/categories/123e4567-e89b-12d3-a456-426614174000/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Customer Feedback & Support"}'
```

4. **Get category statistics**:
```bash
curl -X GET /api/v1/categories/123e4567-e89b-12d3-a456-426614174000/stats/ \
  -H "Authorization: Bearer <token>"
```

5. **Delete category**:
```bash
curl -X DELETE /api/v1/categories/123e4567-e89b-12d3-a456-426614174000/ \
  -H "Authorization: Bearer <token>"
```

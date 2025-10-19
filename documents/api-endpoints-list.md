# Dynamic Forms System - API Endpoints

## API Versioning Strategy

**Base URL Structure**: `/api/v{version}/{resource}/`

**Current Version**: `v1`

**Versioning Approach**: URL-based versioning (most common and explicit)

### Why URL Versioning?
- ✅ Clear and explicit in URLs
- ✅ Easy to cache and proxy
- ✅ Simple for clients to understand
- ✅ Backward compatibility support
- ✅ Can run multiple versions simultaneously

### Version Lifecycle
- **v1** - Current stable version
- **v2** - Future major changes (breaking changes only)
- Deprecated versions will be marked and supported for 6-12 months

---

## 1. Authentication & User Management

### Authentication
- `POST /api/v1/auth/register/` - Register new user
- `POST /api/v1/auth/login/` - Login with email/password
- `POST /api/v1/auth/logout/` - Logout user
- `POST /api/v1/auth/refresh/` - Refresh JWT token
- `POST /api/v1/auth/otp/send/` - Send OTP to phone
- `POST /api/v1/auth/otp/verify/` - Verify OTP code
- `POST /api/v1/auth/password/reset/` - Request password reset
- `POST /api/v1/auth/password/reset/confirm/` - Confirm password reset
- `POST /api/v1/auth/oauth/google/` - OAuth login with Google (bonus)

### User Profile
- `GET /api/v1/users/me/` - Get current user profile
- `PATCH /api/v1/users/me/` - Update user profile
- `POST /api/v1/users/me/verify-email/` - Send email verification
- `GET /api/v1/users/me/verify-email/{token}/` - Verify email with token

---

## 2. Category Management

- `GET /api/v1/categories/` - List all user's categories
- `POST /api/v1/categories/` - Create new category
- `GET /api/v1/categories/{id}/` - Get category details
- `PATCH /api/v1/categories/{id}/` - Update category
- `DELETE /api/v1/categories/{id}/` - Delete category
- `GET /api/v1/categories/{id}/forms/` - List all forms in category
- `GET /api/v1/categories/{id}/processes/` - List all processes in category

---

## 3. Form Management

### CRUD Operations
- `GET /api/v1/forms/` - List all user's forms (with filters)
- `POST /api/v1/forms/` - Create new form
- `GET /api/v1/forms/{slug}/` - Get form details by slug
- `PATCH /api/v1/forms/{slug}/` - Update form
- `DELETE /api/v1/forms/{slug}/` - Delete form
- `POST /api/v1/forms/{slug}/duplicate/` - Duplicate existing form
- `PATCH /api/v1/forms/{slug}/publish/` - Publish/unpublish form

### Form Fields Management
- `GET /api/v1/forms/{slug}/fields/` - List all fields in form
- `POST /api/v1/forms/{slug}/fields/` - Add field to form
- `GET /api/v1/forms/{slug}/fields/{id}/` - Get field details
- `PATCH /api/v1/forms/{slug}/fields/{id}/` - Update field
- `DELETE /api/v1/forms/{slug}/fields/{id}/` - Delete field
- `POST /api/v1/forms/{slug}/fields/reorder/` - Reorder fields (bulk update)

### Field Options (for Select/Radio/Checkbox)
- `GET /api/v1/forms/{slug}/fields/{field_id}/options/` - List field options
- `POST /api/v1/forms/{slug}/fields/{field_id}/options/` - Add option
- `PATCH /api/v1/forms/{slug}/fields/{field_id}/options/{id}/` - Update option
- `DELETE /api/v1/forms/{slug}/fields/{field_id}/options/{id}/` - Delete option
- `POST /api/v1/forms/{slug}/fields/{field_id}/options/reorder/` - Reorder options

---

## 4. Form Submissions (Public Access)

### Viewing Forms
- `GET /api/v1/public/forms/{slug}/` - Get public form structure
- `POST /api/v1/public/forms/{slug}/verify-password/` - Verify private form password
- `POST /api/v1/public/forms/{slug}/view/` - Track form view

### Submitting Responses
- `POST /api/v1/public/forms/{slug}/submit/` - Submit form response
- `POST /api/v1/public/forms/{slug}/submissions/draft/` - Save draft submission
- `GET /api/v1/public/forms/{slug}/submissions/draft/{session_id}/` - Get draft
- `PATCH /api/v1/public/forms/{slug}/submissions/draft/{session_id}/` - Update draft

---

## 5. Submission Management (Owner)

### View Submissions
- `GET /api/v1/forms/{slug}/submissions/` - List all submissions for form
- `GET /api/v1/forms/{slug}/submissions/{id}/` - Get submission details
- `DELETE /api/v1/forms/{slug}/submissions/{id}/` - Delete submission
- `POST /api/v1/forms/{slug}/submissions/export/` - Export submissions (CSV/JSON)
- `GET /api/v1/forms/{slug}/submissions/stats/` - Get submission statistics

### Bulk Operations
- `POST /api/v1/forms/{slug}/submissions/bulk-delete/` - Delete multiple submissions
- `POST /api/v1/forms/{slug}/submissions/bulk-export/` - Export filtered submissions

---

## 6. Form Analytics & Reporting

### Statistics
- `GET /api/v1/forms/{slug}/analytics/` - Get form analytics overview
- `GET /api/v1/forms/{slug}/analytics/views/` - View count over time
- `GET /api/v1/forms/{slug}/analytics/submissions/` - Submission count over time
- `GET /api/v1/forms/{slug}/analytics/completion-rate/` - Calculate completion rate
- `GET /api/v1/forms/{slug}/analytics/drop-off/` - Analyze drop-off points

### Aggregated Reports
- `GET /api/v1/forms/{slug}/reports/summary/` - Summary report with aggregations
- `GET /api/v1/forms/{slug}/reports/field/{field_id}/` - Field-specific report
- `GET /api/v1/forms/{slug}/reports/real-time/` - Real-time report data (WebSocket)

### Real-time Updates (WebSocket)
- `WS /ws/v1/forms/{slug}/reports/live/` - Live report updates

---

## 7. Process Management

### CRUD Operations
- `GET /api/v1/processes/` - List all user's processes
- `POST /api/v1/processes/` - Create new process
- `GET /api/v1/processes/{slug}/` - Get process details
- `PATCH /api/v1/processes/{slug}/` - Update process
- `DELETE /api/v1/processes/{slug}/` - Delete process
- `POST /api/v1/processes/{slug}/duplicate/` - Duplicate process
- `PATCH /api/v1/processes/{slug}/publish/` - Publish/unpublish process

### Process Steps Management
- `GET /api/v1/processes/{slug}/steps/` - List all steps
- `POST /api/v1/processes/{slug}/steps/` - Add step to process
- `GET /api/v1/processes/{slug}/steps/{id}/` - Get step details
- `PATCH /api/v1/processes/{slug}/steps/{id}/` - Update step
- `DELETE /api/v1/processes/{slug}/steps/{id}/` - Delete step
- `POST /api/v1/processes/{slug}/steps/reorder/` - Reorder steps

---

## 8. Process Execution (Public Access)

### Starting & Viewing Process
- `GET /api/v1/public/processes/{slug}/` - Get public process structure
- `POST /api/v1/public/processes/{slug}/verify-password/` - Verify password
- `POST /api/v1/public/processes/{slug}/start/` - Start new process progress
- `POST /api/v1/public/processes/{slug}/view/` - Track process view

### Progress Tracking
- `GET /api/v1/public/processes/{slug}/progress/{session_id}/` - Get user progress
- `GET /api/v1/public/processes/{slug}/progress/{session_id}/current-step/` - Get current step
- `POST /api/v1/public/processes/{slug}/progress/{session_id}/next/` - Move to next step (linear)
- `POST /api/v1/public/processes/{slug}/progress/{session_id}/previous/` - Go to previous step

### Step Completion
- `POST /api/v1/public/processes/{slug}/steps/{step_id}/complete/` - Complete step with submission
- `GET /api/v1/public/processes/{slug}/steps/{step_id}/form/` - Get form for step
- `POST /api/v1/public/processes/{slug}/complete/` - Mark process as completed

---

## 9. Process Analytics (Owner)

### Statistics
- `GET /api/v1/processes/{slug}/analytics/` - Process analytics overview
- `GET /api/v1/processes/{slug}/analytics/views/` - View count over time
- `GET /api/v1/processes/{slug}/analytics/completions/` - Completion count over time
- `GET /api/v1/processes/{slug}/analytics/completion-rate/` - Overall completion rate
- `GET /api/v1/processes/{slug}/analytics/step-drop-off/` - Drop-off by step
- `GET /api/v1/processes/{slug}/analytics/average-time/` - Average completion time

### Progress Tracking
- `GET /api/v1/processes/{slug}/progress/` - List all progress records
- `GET /api/v1/processes/{slug}/progress/{id}/` - Get specific progress details
- `GET /api/v1/processes/{slug}/progress/abandoned/` - List abandoned processes

---

## 10. Dashboard & Overview

### User Dashboard
- `GET /api/v1/dashboard/overview/` - Get user dashboard overview
- `GET /api/v1/dashboard/recent-activity/` - Recent forms and processes
- `GET /api/v1/dashboard/statistics/` - Aggregated user statistics

### Search & Filter
- `GET /api/v1/search/` - Global search across forms and processes
- `GET /api/v1/search/forms/` - Search in forms only
- `GET /api/v1/search/processes/` - Search in processes only

---

## 11. Admin Reports (Periodic & Scheduled)

### Report Configuration
- `GET /api/v1/admin/reports/config/` - Get current report configuration
- `POST /api/v1/admin/reports/config/` - Create report schedule
- `PATCH /api/v1/admin/reports/config/{id}/` - Update report schedule
- `DELETE /api/v1/admin/reports/config/{id}/` - Delete report schedule

### Manual Reports
- `POST /api/v1/admin/reports/generate/` - Generate report manually
- `GET /api/v1/admin/reports/history/` - List generated reports
- `GET /api/v1/admin/reports/{id}/download/` - Download generated report

### Webhook Configuration
- `POST /api/v1/admin/webhooks/` - Create webhook for reports
- `GET /api/v1/admin/webhooks/` - List webhooks
- `PATCH /api/v1/admin/webhooks/{id}/` - Update webhook
- `DELETE /api/v1/admin/webhooks/{id}/` - Delete webhook
- `POST /api/v1/admin/webhooks/{id}/test/` - Test webhook

---

## 12. System & Health

- `GET /api/v1/health/` - Health check endpoint
- `GET /api/v1/version/` - API version information
- `GET /api/v1/docs/` - API documentation (Swagger/ReDoc)
- `GET /api/v1/schema/` - OpenAPI schema

---

## Version Management

### Version Information Endpoint
The `/api/v1/version/` endpoint returns:
```json
{
  "version": "1.0.0",
  "api_version": "v1",
  "deprecated": false,
  "sunset_date": null,
  "latest_version": "v1",
  "supported_versions": ["v1"],
  "changelog_url": "https://api.example.com/changelog"
}
```

### Deprecation Headers
When a version is deprecated, responses include:
```
Sunset: Sat, 31 Dec 2024 23:59:59 GMT
Deprecation: true
Link: <https://api.example.com/v2/>; rel="successor-version"
```

### Migration Strategy
When introducing breaking changes (v2):
1. Announce deprecation 6 months in advance
2. Run v1 and v2 simultaneously for transition period
3. Provide migration guide and tooling
4. Maintain v1 for minimum 6 months after v2 release
5. Send deprecation warnings in API responses

### Backward Compatibility Rules
Within same major version (v1.x):
- ✅ Can add new endpoints
- ✅ Can add new optional fields
- ✅ Can add new response fields
- ❌ Cannot remove endpoints
- ❌ Cannot remove request/response fields
- ❌ Cannot change field types
- ❌ Cannot make optional fields required

Breaking changes require new major version (v2)

---

## Implementation in Django

### URL Configuration Structure
```python
# urls.py
urlpatterns = [
    path('api/v1/', include('api.v1.urls')),
    # Future versions
    # path('api/v2/', include('api.v2.urls')),
]
```

### Version-specific ViewSets
```python
# api/v1/views/forms.py
class FormViewSetV1(viewsets.ModelViewSet):
    # v1 implementation
    pass

# api/v2/views/forms.py (future)
class FormViewSetV2(viewsets.ModelViewSet):
    # v2 with breaking changes
    pass
```

### Content Negotiation (Alternative)
If needed, also support header-based versioning:
```
Accept: application/vnd.dynamicforms.v1+json
```

But URL versioning remains primary method.

---

### Core Features Count:
- **Authentication**: 10 endpoints
- **Categories**: 7 endpoints
- **Forms CRUD**: 8 endpoints
- **Form Fields**: 11 endpoints
- **Public Form Access**: 6 endpoints
- **Form Submissions**: 9 endpoints
- **Form Analytics**: 10 endpoints (+ 1 WebSocket)
- **Processes CRUD**: 8 endpoints
- **Process Steps**: 7 endpoints
- **Process Execution**: 10 endpoints
- **Process Analytics**: 9 endpoints
- **Dashboard**: 5 endpoints
- **Admin Reports**: 11 endpoints
- **System**: 4 endpoints

**Total: ~115 REST endpoints + 1 WebSocket endpoint**

---

## HTTP Methods Summary

- `GET` - Retrieve data
- `POST` - Create new resource or trigger action
- `PATCH` - Partial update
- `DELETE` - Remove resource
- `WS` - WebSocket connection

---

## Authentication Requirements

- 🔓 **Public**: `/api/public/*` - No authentication required
- 🔐 **Authenticated**: All other endpoints require JWT token
- 👑 **Owner Only**: User must own the resource (form/process)
- 🛡️ **Admin Only**: `/api/admin/*` - Requires staff permissions

---

## Query Parameters (Common)

- `page` - Pagination page number
- `page_size` - Items per page
- `search` - Search query
- `category` - Filter by category
- `visibility` - Filter by public/private
- `is_active` - Filter by active status
- `ordering` - Sort field (e.g., `-created_at`)
- `date_from` - Filter from date
- `date_to` - Filter to date
# Dynamic Forms System

A comprehensive RESTful API system for creating, managing, and monitoring dynamic forms and multi-step processes. Built with Django REST Framework, featuring real-time analytics, WebSocket support, and advanced form submission tracking.

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.2.7-green.svg)](https://www.djangoproject.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📋 Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Prerequisites](#-prerequisites)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
  - [Local Development](#local-development)
  - [Docker Setup](#docker-setup)
- [Configuration](#-configuration)
- [API Documentation](#-api-documentation)
- [Authentication](#-authentication)
- [API Endpoints](#-api-endpoints)
- [Examples](#-examples)
- [Development](#-development)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Project Structure](#-project-structure)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Features

### Core Functionality
- **Dynamic Form Builder**: Create forms with multiple field types (text, number, email, select, checkbox, radio, textarea, date, file)
- **Process Management**: Build linear or free-form multi-step processes combining multiple forms
- **Category Organization**: Organize forms and processes into custom categories with color coding
- **Access Control**: Public forms or password-protected private forms
- **Draft Submissions**: Save and resume form submissions later
- **Session Management**: Support for both authenticated and anonymous submissions

### Analytics & Reporting
- **Real-time Analytics**: WebSocket-based live analytics for form views and submissions
- **Advanced Reporting**: Aggregate data, completion rates, drop-off analysis
- **Export Functionality**: Export submissions as CSV, JSON, or Excel
- **Process Analytics**: Track progress through multi-step processes
- **Dashboard**: Overview statistics, recent activity, and search functionality

### Authentication & Security
- **JWT Authentication**: Secure token-based authentication
- **Email/Password Login**: Traditional authentication method
- **Google OAuth**: Social authentication via Google
- **OTP Verification**: Two-factor authentication via SMS
- **Password Reset**: Secure password recovery flow
- **Email Verification**: Account verification via email

### Admin Features
- **Webhook Management**: Configure webhooks for form events
- **Scheduled Reports**: Automated report generation and delivery
- **Bulk Operations**: Bulk delete and export submissions
- **User Management**: Full user profile management

---

## 🛠️ Tech Stack

### Backend
- **Django 5.2.7** - Web framework
- **Django REST Framework 3.16.1** - API toolkit
- **PostgreSQL** - Database
- **Redis** - Caching and message broker
- **Celery 5.5.3** - Async task processing
- **Django Channels 4.3.1** - WebSocket support
- **Daphne 4.2.1** - ASGI server

### Authentication & Social
- **djangorestframework-simplejwt 5.5.1** - JWT authentication
- **django-allauth 65.13.0** - Social authentication
- **dj-rest-auth 7.0.1** - REST API authentication

### API Documentation
- **drf-spectacular 0.28.0** - OpenAPI 3.0 schema generation
- **Swagger UI** - Interactive API documentation
- **ReDoc** - Alternative API documentation

### Development Tools
- **Python Decouple** - Environment variable management
- **Docker & Docker Compose** - Containerization

---

## 📦 Prerequisites

- **Python 3.12+**
- **PostgreSQL 12+**
- **Redis 7+**
- **Docker & Docker Compose** (optional, for containerized setup)
- **Git**

---

## 🚀 Quick Start

### Using Docker (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd dynamic-form-system

# Copy and configure environment variables
cp .env.example .env
# Edit .env with your settings

# Build and start services
make build
make up

# Run migrations and create superuser
make migrate
make createsuperuser

# Access the API
# - API: http://localhost:8001
# - Swagger UI: http://localhost:8001/api/v1/swagger/
# - ReDoc: http://localhost:8001/api/v1/redoc/
```

### Local Development

```bash
# Clone and setup
git clone <repository-url>
cd dynamic-form-system
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure database and environment
# Edit .env file with your settings

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
ENVIRONMENT=development

# Database
DB_NAME=dynamicformdb
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Email (for production, use SMTP)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@dynamicforms.com

# Frontend
FRONTEND_URL=http://localhost:3000

# Google OAuth (optional)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# API
API_VERSION=1.0.0
```

---

## 📚 API Documentation

### Interactive Documentation

Once the server is running, access the interactive API documentation:

- **Swagger UI**: `http://localhost:8000/api/v1/swagger/`
- **ReDoc**: `http://localhost:8000/api/v1/redoc/`
- **OpenAPI Schema**: `http://localhost:8000/api/v1/schema/`

### API Base URL

All API endpoints are versioned under `/api/v1/`:

```
Base URL: http://localhost:8000/api/v1/
```

---

## 🔐 Authentication

### JWT Authentication

The API uses JWT (JSON Web Tokens) for authentication. Include the token in the `Authorization` header:

```bash
Authorization: Bearer <access_token>
```

### Getting JWT Tokens

**1. Register a new user:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123",
    "password_confirm": "securepassword123",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

**2. Login:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe"
  }
}
```

**3. Google OAuth:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/oauth/google/ \
  -H "Content-Type: application/json" \
  -d '{
    "access_token": "ya29.a0AfH6SMBxxxxx"
  }'
```

**4. Refresh Token:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "your_refresh_token_here"
  }'
```

For detailed Google OAuth examples, see [GOOGLE_OAUTH_CURL.md](documents/GOOGLE_OAUTH_CURL.md)

---

## 🔌 API Endpoints

### Authentication & User Management

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `POST` | `/api/v1/auth/register/` | Register new user | ❌ |
| `POST` | `/api/v1/auth/login/` | Login with email/password | ❌ |
| `POST` | `/api/v1/auth/logout/` | Logout user | ✅ |
| `POST` | `/api/v1/auth/refresh/` | Refresh JWT token | ❌ |
| `POST` | `/api/v1/auth/otp/send/` | Send OTP to phone | ❌ |
| `POST` | `/api/v1/auth/otp/verify/` | Verify OTP code | ❌ |
| `POST` | `/api/v1/auth/password/reset/` | Request password reset | ❌ |
| `POST` | `/api/v1/auth/password/reset/confirm/` | Confirm password reset | ❌ |
| `POST` | `/api/v1/auth/oauth/google/` | Google OAuth login | ❌ |
| `GET` | `/api/v1/users/me/` | Get current user profile | ✅ |
| `PATCH` | `/api/v1/users/me/` | Update user profile | ✅ |
| `POST` | `/api/v1/users/me/verify-email/` | Send email verification | ✅ |
| `GET` | `/api/v1/users/me/verify-email/{token}/` | Verify email with token | ✅ |

### Category Management

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET` | `/api/v1/categories/` | List all user's categories | ✅ |
| `POST` | `/api/v1/categories/` | Create new category | ✅ |
| `GET` | `/api/v1/categories/{id}/` | Get category details | ✅ |
| `PATCH` | `/api/v1/categories/{id}/` | Update category | ✅ |
| `DELETE` | `/api/v1/categories/{id}/` | Delete category | ✅ |
| `GET` | `/api/v1/categories/{id}/forms/` | List forms in category | ✅ |
| `GET` | `/api/v1/categories/{id}/processes/` | List processes in category | ✅ |
| `GET` | `/api/v1/categories/{id}/stats/` | Get category statistics | ✅ |
| `POST` | `/api/v1/categories/bulk-delete/` | Bulk delete categories | ✅ |
| `GET` | `/api/v1/categories/most-used/` | Get most used categories | ✅ |

### Form Management

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET` | `/api/v1/forms/` | List all user's forms | ✅ |
| `POST` | `/api/v1/forms/` | Create new form | ✅ |
| `GET` | `/api/v1/forms/{slug}/` | Get form details | ✅ |
| `PATCH` | `/api/v1/forms/{slug}/` | Update form | ✅ |
| `DELETE` | `/api/v1/forms/{slug}/` | Delete form | ✅ |
| `POST` | `/api/v1/forms/{slug}/duplicate/` | Duplicate form | ✅ |
| `PATCH` | `/api/v1/forms/{slug}/publish/` | Publish/unpublish form | ✅ |
| `GET` | `/api/v1/forms/{slug}/fields/` | List form fields | ✅ |
| `POST` | `/api/v1/forms/{slug}/fields/` | Add field to form | ✅ |
| `GET` | `/api/v1/forms/{slug}/fields/{id}/` | Get field details | ✅ |
| `PATCH` | `/api/v1/forms/{slug}/fields/{id}/` | Update field | ✅ |
| `DELETE` | `/api/v1/forms/{slug}/fields/{id}/` | Delete field | ✅ |
| `POST` | `/api/v1/forms/{slug}/fields/reorder/` | Reorder fields | ✅ |
| `GET` | `/api/v1/forms/{slug}/fields/{field_id}/options/` | List field options | ✅ |
| `POST` | `/api/v1/forms/{slug}/fields/{field_id}/options/` | Add option | ✅ |
| `PATCH` | `/api/v1/forms/{slug}/fields/{field_id}/options/{id}/` | Update option | ✅ |
| `DELETE` | `/api/v1/forms/{slug}/fields/{field_id}/options/{id}/` | Delete option | ✅ |
| `POST` | `/api/v1/forms/{slug}/fields/{field_id}/options/reorder/` | Reorder options | ✅ |

### Public Form Access

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET` | `/api/v1/public/forms/{slug}/` | Get public form structure | ❌ |
| `POST` | `/api/v1/public/forms/{slug}/verify-password/` | Verify private form password | ❌ |
| `POST` | `/api/v1/public/forms/{slug}/view/` | Track form view | ❌ |
| `POST` | `/api/v1/public/forms/{slug}/submit/` | Submit form response | ❌ |
| `POST` | `/api/v1/public/forms/{slug}/submissions/draft/` | Save draft | ❌ |
| `GET` | `/api/v1/public/forms/{slug}/submissions/draft/{session_id}/` | Get draft | ❌ |
| `PATCH` | `/api/v1/public/forms/{slug}/submissions/draft/{session_id}/` | Update draft | ❌ |

### Submission Management (Owner)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET` | `/api/v1/forms/{slug}/submissions/` | List submissions | ✅ |
| `GET` | `/api/v1/forms/{slug}/submissions/{id}/` | Get submission details | ✅ |
| `DELETE` | `/api/v1/forms/{slug}/submissions/{id}/` | Delete submission | ✅ |
| `GET` | `/api/v1/forms/{slug}/submissions/stats/` | Get submission statistics | ✅ |
| `POST` | `/api/v1/forms/{slug}/submissions/export/` | Export submissions | ✅ |
| `POST` | `/api/v1/forms/{slug}/submissions/bulk-delete/` | Bulk delete submissions | ✅ |
| `POST` | `/api/v1/forms/{slug}/submissions/bulk-export/` | Bulk export submissions | ✅ |

### Process Management

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET` | `/api/v1/processes/` | List all user's processes | ✅ |
| `POST` | `/api/v1/processes/` | Create new process | ✅ |
| `GET` | `/api/v1/processes/{slug}/` | Get process details | ✅ |
| `PATCH` | `/api/v1/processes/{slug}/` | Update process | ✅ |
| `DELETE` | `/api/v1/processes/{slug}/` | Delete process | ✅ |
| `POST` | `/api/v1/processes/{slug}/duplicate/` | Duplicate process | ✅ |
| `PATCH` | `/api/v1/processes/{slug}/publish/` | Publish/unpublish process | ✅ |
| `GET` | `/api/v1/processes/{slug}/steps/` | List process steps | ✅ |
| `POST` | `/api/v1/processes/{slug}/steps/` | Add step to process | ✅ |
| `GET` | `/api/v1/processes/{slug}/steps/{id}/` | Get step details | ✅ |
| `PATCH` | `/api/v1/processes/{slug}/steps/{id}/` | Update step | ✅ |
| `DELETE` | `/api/v1/processes/{slug}/steps/{id}/` | Delete step | ✅ |
| `POST` | `/api/v1/processes/{slug}/steps/reorder/` | Reorder steps | ✅ |

### Public Process Execution

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET` | `/api/v1/public/processes/{slug}/` | Get public process structure | ❌ |
| `POST` | `/api/v1/public/processes/{slug}/verify-password/` | Verify private process password | ❌ |
| `POST` | `/api/v1/public/processes/{slug}/view/` | Track process view | ❌ |
| `POST` | `/api/v1/public/processes/{slug}/start/` | Start process execution | ❌ |
| `GET` | `/api/v1/public/processes/{slug}/progress/{progress_id}/` | Get progress details | ❌ |
| `GET` | `/api/v1/public/processes/{slug}/progress/{progress_id}/current-step/` | Get current step | ❌ |
| `POST` | `/api/v1/public/processes/{slug}/progress/{progress_id}/next/` | Move to next step | ❌ |
| `POST` | `/api/v1/public/processes/{slug}/progress/{progress_id}/previous/` | Move to previous step | ❌ |
| `GET` | `/api/v1/public/processes/{slug}/progress/{progress_id}/step/{step_id}/form/` | Get step form | ❌ |
| `POST` | `/api/v1/public/processes/{slug}/progress/{progress_id}/step/{step_id}/complete/` | Complete step | ❌ |
| `POST` | `/api/v1/public/processes/{slug}/progress/{progress_id}/complete/` | Complete process | ❌ |

### Process Analytics

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET` | `/api/v1/processes/{slug}/analytics/overview/` | Get analytics overview | ✅ |
| `GET` | `/api/v1/processes/{slug}/analytics/views/` | Get views analytics | ✅ |
| `GET` | `/api/v1/processes/{slug}/analytics/completions/` | Get completions analytics | ✅ |
| `GET` | `/api/v1/processes/{slug}/analytics/completion-rate/` | Get completion rate | ✅ |
| `GET` | `/api/v1/processes/{slug}/analytics/step-drop-off/` | Get step drop-off analysis | ✅ |
| `GET` | `/api/v1/processes/{slug}/analytics/average-time/` | Get average completion time | ✅ |
| `GET` | `/api/v1/processes/{slug}/progress/` | List all progress records | ✅ |
| `GET` | `/api/v1/processes/{slug}/progress/{progress_id}/` | Get progress details | ✅ |
| `GET` | `/api/v1/processes/{slug}/abandoned/` | List abandoned progress | ✅ |

### Form Analytics

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET` | `/api/v1/forms/{slug}/analytics/overview/` | Get analytics overview | ✅ |
| `GET` | `/api/v1/forms/{slug}/analytics/views/timeseries/` | Get views time series | ✅ |
| `GET` | `/api/v1/forms/{slug}/analytics/submissions/timeseries/` | Get submissions time series | ✅ |
| `GET` | `/api/v1/forms/{slug}/analytics/completion-rate/` | Get completion rate | ✅ |
| `GET` | `/api/v1/forms/{slug}/analytics/drop-off/` | Get drop-off analysis | ✅ |
| `GET` | `/api/v1/forms/{slug}/analytics/summary-report/` | Get summary report | ✅ |
| `GET` | `/api/v1/forms/{slug}/analytics/fields/{field_id}/report/` | Get field-specific report | ✅ |
| `GET` | `/api/v1/forms/{slug}/analytics/reports/real-time/` | Get real-time report with WebSocket URL | ✅ |

### Dashboard & Search

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET` | `/api/v1/dashboard/overview/` | Get dashboard overview | ✅ |
| `GET` | `/api/v1/dashboard/statistics/` | Get dashboard statistics | ✅ |
| `GET` | `/api/v1/dashboard/recent-activity/` | Get recent activity | ✅ |
| `GET` | `/api/v1/search/` | Global search (forms + processes) | ✅ |
| `GET` | `/api/v1/search/forms/` | Search forms only | ✅ |
| `GET` | `/api/v1/search/processes/` | Search processes only | ✅ |

### System Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET` | `/api/v1/health/` | Health check | ❌ |
| `GET` | `/api/v1/version/` | API version info | ❌ |

### Admin Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET` | `/api/v1/admin/webhooks/` | List webhooks | ✅ (Admin) |
| `POST` | `/api/v1/admin/webhooks/` | Create webhook | ✅ (Admin) |
| `GET` | `/api/v1/admin/webhooks/{id}/` | Get webhook details | ✅ (Admin) |
| `PATCH` | `/api/v1/admin/webhooks/{id}/` | Update webhook | ✅ (Admin) |
| `DELETE` | `/api/v1/admin/webhooks/{id}/` | Delete webhook | ✅ (Admin) |
| `POST` | `/api/v1/admin/webhooks/{id}/test/` | Test webhook | ✅ (Admin) |
| `GET` | `/api/v1/admin/reports/config/` | List report configurations | ✅ (Admin) |
| `POST` | `/api/v1/admin/reports/config/` | Create report configuration | ✅ (Admin) |
| `PATCH` | `/api/v1/admin/reports/config/{id}/` | Update report configuration | ✅ (Admin) |
| `DELETE` | `/api/v1/admin/reports/config/{id}/` | Delete report configuration | ✅ (Admin) |
| `POST` | `/api/v1/admin/reports/generate/` | Generate manual report | ✅ (Admin) |
| `GET` | `/api/v1/admin/reports/history/` | List report history | ✅ (Admin) |
| `GET` | `/api/v1/admin/reports/history/{id}/download/` | Download report | ✅ (Admin) |

---

## 💡 Examples

### Complete Registration and Login Flow

```bash
# 1. Register a new user
curl -X POST http://localhost:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!",
    "first_name": "John",
    "last_name": "Doe"
  }'

# 2. Login and get tokens
RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "SecurePass123!"
  }')

# Extract access token (requires jq)
ACCESS_TOKEN=$(echo $RESPONSE | jq -r '.access')

# 3. Get user profile
curl -X GET http://localhost:8000/api/v1/users/me/ \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json"
```

### Create a Form with Fields

```bash
ACCESS_TOKEN="your_access_token_here"

# 1. Create a category
CATEGORY_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/categories/ \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Surveys",
    "description": "Customer surveys",
    "color": "#FF5733"
  }')

CATEGORY_ID=$(echo $CATEGORY_RESPONSE | jq -r '.id')

# 2. Create a form
FORM_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/forms/ \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{
    \"title\": \"Customer Satisfaction Survey\",
    \"description\": \"Help us improve our service\",
    \"category\": \"${CATEGORY_ID}\",
    \"visibility\": \"public\"
  }")

FORM_SLUG=$(echo $FORM_RESPONSE | jq -r '.unique_slug')

# 3. Add a text field
curl -X POST http://localhost:8000/api/v1/forms/${FORM_SLUG}/fields/ \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "field_type": "text",
    "label": "Name",
    "is_required": true,
    "order_index": 0
  }'

# 4. Add a select field
SELECT_FIELD_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/forms/${FORM_SLUG}/fields/ \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "field_type": "select",
    "label": "Rating",
    "is_required": true,
    "order_index": 1
  }')

FIELD_ID=$(echo $SELECT_FIELD_RESPONSE | jq -r '.id')

# 5. Add options to select field
curl -X POST http://localhost:8000/api/v1/forms/${FORM_SLUG}/fields/${FIELD_ID}/options/ \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "label": "Excellent",
    "value": "5",
    "order_index": 0
  }'

curl -X POST http://localhost:8000/api/v1/forms/${FORM_SLUG}/fields/${FIELD_ID}/options/ \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "label": "Good",
    "value": "4",
    "order_index": 1
  }'
```

### Submit a Form (Public Access)

```bash
# Submit without authentication
curl -X POST http://localhost:8000/api/v1/public/forms/customer-satisfaction-survey/submit/ \
  -H "Content-Type: application/json" \
  -d '{
    "answers": [
      {
        "field_id": "field-uuid-1",
        "value": "John Doe"
      },
      {
        "field_id": "field-uuid-2",
        "value": "5"
      }
    ],
    "session_id": "session-123"
  }'
```

### Create and Execute a Process

```bash
ACCESS_TOKEN="your_access_token_here"

# 1. Create a process
PROCESS_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/processes/ \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Onboarding Process",
    "description": "New employee onboarding",
    "process_type": "linear",
    "visibility": "public"
  }')

PROCESS_SLUG=$(echo $PROCESS_RESPONSE | jq -r '.unique_slug')

# 2. Add steps to process
curl -X POST http://localhost:8000/api/v1/processes/${PROCESS_SLUG}/steps/ \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{
    \"form\": \"form-slug-1\",
    \"title\": \"Personal Information\",
    \"order_index\": 0
  }"

# 3. Start process execution (public)
START_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/public/processes/${PROCESS_SLUG}/start/ \
  -H "Content-Type: application/json")

PROGRESS_ID=$(echo $START_RESPONSE | jq -r '.progress_id')

# 4. Get current step and complete it
curl -X POST http://localhost:8000/api/v1/public/processes/${PROCESS_SLUG}/progress/${PROGRESS_ID}/step/{step_id}/complete/ \
  -H "Content-Type: application/json" \
  -d '{
    "answers": [
      {
        "field_id": "field-uuid",
        "value": "answer value"
      }
    ]
  }'
```

For more examples, see:
- [CURL_EXAMPLES.md](documents/CURL_EXAMPLES.md) - Detailed curl examples
- [GOOGLE_OAUTH_CURL.md](documents/GOOGLE_OAUTH_CURL.md) - Google OAuth examples

---

## 🛠️ Development

### Project Structure

```
dynamic-form-system/
├── accounts/          # User authentication and management
├── categories/        # Category management
├── forms/            # Form builder and management
├── processes/        # Multi-step process management
├── submissions/      # Form submission handling
├── analytics/        # Analytics and reporting
├── notifications/    # Webhooks and scheduled reports
├── core/             # Core settings and configuration
├── shared/           # Shared utilities and constants
├── documents/        # Documentation
├── requirements.txt  # Python dependencies
├── Dockerfile        # Docker image definition
├── docker-compose.yml # Docker Compose configuration
└── manage.py        # Django management script
```

### Running Locally

```bash
# Activate virtual environment
source venv/bin/activate

# Run development server
python manage.py runserver

# Run with custom settings
python manage.py runserver --settings=core.settings.dev
```

### Code Style

The project follows PEP 8 Python style guidelines. Consider using:
- **Black** - Code formatting
- **Flake8** - Linting
- **isort** - Import sorting

---

## 🧪 Testing

### Run All Tests

```bash
# Using Docker (recommended)
make test-all

# Locally
python manage.py test
```

### Run Specific Tests

```bash
# Test specific app
python manage.py test accounts

# Test specific file
python manage.py test accounts.tests

# Test specific test case
python manage.py test accounts.tests.UserModelTest

# With Docker
make test-specific TEST=accounts.tests
```

### Test Coverage

```bash
# Install coverage
pip install coverage

# Run with coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # Generate HTML report
```

---

## 🚀 Deployment

### Using Docker (Production)

```bash
# Build for production
docker compose -f docker-compose.prod.yml build

# Start services
docker compose -f docker-compose.prod.yml up -d

# Run migrations
docker compose -f docker-compose.prod.yml exec web python manage.py migrate

# Collect static files
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

### Production Settings

Use `core.settings.prod` for production:

```bash
export DJANGO_SETTINGS_MODULE=core.settings.prod
python manage.py check --deploy
```

Key production settings:
- HTTPS enforcement
- Security headers (HSTS, CSP)
- Redis caching
- Database connection pooling
- File logging with rotation
- Email via SMTP

See [core/settings/prod.py](core/settings/prod.py) for full configuration.

### Environment Checklist

Before deploying to production:

- [ ] Set `DEBUG=False`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Set strong `SECRET_KEY`
- [ ] Configure production database
- [ ] Set up Redis
- [ ] Configure SMTP email
- [ ] Set `STATIC_ROOT` and run `collectstatic`
- [ ] Configure HTTPS/SSL
- [ ] Set up monitoring/logging
- [ ] Configure Celery workers
- [ ] Set up backup strategy

---

## 📊 Architecture

### Clean Architecture

The project follows clean architecture principles:

- **Repository Layer**: Database access abstraction
- **Service Layer**: Business logic
- **View Layer**: API endpoints and request handling
- **Serializer Layer**: Data validation and transformation

### Key Design Patterns

- **Repository Pattern**: Centralized database operations
- **Service Pattern**: Business logic encapsulation
- **Dependency Injection**: Loose coupling between layers

---

## 📝 Additional Documentation

- [API Endpoints List](documents/api-endpoints-list.md) - Complete endpoint reference
- [Database Schema](documents/database-schema-docs.md) - Database structure documentation
- [Docker Setup](documents/DOCKER_SETUP.md) - Docker configuration guide
- [Testing Summary](documents/TESTING_SUMMARY.md) - Testing documentation

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Write tests for new features
- Follow PEP 8 style guide
- Update documentation
- Add type hints where appropriate
- Keep commits atomic and descriptive

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Django REST Framework team
- Django Channels for WebSocket support
- All open-source contributors

---

## 📧 Support

For issues, questions, or contributions, please open an issue on GitHub.

---

**Built with ❤️ using Django and Django REST Framework**

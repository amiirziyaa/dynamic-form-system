# Google OAuth Authentication - cURL Examples

## Overview

Google OAuth authentication with this API requires two steps:
1. **Get Google OAuth Access Token** from Google (using Google OAuth 2.0 flow)
2. **Exchange Google Token** for JWT tokens (access + refresh) via our API

## Endpoints

- **Primary**: `POST /api/v1/auth/oauth/google/`
- **Legacy**: `POST /api/v1/auth/google/` (alias)

## Prerequisites

Before using these endpoints, you need:
1. Google OAuth credentials (`GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`) configured in your `.env`
2. A Google OAuth access token obtained from Google's OAuth 2.0 flow

---

## Step 1: Get Google OAuth Access Token

There are several ways to get a Google OAuth access token:

### Option A: Using Google OAuth Playground (Testing)

1. Visit: https://developers.google.com/oauthplayground/
2. Select Google APIs:
   - `https://www.googleapis.com/auth/userinfo.email`
   - `https://www.googleapis.com/auth/userinfo.profile`
3. Click "Authorize APIs"
4. Sign in with your Google account
5. Click "Exchange authorization code for tokens"
6. Copy the **Access token**

### Option B: Using Google OAuth 2.0 Flow (Production)

```bash
# 1. Get authorization code from Google
# Redirect user to:
https://accounts.google.com/o/oauth2/v2/auth?client_id=YOUR_CLIENT_ID&redirect_uri=YOUR_REDIRECT_URI&response_type=code&scope=email%20profile

# 2. Exchange authorization code for access token
curl -X POST https://oauth2.googleapis.com/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "code=AUTHORIZATION_CODE" \
  -d "grant_type=authorization_code" \
  -d "redirect_uri=YOUR_REDIRECT_URI"

# Response:
# {
#   "access_token": "ya29.a0AfH6SMBxxxxx",
#   "expires_in": 3599,
#   "token_type": "Bearer",
#   ...
# }
```

### Option C: Using a Test Token (Development Only)

For development/testing, you can use a mock token (the adapter will validate it):

```bash
# This will fail validation but you can test the endpoint
GOOGLE_ACCESS_TOKEN="test_token_12345"
```

---

## Step 2: Exchange Google Token for JWT Tokens

Once you have a Google OAuth access token, send it to our API:

### Basic Request

```bash
curl -X POST http://localhost:8000/api/v1/auth/oauth/google/ \
  -H "Content-Type: application/json" \
  -d '{
    "access_token": "ya29.a0AfH6SMBxxxxx"
  }'
```

### Complete Example (with response handling)

```bash
# Set variables
BASE_URL="http://localhost:8000"
GOOGLE_ACCESS_TOKEN="ya29.a0AfH6SMBxxxxx"

# Login/Register with Google
curl -X POST ${BASE_URL}/api/v1/auth/oauth/google/ \
  -H "Content-Type: application/json" \
  -d "{
    \"access_token\": \"${GOOGLE_ACCESS_TOKEN}\"
  }" \
  -w "\nHTTP Status: %{http_code}\n"
```

### Success Response (200/201)

```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "pk": "123e4567-e89b-12d3-a456-426614174000",
    "email": "user@gmail.com",
    "first_name": "John",
    "last_name": "Doe",
    "username": "user@gmail.com"
  }
}
```

### Error Responses

**400 Bad Request** - Invalid token or missing access_token:
```json
{
  "access_token": ["This field is required."]
}
```

**401 Unauthorized** - Authentication failed:
```json
{
  "non_field_errors": ["Invalid token or authentication failed"]
}
```

---

## Step 3: Use JWT Tokens for Authenticated Requests

After successful login, use the JWT access token for authenticated requests:

```bash
# Save the access token
ACCESS_TOKEN="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."

# Make authenticated request
curl -X GET http://localhost:8000/api/v1/users/me/ \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json"
```

---

## Complete Flow Example

```bash
#!/bin/bash

# Configuration
BASE_URL="http://localhost:8000"
GOOGLE_ACCESS_TOKEN="ya29.a0AfH6SMBxxxxx"  # Get this from Google OAuth

echo "Step 1: Login/Register with Google OAuth..."
RESPONSE=$(curl -s -X POST ${BASE_URL}/api/v1/auth/oauth/google/ \
  -H "Content-Type: application/json" \
  -d "{
    \"access_token\": \"${GOOGLE_ACCESS_TOKEN}\"
  }")

echo "Response:"
echo $RESPONSE | jq '.'

# Extract access token (requires jq)
ACCESS_TOKEN=$(echo $RESPONSE | jq -r '.access')
REFRESH_TOKEN=$(echo $RESPONSE | jq -r '.refresh')

echo ""
echo "Step 2: Use the access token..."
echo "Access Token: ${ACCESS_TOKEN:0:50}..."
echo "Refresh Token: ${REFRESH_TOKEN:0:50}..."

# Example: Get user profile
echo ""
echo "Step 3: Get user profile..."
curl -s -X GET ${BASE_URL}/api/v1/users/me/ \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" | jq '.'
```

---

## Using Legacy Endpoint

The legacy endpoint works the same way:

```bash
curl -X POST http://localhost:8000/api/v1/auth/google/ \
  -H "Content-Type: application/json" \
  -d '{
    "access_token": "ya29.a0AfH6SMBxxxxx"
  }'
```

---

## Testing with Invalid Token

```bash
# This should return 400 or 401
curl -X POST http://localhost:8000/api/v1/auth/oauth/google/ \
  -H "Content-Type: application/json" \
  -d '{
    "access_token": "invalid_token_12345"
  }'
```

---

## Refresh Token Example

When the access token expires, use the refresh token:

```bash
REFRESH_TOKEN="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."

curl -X POST http://localhost:8000/api/v1/auth/refresh/ \
  -H "Content-Type: application/json" \
  -d "{
    \"refresh\": \"${REFRESH_TOKEN}\"
  }"
```

---

## Notes

1. **First-time login**: If the user doesn't exist, they will be automatically registered
2. **Existing users**: If a user with the same email exists, they will be logged in
3. **Token validation**: The API validates the Google access token with Google's API
4. **JWT tokens**: Access tokens expire in 60 minutes (configurable), refresh tokens in 7 days
5. **Production**: Make sure to use HTTPS in production and configure `ALLOWED_HOSTS`

---

## Environment Variables Required

Make sure these are set in your `.env` file:

```bash
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
FRONTEND_URL=https://your-frontend-domain.com
```


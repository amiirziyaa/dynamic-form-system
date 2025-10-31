# Accounts API - cURL Examples

## Base URL
```
http://localhost:8000
```

---

## 1. Register a New User

**Endpoint:** `POST /api/v1/auth/register/`

### Request

```bash
curl -X POST http://localhost:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "+1234567890",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!"
  }'
```

### Response (Success - 201 Created)
```json
{
  "message": "User registered successfully",
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "john.doe@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "+1234567890",
    "is_active": true,
    "email_verified": false,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z",
    "last_login": null
  },
  "tokens": {
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  }
}
```

### Register without phone number (optional field)
```bash
curl -X POST http://localhost:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "jane.smith@example.com",
    "first_name": "Jane",
    "last_name": "Smith",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!"
  }'
```

### Error Response (400 Bad Request)
```json
{
  "password": ["This field may not be blank."],
  "password_confirm": ["This field is required."],
  "email": ["This field is required."]
}
```

---

## 2. Login

**Endpoint:** `POST /api/v1/auth/login/`

### Request

```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@example.com",
    "password": "SecurePass123!"
  }'
```

### Response (Success - 200 OK)
```json
{
  "message": "Login successful",
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "john.doe@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "+1234567890",
    "is_active": true,
    "email_verified": false,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z",
    "last_login": "2024-01-15T10:35:00Z"
  },
  "tokens": {
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  }
}
```

### Error Response (400 Bad Request)
```json
{
  "non_field_errors": ["Invalid email or password"]
}
```

---

## 3. Complete Example: Register → Login

### Step 1: Register
```bash
curl -X POST http://localhost:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@example.com",
    "first_name": "Test",
    "last_name": "User",
    "password": "TestPass123!",
    "password_confirm": "TestPass123!"
  }'
```

**Save the response tokens if you want to use them later.**

### Step 2: Login (after registration)
```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@example.com",
    "password": "TestPass123!"
  }'
```

### Step 3: Using Access Token (Example: Get User Profile)

```bash
# Replace YOUR_ACCESS_TOKEN with the access token from login response
curl -X GET http://localhost:8000/api/v1/users/me/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

---

## 4. Quick Test Script

### Using environment variables

```bash
# Register
export EMAIL="testuser@example.com"
export PASSWORD="TestPass123!"
export BASE_URL="http://localhost:8000"

# Register
curl -X POST ${BASE_URL}/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"${EMAIL}\",
    \"first_name\": \"Test\",
    \"last_name\": \"User\",
    \"password\": \"${PASSWORD}\",
    \"password_confirm\": \"${PASSWORD}\"
  }"

# Login (save access token)
LOGIN_RESPONSE=$(curl -s -X POST ${BASE_URL}/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"${EMAIL}\",
    \"password\": \"${PASSWORD}\"
  }")

# Extract access token (requires jq: apt-get install jq)
ACCESS_TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.tokens.access')

# Use access token
curl -X GET ${BASE_URL}/api/v1/users/me/ \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json"
```

---

## 5. Pretty Print JSON (with jq)

```bash
# Register with pretty output
curl -X POST http://localhost:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User",
    "password": "TestPass123!",
    "password_confirm": "TestPass123!"
  }' | jq '.'

# Login with pretty output
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!"
  }' | jq '.'
```

---

## 6. Common Errors and Solutions

### Error: "Passwords don't match"
**Solution:** Ensure `password` and `password_confirm` are identical.

### Error: "This password is too short"
**Solution:** Password must be at least 8 characters.

### Error: "This password is too common"
**Solution:** Use a stronger password (not common words).

### Error: "Invalid email or password"
**Possible causes:**
- Wrong email or password
- Account is inactive
- User doesn't exist

### Error: "User with this email already exists"
**Solution:** Use a different email address.

---

## 7. Password Requirements

According to Django's password validators:
- Minimum 8 characters
- Cannot be entirely numeric
- Cannot be too similar to personal information (email, name)
- Cannot be a common password

**Recommended passwords:**
- ✅ `SecurePass123!`
- ✅ `MyP@ssw0rd2024`
- ✅ `TestUser!23`
- ❌ `password` (too common)
- ❌ `12345678` (too simple)
- ❌ `john` (too short)

---

## 8. Example Response Fields Explained

### User Object
- `id`: UUID - Unique user identifier
- `email`: User's email address (used for login)
- `first_name`: User's first name
- `last_name`: User's last name
- `phone_number`: Phone number (optional, for OTP)
- `is_active`: Boolean - Whether account is active
- `email_verified`: Boolean - Whether email is verified
- `created_at`: Timestamp - Account creation time
- `updated_at`: Timestamp - Last update time
- `last_login`: Timestamp - Last login time (null if never logged in)

### Tokens
- `access`: JWT access token (use in Authorization header)
- `refresh`: JWT refresh token (use to get new access token)

---

## 9. Using the Tokens

### Access Token (Expires in 60 minutes)
```bash
# Use in Authorization header
curl -X GET http://localhost:8000/api/v1/users/me/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

### Refresh Token (Expires in 7 days)
```bash
# Refresh access token
curl -X POST http://localhost:8000/api/v1/auth/refresh/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  }'
```

---

## 10. Testing with Different Ports

If your Django server runs on a different port:

```bash
# For port 8001
curl -X POST http://localhost:8001/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{...}'

# For custom domain
curl -X POST https://api.yourdomain.com/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{...}'
```

---

## Quick Reference Card

```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","first_name":"User","last_name":"Name","password":"Pass123!","password_confirm":"Pass123!"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"Pass123!"}'

# Get Profile (requires access token)
curl -X GET http://localhost:8000/api/v1/users/me/ \
  -H "Authorization: Bearer ACCESS_TOKEN"
```


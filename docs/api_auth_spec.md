# Authentication API Specification

## Overview
The Agentic Travel Tech backend uses JSON Web Tokens (JWT) for secure, stateless authentication. 
The system implements a dual-token architecture:
1. **Access Token:** Short-lived (e.g., 15 minutes), passed in the `Authorization: Bearer` header.
2. **Refresh Token:** Long-lived (e.g., 7 days), used to request new access tokens without requiring the user to log in again.

---

## 1. Register User

Creates a new user account. Passwords must be hashed using bcrypt before being stored in the database.

**Endpoint:** `POST /api/v1/auth/register`
**Content-Type:** `application/json`

### Request Payload
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

### Responses
**201 Created**
```json
{
  "id": 1,
  "email": "user@example.com",
  "created_at": "2026-10-10T12:00:00Z"
}
```

**400 Bad Request**
```json
{
  "detail": "Email already registered."
}
```

---

## 2. Login (Generate Tokens)

Authenticates a user and returns both an access token and a refresh token.

**Endpoint:** `POST /api/v1/auth/login`
**Content-Type:** `application/json`

### Request Payload
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

### Responses
**200 OK**
```json
{
  "access_token": "eyJhbG...",
  "refresh_token": "def502...",
  "token_type": "bearer",
  "expires_in": 900
}
```
*(Note: `expires_in` represents the access token lifespan in seconds. 900 = 15 minutes).*

**401 Unauthorized**
```json
{
  "detail": "Incorrect email or password."
}
```

---

## 3. Refresh Token

Trades a valid, unexpired refresh token for a brand new access token.

**Endpoint:** `POST /api/v1/auth/refresh`
**Content-Type:** `application/json`

### Request Payload
```json
{
  "refresh_token": "def502..."
}
```

### Responses
**200 OK**
```json
{
  "access_token": "eyJhbG...",
  "token_type": "bearer",
  "expires_in": 900
}
```

**401 Unauthorized** (Refresh token expired or invalid)
```json
{
  "detail": "Invalid refresh token. Please log in again."
}
```

---

## 4. Get Current User (Me)

Retrieves the profile information of the currently authenticated user.

**Endpoint:** `GET /api/v1/auth/me`
**Headers:** `Authorization: Bearer <access_token>`

### Responses
**200 OK**
```json
{
  "id": 1,
  "email": "user@example.com",
  "created_at": "2026-10-10T12:00:00Z"
}
```

**401 Unauthorized**
```json
{
  "detail": "Could not validate credentials."
}
```

---

## Security Requirements
1. **Password Hashing:** Use `passlib` with `bcrypt`. Raw passwords must never be stored.
2. **Token Expiry:** Access tokens must be short-lived (15 minutes). Refresh tokens can be longer (7 days).
3. **Algorithm:** JWT tokens must be signed using `HS256` with a secure `SECRET_KEY`.

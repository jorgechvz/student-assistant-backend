# API Reference

## Base URL

```
http://localhost:8000/api/v1
```

All endpoints require authentication unless stated otherwise. Authentication is handled via `httponly` cookies (`access_token` and `refresh_token`).

---

## Authentication (`/auth`)

### POST `/auth/signup`

Register a new user account.

**Request Body:**
```json
{
  "email": "student@university.edu",
  "password": "securepassword123",
  "full_name": "Jane Doe"
}
```

**Response** `201 Created`:
```json
{
  "user": {
    "id": "507f1f77bcf86cd799439011",
    "email": "student@university.edu",
    "full_name": "Jane Doe",
    "is_active": true
  },
  "access_token": "eyJhbGciOi...",
  "refresh_token": "eyJhbGciOi...",
  "token_type": "bearer"
}
```

**Errors:**
- `400` — Email already in use
- `500` — Internal server error

---

### POST `/auth/login`

Authenticate an existing user.

**Request Body:**
```json
{
  "email": "student@university.edu",
  "password": "securepassword123"
}
```

**Response** `200 OK`: Same shape as signup response.

**Errors:**
- `401` — Invalid email, inactive user, or wrong password

---

### POST `/auth/logout`

Clear authentication cookies. No request body required.

**Response** `200 OK`:
```json
{ "message": "Successfully logged out" }
```

---

### POST `/auth/refresh`

Refresh the access token using the refresh token cookie.

**Response** `200 OK`: Same shape as login response with new tokens.

**Errors:**
- `401` — Refresh token not found or invalid

---

### GET `/auth/me`

Get the current authenticated user's information.

**Response** `200 OK`:
```json
{
  "id": "507f1f77bcf86cd799439011",
  "email": "student@university.edu",
  "full_name": "Jane Doe",
  "is_active": true
}
```

---

## User Settings (`/user`)

### GET `/user/profile`

Get the current user's full profile including integration status.

**Response** `200 OK`:
```json
{
  "id": "507f1f77bcf86cd799439011",
  "email": "student@university.edu",
  "full_name": "Jane Doe",
  "is_active": true,
  "created_at": "2026-01-15T10:30:00",
  "has_canvas": true,
  "has_google": true,
  "has_notion": false
}
```

---

### PATCH `/user/profile`

Update user profile information.

**Request Body** (all fields optional):
```json
{
  "full_name": "Jane Smith",
  "email": "jane.smith@university.edu"
}
```

**Response** `200 OK`: Updated `UserProfileResponse`.

**Errors:**
- `400` — Email already in use by another account

---

### POST `/user/change-password`

Change the user's password.

**Request Body:**
```json
{
  "current_password": "oldpassword123",
  "new_password": "newSecurePassword456"
}
```

**Response** `200 OK`:
```json
{ "message": "Password changed successfully" }
```

**Errors:**
- `400` — Current password is incorrect

---

### DELETE `/user/account`

Permanently delete the user account and **all associated data** (integration tokens, chat sessions, messages).

**Request Body:**
```json
{
  "password": "currentpassword123"
}
```

**Response** `200 OK`:
```json
{ "message": "Account deleted successfully" }
```

**Errors:**
- `400` — Incorrect password

---

### GET `/user/integrations`

Get the connection status of all integrations.

**Response** `200 OK`:
```json
{
  "canvas": true,
  "google": true,
  "notion": false,
  "canvas_user_name": "Jane Doe",
  "google_email": "jane@gmail.com",
  "notion_workspace_name": null
}
```

---

### DELETE `/user/integrations/{integration}`

Disconnect a specific integration. Valid values: `canvas`, `google`, `notion`.

**Response** `200 OK`:
```json
{ "message": "Canvas disconnected successfully" }
```

**Errors:**
- `400` — Unknown integration name

---

## Chat (`/chat`)

### POST `/chat`

Send a message and receive a complete response (non-streaming).

**Request Body:**
```json
{
  "message": "What assignments are due this week?",
  "session_id": "optional-existing-session-id",
  "canvas_token": "optional-override",
  "canvas_base_url": "optional-override"
}
```

**Response** `200 OK`:
```json
{
  "response": "You have 3 assignments due this week...",
  "session_id": "507f1f77bcf86cd799439011"
}
```

---

### POST `/chat/stream`

Send a message and receive a streaming response via **Server-Sent Events (SSE)**.

**Request Body:** Same as `/chat`.

**Response** `200 OK` (`text/event-stream`):
```
data: {"type": "session", "session_id": "507f1f77bcf86cd799439011"}

data: {"type": "token", "content": "You "}

data: {"type": "token", "content": "have "}

data: {"type": "token", "content": "3 assignments..."}

data: {"type": "done"}
```

---

### GET `/chat/sessions`

List the current user's chat sessions.

**Response** `200 OK`:
```json
[
  {
    "id": "507f1f77bcf86cd799439011",
    "title": "Week 5 Assignments",
    "is_active": true,
    "created_at": "2026-02-10T14:30:00Z"
  }
]
```

---

### GET `/chat/sessions/{session_id}/messages`

Get all messages in a specific chat session.

**Response** `200 OK`:
```json
[
  {
    "role": "user",
    "content": "What assignments are due this week?",
    "created_at": "2026-02-10T14:30:00Z"
  },
  {
    "role": "assistant",
    "content": "You have 3 assignments due...",
    "created_at": "2026-02-10T14:30:05Z"
  }
]
```

---

### DELETE `/chat/sessions/{session_id}`

Delete a chat session and all its messages.

**Response** `200 OK`:
```json
{ "message": "Session deleted" }
```

---

## Canvas LMS (`/canvas`)

### POST `/canvas/setup`

Connect a Canvas LMS account by providing an access token.

**Request Body:**
```json
{
  "canvas_base_url": "https://university.instructure.com",
  "access_token": "canvas_api_token_here"
}
```

**Response** `200 OK`:
```json
{
  "message": "Canvas connected successfully",
  "canvas_user_name": "Jane Doe"
}
```

---

### GET `/canvas/status`

Check Canvas connection status.

**Response** `200 OK`:
```json
{
  "connected": true,
  "canvas_base_url": "https://university.instructure.com",
  "canvas_user_name": "Jane Doe"
}
```

---

### GET `/canvas/upcoming-assignments`

Get all upcoming assignments across all enrolled courses.

**Response** `200 OK`:
```json
[
  {
    "course": "CS 101 - Intro to Programming",
    "assignment": "Homework 5",
    "due_at": "2026-02-15T23:59:00Z",
    "points": 100,
    "html_url": "https://university.instructure.com/..."
  }
]
```

---

### DELETE `/canvas/disconnect`

Disconnect Canvas integration.

**Response** `200 OK`:
```json
{ "message": "Canvas disconnected" }
```

---

## Google Calendar (`/auth/google`)

### GET `/auth/google/authorize`

Initiates the Google OAuth flow. Redirects the user to Google's consent screen.

**Query Parameters:** None (user ID extracted from cookie).

**Response:** `302 Redirect` to Google OAuth URL.

---

### GET `/auth/google/callback`

Handles the OAuth callback from Google. Exchanges the authorization code for tokens.

**Query Parameters:** `code`, `state` (set automatically by OAuth flow).

**Response:** `302 Redirect` to frontend success URL.

---

### GET `/auth/google/status`

Check Google Calendar connection status.

**Response** `200 OK`:
```json
{
  "connected": true,
  "email": "jane@gmail.com",
  "name": "Jane Doe",
  "picture": "https://lh3.googleusercontent.com/...",
  "expires_at": "2026-02-12T15:30:00Z"
}
```

---

### DELETE `/auth/google/disconnect`

Disconnect Google Calendar integration and revoke the token.

---

## Notion (`/auth/notion`)

### GET `/auth/notion/authorize`

Initiates the Notion OAuth flow. Redirects to Notion's consent screen.

**Response:** `302 Redirect` to Notion OAuth URL.

---

### GET `/auth/notion/callback`

Handles the OAuth callback from Notion.

**Response:** `302 Redirect` to frontend success URL.

---

### GET `/auth/notion/status`

Check Notion connection status.

**Response** `200 OK`:
```json
{
  "connected": true,
  "workspace_name": "Jane's Workspace",
  "workspace_icon": "https://..."
}
```

---

### DELETE `/auth/notion/disconnect`

Disconnect Notion integration and revoke the token.

---

## Error Responses

All error responses follow this format:

```json
{
  "detail": "Human-readable error message"
}
```

| Status Code | Meaning |
|-------------|---------|
| `400` | Bad Request — Invalid input or business rule violation |
| `401` | Unauthorized — Missing, invalid, or expired authentication |
| `404` | Not Found — Resource does not exist |
| `500` | Internal Server Error — Unexpected server failure |

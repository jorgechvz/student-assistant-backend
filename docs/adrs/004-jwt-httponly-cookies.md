# ADR-004: JWT Authentication with HttpOnly Cookies

## Status

Accepted

## Context

The application needs to authenticate users across a decoupled frontend (React SPA) and backend (FastAPI). We needed an authentication mechanism that:
- Works with a single-page application making API calls.
- Protects against common web attacks (XSS, CSRF).
- Supports token refresh without requiring re-login.
- Is stateless on the server side.

Common approaches:
1. **JWT in `Authorization` header** — Simple but tokens stored in `localStorage` are vulnerable to XSS.
2. **Session cookies** — Server-side state, harder to scale.
3. **JWT in `httponly` cookies** — Stateless auth with XSS protection.

## Decision

We use **JWT tokens stored in `httponly` cookies** with a dual-token strategy:

- **Access token**: Short-lived (30 minutes), used for API authentication.
- **Refresh token**: Long-lived (7 days), used only to obtain new access tokens.
- Both tokens are set as `httponly`, `secure`, and `SameSite` cookies.
- Tokens are created with `PyJWT` and passwords are hashed with `bcrypt`.

Cookie configuration is environment-aware:
- Development: `secure=false`, `samesite=lax`
- Production: `secure=true`, `samesite=none` (for cross-origin SPA)

## Consequences

### Positive
- `httponly` cookies are inaccessible to JavaScript, eliminating XSS-based token theft.
- `SameSite` cookie attribute provides CSRF protection.
- Stateless — no server-side session storage required.
- Configurable cookie settings per environment (dev vs. prod).
- Refresh token flow allows seamless re-authentication.

### Negative
- Cross-origin requests require `credentials: 'include'` on the frontend and proper CORS configuration on the backend.
- Cookie-based auth doesn't work for non-browser clients (mobile apps, CLI tools) without adaptation.
- Token revocation is not immediate — compromised tokens remain valid until expiry.
- `SameSite=none` in production requires `Secure=true`, mandating HTTPS.

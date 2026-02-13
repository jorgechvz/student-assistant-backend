# ADR-009: Canvas LMS Personal Access Tokens vs OAuth

## Status

Accepted

## Context

Canvas LMS supports two authentication methods:
1. **OAuth 2.0** — Standard authorization flow where users grant access through Canvas UI.
2. **Personal Access Tokens** — User-generated tokens from Canvas Settings.

We needed to choose how users would connect their Canvas accounts to the assistant.

## Decision

We chose **Personal Access Tokens** for Canvas LMS integration.

Users generate a token in Canvas (Account → Settings → New Access Token) and provide it along with their Canvas instance URL through the application's settings page. The token and URL are validated against the Canvas API before being stored.

The setup flow:
1. User enters `canvas_base_url` and `access_token` in the frontend settings.
2. Backend calls `POST /canvas/setup`.
3. Backend validates the token by calling Canvas's `/api/v1/users/self` endpoint.
4. If valid, the token is stored in the `canvas_tokens` collection.

## Consequences

### Positive
- **Simpler implementation** — No OAuth redirect flow, no authorization server registration, no client credentials to manage per institution.
- **Institution-agnostic** — Works with any Canvas instance without requiring admin approval for an OAuth application.
- **User control** — Students can revoke their token at any time from Canvas settings.
- **No token refresh needed** — Personal access tokens don't expire unless manually revoked.

### Negative
- **User friction** — Students must manually navigate Canvas settings to generate a token (less seamless than OAuth "click to connect").
- **Security responsibility** — The token provides full API access to the student's Canvas account; it must be stored securely.
- **No granular scopes** — Personal access tokens grant the same permissions as the user, unlike OAuth where scopes can be restricted.
- **No institutional branding** — OAuth would show a branded consent screen; personal tokens are a manual process.

### Mitigation
- Clear setup instructions are provided in the frontend and documentation.
- Tokens are stored in MongoDB with access restricted to the owning user.
- Account deletion cascades to token deletion.

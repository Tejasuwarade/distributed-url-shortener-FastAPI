# JWT Authentication Design

This project uses bcrypt password hashing and stateless JWT tokens for API authentication.

## Endpoints

### Signup

```http
POST /api/v1/auth/signup
```

Request:

```json
{
  "email": "user@example.com",
  "password": "strongpassword123",
  "name": "Example User"
}
```

Only the password hash is stored. The raw password is never persisted.

### Login

```http
POST /api/v1/auth/login
```

Request:

```json
{
  "email": "user@example.com",
  "password": "strongpassword123"
}
```

Response:

```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer",
  "expires_in": 900
}
```

### Refresh

```http
POST /api/v1/auth/refresh
```

Request:

```json
{
  "refresh_token": "..."
}
```

### Protected Routes

Protected routes require:

```http
Authorization: Bearer <access_token>
```

Examples:

- `GET /api/v1/users/me`
- `GET /api/v1/users/admin-check`
- `POST /api/v1/urls`

Redirects remain public:

```http
GET /{short_code}
```

## JWT Flow

1. User signs up with email and password.
2. Server hashes the password using bcrypt.
3. User logs in with email and password.
4. Server verifies the password hash.
5. Server returns an access token and refresh token.
6. Client sends the access token in the `Authorization` header.
7. FastAPI dependencies validate the token and load the current user.
8. When the access token expires, the client uses the refresh token to get a new token pair.

## Access Tokens vs Refresh Tokens

Access tokens are short-lived. They are used on normal API requests and should expire quickly to limit damage if stolen.

Refresh tokens are longer-lived. They are used only to mint a new access token. They should be stored more carefully than access tokens.

This starter uses:

- Access token: 15 minutes
- Refresh token: 7 days

These values are configured through `.env`.

## Password Hashing

Passwords are hashed with bcrypt through `pwdlib`.

Hashing is one-way:

- The API never stores raw passwords.
- Login verifies the submitted password against the stored hash.
- If the database leaks, attackers still do not immediately get user passwords.

Never encrypt passwords for later decryption. Passwords should be hashed, not encrypted.

## Auth Middleware

`AuthContextMiddleware` reads the `Authorization` header when present and decodes token context into `request.state`.

It does not make every route protected. That is intentional:

- Public routes like health checks, signup, login, and redirects should remain public.
- Protected routes use dependencies like `get_current_user`.

Middleware is useful for request-wide context. Dependencies are better for route-level authorization decisions.

## Dependency Injection

FastAPI dependencies are used for:

- Database sessions.
- Current-user loading.
- Role checks.

`get_current_user` validates the access token, loads the user from PostgreSQL, checks `is_active`, and returns the user object.

`require_roles(UserRole.ADMIN)` builds on top of `get_current_user` and rejects users without the required role.

## Role-Based Authorization

The initial role model is intentionally simple:

```text
user
admin
```

Use route dependencies to enforce permissions:

```python
current_user: User = Depends(require_roles(UserRole.ADMIN))
```

For larger systems, move from simple roles to permission-based access control or policy-based authorization.

## Security Pitfalls

Avoid these mistakes:

- Storing raw passwords.
- Using weak JWT secrets.
- Putting JWTs in URLs.
- Using long-lived access tokens.
- Accepting tokens without checking expiration.
- Trusting the JWT role forever after a user is disabled.
- Skipping HTTPS in production.
- Returning different login errors for "email not found" vs "wrong password".
- Storing refresh tokens insecurely in browser local storage for high-risk apps.

## How Authentication Scales

JWT access tokens scale well because normal API requests do not need a central session lookup. Any API replica can validate the token if it has the signing secret or public key.

At larger scale, common improvements are:

- Use asymmetric signing such as RS256 with a private signing key and public verification keys.
- Rotate signing keys and expose a JWKS endpoint.
- Store refresh tokens server-side as hashed token records so they can be revoked.
- Use Redis for token denylisting when immediate logout/revocation is required.
- Add rate limiting to signup and login.
- Add email verification and password reset flows.
- Use MFA for admin users.
- Keep auth services highly available because login is a critical path.

The current implementation is a strong starter for a monolith or small distributed system. For a large production system, refresh token rotation and server-side refresh token storage should be added.

# Distributed URL Shortener System

A production-oriented FastAPI starter for a distributed URL shortener using PostgreSQL, Redis, SQLAlchemy, Alembic, and Docker.

## What This System Does

The API creates short links, redirects short codes to original URLs, stores source-of-truth data in PostgreSQL, and uses Redis as a fast lookup cache.

Core flow:

1. Client posts an original URL to `POST /api/v1/urls`.
2. The service generates a random short code.
3. The repository persists the mapping in PostgreSQL.
4. The service warms Redis with `short_code -> original_url`.
5. Redirect requests to `GET /{short_code}` first check Redis, then fall back to PostgreSQL.

## Folder Structure

```text
.
├── alembic/                 # Database migration environment
│   ├── env.py               # Async Alembic configuration using app settings
│   └── versions/            # Generated migration files live here
├── app/
│   ├── core/                # Cross-cutting infrastructure config
│   ├── middleware/          # HTTP middleware and exception handlers
│   ├── models/              # SQLAlchemy ORM entities
│   ├── repositories/        # Database access layer
│   ├── routers/             # FastAPI route definitions
│   ├── schemas/             # Pydantic request/response DTOs
│   ├── services/            # Business logic orchestration
│   ├── utils/               # Small stateless helpers
│   └── main.py              # FastAPI app factory
├── Dockerfile               # API image definition
├── docker-compose.yml       # API, PostgreSQL, and Redis stack
├── alembic.ini              # Alembic CLI config
├── requirements.txt         # Python dependencies
└── .env.example             # Environment variable template
```

## Why Each Folder Exists

`routers` contains HTTP-only concerns: request dependencies, status codes, response models, and route paths. Routers should stay thin.

`services` contains business workflows. For example, URL creation requires short-code generation, uniqueness checks, persistence, and cache warming.

`repositories` isolates database queries. This keeps SQLAlchemy details away from routers and services and makes future storage changes easier.

`models` contains SQLAlchemy ORM classes. These describe database tables and indexes.

`schemas` contains Pydantic models for input and output contracts. They protect the boundary between external API payloads and internal ORM objects.

`core/config` owns application settings, database setup, Redis setup, and logging configuration.

`middleware` contains request-wide behavior such as request logging and centralized error responses.

`utils` contains small reusable helpers that do not need framework or database dependencies.

`alembic` contains migration code so schema changes are versioned and repeatable across environments.

## Clean Architecture Shape

This starter follows a practical layered design:

```text
HTTP request
  -> router
  -> service
  -> repository
  -> database
```

The dependency direction is inward. Routers depend on services, services depend on repositories, and repositories depend on models/database sessions. Business logic does not live in route functions.

## Async Best Practices Used

- FastAPI endpoints are `async def`.
- SQLAlchemy uses `create_async_engine` with `asyncpg`.
- Redis uses `redis.asyncio`.
- Alembic runs migrations through an async engine.
- Blocking work is avoided in request handlers.

## Configuration With `.env`

Copy the template:

```bash
cp .env.example .env
```

Important variables:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/url_shortener
REDIS_URL=redis://redis:6379/0
BASE_URL=http://localhost:8000
SHORT_CODE_LENGTH=8
LOG_LEVEL=INFO
```

Settings are loaded through `pydantic-settings` in `app/core/config.py`. This gives typed, validated configuration and keeps secrets out of source code.

## Running With Docker

```bash
docker compose up --build
```

The API will be available at:

```text
http://localhost:8000
```

Interactive docs:

```text
http://localhost:8000/docs
```

Health check:

```text
GET http://localhost:8000/api/v1/health
```

## Authentication Quick Start

Create a user:

```bash
curl -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"strongpassword123","name":"Example User"}'
```

Login:

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"strongpassword123"}'
```

Use the returned access token:

```bash
curl http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer ACCESS_TOKEN_HERE"
```

More detail is in `docs/authentication.md`.

## Database Migrations

The initial migration is included in `alembic/versions`.

Apply migrations manually:

```bash
docker compose run --rm api alembic upgrade head
```

The API container also runs `alembic upgrade head` on startup.

Create future migrations after model changes:

```bash
docker compose run --rm api alembic revision --autogenerate -m "describe change"
```

## API Examples

Create a short URL:

```bash
curl -X POST http://localhost:8000/api/v1/urls \
  -H "Content-Type: application/json" \
  -d '{"original_url":"https://example.com/some/long/path"}'
```

Response:

```json
{
  "original_url": "https://example.com/some/long/path",
  "short_code": "aB12Cd34",
  "short_url": "http://localhost:8000/aB12Cd34"
}
```

Redirect:

```bash
curl -i http://localhost:8000/aB12Cd34
```

Stats:

```bash
curl http://localhost:8000/api/v1/urls/aB12Cd34
```

## Step-by-Step Concepts

### 1. FastAPI App Factory

`app/main.py` exposes `create_app()`. This pattern makes the app easier to test and lets Gunicorn create workers using the same factory.

### 2. Lifespan Startup and Shutdown

FastAPI's lifespan hook initializes Redis before traffic is served and closes it during shutdown. This avoids creating Redis clients per request.

### 3. PostgreSQL With SQLAlchemy ORM

`app/core/database.py` creates one async engine and one async session factory. Each request receives an `AsyncSession` through dependency injection.

### 4. Redis Cache

`app/core/redis.py` creates a shared async Redis client. URL resolution first checks Redis because redirects are read-heavy and latency-sensitive.

### 5. Repository Layer

`URLRepository` owns database operations: create a URL, find by short code, check uniqueness, and increment click counts.

### 6. Service Layer

`URLService` coordinates business rules. It does not know HTTP status codes, and it does not expose raw SQLAlchemy query details to routers.

### 7. Schemas

Pydantic schemas validate incoming requests and shape outgoing responses. `HttpUrl` rejects invalid URL inputs before business logic runs.

### 8. Exception Handling

Centralized handlers translate validation, HTTP, database, and unexpected errors into consistent JSON responses while logging server-side failures.

### 9. Logging

Request logging middleware emits method, path, status, duration, and request ID. The response includes `X-Request-ID` for tracing.

### 10. Docker

Docker Compose starts the API, PostgreSQL, and Redis together with health checks. This mirrors the production dependency graph in a local environment.

## Production Notes

For a real high-scale deployment, consider:

- Moving click counting to an async queue or Redis counter flush job.
- Adding rate limiting at the edge or via Redis middleware.
- Adding custom aliases with ownership/authentication.
- Adding expiry timestamps for temporary links.
- Using observability tooling such as OpenTelemetry, Prometheus, and structured JSON logs.
- Running multiple API replicas behind a load balancer.
- Using a stronger ID generation strategy such as Snowflake IDs, ULIDs, or a dedicated key-generation service if predictable collision bounds are required.

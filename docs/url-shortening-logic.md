# URL Shortening Logic

This document explains the scalable URL shortening design used by the service.

## Current Flow

For authenticated URL creation:

1. Validate the incoming URL through Pydantic `HttpUrl`.
2. Validate optional custom alias format and optional future expiration.
3. Hash the normalized original URL with SHA-256.
4. If no custom alias or expiration is provided, check whether this user already has an active short URL for the same original URL hash.
5. If a duplicate exists, return the existing short URL.
6. Otherwise, get the next numeric value from PostgreSQL sequence `url_short_code_seq`.
7. Encode that number with Base62.
8. Insert the URL row.
9. Let PostgreSQL unique constraints protect against collisions.
10. Cache the short code in Redis.

## Base62

Base62 uses 62 characters:

```text
0-9 A-Z a-z
```

A normal decimal number uses 10 symbols. Base62 uses 62 symbols, so it can represent large numbers with fewer characters.

Example:

```text
61 decimal  -> z
62 decimal  -> 10
3843 decimal -> zz
3844 decimal -> 100
```

This makes Base62 useful for short URLs because it creates compact, URL-safe identifiers.

## Why Sequence ID + Base62

The implementation uses:

```text
PostgreSQL sequence number -> Base62 short code
```

Benefits:

- No random collision probability.
- Very fast generation.
- Easy to reason about.
- Works well for a single primary PostgreSQL writer.
- Keeps codes compact.

The database still has unique constraints on `short_code` and `custom_alias`. Those constraints are the final source of truth.

## Collision Handling

There are several possible collision scenarios:

- A generated short code conflicts with an existing custom alias.
- A custom alias conflicts with an existing generated code.
- A concurrent request tries to reserve the same alias.

The service handles this with two layers:

1. Pre-check with `code_or_alias_exists`.
2. Database unique constraints on `short_code` and `custom_alias`.

The pre-check is for user-friendly errors. The database constraint is the real concurrency-safe protection.

## Duplicate URL Handling

If the same authenticated user submits the same original URL again without a custom alias or expiration, the service returns the existing active URL instead of creating another row.

This is powered by:

```text
original_url -> SHA-256 hash -> original_url_hash
```

The database indexes:

```text
(user_id, original_url_hash, is_active)
```

This avoids indexing the full long URL.

## Custom Alias Support

Custom aliases allow a user to choose a readable short path:

```json
{
  "original_url": "https://example.com/docs",
  "custom_alias": "docs"
}
```

The short URL becomes:

```text
http://localhost:8000/docs
```

Aliases are limited to letters, numbers, underscore, and hyphen. They are globally unique.

## URL Expiration

`expires_at` allows temporary links.

Lookup queries reject expired URLs:

```sql
expires_at IS NULL OR expires_at > now()
```

Redis cache TTL is also capped so cached redirects do not outlive the URL expiration.

## Random IDs vs Hashing vs Sequence IDs

### Random IDs

Random codes are easy to generate independently across many servers.

Tradeoffs:

- Collisions are possible.
- Collision probability grows with traffic.
- You need retry logic and unique constraints.
- Good randomness must come from secure random generators.

### Hashing

Hashing the original URL can produce deterministic short codes.

Tradeoffs:

- Same URL always maps to the same code unless salted.
- Hash output usually needs truncation, which reintroduces collisions.
- Can leak that two users shortened the same URL.
- Harder to support multiple short links for the same URL.

### Database Sequence IDs

Sequence IDs are simple and collision-free within one database writer.

Tradeoffs:

- Codes are predictable unless transformed or shuffled.
- A single sequence can become coordination-heavy in multi-region systems.
- Needs a database round trip unless IDs are allocated in batches.

This project uses sequence IDs plus Base62 because it is simple, fast, and production-friendly for a single primary database setup.

## Bitly-Like Systems Internally

A Bitly-like system usually has:

- API service for creation and management.
- Redirect service optimized for low latency.
- Key-generation service or distributed ID generator.
- PostgreSQL, MySQL, Cassandra, DynamoDB, or similar storage for mappings.
- Redis or CDN edge cache for hot links.
- Analytics pipeline for click events.
- Background workers for aggregation, abuse checks, and expiration.

The redirect path is usually extremely lean:

```text
short code -> cache lookup -> storage lookup -> redirect
```

Analytics is often asynchronous so redirects stay fast.

## Distributed ID Generation

At high scale, one database sequence may not be enough. Alternatives include:

- Snowflake-style IDs: timestamp + worker ID + sequence.
- Segment allocation: each app instance reserves a block of IDs.
- Redis atomic counters.
- Database sequences per shard.
- UUID/ULID-based identifiers.

The goal is to avoid coordination while still producing unique IDs.

## Scaling URL Lookups

Redirects are read-heavy. The usual scaling path is:

1. Cache hot short codes in Redis.
2. Add database indexes on lookup columns.
3. Add read replicas for lookup reads if needed.
4. Use CDN or edge caching for extremely hot public links.
5. Split analytics writes from redirect latency.
6. Partition or shard the mapping table when one database no longer fits.

The most important rule: do not let every redirect hit the primary database.

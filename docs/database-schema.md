# Database Schema Design

This document explains the scalable PostgreSQL schema for the distributed URL shortener.

## Tables

### users

Stores accounts that own shortened URLs.

Important columns:

- `id`: UUID primary key.
- `email`: unique login/contact identifier.
- `name`: optional display name.
- `is_active`: soft account status.
- `created_at`, `updated_at`: audit timestamps.

Why this table exists:

Users are separate from URLs because one user can own many URLs. Keeping users separate avoids repeating user information on every URL row.

### urls

Stores the canonical URL mapping.

Important columns:

- `id`: UUID primary key.
- `user_id`: optional foreign key to `users.id`.
- `original_url`: destination URL.
- `short_code`: generated short code, globally unique.
- `custom_alias`: optional user-selected alias, globally unique.
- `clicks`: denormalized aggregate counter for quick stats.
- `is_active`: soft delete/disable flag.
- `expires_at`: optional expiration timestamp.
- `created_at`, `updated_at`: audit timestamps.

Why this table exists:

This is the read-critical table. Redirects need to find one row by `short_code` or `custom_alias` as fast as possible.

### analytics

Stores individual click events.

Important columns:

- `id`: UUID primary key.
- `url_id`: foreign key to `urls.id`.
- `clicked_at`: event timestamp.
- `ip_address`: PostgreSQL `INET` type for IP storage.
- `user_agent`: browser/client metadata.
- `referer`: source page.
- `country`: optional country code.
- `device_type`: optional parsed device category.

Why this table exists:

Analytics is separated from `urls` because one URL can have millions of clicks. Putting every click into the `urls` table would create repeated data and heavy write contention.

## Relationships

```text
users 1 -> many urls
urls  1 -> many analytics
```

Foreign keys:

- `urls.user_id -> users.id` with `ON DELETE SET NULL`
- `analytics.url_id -> urls.id` with `ON DELETE CASCADE`

`ON DELETE SET NULL` preserves short URLs if a user account is removed. `ON DELETE CASCADE` removes analytics when the URL itself is removed.

## Normalization Decisions

The schema is normalized around ownership, URL identity, and click events:

- User data lives once in `users`.
- URL mapping data lives once in `urls`.
- Click event data lives in `analytics`.

This avoids storing repeated user fields on URL rows and avoids storing repeated URL fields on analytics rows.

The `clicks` column in `urls` is intentionally denormalized. It duplicates a count that could be calculated from `analytics`, but it makes common stats reads much faster. In high-scale systems this counter is often updated through Redis counters or an async queue instead of synchronously on every redirect.

## Indexing Strategy

Indexes are added for the queries the system expects to run frequently.

### URL Redirect Lookup

```sql
CREATE INDEX ix_urls_short_code ON urls (short_code);
CREATE INDEX ix_urls_custom_alias ON urls (custom_alias);
CREATE INDEX ix_urls_lookup_active ON urls (short_code, is_active, expires_at);
```

Redirects need to find one URL by short code or custom alias. Without an index, PostgreSQL would scan the table row by row. With an index, PostgreSQL can jump directly to the matching row using a B-tree lookup.

### User Dashboard Queries

```sql
CREATE INDEX ix_urls_user_created_at ON urls (user_id, created_at);
```

This supports queries like "show me all URLs created by this user, newest first".

### Expiration Jobs

```sql
CREATE INDEX ix_urls_expires_at ON urls (expires_at) WHERE expires_at IS NOT NULL;
```

This partial index helps background jobs find expired URLs without indexing rows that never expire.

### Analytics Queries

```sql
CREATE INDEX ix_analytics_url_clicked_at ON analytics (url_id, clicked_at);
CREATE INDEX ix_analytics_clicked_at ON analytics (clicked_at);
CREATE INDEX ix_analytics_country_clicked_at ON analytics (country, clicked_at);
```

These support per-URL time series, global time-window reporting, and country-based reporting.

## Why Indexes Are Needed

Indexes trade extra storage and write overhead for much faster reads.

Without an index on `short_code`, a redirect lookup on a table with 100 million URLs may require scanning many rows. With an index, PostgreSQL uses the short code to navigate a compact B-tree structure and find the row in logarithmic time.

For a URL shortener, redirect lookup is the hottest path. That lookup must be indexed.

## How URL Lookup Performance Works

The ideal redirect path is:

1. Check Redis with key `url:{short_code}`.
2. If Redis hits, return the original URL immediately.
3. If Redis misses, query PostgreSQL using the indexed `short_code` or `custom_alias`.
4. Store the result back in Redis with a TTL.
5. Redirect the user.

Redis handles repeated hot links. PostgreSQL remains the source of truth.

## UUID vs Auto-Increment IDs

### UUID Benefits

- Safer to expose in APIs because they are hard to guess.
- Can be generated independently across distributed services.
- Avoid coordination bottlenecks when multiple writers exist.
- Better for public identifiers.

### UUID Costs

- Larger than integers: 16 bytes instead of 4 or 8 bytes.
- Random UUIDs can fragment B-tree indexes more than sequential IDs.
- Joins and indexes consume more memory.

### Auto-Increment Benefits

- Small and fast.
- Great locality in indexes.
- Excellent for high-write internal event tables.

### Auto-Increment Costs

- Easy to enumerate if exposed publicly.
- Sequence coordination can matter in multi-region writes.
- Can leak business volume.

### Decision Here

This schema uses UUIDs for `users`, `urls`, and `analytics` because these records may be referenced across services or exposed through APIs. At extreme analytics scale, `analytics.id` could be changed to `BIGINT` or the table could be partitioned by time.

## How Queries Scale

### Redirect Query

The critical query is:

```sql
SELECT *
FROM urls
WHERE short_code = :code
  AND is_active = true
  AND (expires_at IS NULL OR expires_at > now());
```

This scales because `short_code` is unique and indexed. PostgreSQL should only need to find one matching row.

### User URL List Query

```sql
SELECT *
FROM urls
WHERE user_id = :user_id
ORDER BY created_at DESC
LIMIT 50;
```

This scales because of the `(user_id, created_at)` index.

### Analytics Query

```sql
SELECT date_trunc('day', clicked_at), count(*)
FROM analytics
WHERE url_id = :url_id
  AND clicked_at >= :start
GROUP BY 1;
```

This scales for moderate data volumes because of the `(url_id, clicked_at)` index. At very high volume, analytics should be partitioned by time and/or streamed into an OLAP system.

## How Database Bottlenecks Occur

Common bottlenecks in real URL shorteners:

- Too many redirects hitting PostgreSQL instead of Redis.
- Missing index on `short_code`.
- Synchronous analytics inserts on every redirect.
- Updating `urls.clicks` on every click, causing row-level write contention.
- Analytics table growing without partitioning.
- Large indexes no longer fitting in memory.
- Too many open database connections from many API replicas.

Typical mitigations:

- Cache hot redirects in Redis.
- Use connection pooling.
- Batch analytics writes through Kafka, Redis Streams, or a background worker.
- Store click counters in Redis and flush periodically.
- Partition analytics by month/week/day.
- Add read replicas for dashboard and analytics reads.

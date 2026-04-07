PROJECT: Private Torrent Distribution Platform
DOCUMENT: Architecture / Implementation Spec
VERSION: v0.8 Implementation Status Alignment
STATUS DATE: 2026-04-07
TARGET USERS: 20-50
DEPLOYMENT: Docker Compose
TRACKER: External tracker service (primary choice: XBT Tracker; fallback: Torrust Tracker)
WEBSITE: FastAPI + Vue 3
DATABASE: PostgreSQL
CACHE: Redis + tracker snapshot cache tables

Status note:

- This document is still the target architecture / implementation spec.
- It now also records the current repository implementation status as of 2026-04-07.
- "Implemented" below means the code exists in the repository; it does not imply the Docker stack, XBT announce flow, or BT client behavior has been fully runtime-accepted.
- Basic static verification completed on 2026-04-07: `npm run build` in `frontend/` and `python -m compileall backend/app` both passed.
- Follow-up static verification completed on 2026-04-07 after the MVP-gap pass: `npm run build` in `frontend/`, `python -m compileall backend/app backend/alembic`, and `git diff --check` passed.
- Follow-up static verification completed on 2026-04-07 after the Compose/auth-rate-limit/UI-feedback pass: `npm run build` in `frontend/`, `python -m compileall backend/app backend/alembic`, and `git diff --check` passed.
- Follow-up static verification completed on 2026-04-07 after the SQLAdmin/ConfirmDialog pass: `npm run build` in `frontend/`, `python -m compileall backend/app backend/alembic`, and `git diff --check` passed.
- Follow-up static verification completed on 2026-04-07 after the bigint/audit-log pass: `npm run build` in `frontend/`, `python -m compileall backend/app backend/alembic`, and `git diff --check` passed.
- Follow-up static verification completed on 2026-04-07 after the unified API error-envelope pass: `npm run build` in `frontend/`, `python -m compileall backend/app`, `git diff --check`, and a lightweight FastAPI TestClient error-shape check passed.
- Follow-up static verification completed on 2026-04-07 after the admin/security/RSS-key-rotation pass: `npm run build` in `frontend/`, `python -m compileall backend/app backend/alembic`, and `git diff --check` passed.
- Development data policy: this project is not published yet and is only being run for local testing. Historical local database compatibility is not a requirement at this stage. If a schema change conflicts with local test data, it is acceptable to clear the local Docker data directories/volumes and recreate the database. Alembic may remain as tooling, but migration compatibility is not an MVP acceptance requirement.

================================================
CURRENT IMPLEMENTATION SNAPSHOT (2026-04-07)
================================================

Implemented in the repository:

- FastAPI backend structure, Vue 3/Vite/Tailwind frontend structure, Dockerfiles, and Docker Compose stack.
- PostgreSQL, Redis, backend, frontend, Nginx, XBT tracker, and XBT tracker-db services are declared.
- User registration, login, basic in-memory auth rate limiting, JWT bearer auth, `/api/auth/me`, and profile APIs.
- Role enum values `admin`, `uploader`, and `user`; first registered user becomes `admin`.
- Per-user `tracker_credential` and separate `rss_key` generation.
- Categories, torrents, torrent files, download logs, tracker user stats cache, and tracker torrent stats cache models.
- Torrent upload API with `.torrent` validation, 10 MiB size limit, bencode parsing, info_hash extraction, file list extraction, duplicate info_hash rejection, original torrent file storage, and a dedicated `nfo_text` input path.
- Torrent list and detail APIs and pages.
- Download endpoint that reads the original torrent, rewrites `announce` and `announce-list` in memory, records `download_logs`, and returns a rewritten `.torrent`.
- RSS feed endpoints and RSS download endpoint using `rss_key`, with non-active users rejected during RSS key authentication.
- SQLAdmin internal admin integration and admin APIs for users, categories, torrents, site settings, and manual tracker sync.
- SQLAdmin user role/status edits now enforce the last-active-admin rule and run the same XBT user sync path as the Admin API.
- XBT integration code for user/torrent provisioning and direct XBT DB stat readback.
- Configurable scheduled tracker stats sync loop via `TRACKER_SYNC_INTERVAL_SECONDS`.
- New password hashes use bcrypt; legacy `pbkdf2_sha256` hashes remain verifiable for login-time upgrade.
- Alembic migration coverage includes `site_settings` and `audit_logs`.
- Bigint alignment is implemented for primary IDs, foreign keys, torrent sizes, file sizes, and tracker traffic byte counters, with a SQLite-compatible local-test variant.
- Admin API write operations now record baseline audit logs for site settings, users, categories, torrents, and manual tracker sync; SQLAdmin includes a read-only Audit Log view.
- API errors now use a shared JSON response envelope with `detail`, `error.code`, `error.message`, `error.status_code`, `error.request_id`, and optional `error.details`; `X-Request-ID` is set on responses and exposed to the frontend API client.
- Frontend routes and pages for login, register, torrent list, torrent detail, upload, profile, RSS, and admin entry.
- AppShell, header/sidebar navigation, responsive torrent table/card display, route-level lazy loading, route transitions, basic skeleton loaders, inline error states, shared toast and confirm feedback, local appearance preferences, RSS key self-rotation, admin audit-log panel, and frontend admin panels for users, categories, and torrent operations.
- Baseline security hardening now includes configurable trusted hosts, backend and Nginx security headers, production startup refusal for default secrets, profile avatar URL scheme validation, and stricter registration normalization.

Partially implemented or pending runtime verification:

- XBT container, XBT schema, provisioning code, and `xbt_db` sync path exist, but the final XBT PoC and BT client announce validation remain pending.
- Tracker stats cache display, admin-triggered sync, and configurable 30-60 second scheduled sync loop exist; runtime acceptance against live XBT data remains pending.
- Redis is part of the stack and has a helper module, but it is not yet materially used as a hot stats cache.
- RSS XML generation and RSS download rewriting exist, but downloader consumption should still be tested end-to-end.
- SQLAdmin user role/status hooks exist for last-active-admin protection and XBT sync; browser-level runtime acceptance remains pending.
- Frontend route guards, route-level lazy loading, shared toast feedback, and a shared confirm dialog exist; deeper accessibility polish remains future hardening work.

Known implementation deviations to resolve before MVP acceptance:

- [x] Completed - New password hashes now use bcrypt; legacy `pbkdf2_sha256` hashes remain supported only for login-time upgrade.
- [x] Completed - RSS key lookup rejects non-active users in both feed and RSS download paths.
- [x] Completed - The Docker Compose public entrypoint is now Nginx on host `80:80`; the `frontend` service stays internal to the Compose network.
- [x] Completed - Alembic now includes a `site_settings` migration; because the project is unpublished and local-test-only, historical database migration compatibility is not required for MVP.
- [x] Completed - `Integer` / `bigint` choices are aligned to bigint for IDs and byte counters in models and fresh Alembic schema, with SQLite remaining usable for local tests.
- [x] Completed - The upload form and API expose a dedicated `nfo_text` input path.
- [x] Completed - Basic in-memory auth rate limiting is implemented for login and registration endpoints.
- [x] Completed - Unified API error response shape and request correlation IDs are implemented for HTTP errors, request validation errors, and unhandled API exceptions.
- [x] Completed for MVP baseline - Security hardening now covers default-secret guardrails, security headers, trusted host configuration, profile URL validation, stricter registration normalization, and a baseline admin audit log. Deeper production security review remains future hardening.

================================================
1. PROJECT GOAL
================================================

Build a lightweight private torrent platform.

This project is not a full forum-style PT community in phase 1.
It is a private torrent distribution website with:

- user accounts
- role-based upload permissions
- torrent metadata pages
- per-user tracker credential download rewriting
- tracker-backed traffic and swarm statistics
- RSS feeds

Immediate required features:

- register/login
- role management
- torrent upload
- torrent list and detail pages
- torrent download endpoint
- tracker integration
- RSS output
- basic internal admin management

Not in current urgent scope:

- comments and forums
- invite system
- messaging
- advanced anti-cheat
- scheduled publishing
- plugin runtime
- full moderation workflow
- custom tracker implementation

================================================
2. IMPLEMENTATION PRINCIPLES
================================================

1. Use an external tracker instead of building a custom tracker.
2. Keep website logic and tracker service separated.
3. The website is the source of truth for users, roles, categories, torrent metadata, and page permissions.
4. The tracker is the source of truth for announce/scrape/peer state and traffic statistics.
5. Every user must have a unique tracker credential.
6. Default to an XBT-style private credential model, but do not hardcode the final announce URL shape until XBT PoC confirms it.
7. Rewrite the torrent announce URL or tracker credential at download time.
8. Keep the backend monolithic in phase 1.
9. Prefer stable open-source components for infrastructure and internal admin tools.
10. Optimize for maintainability and correctness over feature count.

================================================
3. RECOMMENDED STACK
================================================

Frontend:

- Vue 3
- Vite
- Tailwind CSS
- Vue Router
- Pinia
- lightweight headless components only where needed

Frontend UI rule:

- do not build the public site around a heavy visual component framework
- use Tailwind utilities plus shared design tokens for a more modern and consistent data-first interface

Backend:

- FastAPI
- SQLAlchemy 2.x
- Alembic
- Pydantic
- PyJWT or python-jose
- passlib[bcrypt]
- psycopg2 or asyncpg
- redis-py
- feedgen
- torf or a permissive-license bencode library
- SQLAdmin for internal admin pages in MVP

Database:

- PostgreSQL 15+

Cache:

- Redis 7+

Reverse Proxy:

- Nginx

Tracker:

- XBT Tracker (primary choice because it matches PT private passkey or torrent_pass semantics more closely)
- Torrust Tracker (fallback choice because it is more modern and container-friendly, but still needs PT-specific PoC)

================================================
4. HIGH LEVEL ARCHITECTURE
================================================

[ Browser ]
    |
    v
[ Nginx ]
    |
    +--------------------------+
    |                          |
    v                          v
[ Frontend ]              [ Backend API ]
                               |
                 +-------------+-------------+
                 |                           |
                 v                           v
            [ PostgreSQL ]               [ Redis ]
                 |
                 v
      [ tracker snapshot cache tables ]

[ BT Client ] -----------------------> [ Tracker Service: XBT / Torrust ]

Responsibilities:

Frontend:

- login/register pages
- torrent list/detail/upload pages
- profile page
- RSS key display
- user-facing actions

Backend:

- auth
- roles and permissions
- torrent metadata management
- torrent parsing
- torrent download rewriting
- RSS generation
- internal admin
- tracker stats cache refresh

Tracker:

- announce
- scrape
- peer state
- traffic accounting
- seeder/leecher/snatch counts

================================================
5. SERVICE BOUNDARIES
================================================

Website handles:

- users
- roles
- upload permissions
- tracker credential assignment
- RSS key assignment
- categories
- torrent metadata
- torrent pages
- torrent upload
- torrent download rewriting
- RSS
- internal admin

Tracker handles:

- announce requests
- scrape requests
- peer list responses
- uploaded/downloaded accounting
- seeder/leecher state
- snatch/finish counters

Important:

- The website is not allowed to compute official uploaded/downloaded totals by itself.
- Website `download_logs` only record website file downloads, not actual BT transfer volume.
- Website stats pages must display tracker-backed cached stats, not locally inferred values.

================================================
6. ROLES AND PERMISSIONS
================================================

Role enum values:

- admin
- uploader
- user

Permissions:

- user:
  - register/login
  - view allowed pages
  - download rewritten torrents
  - use RSS
- uploader:
  - all user permissions
  - upload torrents
- admin:
  - all uploader permissions
  - manage users and roles
  - manage categories
  - manage torrent visibility and flags
  - appoint other admins and uploaders

Safety rule:

- the system must prevent removal or demotion of the last remaining admin

================================================
7. TRACKER CREDENTIAL MODEL
================================================

Each website user must own one unique tracker credential.

This credential is opaque from the website point of view.
In phase 1, the preferred interpretation is an XBT-style private user credential:

- website-side `tracker_credential` maps directly to the tracker-side private user credential
- the preferred model is similar to `torrent_pass`
- the preferred announce format is an XBT-style `/<tracker_credential>/announce`

Phase 1 rule:

- store one unique `tracker_credential` per user
- use it when rewriting torrent files for that user
- do not hardcode the final URL/path form until XBT PoC confirms it

Decision rule after PoC:

- if XBT PoC succeeds, freeze the tracker model around native XBT private credentials
- if XBT proves unsuitable for deployment or sync integration, start the Torrust fallback PoC
- only if XBT is unsuitable should the spec keep `tracker_credential` abstract and map it to a Torrust-compatible form

NexusPHP note:

- NexusPHP may be referenced as a business-pattern example for per-user tracker credentials
- phase 1 does not reuse or port a NexusPHP tracker implementation

================================================
8. STATS OWNERSHIP AND CACHE STRATEGY
================================================

Source of truth:

- tracker user traffic stats come from the selected tracker
- tracker torrent swarm stats come from the selected tracker

Website cache strategy:

- store snapshot cache in PostgreSQL for durable reads
- optionally use Redis for short-lived hot cache
- never edit cached tracker stats manually in admin UI

Preferred sync strategy:

- if XBT is selected, use periodic pull from the XBT tracker database or a small read-only adapter service

Fallback sync strategy:

- if Torrust is selected later and its management API or event path is sufficient, switch to that sync route
- regardless of implementation, MVP refreshes every 30 to 60 seconds

Display rule:

- all website ratio, seeder, leecher, snatch, uploaded, and downloaded values must come from tracker cache

================================================
9. DATABASE SCHEMA
================================================

9.1 users

fields:

- id: bigint primary key
- username: varchar(32), unique, not null
- email: varchar(255), unique, not null
- password_hash: varchar(255), not null
- role: varchar(20), not null, default 'user'
- status: varchar(20), not null, default 'active'
- tracker_credential: varchar(128), unique, not null
- rss_key: varchar(64), unique, not null
- created_at: timestamptz, not null
- updated_at: timestamptz, not null
- last_login_at: timestamptz, null

status enum values:

- active
- banned
- pending

9.2 categories

fields:

- id: bigint primary key
- name: varchar(64), not null
- slug: varchar(64), unique, not null
- sort_order: int, default 0
- is_enabled: boolean, default true
- created_at: timestamptz, not null

9.3 torrents

fields:

- id: bigint primary key
- name: varchar(255), not null
- subtitle: varchar(255), null
- description: text, null
- info_hash: varchar(40), unique, not null
- size_bytes: bigint, not null
- owner_id: bigint, foreign key users.id, not null
- category_id: bigint, foreign key categories.id, not null
- torrent_path: varchar(1024), not null
- cover_image_url: varchar(1024), null
- nfo_text: text, null
- media_info: text, null
- is_visible: boolean, default true
- is_free: boolean, default false
- created_at: timestamptz, not null
- updated_at: timestamptz, not null

9.4 torrent_files

fields:

- id: bigint primary key
- torrent_id: bigint, foreign key torrents.id, not null
- file_path: varchar(2048), not null
- file_size_bytes: bigint, not null

9.5 download_logs

fields:

- id: bigint primary key
- torrent_id: bigint, foreign key torrents.id, not null
- user_id: bigint, foreign key users.id, not null
- ip: varchar(64), not null
- downloaded_at: timestamptz, not null

Meaning:

- this table tracks website download actions only
- it is not tracker traffic truth

9.6 tracker_user_stats_cache

fields:

- user_id: bigint primary key, foreign key users.id
- uploaded_bytes: bigint, not null, default 0
- downloaded_bytes: bigint, not null, default 0
- ratio: numeric(18,6), null
- updated_at: timestamptz, not null
- source: varchar(32), not null, default 'tracker'

Meaning:

- snapshot cache of tracker-backed user traffic stats

9.7 tracker_torrent_stats_cache

fields:

- torrent_id: bigint primary key, foreign key torrents.id
- seeders: int, not null, default 0
- leechers: int, not null, default 0
- snatches: int, not null, default 0
- finished: int, not null, default 0
- updated_at: timestamptz, not null
- source: varchar(32), not null, default 'tracker'

Meaning:

- snapshot cache of tracker-backed torrent stats

Phase 1 non-goal:

- do not maintain a website-owned `peers` table unless the selected tracker integration later proves it is necessary

================================================
10. BACKEND PROJECT STRUCTURE
================================================

backend/
  app/
    main.py
    core/
      config.py
      security.py
      database.py
      redis.py
    api/
      auth.py
      users.py
      torrents.py
      rss.py
      admin.py
    models/
      user.py
      category.py
      torrent.py
      torrent_file.py
      download_log.py
      tracker_user_stats_cache.py
      tracker_torrent_stats_cache.py
    schemas/
      auth.py
      user.py
      torrent.py
      rss.py
      admin.py
      tracker_stats.py
    services/
      auth_service.py
      user_service.py
      torrent_service.py
      torrent_download_service.py
      torrent_parse_service.py
      rss_service.py
      tracker_sync_service.py
      tracker_credential_service.py
    dependencies/
      auth.py
      roles.py
      admin.py
  alembic/
  requirements.txt
  Dockerfile

================================================
11. FRONTEND PROJECT STRUCTURE
================================================

frontend/
  src/
    api/
      auth.ts
      torrents.ts
      users.ts
      rss.ts
      admin.ts
    layouts/
      AppShell.vue
    router/
      index.ts
    stores/
      auth.ts
      appearance.ts
    composables/
      usePageTransition.ts
      useAppearance.ts
    styles/
      app.css
      tokens.css
    views/
      LoginView.vue
      RegisterView.vue
      TorrentListView.vue
      TorrentDetailView.vue
      UploadTorrentView.vue
      ProfileView.vue
    App.vue
    main.ts
  package.json
  Dockerfile

Internal admin UI strategy in MVP:

- use SQLAdmin for internal admin pages served by FastAPI
- do not require admin UI to be implemented in Vue in phase 1

================================================
12. API SPECIFICATION
================================================

12.1 Authentication

POST /api/auth/register

request:

{
  "username": "alice",
  "email": "alice@example.com",
  "password": "strong-password"
}

response:

{
  "id": 1,
  "username": "alice",
  "email": "alice@example.com",
  "role": "user"
}

POST /api/auth/login

response:

{
  "access_token": "jwt-token",
  "token_type": "bearer"
}

GET /api/auth/me

response:

{
  "id": 1,
  "username": "alice",
  "email": "alice@example.com",
  "role": "user",
  "tracker_credential": "masked",
  "rss_key": "masked"
}

12.2 User APIs

- GET /api/users/profile
- PATCH /api/users/profile

12.3 Torrent APIs

- GET /api/torrents
- GET /api/torrents/{id}
- POST /api/torrents/upload
- GET /api/torrents/{id}/download

Upload permission:

- only `admin` and `uploader` can upload

Download behavior:

- require authenticated user
- record `download_logs`
- load original torrent bytes
- inject user-specific tracker credential in the selected tracker-compatible format
- return rewritten torrent file

12.4 RSS APIs

- GET /rss/torrents?key=<rss_key>
- GET /rss/category/{slug}?key=<rss_key>
- GET /rss/download/{torrent_id}?key=<rss_key>

12.5 Admin APIs

- GET /api/admin/users
- PATCH /api/admin/users/{id}
- GET /api/admin/torrents
- PATCH /api/admin/torrents/{id}
- GET /api/admin/categories
- POST /api/admin/categories
- PATCH /api/admin/categories/{id}

Admin user payload example:

{
  "role": "uploader",
  "status": "active"
}

Role assignment rules:

- only admins can change roles
- only admins can create other admins
- system must reject demotion of the last admin

12.6 Common response conventions

List endpoints should generally return:

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "page_size": 20
}
```

Error responses should use the shared compatible envelope:

```json
{
  "detail": "Human readable message",
  "error": {
    "code": "some_error_code",
    "message": "Human readable message",
    "status_code": 400,
    "request_id": "request-correlation-id",
    "details": {}
  }
}
```

Notes:

- `detail` remains at the top level for compatibility with older callers.
- `error.details` is optional and is mainly used for validation details.
- API error responses should also include the `X-Request-ID` header.
- time values should use ISO 8601 strings.
- byte fields should use raw integers, not formatted strings.
- `tracker_credential` and `rss_key` should return masked values by default.

================================================
13. AUTHENTICATION AND SECURITY
================================================

Website API auth:

- JWT bearer auth

Password handling:

- bcrypt hash only
- never store plain password

Tracker credential handling:

- generate a unique random opaque secret for each user
- store it once on registration
- allow future rotation in admin/user settings
- do not expose the raw value except where explicitly required

RSS key handling:

- separate from tracker credential
- unique random secret

Security rules:

- validate upload file type is `.torrent`
- enforce upload size limits
- sanitize descriptions if HTML is allowed
- rate-limit auth endpoints
- do not expose raw storage paths
- ban users by website permissions and, if required later, by tracker-side mapping policy

================================================
14. TRACKER INTEGRATION DESIGN
================================================

Primary tracker:

- XBT Tracker

Fallback tracker:

- Torrust Tracker

Deployment rules:

- the tracker must run as its own container or service, not inside the same image as `backend`
- if XBT is selected, provide a separate `tracker-db` based on MySQL or MariaDB
- if Torrust is selected, use either its SQLite volume mode or a dedicated MySQL service

Tracker integration contract:

1. Store original uploaded torrent files unchanged.
2. On each download request, rewrite torrent bytes in memory.
3. Inject a user-specific tracker credential in a tracker-compatible way.
4. Return the rewritten torrent file as attachment.
5. Treat tracker stats as source of truth.
6. Refresh tracker stats into website cache.

PoC gate:

- Before implementation is finalized, complete the XBT PoC and confirm:
  - XBT container deployment is stable in the stack
  - the XBT-style private credential model satisfies PT requirements directly
  - the website can read back user-level and torrent-level stats from XBT
- Only if XBT is unsuitable should the Torrust fallback PoC be executed:
  - can Torrust satisfy PT private-user credential semantics
  - can Torrust expose a sync path suitable for website cache refresh

Implementation rule:

- the spec defaults to an XBT-style private credential model, but it must not freeze one concrete URL form until XBT PoC succeeds

Stats sync rule:

- if XBT is selected, periodic pull is the default MVP sync path
- if Torrust is selected later and its management API or event path is sufficient, use that route instead

================================================
15. TORRENT PARSING RULES
================================================

On upload, parse the `.torrent` file and extract:

- info_hash
- top-level name
- total size
- file list
- piece length if needed

Rules:

- store info_hash as lowercase hex string
- reject duplicate info_hash
- keep original torrent bytes unchanged in storage
- separate display name from original torrent metadata name if needed

================================================
16. RSS FEED RULES
================================================

Each RSS item should include:

- title
- link
- guid
- pubDate
- description
- enclosure

Rules:

- validate `rss_key`
- only include visible torrents
- enclosure should point to an RSS download endpoint that can authenticate by `rss_key`
- some RSS consumers download by enclosure directly, so the RSS download endpoint must support tracker credential rewriting too

================================================
17. PAGE REQUIREMENTS
================================================

User-facing pages:

- Login Page
- Register Page
- Torrent List Page
- Torrent Detail Page
- Upload Page
- Profile Page

Page inventory and purpose:

1. Home / Torrent List Page

- default entry page after login
- in MVP, homepage and torrent list page can be the same page
- primary purpose: browse, search, filter, compare, and enter download flow
- core modules: top search, category filter, sort controls, torrent list, quick stats, pagination, quick download action

2. Torrent Detail Page

- primary purpose: help the user decide whether to download this torrent
- core modules: title summary, download action area, tracker stats summary, basic metadata, description, file list, MediaInfo or NFO, cover image if available

3. Upload Page

- primary purpose: allow `admin` and `uploader` to submit a new torrent with low error rate
- core modules: upload permission notice, torrent file and category section, display metadata section, advanced info section, validation summary, submit action bar

4. Profile / Settings Page

- primary purpose: show account identity, tracker-backed stats, RSS access, and basic personal preferences
- core modules: account info, tracker-backed uploaded and downloaded stats, ratio, masked tracker credential, RSS key area, appearance preferences

5. RSS Access Page or RSS Panel

- primary purpose: expose RSS URLs, usage notes, and copy actions clearly
- this may be a dedicated page or a profile sub-panel in MVP
- core modules: RSS feed URLs, copy buttons, refresh or regenerate action if later supported, usage instructions

6. Login Page

- primary purpose: authenticate quickly with minimal friction
- core modules: username or email input, password input, submit action, error feedback

7. Register Page

- primary purpose: create a user account cleanly
- core modules: username, email, password, confirm password, submit action, validation feedback

8. Internal Admin

- served by SQLAdmin in MVP
- not part of the public frontend visual system
- primary purpose: user, role, category, and torrent management

Internal admin in MVP:

- SQLAdmin-based pages for users, categories, and torrents

Upload page access:

- only `admin` and `uploader`

Profile page display:

- username
- email
- role
- tracker-backed uploaded bytes
- tracker-backed downloaded bytes
- tracker-backed ratio
- rss key
- masked tracker credential

Frontend UI direction:

- the public site should feel like a clean data-first private tracker, not a forum portal
- torrent list readability is more important than decorative visual effects
- desktop-first layout is acceptable, but mobile pages must remain usable
- default theme should be light and neutral; dark mode can wait until later
- category tags, stat badges, and download actions should be visually consistent across list/detail/RSS-related pages
- internal admin pages do not need to match the frontend visual language in MVP

Frontend implementation rules:

- use Tailwind CSS as the primary styling system for the public site
- keep design tokens centralized with CSS variables for colors, spacing, radii, shadows, and z-index layers
- avoid ad-hoc inline style decisions per page
- use one shared app shell with header, content area, and responsive navigation

Layout rules:

- use fluid responsive layout with CSS Grid and Flexbox
- avoid fixed-position page composition except for intentionally sticky navigation or toolbars
- main content should use a max-width container on large screens and comfortable side padding on smaller screens
- desktop should favor a left sidebar plus top header layout
- tablet and mobile should collapse sidebar into a drawer or overlay menu

Navigation and URL behavior:

- list filters, search keywords, sort mode, and pagination should be reflected in URL query parameters
- returning from torrent detail to torrent list should preserve previous list state and scroll position
- each primary page should expose a clear page title and location cue
- destructive or permission-sensitive actions should require explicit confirmation

Torrent list presentation:

- desktop uses a dense but readable table-oriented layout
- mobile should switch to a stacked card list or priority-column layout instead of forcing a wide unreadable table
- download action, title, category, and key stats must remain visible without excessive horizontal scrolling

Motion and transitions:

- page transitions should feel smooth and modern but restrained
- route transitions should animate the content pane, not the entire browser viewport
- prefer opacity and small translate or scale transitions over large sliding or parallax effects
- default transition duration should stay roughly in the 140ms to 220ms range
- use route-aware transitions through Vue Router and `RouterView` slot patterns
- support route-specific transitions only where they add clarity, such as list to detail or modal-like overlays
- respect reduced-motion preferences and provide a low-motion mode

Loading and state feedback:

- use skeleton loaders for list and detail pages
- define empty states for no torrents, no search results, and no upload permission
- define clear inline error states for login, upload, RSS key errors, and tracker stats loading failures
- optimistic UI should be limited to low-risk actions; data integrity is more important than perceived speed
- use toast feedback for successful login, upload completion, role changes, and recoverable warnings

Background and appearance rules:

- default site background should be a solid color, not a large default illustration
- optional user appearance customization may allow a background image URL or background image API source
- custom background images must not reduce text readability; apply overlay, blur, dimming, or contrast safeguards when needed
- custom background fetching should be client-side only in MVP; backend should not proxy arbitrary third-party image URLs
- if host restrictions are needed, support an allowlist for approved image hosts or API domains
- appearance settings may be stored in local storage first; server-side sync can be added later

Visual style rules:

- build the palette relative to the chosen background color so that cards, text, badges, and buttons always keep obvious contrast from the background
- use a light neutral palette with stronger contrast on tables, cards, badges, and action buttons
- visual tone should be modern and crisp, but not glossy or game-like
- border radius, shadow depth, and accent colors should be restrained and consistent
- icon usage should come from one consistent icon family only

Button hierarchy rules:

- each primary area should have only one clearly dominant primary button
- secondary actions should look clearly weaker than the primary action
- danger actions must be visually distinct from normal actions
- danger actions must require a confirmation modal or confirmation step after click before execution

Accessibility and usability:

- keyboard navigation must work for login, filters, upload form, and admin-critical actions
- focus states must remain visible even with custom styling
- contrast should prioritize data legibility over visual subtlety
- touch targets on mobile should remain usable for filters, pagination, and download actions

Performance rules:

- use route-level lazy loading for major pages
- avoid animating expensive layout properties when opacity or transform will achieve the same result
- avoid replaying full-page animations on every small list filter change
- background images and cover images should lazy load when possible
- keyword search inputs should use debounce to reduce unnecessary requests

Appearance settings placement:

- appearance preferences may live in the profile page or in a dedicated settings drawer
- phase 1 appearance preferences can include background mode, custom image source, reduced motion, and list density

================================================
18. DOCKER COMPOSE SPEC
================================================

Required services:

- nginx
- frontend
- backend
- postgres
- redis
- tracker

Example services:

- `postgres`: PostgreSQL 15
- `redis`: Redis 7
- `backend`: FastAPI app
- `frontend`: Vue app
- `tracker`: XBT Tracker (primary) or Torrust Tracker (fallback)
- `tracker-db`: MySQL or MariaDB for XBT; optional MySQL or SQLite volume for Torrust
- tracker runs as a separate service, not inside the `backend` image
- `nginx`: reverse proxy

================================================
19. ENVIRONMENT VARIABLES
================================================

Backend:

- APP_NAME=pt-platform
- APP_ENV=production
- SECRET_KEY=change-me
- JWT_SECRET_KEY=change-me
- JWT_EXPIRE_MINUTES=1440
- DATABASE_URL=postgresql+psycopg2://ptuser:ptpass@postgres:5432/ptapp
- REDIS_URL=redis://redis:6379/0
- TORRENT_STORAGE_PATH=/app/data/torrents
- UPLOAD_STORAGE_PATH=/app/data/uploads
- PUBLIC_WEB_BASE_URL=https://app.example.com
- TRACKER_IMPL=xbt
- TRACKER_BASE_URL=https://tracker.example.com/announce
- TRACKER_CREDENTIAL_MODE=xbt_path
- TRACKER_CREDENTIAL_QUERY_KEY=passkey
- TRACKER_SYNC_MODE=xbt_db
- TRACKER_SYNC_INTERVAL_SECONDS=60
- TRACKER_SYNC_TIMEOUT_SECONDS=10
- TRACKER_USER_STATS_ENDPOINT=
- TRACKER_TORRENT_STATS_ENDPOINT=
- XBT_TRACKER_DB_DSN=mysql+pymysql://tracker:tracker-pass@tracker-db:3306/xbt
- ALLOW_PUBLIC_TORRENT_LIST=true
- ALLOW_USER_REGISTRATION=true
- AUTH_RATE_LIMIT_ENABLED=true
- AUTH_RATE_LIMIT_WINDOW_SECONDS=60
- AUTH_LOGIN_RATE_LIMIT_ATTEMPTS=8
- AUTH_REGISTER_RATE_LIMIT_ATTEMPTS=5
- AUTO_CREATE_TABLES=true
- CORS_ALLOWED_ORIGINS=https://app.example.com

Frontend:

- VITE_API_BASE_URL=https://app.example.com/api
- VITE_DEFAULT_THEME=light
- VITE_ENABLE_PAGE_TRANSITIONS=true
- VITE_ALLOW_CUSTOM_BACKGROUND=true
- VITE_BACKGROUND_HOST_ALLOWLIST=

Note:

- current implementation default is `TRACKER_SYNC_MODE=xbt_db`, using direct XBT database readback through `XBT_TRACKER_DB_DSN`
- [x] Completed - `TRACKER_SYNC_INTERVAL_SECONDS` is implemented as the configurable periodic-sync interval; the current default is 60 seconds, and the target cadence remains 30-60 seconds
- [x] Completed - Auth rate limiting is configurable through the `AUTH_RATE_LIMIT_*` variables and defaults to per-IP in-memory limits for login and registration.
- replace `TRACKER_SYNC_MODE` with a Torrust-specific API or event mode later only if the fallback PoC proves it is suitable

================================================
20. MVP DEVELOPMENT ORDER
================================================

Step 1

- initialize backend and frontend projects
- set up docker compose
- connect postgres and redis

Step 2

- implement users table and auth
- implement roles
- implement tracker credential generation
- implement frontend login/register flow

Step 3

- implement categories and torrents schema
- implement torrent upload API
- implement torrent parsing utility
- save uploaded torrent file

Step 4

- implement torrent list API and page
- implement torrent detail API and page
- implement SQLAdmin internal admin

Step 5

- implement download endpoint with per-user tracker credential rewrite
- implement RSS endpoints

Step 6

- deploy XBT Tracker
- complete XBT tracker credential PoC
- confirm BT client announce success

Step 7

- implement tracker stats cache sync
- show tracker-backed stats on pages

Step 8

- harden permissions
- polish UI
- implement shared app shell, transitions, and appearance preferences

Current step status as of 2026-04-07:

- [x] Step 1 is implemented in code.
- [x] Step 2 is implemented in code; bcrypt-only new password hashing is aligned, with legacy `pbkdf2_sha256` kept only for login-time upgrade.
- [x] Step 3 is implemented in code, including the dedicated `nfo_text` upload path; additional production validation remains future hardening.
- [x] Step 4 is implemented in code.
- [x] Step 5 is implemented in code and still needs downloader/RSS consumption runtime testing.
- [ ] Step 6 is partially implemented: XBT container/config/schema and provisioning code exist, but XBT PoC and BT client announce validation are not complete.
- [x] Step 7 scheduled-sync code is implemented: cache tables, display paths, XBT DB sync code, manual admin sync, and configurable 30-60 second scheduled sync exist; live XBT runtime verification remains pending.
- [x] Step 8 MVP baseline is implemented: AppShell, transitions, responsive layout, appearance preferences, route-level lazy loading, shared toast feedback, SQLAdmin role/status hardening, shared confirm dialogs, frontend admin management panels, RSS key rotation, a baseline admin audit log, security header/default-secret hardening, and a unified API error envelope exist. Deeper accessibility polish and production security review remain future hardening.

================================================
21. ACCEPTANCE CRITERIA
================================================

The system is minimally usable when all of the following work:

1. A user can register and log in.
2. An admin can appoint an uploader or another admin.
3. An uploader or admin can upload a torrent.
4. The uploaded torrent appears on the torrent list page.
5. A user can open the torrent detail page.
6. A user can download a rewritten torrent.
7. The rewritten torrent contains a unique tracker credential for that user in the confirmed tracker-compatible format.
8. A BT client can announce to the selected tracker successfully; MVP defaults to XBT as the validation target.
9. The website can display tracker-backed uploaded/downloaded and torrent swarm stats from cache.
10. RSS endpoint returns valid XML.
11. RSS feed can be consumed by a downloader.

Current acceptance status as of 2026-04-07:

- [x] Items 1-7 are implemented in code, including frontend admin role/status management, but still need full Docker-stack regression testing.
- [ ] Item 8 is pending and is the main PoC gate.
- [x] Item 9 code paths are implemented, including cache read/display and scheduled refresh; real XBT data verification remains pending.
- [x] Items 10-11 have code paths implemented; valid XML and downloader consumption should still be verified against a running deployment.

================================================
22. OPEN QUESTIONS / POC CHECKLIST
================================================

These items must be validated before freezing the final tracker implementation:

1. What exact announce URL form, private credential format, and stats readback path will be used for XBT in the deployed stack?
2. Should the website sync XBT stats by direct database reads, read-only views, or a small adapter service?
3. If XBT proves unsuitable operationally, can Torrust satisfy PT-style per-user credential and stats ownership requirements?
4. If Torrust is used as fallback, which management API, event, or pull path is appropriate, and what refresh interval should be used?
5. Does phase 1 need tracker-side ban synchronization, or is website-side download denial enough?
6. [x] Resolved on 2026-04-07: the public Docker Compose entrypoint is Nginx on host port 80; the frontend service is no longer directly published on host port 8080.
7. [x] Resolved on 2026-04-07: SQLAdmin may keep direct user role/status edits, but those edits now run model-hook protection for the last-active-admin rule and XBT user sync path.
8. [x] Resolved on 2026-04-07: RSS key authentication explicitly rejects all non-active users in the shared RSS key lookup path used by both feed and RSS download endpoints.

Until these are verified, the spec intentionally keeps the tracker credential transport and sync transport abstract.

================================================
END OF DOCUMENT
================================================

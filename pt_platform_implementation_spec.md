PROJECT: Private Torrent Distribution Platform
DOCUMENT: Architecture / Implementation Spec
VERSION: v0.5 Frontend Pages Draft
TARGET USERS: 20-50
DEPLOYMENT: Docker Compose
TRACKER: External tracker service (primary choice: Trunker)
WEBSITE: FastAPI + Vue 3
DATABASE: PostgreSQL
CACHE: Redis + tracker snapshot cache tables

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
6. Do not hardcode the tracker credential transport format until Trunker PoC confirms it.
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

- Trunker

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

[ BT Client ] -----------------------> [ Trunker ]

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

This credential is an opaque value from the website point of view.
It may later be represented as:

- a passkey in announce path
- a passkey in query string
- a tracker-recognized token
- a website-to-tracker mapping key

Phase 1 rule:

- store one unique `tracker_credential` per user
- use it when rewriting torrent files for that user
- do not hardcode the exact Trunker credential shape in the spec until PoC confirms it

Decision rule after PoC:

- if Trunker natively supports per-user passkey-style credentials, use that directly
- otherwise add a small mapping layer between website users and tracker-recognizable credentials

NexusPHP note:

- NexusPHP may be referenced as a business-pattern example for per-user tracker credentials
- phase 1 does not reuse or port a NexusPHP tracker implementation

================================================
8. STATS OWNERSHIP AND CACHE STRATEGY
================================================

Source of truth:

- tracker user traffic stats come from Trunker
- tracker torrent swarm stats come from Trunker

Website cache strategy:

- store snapshot cache in PostgreSQL for durable reads
- optionally use Redis for short-lived hot cache
- never edit cached tracker stats manually in admin UI

Preferred sync strategy:

- use Trunker push or event integration if confirmed by PoC

Fallback sync strategy:

- periodic pull from Trunker-supported stats/admin endpoints every 30 to 60 seconds

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
- source: varchar(32), not null, default 'trunker'

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
- source: varchar(32), not null, default 'trunker'

Meaning:

- snapshot cache of tracker-backed torrent stats

Phase 1 non-goal:

- do not maintain a website-owned `peers` table unless Trunker integration later proves it is necessary

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
- inject user-specific tracker credential in the Trunker-compatible format
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

- Trunker

Tracker integration contract:

1. Store original uploaded torrent files unchanged.
2. On each download request, rewrite torrent bytes in memory.
3. Inject a user-specific tracker credential in a Trunker-compatible way.
4. Return the rewritten torrent file as attachment.
5. Treat tracker stats as source of truth.
6. Refresh tracker stats into website cache.

PoC gate:

- Before implementation is finalized, confirm exactly how Trunker recognizes a unique website user:
  - native passkey-style credential
  - token or query-based credential
  - tracker-side app/user mapping
  - custom bridge service

Implementation rule:

- the spec must not assume `announce/<passkey>` until the PoC proves that format

Stats sync rule:

- if Trunker supports a suitable push/event path for website sync, use it
- otherwise implement periodic pull sync as the default MVP path

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
- `tracker`: Trunker
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
- TRACKER_BASE_URL=https://tracker.example.com
- TRACKER_SYNC_MODE=pull
- TRACKER_SYNC_INTERVAL_SECONDS=30
- ALLOW_PUBLIC_TORRENT_LIST=true
- ALLOW_USER_REGISTRATION=true

Frontend:

- VITE_API_BASE_URL=https://app.example.com/api
- VITE_DEFAULT_THEME=light
- VITE_ENABLE_PAGE_TRANSITIONS=true
- VITE_ALLOW_CUSTOM_BACKGROUND=true
- VITE_BACKGROUND_HOST_ALLOWLIST=

Note:

- replace `TRACKER_SYNC_MODE` with push/event mode later if Trunker PoC confirms it

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

- deploy Trunker
- complete tracker credential PoC
- confirm BT client announce success

Step 7

- implement tracker stats cache sync
- show tracker-backed stats on pages

Step 8

- harden permissions
- polish UI
- implement shared app shell, transitions, and appearance preferences

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
7. The rewritten torrent contains a unique tracker credential for that user in the confirmed Trunker-compatible format.
8. A BT client can announce to Trunker successfully.
9. The website can display tracker-backed uploaded/downloaded and torrent swarm stats from cache.
10. RSS endpoint returns valid XML.
11. RSS feed can be consumed by a downloader.

================================================
22. OPEN QUESTIONS / POC CHECKLIST
================================================

These items must be validated before freezing the final tracker implementation:

1. What exact per-user credential format does Trunker support for announce authentication?
2. Does Trunker expose a direct mechanism suitable for syncing per-user and per-torrent stats into the website?
3. If Trunker has push/event integration, is it sufficient for website cache refresh?
4. If not, which pull endpoint and refresh interval are appropriate?
5. Does phase 1 need tracker-side ban synchronization, or is website-side download denial enough?

Until these are verified, the spec intentionally keeps the tracker credential transport and sync transport abstract.

================================================
END OF DOCUMENT
================================================

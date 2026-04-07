PROJECT: 私有种子分发平台
DOCUMENT: 架构 / 实施规格说明（中文版）
VERSION: v0.8 实现状态对齐版（ZH-CN）
STATUS DATE: 2026-04-07
SOURCE: 对应 `pt_platform_implementation_spec.md`
TARGET USERS: 20-50
DEPLOYMENT: Docker Compose
TRACKER: 外部 Tracker 服务（首选：XBT Tracker；备选：Torrust Tracker）
WEBSITE: FastAPI + Vue 3
DATABASE: PostgreSQL
CACHE: Redis + Tracker 统计快照缓存表

说明：

- 本文是英文 spec 的中文对照版。
- API 路径、数据表字段名、环境变量名、目录名尽量保持英文原样，避免后续实现时对不上。
- 本文里的“站点”指 Web 站点与后端 API；“Tracker”指独立 Tracker 服务，默认指 XBT Tracker。
- 本文仍然是目标架构 / 实施规格，同时从 v0.8 开始记录当前仓库实现状态。
- 下文“已实现”表示代码已在仓库中存在，不等于 Docker 栈、XBT announce 或 BT 客户端行为已经完成运行时验收。
- 2026-04-07 已完成基础静态验证：`frontend/` 下 `npm run build` 通过，`python -m compileall backend/app` 通过。
- 2026-04-07 MVP 缺口修补后已再次完成静态验证：`frontend/` 下 `npm run build` 通过，`python -m compileall backend/app backend/alembic` 通过，`git diff --check` 通过。
- 2026-04-07 Compose / 认证限流 / UI 反馈补强后已再次完成静态验证：`frontend/` 下 `npm run build` 通过，`python -m compileall backend/app backend/alembic` 通过，`git diff --check` 通过。
- 2026-04-07 SQLAdmin / ConfirmDialog 补强后已再次完成静态验证：`frontend/` 下 `npm run build` 通过，`python -m compileall backend/app backend/alembic` 通过，`git diff --check` 通过。
- 2026-04-07 bigint / audit log 补强后已再次完成静态验证：`frontend/` 下 `npm run build` 通过，`python -m compileall backend/app backend/alembic` 通过，`git diff --check` 通过。
- 开发数据策略：本项目尚未发布，目前只在本地测试运行；此阶段不要求兼容历史本地数据库数据。若 schema 改动与本地测试数据冲突，可以清空本地 Docker 数据目录 / volume 后重新建库。Alembic 可以作为工具保留，但“迁移兼容性”不是 MVP 验收要求。

================================================
当前实现状态快照（2026-04-07）
================================================

仓库中已实现：

- FastAPI 后端结构、Vue 3 / Vite / Tailwind 前端结构、Dockerfile 与 Docker Compose 栈。
- PostgreSQL、Redis、backend、frontend、Nginx、XBT tracker、XBT tracker-db 服务声明。
- 用户注册、登录、基础内存认证限流、JWT bearer auth、`/api/auth/me` 与 Profile API。
- 角色枚举 `admin`、`uploader`、`user`；首个注册用户自动成为 `admin`。
- 每用户 `tracker_credential` 与独立 `rss_key` 生成。
- categories、torrents、torrent_files、download_logs、tracker_user_stats_cache、tracker_torrent_stats_cache 模型。
- 种子上传 API，包括 `.torrent` 校验、10 MiB 大小限制、bencode 解析、info_hash 提取、文件列表提取、重复 info_hash 拒绝、原始 torrent 文件保存，以及独立 `nfo_text` 输入路径。
- 种子列表 API / 页面与种子详情 API / 页面。
- 下载端点：读取原始 torrent，在内存中重写 `announce` 与 `announce-list`，写入 `download_logs`，返回重写后的 `.torrent`。
- RSS feed 端点与基于 `rss_key` 的 RSS 下载端点，并在 RSS key 鉴权时拒绝非 active 用户。
- SQLAdmin 内部后台，以及用户、分类、种子、站点设置、手动 tracker sync 的 Admin API。
- SQLAdmin 用户 role/status 编辑现在会执行最后一个 active admin 保护，并走与 Admin API 一致的 XBT 用户同步路径。
- XBT 用户 / 种子 provision 与 XBT 数据库直读统计同步代码。
- 通过 `TRACKER_SYNC_INTERVAL_SECONDS` 配置的周期性 tracker 统计同步循环。
- 新密码 hash 使用 bcrypt；旧 `pbkdf2_sha256` hash 仅保留登录时校验并升级的兼容路径。
- Alembic 迁移已包含 `site_settings` 与 `audit_logs`。
- 主键 ID、外键、种子大小、文件大小和 tracker 流量字节计数已对齐为 bigint，并保留 SQLite 本地测试兼容变体。
- Admin API 写操作现在会为站点设置、用户、分类、种子和手动 tracker sync 记录基础审计日志；SQLAdmin 中也提供只读 Audit Log 视图。
- 前端登录、注册、种子列表、种子详情、上传、Profile、RSS、Admin 入口页面与路由。
- AppShell、header/sidebar 导航、响应式种子表格 / 卡片、路由级懒加载、路由过渡、基础 skeleton loader、内联错误状态、共享 toast 与 confirm 反馈、本地外观偏好，以及 admin 审计日志面板。

部分实现或等待运行时验证：

- XBT 容器、XBT schema、provision 代码与 `xbt_db` 同步路径已经存在，但最终 XBT PoC 与 BT 客户端 announce 验证仍未完成。
- Tracker 统计缓存展示、Admin 手动触发 sync、可配置的 30-60 秒周期同步循环已经存在；真实 XBT 数据回读仍需运行时验收。
- Redis 已在栈中并有 helper 模块，但暂未真正作为热点统计缓存使用。
- RSS XML 生成与 RSS 下载重写已实现，但仍需要用真实下载器做端到端消费验证。
- SQLAdmin 用户 role/status model hook 已支持最后一个 active admin 保护与 XBT 用户同步；仍需在浏览器中做运行时验收。
- 前端路由守卫、route-level lazy loading、共享 toast 反馈与共享 confirm 对话框已实现；更完整的可访问性打磨仍是后续强化项。

MVP 验收前需要处理的已知偏差：

- [x] 已完成 - 新密码 hash 现在使用 bcrypt；旧 `pbkdf2_sha256` hash 仅保留登录时校验并升级的兼容路径。
- [x] 已完成 - RSS key 查询已经在 feed 与 RSS 下载路径中拒绝非 active 用户。
- [x] 已完成 - Docker Compose 对外入口已明确为宿主机 `80:80` 上的 Nginx；`frontend` 服务仅保留在 Compose 内部网络。
- [x] 已完成 - Alembic 已新增 `site_settings` 迁移；由于项目尚未发布、仅本地测试运行，MVP 阶段不要求兼容历史数据库迁移。
- [x] 已完成 - `Integer` / `bigint` 已在模型和新建库 Alembic schema 中对齐：ID 与字节计数字段使用 bigint，并保留 SQLite 本地测试兼容。
- [x] 已完成 - 上传表单与 API 已有单独的 `nfo_text` 输入路径。
- [x] 已完成 - 登录与注册端点已实现基础内存认证限流。
- [ ] 待处理 - 生产级统一错误返回与更完整的安全加固仍未完成；基础 admin 审计日志已存在。

================================================
1. 项目目标
================================================

构建一个轻量级私有种子平台。

这个项目在第一阶段不是完整的 PT 社区站，也不是论坛型站点。
第一阶段的目标更接近一个“私有种子分发网站”，它需要具备：

- 用户账号体系
- 基于角色的上传权限
- 种子元数据页面
- 按用户重写 tracker 凭证的下载能力
- 由 tracker 提供真实流量与 swarm 统计
- RSS 订阅能力

当前必须优先完成的能力：

- 注册 / 登录
- 角色管理
- 种子上传
- 种子列表页与详情页
- 种子下载端点
- Tracker 集成
- RSS 输出
- 基础内部管理能力

当前不在紧急范围内的能力：

- 评论和论坛
- 邀请系统
- 站内消息
- 高级反作弊
- 定时发布
- 插件运行时
- 完整审核流程
- 自研 Tracker

================================================
2. 实施原则
================================================

1. 使用外部 Tracker，不自研 Tracker。
2. 站点业务逻辑与 Tracker 服务保持分离。
3. 用户、角色、分类、种子元数据、页面权限以站点为真源。
4. `announce / scrape / peer 状态 / 流量统计` 以 Tracker 为真源。
5. 每个用户必须拥有唯一的 tracker credential。
6. 默认按 XBT 风格私有凭证模型设计，但在 XBT PoC 验证之前，不要把具体 announce URL 形式写死。
7. 用户下载种子时，再动态重写 `announce URL` 或 tracker credential。
8. 第一阶段后端保持单体架构。
9. 优先复用成熟稳定的开源基础设施和内部管理工具。
10. 优先保证可维护性与正确性，而不是一次做太多功能。

================================================
3. 推荐技术栈
================================================

前端：

- Vue 3
- Vite
- Tailwind CSS
- Vue Router
- Pinia
- 仅在必要时使用轻量 Headless 组件

前端选型规则：

- 公共前台不要建立在重型可视化组件库之上
- 使用 Tailwind 工具类 + 统一设计令牌，更适合做现代化、数据优先、可控度高的前台

后端：

- FastAPI
- SQLAlchemy 2.x
- Alembic
- Pydantic
- PyJWT 或 python-jose
- passlib[bcrypt]
- psycopg2 或 asyncpg
- redis-py
- feedgen
- torf 或宽松许可证的 bencode 库
- SQLAdmin（MVP 阶段内部管理后台）

数据库：

- PostgreSQL 15+

缓存：

- Redis 7+

反向代理：

- Nginx

Tracker：

- XBT Tracker（首选：更贴合 PT 私有 passkey / torrent_pass 模型）
- Torrust Tracker（备选：更现代、容器化更友好，但私有用户统计模型需额外 PoC）

================================================
4. 高层架构
================================================

[ 浏览器 ]
    |
    v
[ Nginx ]
    |
    +--------------------------+
    |                          |
    v                          v
[ 前端 ]                  [ 后端 API ]
                               |
                 +-------------+-------------+
                 |                           |
                 v                           v
            [ PostgreSQL ]               [ Redis ]
                 |
                 v
      [ tracker 统计快照缓存表 ]

[ BT 客户端 ] ---------------------> [ Tracker Service: XBT / Torrust ]

职责划分：

前端负责：

- 登录 / 注册页面
- 列表、详情、上传、个人资料等用户页面
- RSS key 展示
- 用户态交互

后端负责：

- 认证
- 角色与权限
- 种子元数据管理
- 种子解析
- 下载时动态重写种子文件
- RSS 生成
- 内部管理功能
- Tracker 统计缓存刷新

Tracker 负责：

- announce
- scrape
- peer 状态
- 上传 / 下载统计
- seeders / leechers / snatches

================================================
5. 服务边界
================================================

站点负责：

- users
- roles
- 上传权限
- tracker credential 分配
- RSS key 分配
- categories
- torrent metadata
- torrent 页面
- torrent 上传
- torrent 下载重写
- RSS
- 内部管理后台

Tracker 负责：

- announce 请求
- scrape 请求
- peer list 响应
- uploaded / downloaded 统计
- seeder / leecher 状态
- snatch / finished 计数

重要规则：

- 站点不能自己计算官方上传 / 下载总量。
- `download_logs` 只表示用户从网页下载过 `.torrent` 文件，不代表真实 BT 传输统计。
- 站点展示的 ratio、seeders、leechers、snatches、uploaded、downloaded 都必须来自 Tracker 缓存。

================================================
6. 角色与权限
================================================

角色枚举：

- admin
- uploader
- user

权限说明：

- user：
  - 注册 / 登录
  - 浏览允许访问的页面
  - 下载重写后的种子
  - 使用 RSS
- uploader：
  - 拥有所有 user 权限
  - 可以上传种子
- admin：
  - 拥有所有 uploader 权限
  - 管理用户与角色
  - 管理分类
  - 管理种子可见性与标记
  - 任命其他 admin 与 uploader

安全规则：

- 系统必须防止最后一个 admin 被降级或移除

================================================
7. Tracker 凭证模型
================================================

每个网站用户都必须有一个唯一的 tracker credential。

从站点角度看，它是一个不透明凭证。
第一阶段优先按 XBT 风格理解它：

- 网站侧 `tracker_credential` 直接对应 Tracker 侧的私有用户凭证
- 优先采用类似 `torrent_pass` 的 per-user credential 模型
- 首选 announce 形式为 XBT 风格的 `/<tracker_credential>/announce`

第一阶段规则：

- 在 `users` 表中为每个用户存储一个唯一的 `tracker_credential`
- 用户下载种子时，把该凭证注入到重写后的 `.torrent` 文件中
- 在 XBT PoC 确认之前，不把最终 URL/path 细节写死

PoC 之后的决策规则：

- 如果 XBT PoC 成功，就冻结为 XBT 原生私有凭证模型
- 如果 XBT 在部署、同步或集成上不合适，再启动 Torrust 备选 PoC
- 只有在 XBT 不适合时，才考虑把 `tracker_credential` 继续保持抽象并映射到 Torrust 可识别格式

关于 NexusPHP：

- 可以把 NexusPHP 视为“业务模式参考”，尤其是每用户 tracker 凭证这类做法
- 第一阶段不直接移植或复用 NexusPHP 的 tracker 实现

================================================
8. 统计归属与缓存策略
================================================

真源定义：

- 用户上传 / 下载流量真源来自所选 Tracker
- 种子 swarm 统计真源来自所选 Tracker

站点缓存策略：

- 在 PostgreSQL 中存持久化快照，便于稳定读取
- Redis 可作为热缓存
- 后台不允许人工修改 Tracker 缓存统计

首选同步策略：

- 如果采用 XBT，MVP 默认通过 Tracker 数据库或小型适配层定时拉取统计

兜底同步策略：

- 如果后续切换到 Torrust，且其管理 API / event 路径足够支撑站点同步，则允许改为对应接口同步
- 无论使用哪种 Tracker，MVP 默认每 `30-60 秒` 刷新一次

展示规则：

- 站点页面中的 ratio、seeders、leechers、snatches、uploaded、downloaded 都必须从缓存中读取

================================================
9. 数据库结构
================================================

9.1 users

字段：

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

status 枚举：

- active
- banned
- pending

9.2 categories

字段：

- id: bigint primary key
- name: varchar(64), not null
- slug: varchar(64), unique, not null
- sort_order: int, default 0
- is_enabled: boolean, default true
- created_at: timestamptz, not null

9.3 torrents

字段：

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

字段：

- id: bigint primary key
- torrent_id: bigint, foreign key torrents.id, not null
- file_path: varchar(2048), not null
- file_size_bytes: bigint, not null

9.5 download_logs

字段：

- id: bigint primary key
- torrent_id: bigint, foreign key torrents.id, not null
- user_id: bigint, foreign key users.id, not null
- ip: varchar(64), not null
- downloaded_at: timestamptz, not null

含义：

- 这张表只记录网站层面的下载动作
- 它不是 BT 流量真源

9.6 tracker_user_stats_cache

字段：

- user_id: bigint primary key, foreign key users.id
- uploaded_bytes: bigint, not null, default 0
- downloaded_bytes: bigint, not null, default 0
- ratio: numeric(18,6), null
- updated_at: timestamptz, not null
- source: varchar(32), not null, default 'tracker'

含义：

- Tracker 用户流量统计的快照缓存

9.7 tracker_torrent_stats_cache

字段：

- torrent_id: bigint primary key, foreign key torrents.id
- seeders: int, not null, default 0
- leechers: int, not null, default 0
- snatches: int, not null, default 0
- finished: int, not null, default 0
- updated_at: timestamptz, not null
- source: varchar(32), not null, default 'tracker'

含义：

- Tracker 种子统计的快照缓存

第一阶段非目标：

- 除非后续集成证明确有必要，否则不维护网站自有 `peers` 表

================================================
10. 后端项目结构
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
11. 前端项目结构
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

内部管理后台策略：

- MVP 阶段优先用 SQLAdmin 提供内部管理页面
- 第一阶段不要求管理后台必须由 Vue 实现

================================================
12. API 规格
================================================

12.1 Authentication

POST /api/auth/register

request:

```json
{
  "username": "alice",
  "email": "alice@example.com",
  "password": "strong-password"
}
```

response:

```json
{
  "id": 1,
  "username": "alice",
  "email": "alice@example.com",
  "role": "user"
}
```

POST /api/auth/login

response:

```json
{
  "access_token": "jwt-token",
  "token_type": "bearer"
}
```

GET /api/auth/me

response:

```json
{
  "id": 1,
  "username": "alice",
  "email": "alice@example.com",
  "role": "user",
  "tracker_credential": "masked",
  "rss_key": "masked"
}
```

12.2 User APIs

- GET /api/users/profile
- PATCH /api/users/profile

12.3 Torrent APIs

- GET /api/torrents
- GET /api/torrents/{id}
- POST /api/torrents/upload
- GET /api/torrents/{id}/download

上传权限：

- 只有 `admin` 和 `uploader` 能上传

下载行为：

- 需要已登录用户
- 写入 `download_logs`
- 读取原始 torrent bytes
- 按所选 Tracker 可识别格式注入该用户的 tracker credential
- 返回重写后的 `.torrent` 文件

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

Admin 用户更新 payload 示例：

```json
{
  "role": "uploader",
  "status": "active"
}
```

角色分配规则：

- 只有 admin 可以改角色
- 只有 admin 可以创建其他 admin
- 系统必须拒绝把最后一个 admin 降级

12.6 通用返回约定

列表接口建议统一返回：

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "page_size": 20
}
```

详情接口建议：

- 直接返回对象
- 或返回 `{ "message": "...", "data": {...} }` 风格，但项目内必须统一

错误返回建议统一包含：

```json
{
  "code": "SOME_ERROR_CODE",
  "message": "Human readable message",
  "details": {}
}
```

约定：

- 时间统一返回 ISO 8601 字符串
- bytes 相关字段统一返回整数，不返回格式化字符串
- `tracker_credential`、`rss_key` 默认应返回 masked 版本
- 401 用于未登录
- 403 用于已登录但无权限
- 404 用于资源不存在或当前用户不可见
- 422 或 400 用于参数校验失败

12.7 上传接口细化约定

`POST /api/torrents/upload` 建议字段：

- torrent_file
- category_id
- name
- subtitle
- description
- cover_image_url
- media_info

建议校验规则：

- `torrent_file` 必填
- `category_id` 必填
- `torrent_file` 默认大小限制建议为 10 MiB，可配置
- `cover_image_url` 仅允许 `http://` 或 `https://`
- `name` 允许留空，留空时使用 torrent metadata 中的名称
- `description`、`media_info` 允许为空，但服务端要做最大长度限制

上传成功后的行为：

- 保存原始 torrent 文件
- 解析并提取文件列表与 info_hash
- 检查重复 `info_hash`
- 写入 torrents 与 torrent_files
- 返回新建 torrent 的 `id`

================================================
13. 认证与安全
================================================

站点 API 认证：

- JWT bearer auth

密码处理：

- 只使用 bcrypt hash
- 永远不存明文密码

Tracker 凭证处理：

- 为每个用户生成唯一随机 opaque secret
- 注册时生成并保存
- 未来允许在用户设置或后台中轮换
- 除明确需要外，不直接暴露原始值

RSS key 处理：

- 与 tracker credential 分离
- 独立随机生成

安全规则：

- 校验上传文件必须是 `.torrent`
- 限制上传大小
- 如果允许 HTML 描述，则必须做清洗
- 对登录 / 注册等接口做限流
- API 不能暴露真实内部存储路径
- 用户封禁以站点权限为准；如未来有需要，再补充 Tracker 侧封禁同步

================================================
14. Tracker 集成设计
================================================

首选 Tracker：

- XBT Tracker

备选 Tracker：

- Torrust Tracker

部署规则：

- Tracker 必须作为独立容器 / 独立服务部署，不与 `backend` 合并为同一个镜像
- 如果采用 XBT，额外提供独立的 `tracker-db`（MySQL / MariaDB）
- 如果采用 Torrust，可按其实现选择 SQLite 卷或独立 MySQL

Tracker 集成约定：

1. 原始上传的 `.torrent` 文件保持原样存储。
2. 每次下载请求时，在内存中重写 torrent bytes。
3. 按所选 Tracker 可兼容的方式注入用户专属 tracker credential。
4. 将重写后的种子文件作为附件返回。
5. 把 Tracker 统计视为真源。
6. 将 Tracker 统计刷新到站点缓存。

PoC 闸门：

- 在最终实现前，必须先完成 XBT PoC，确认：
  - XBT 容器部署是否稳定
  - XBT 风格私有凭证是否能直接满足 PT 站需求
  - 站点如何从 XBT 侧拉取用户级 / 种子级统计
- 只有在 XBT 不适合时，才继续验证 Torrust：
  - Torrust 是否能满足 PT 私有用户凭证模型
  - Torrust 的统计同步方式是否足够支撑站点缓存

实施规则：

- 默认按 XBT 风格设计，但在 XBT PoC 证明之前，不把最终实现写死成某个具体 URL 形式

统计同步规则：

- 如果采用 XBT，MVP 默认采用周期性 pull 同步
- 如果后续切换 Torrust，且其管理 API / event 路径足够成熟，可改为对应同步方式

================================================
15. 种子解析规则
================================================

上传时，需要从 `.torrent` 文件中提取：

- info_hash
- 顶层 name
- 总大小
- 文件列表
- piece length（如有需要）

规则：

- `info_hash` 统一存为小写 hex string
- 如果 `info_hash` 已存在，则拒绝重复上传
- 原始 torrent bytes 原样保存
- 展示用标题与原始 torrent metadata name 可以分离

================================================
16. RSS Feed 规则
================================================

每个 RSS item 应包含：

- title
- link
- guid
- pubDate
- description
- enclosure

规则：

- 必须校验 `rss_key`
- 只包含可见种子
- enclosure 应指向支持 `rss_key` 鉴权的下载端点
- 某些 RSS 客户端会直接用 enclosure 下载，因此 RSS 下载端点也必须支持重写 tracker credential

================================================
17. 页面要求
================================================

用户前台页面：

- Login Page
- Register Page
- Torrent List Page
- Torrent Detail Page
- Upload Page
- Profile Page

页面清单与用途：

1. Home / Torrent List Page

- 登录后的默认入口页
- MVP 中首页与种子列表页可以是同一页
- 主要目的：浏览、搜索、筛选、比较并进入下载流程
- 核心模块：顶部搜索、分类筛选、排序控件、种子列表、快速统计、分页、快速下载动作

2. Torrent Detail Page

- 主要目的：帮助用户判断是否下载该种子
- 核心模块：标题摘要区、下载操作区、Tracker 统计摘要、基础元数据、描述、文件列表、MediaInfo / NFO、封面图

3. Upload Page

- 主要目的：让 `admin` 与 `uploader` 以较低出错率完成上传
- 核心模块：权限提示、torrent 文件与分类区、展示信息区、高级信息区、校验摘要、提交操作栏

4. Profile / Settings Page

- 主要目的：展示账号信息、Tracker 统计、RSS 访问方式与个人偏好
- 核心模块：账号信息、Tracker 上传下载统计、ratio、掩码后的 tracker credential、RSS key 区域、外观设置

5. RSS Access Page or RSS Panel

- 主要目的：清晰展示 RSS 链接、使用说明与复制操作
- MVP 中可以是独立页面，也可以是 Profile 下的一个子面板
- 核心模块：RSS feed URL、复制按钮、未来可选的 regenerate 操作、简要使用说明

6. Login Page

- 主要目的：尽快完成登录，减少阻力
- 核心模块：用户名 / 邮箱输入、密码输入、提交按钮、错误反馈

7. Register Page

- 主要目的：清晰完成注册
- 核心模块：用户名、邮箱、密码、确认密码、提交按钮、校验反馈

8. Internal Admin

- MVP 中由 SQLAdmin 提供
- 不要求与公共前台保持同一视觉系统
- 主要目的：管理用户、角色、分类、种子

MVP 内部管理后台：

- 使用 SQLAdmin 管理 users、categories、torrents

上传页访问权限：

- 只有 `admin` 和 `uploader`

Profile 页展示：

- username
- email
- role
- tracker-backed uploaded bytes
- tracker-backed downloaded bytes
- tracker-backed ratio
- rss key
- masked tracker credential

前台 UI 方向：

- 公共前台应表现为“干净、数据优先、现代化”的私有 Tracker 界面，而不是论坛门户
- 列表页可读性高于装饰性
- 可以桌面优先，但移动端必须可用
- 默认主题采用浅色中性风格；暗色模式可以后置
- 分类标签、统计徽标、下载动作在列表、详情、RSS 相关页面中要保持一致
- 内部管理后台不要求匹配前台视觉

前台实现规则：

- 公共前台主要使用 Tailwind CSS
- 设计令牌通过 CSS variables 统一管理颜色、间距、圆角、阴影、层级
- 避免每个页面各自随意写样式决策
- 使用共享 `AppShell` 统一 header、content、响应式导航

布局规则：

- 使用流式响应式布局，主要依赖 CSS Grid 与 Flexbox
- 除必要的 sticky 导航或工具条外，避免过多 fixed 定位
- 大屏使用最大宽度容器，小屏保持舒适边距
- 桌面端优先采用“左侧导航 + 顶部栏”的结构
- 平板与手机端将侧栏折叠成抽屉或 overlay 菜单

导航与 URL 行为：

- 列表页的筛选、搜索、排序、分页要反映到 URL query 中
- 从详情页返回列表页时，要保留列表状态和滚动位置
- 每个主页面都应有明确的标题与当前位置提示
- 危险操作或权限敏感操作必须要求显式确认

列表页展示规则：

- 桌面端使用“密度较高但可读”的表格型布局
- 手机端改为卡片列表或优先字段布局，避免强行保留超宽表格
- 下载动作、标题、分类、关键统计在移动端也要尽量保持可见

动效与切换规则：

- 页面切换要流畅、现代，但必须克制
- 路由动画只作用于内容区域，不要整页夸张滑动
- 优先使用 opacity 与小幅 translate / scale，而不是大范围位移或花哨 parallax
- 默认动效时长控制在 `140ms-220ms`
- 使用 Vue Router 的 `RouterView` slot 模式做 route-aware transition
- 只有在能提升理解时才做页面特定动画，例如列表进入详情、抽屉、覆盖层
- 必须尊重 reduced-motion 偏好，并提供低动态模式

加载与状态反馈：

- 列表页和详情页使用 skeleton loader
- 提供空状态：无种子、无搜索结果、无上传权限
- 提供明确的内联错误状态：登录失败、上传失败、RSS key 错误、Tracker 统计读取失败
- 乐观更新只用于低风险动作；数据正确性优先于“看起来更快”
- 对登录成功、上传完成、角色变更、可恢复警告使用 toast 反馈

背景与外观规则：

- 默认站点背景使用纯色，不使用大幅默认插图
- 可选支持用户自定义背景图片 URL 或背景图片 API
- 自定义背景不能降低文字可读性；必要时叠加遮罩、模糊、压暗或提高对比
- MVP 阶段自定义背景由前端直接拉取；后端不代理任意第三方图片 URL
- 如有需要，可以限制允许的图片域名或 API 域名白名单
- 外观设置可先存本地 local storage，未来再考虑服务端同步

视觉风格规则：

- 色板应围绕背景色建立：卡片、文字、徽标、按钮与背景之间必须保持明显对比
- 整体采用浅色、中性、清晰的配色方案
- 页面风格要现代、干净、利落，但不要做成游戏化或过于 glossy 的视觉
- 圆角、阴影、强调色使用都要克制且一致
- 图标仅使用一套统一的 icon family

按钮层级规则：

- 每个主操作区域只应有一个明显占主导的 primary button
- secondary actions 必须明显弱于 primary action
- danger action 必须与普通操作有明显区分
- danger action 在点击后必须弹出确认框或二次确认步骤，确认后才能执行

可访问性与可用性：

- 键盘操作必须覆盖登录、筛选、上传表单和关键后台动作
- 自定义样式下也必须保留清晰 focus 状态
- 对比度优先保证数据可读性，而不是追求过于细腻的视觉
- 手机端的筛选、分页、下载按钮必须保证可点击区域足够大

性能规则：

- 主页面使用 route-level lazy loading
- 动效避免修改昂贵的布局属性，优先 transform / opacity
- 列表筛选变动时不要重复播放整页过渡动画
- 背景图与封面图尽可能懒加载
- 关键词搜索应使用 debounce，避免无意义频繁请求

外观设置位置：

- 外观偏好可以放在 Profile 页中，也可以放进独立设置抽屉
- 第一阶段外观设置可包含：背景模式、自定义图片源、低动态模式、列表密度

17.1 前端路由建议

建议前端路由：

- `/login`
- `/register`
- `/`
- `/torrents`
- `/torrents/:id`
- `/upload`
- `/profile`
- `/rss`
- `/admin`（可跳转到后端 SQLAdmin，或仅作为入口说明页）

路由行为建议：

- `/` 在登录后默认跳转到 `/torrents`
- 若开启公开列表模式，未登录用户也可访问 `/` 与 `/torrents`
- `/upload` 仅 `admin` 与 `uploader` 可见
- `/profile`、`/rss` 需要登录

17.2 页面模块骨架建议

首页 / 列表页模块顺序建议：

1. 顶部标题区
2. 全局搜索与快速筛选区
3. 分类筛选 / 排序条
4. 列表主体区
5. 分页区
6. 空状态 / 错误状态区

详情页模块顺序建议：

1. 标题与标签区
2. 下载主操作区
3. 统计摘要区
4. 基础元数据区
5. 描述区
6. 文件列表区
7. MediaInfo / NFO 区
8. 封面图或扩展展示区

上传页模块顺序建议：

1. 页面标题与权限提示
2. 基础上传区：torrent 文件、分类
3. 展示信息区：标题、副标题、描述、封面
4. 高级信息区：MediaInfo、NFO、附加说明
5. 校验摘要区
6. 提交操作区

Profile / Settings 页模块顺序建议：

1. 账号摘要区
2. Tracker 统计区
3. 凭证与 RSS 区
4. 外观偏好区
5. 未来可扩展的安全设置区

17.3 共享组件清单建议

建议优先抽出的共享组件：

- AppHeader
- AppSidebar
- AppBreadcrumb
- SearchBar
- CategoryFilter
- SortToolbar
- TorrentTable
- TorrentMobileCard
- TorrentStatBadge
- FileTreeList
- EmptyState
- ErrorState
- SkeletonBlock
- ConfirmDialog
- ToastHost
- PageSection
- BackgroundLayer

17.4 表单与交互约定

表单行为建议：

- 输入阶段提供轻量字段级校验
- 提交阶段提供完整错误摘要
- 上传页在移动端也要保证提交按钮可快速到达
- 长表单建议使用分组卡片，而不是一个超长无层次表单

交互约定：

- 复制类操作使用弱按钮或图标按钮，并带 toast
- 危险操作先打开确认框，再允许提交
- 正在提交时，按钮应进入 loading 状态并阻止重复提交
- 无权限时应明确显示原因，而不是静默隐藏所有内容

17.5 初始设计令牌建议

这部分不是最终品牌视觉，而是一个足够开工的初始令牌方案。

建议起始色板：

- 背景色：`slate-50`
- 面板色：`white`
- 边框色：`slate-200`
- 主文字：`slate-900`
- 次文字：`slate-500` 或 `slate-600`
- 主强调色：`blue-600`
- 主强调 hover：`blue-700`
- 成功色：`emerald-600`
- 警告色：`amber-600`
- 危险色：`red-600`
- 信息色：`sky-600`

建议间距体系：

- 4, 8, 12, 16, 24, 32

建议圆角：

- 输入框 / 小按钮：8px
- 卡片 / 面板：12px
- 对话框 / 抽屉：14px

建议阴影层级：

- level 1：轻卡片阴影
- level 2：浮层 / 下拉 / 粘性工具条阴影
- level 3：对话框 / 抽屉阴影

按钮层级建议：

- Primary：主下载、主提交
- Secondary：编辑、重置、切换
- Tertiary / Ghost：复制、查看说明、轻操作
- Danger：删除、封禁、危险变更

17.6 实施前最后的前台确认项

在正式开始做前端前，建议只再确认以下内容：

1. 是否需要公开访客模式
2. 背景图片自定义是只前端本地保存，还是要服务端同步
3. `/rss` 做独立页面，还是挂到 Profile 页内
4. 列表页手机端采用卡片，还是保留横向滚动表格
5. 第一阶段是否需要封面图上传，还是只保留 `cover_image_url`

================================================
18. Docker Compose 规格
================================================

必需服务：

- nginx
- frontend
- backend
- postgres
- redis
- tracker

服务示例：

- `postgres`: PostgreSQL 15
- `redis`: Redis 7
- `backend`: FastAPI app
- `frontend`: Vue app
- `tracker`: XBT Tracker（首选）或 Torrust Tracker（备选）
- `tracker-db`: XBT 使用独立 MySQL / MariaDB；Torrust 可选 SQLite 卷或 MySQL
- Tracker 独立运行，不并入 `backend` 镜像
- `nginx`: reverse proxy

================================================
19. 环境变量
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

说明：

- 当前实现默认 `TRACKER_SYNC_MODE=xbt_db`，通过 `XBT_TRACKER_DB_DSN` 直读 XBT 数据库同步统计。
- [x] 已完成 - `TRACKER_SYNC_INTERVAL_SECONDS` 已作为可配置周期同步间隔实现；当前默认值为 60 秒，目标刷新节奏仍是 30-60 秒。
- [x] 已完成 - 认证限流可通过 `AUTH_RATE_LIMIT_*` 变量配置，默认对登录与注册使用按 IP 统计的内存限流。
- 如果后续改用 Torrust，且其 API / event 路径验证可行，可把 `TRACKER_SYNC_MODE` 改为对应 API / event 模式。

================================================
20. MVP 开发顺序
================================================

Step 1

- 初始化前后端项目
- 搭建 docker compose
- 接通 postgres 与 redis

Step 2

- 实现 users 表与认证
- 实现角色体系
- 实现 tracker credential 生成
- 实现前端登录 / 注册流程

Step 3

- 实现 categories 与 torrents 结构
- 实现 torrent 上传 API
- 实现 torrent 解析工具
- 保存原始 torrent 文件

Step 4

- 实现 torrent 列表 API 与页面
- 实现 torrent 详情 API 与页面
- 接入 SQLAdmin 内部管理后台

Step 5

- 实现按用户 tracker credential 重写的下载端点
- 实现 RSS 端点

Step 6

- 部署 XBT Tracker
- 完成 XBT tracker credential PoC
- 验证 BT 客户端可以成功 announce

Step 7

- 实现 Tracker 统计缓存同步
- 在页面上展示 Tracker 统计

Step 8

- 强化权限控制
- 打磨 UI
- 补齐共享 AppShell、页面动效、外观偏好

截至 2026-04-07 的步骤状态：

- [x] Step 1：代码层面已实现。
- [x] Step 2：代码层面已实现；新密码 hash 已对齐到 bcrypt-only，旧 `pbkdf2_sha256` 仅保留登录时校验并升级的兼容路径。
- [x] Step 3：代码层面已实现，包括独立 `nfo_text` 上传路径；生产级校验仍是后续强化项。
- [x] Step 4：代码层面已实现。
- [x] Step 5：代码层面已实现，仍需做 RSS 下载器消费与端到端运行时测试。
- [ ] Step 6：部分实现；XBT 容器 / 配置 / schema 与 provision 代码已存在，但 XBT PoC 与 BT 客户端 announce 验证尚未完成。
- [x] Step 7：周期同步代码已实现；缓存表、页面展示、XBT DB 同步代码、Admin 手动 sync、可配置 30-60 秒周期同步均已存在；真实 XBT 运行时验证仍待完成。
- [ ] Step 8：部分实现；AppShell、页面过渡、响应式布局、外观偏好、route-level lazy loading、共享 toast 反馈、SQLAdmin role/status 权限加固、共享 confirm 对话框与基础 admin 审计日志已存在；更完整的可访问性打磨和更广的确认覆盖仍待完成。

================================================
21. 验收标准
================================================

系统最小可用的标准如下：

1. 用户可以注册并登录。
2. admin 可以任命 uploader 或其他 admin。
3. uploader 或 admin 可以上传种子。
4. 上传后的种子能出现在列表页。
5. 用户可以打开种子详情页。
6. 用户可以下载重写后的种子文件。
7. 重写后的种子中，包含该用户专属的 tracker credential，并且格式与所选 Tracker 的 PoC 确认结果一致。
8. BT 客户端可以成功向所选 Tracker announce；MVP 默认验证目标为 XBT。
9. 站点可以从缓存中展示 Tracker 提供的上传 / 下载统计与种子 swarm 统计。
10. RSS 端点能返回合法 XML。
11. RSS feed 能被下载器正常消费。

截至 2026-04-07 的验收状态：

- [x] 第 1-7 项已有代码实现，但仍需在完整 Docker 栈中做回归验证。
- [ ] 第 8 项仍待完成，是当前主要 PoC 闸门。
- [x] 第 9 项代码路径已实现，包括缓存读取 / 展示与周期刷新；真实 XBT 数据验证仍待完成。
- [x] 第 10-11 项已有代码路径，但仍需要在运行中的部署里验证 XML 合法性与下载器消费。

================================================
22. 未决问题 / PoC 检查清单
================================================

以下问题在冻结最终 Tracker 方案前必须确认：

1. XBT 在目标部署方式下的 announce URL、私有凭证格式与统计读取路径具体怎么落地？
2. 站点应通过 XBT 数据库直读、只读视图，还是额外的小型适配层来同步用户级 / 种子级统计？
3. 如果 XBT 在运维或集成上不合适，Torrust 是否能满足 PT 式每用户凭证与统计归属要求？
4. 如果切换到 Torrust，应该采用哪个管理 API / event / pull 路径，以及刷新频率定为多少合适？
5. 第一阶段是否需要把封禁同步到 Tracker，还是仅站点侧拒绝下载就足够？
6. [x] 已于 2026-04-07 解决：Docker Compose 对外入口采用宿主机 80 端口上的 Nginx；`frontend` 服务不再直出宿主机 8080。
7. [x] 已于 2026-04-07 解决：SQLAdmin 可以继续直接编辑用户 role/status，但这些编辑现在会通过 model hook 执行最后一个 active admin 保护与 XBT 用户同步路径。
8. [x] 已于 2026-04-07 解决：RSS key 鉴权已经在 feed 与 RSS 下载端点共用的 RSS key 查询路径中显式拒绝所有非 active 用户。

在这些问题确认之前，spec 有意保持以下内容抽象化：

- tracker credential 的实际传输格式
- Tracker 统计同步的具体实现方式

================================================
END OF DOCUMENT
================================================

# SubtitleGroupDiversionSite

基于 `FastAPI + Vue 3 + Tailwind CSS + PostgreSQL + Redis + external tracker` 的私有种子分发站点骨架，当前默认 tracker 方案为 `XBT Tracker`。

## 前端翻译说明

如果你要翻译现有前端文本，直接修改下面这些语言包文件：

- `frontend/src/locales/en-US.ts`
- `frontend/src/locales/zh-CN.ts`

这些文件是当前前端页面文案的主要来源，包含：

- 页面标题
- 导航文字
- 登录 / 注册 / Profile / RSS / 上传 / 管理页等界面文案
- 按钮、表单标签、占位符、空状态提示

规则：

- 修改已有翻译：直接改对应语言包里的 key。
- 新增一种语言：
  1. 把新语言文件放到 `frontend/src/locales/` 下，文件名建议直接用 locale code，例如 `ja-JP.ts`、`fr-FR.ts`。
  2. 在 `frontend/src/locales/index.ts` 里新增 `import`。
  3. 把新的 locale code 加到 `LocaleCode` 类型。
  4. 把新语言加到 `SUPPORTED_LOCALES`，这样语言切换器里才能看到。
  5. 把新语言加到 `LOCALE_MESSAGES`，这样 `t("...")` 才能真正读取到这份语言包。
- 前端组件里不要再直接硬编码文案，统一通过 `t("...")` 读取。
- 路由标题也是多语言驱动的，对应关系在 `frontend/src/router/index.ts` 的 `titleKey`。

补充说明：

- 当前语言选择保存在 `frontend/src/stores/locale.ts`。
- 默认语言可以通过 `VITE_DEFAULT_LOCALE` 配置。
- 后端直接返回的错误信息，以及数据库里的分类名、种子名这类内容，不会被这些前端语言包自动翻译。
- 也就是说，想“多放一份语言”，不是覆盖原文件，而是新增一个 `frontend/src/locales/<你的语言代码>.ts` 文件，再去 `frontend/src/locales/index.ts` 注册。

## 当前状态

当前仓库已经完成第一批基础骨架。

数据策略说明：

- 这个项目目前尚未发布，只在本地测试运行。
- 当前阶段不需要为历史本地测试数据做数据库迁移兼容。
- 如果 schema 改动导致本地数据不兼容，直接清空本地 `data/` 目录或相关 Docker volume 后重建是可以接受的。
- Alembic 配置可以继续保留作工具和发布前整理依据，但 MVP 开发阶段以 `AUTO_CREATE_TABLES=true` 自动建表和本地重建数据为主。

代码结构：

- `backend/`：FastAPI 后端基础结构、用户模型、认证、种子列表/详情接口、分类接口、管理接口骨架
- `frontend/`：Vue 3 + Vite + Tailwind CSS 前端骨架、路由、Pinia、基础页面与 AppShell
- `docker-compose.yml`：Postgres / Redis / Backend / Frontend / XBT Tracker / XBT tracker-db / Nginx 组合
- `pt_platform_implementation_spec.md`：英文 spec
- `pt_platform_implementation_spec.zh-CN.md`：中文 spec

## 已实现

- 注册 / 登录 / `/api/auth/me`
- 登录 / 注册端点基础内存限流
- 首个注册用户自动成为 `admin`
- 默认分类自动初始化
- `.torrent` 上传、基础解析、原始文件保存、`torrents / torrent_files` 落库
- 种子列表页与详情页基础接口
- 下载时按可配置 credential 策略重写 `announce`
- RSS XML 输出与 RSS 下载端点
- SQLAdmin 内部后台接入，管理员可通过 `/internal-admin` 登录
- 管理员接口补充分类管理、种子可见性 / Free 状态调整、手动 tracker sync
- SQLAdmin 用户 role/status 编辑已接入最后一个 active admin 保护与 XBT 用户同步
- 前端 `/admin` 已补充用户角色 / 状态、分类、种子可见性 / Free / 分类调整面板，并对敏感变更使用确认弹窗
- [x] 新密码 hash 使用 `bcrypt_sha256`；不再保留旧 `pbkdf2_sha256` / bcrypt hash 登录兼容路径
- [x] RSS key 鉴权会拒绝非 active 用户
- [x] Profile 支持 RSS key 自助轮换；轮换后旧 RSS URL 会立即失效
- [x] 上传表单与 API 已支持独立 `nfo_text` 输入路径，详情页可展示 NFO 文本
- [x] 已支持通过 `TRACKER_SYNC_INTERVAL_SECONDS` 配置周期性 tracker stats sync
- [x] Alembic 已包含 `site_settings` 迁移；当前默认部署路径仍以 `AUTO_CREATE_TABLES=true` 自动建表为主
- 用户 Profile 基础接口
- 前端登录 / 注册 / 列表 / 详情 / 上传 / Profile / RSS 页面骨架
- 基础响应式布局、路由守卫、路由级懒加载、页面切换动画、全局 toast / confirm 反馈、外观偏好本地存储
- 基础安全加固：后端与 Nginx 安全响应头、生产环境默认密钥启动防呆、可配置 trusted hosts、注册输入归一化与 Profile URL 校验
- Docker Compose 对外 Web 入口已统一为 Nginx，默认映射到宿主机 `80/tcp`

## 尚未完成

- XBT 的真实部署、announce 验证与统计回读需要第一次实际 `docker compose` 验证
- 只有在 XBT 不合适时，才切回 Torrust 备选方案
- 更完整的上传校验、NFO/MediaInfo 深度解析与生产级错误处理
- 更深入的可访问性打磨、生产安全审查、端到端 RSS 下载器消费验证与真实 BT 客户端 announce 验收

## 服务器 Docker 部署

推荐部署路径是 Linux 服务器 + Docker Compose。当前 `docker-compose.yml` 会启动完整运行栈：

| 服务 | 作用 | 对外端口 |
| --- | --- | --- |
| `nginx` | 统一 Web 入口，转发前端、API、RSS、内部后台 | 默认 `80/tcp`，可用 `WEB_HOST` / `WEB_PORT` 调整 |
| `frontend` | Vue 静态站点，由内部 Nginx 托管 | 不直接暴露 |
| `backend` | FastAPI API 与 SQLAdmin | 不直接暴露 |
| `postgres` | 站点主数据库 | 不直接暴露 |
| `redis` | 登录 / 注册限流等缓存能力 | 不直接暴露 |
| `tracker-db` | XBT Tracker 的 MariaDB 数据库 | 不直接暴露 |
| `tracker` | XBT Tracker announce / UDP tracker | `2710/tcp`、`6881/udp` |

### 部署前准备

服务器需要安装：

- Docker
- Docker Compose Plugin

服务器防火墙或云厂商安全组需要放行：

- `80/tcp`：站点入口
- `2710/tcp`：XBT Tracker HTTP announce
- `6881/udp`：XBT Tracker UDP

如果服务器的 `80/tcp` 已经被其他 Nginx、OpenResty、Apache、宝塔面板或现有容器占用，可以让项目只监听本机回环地址上的内部端口，例如 `127.0.0.1:8080`，再由已有的反向代理转发。

### 方式 A：源码构建部署

这是当前最直接、最容易排查问题的部署方式。

```bash
git clone https://github.com/zzzwannasleep/SubtitleGroupDiversionSite.git
cd SubtitleGroupDiversionSite
cp .env.example .env
cp backend/.env.example backend/.env
nano .env
nano backend/.env
docker compose up -d --build
```

第一次启动会下载基础镜像、安装依赖并构建 `backend`、`frontend`、`tracker` 三个本地镜像，耗时会比普通重启更久。

如果服务器 `80/tcp` 已被占用，先在项目根目录 `.env` 覆盖 Web 监听地址：

```env
WEB_HOST=127.0.0.1
WEB_PORT=8080
```

然后重新启动：

```bash
docker compose up -d --build
```

这时站点访问地址要带端口，例如 `http://你的服务器IP:8080`。对应的 `backend/.env` 里也建议同步写成：

```env
PUBLIC_WEB_BASE_URL=http://你的服务器IP:8080
CORS_ALLOWED_ORIGINS=http://你的服务器IP:8080
```

如果你准备让外部 OpenResty/Nginx 继续对外提供域名和 HTTPS，请看下面的“方式 C”。

### 方式 B：使用 GHCR 预构建镜像

仓库里的 GitHub Actions 工作流会构建并推送三组镜像到 GitHub Container Registry。服务器只想拉镜像运行时，可以在项目根目录创建根级 `.env`，用于覆盖 compose 里的镜像名。

先复制示例文件，然后编辑根目录 `.env`，取消 GHCR 镜像变量的注释：

```bash
cp .env.example .env
cp backend/.env.example backend/.env
nano .env
nano backend/.env

docker compose pull backend frontend tracker
docker compose up -d
```

根目录 `.env` 里需要启用这几行：

```env
BACKEND_IMAGE=ghcr.io/zzzwannasleep/subtitlegroupdiversionsite-backend:main
FRONTEND_IMAGE=ghcr.io/zzzwannasleep/subtitlegroupdiversionsite-frontend:main
TRACKER_IMAGE=ghcr.io/zzzwannasleep/subtitlegroupdiversionsite-xbt-tracker:main
```

如果 GHCR package 是私有的，先在服务器登录：

```bash
docker login ghcr.io
```

注意：根级 `.env` 只给 Docker Compose 做变量替换，例如 `WEB_HOST`、`WEB_PORT` 和镜像名；后端运行配置仍然写在 `backend/.env`。

如果服务器 `80/tcp` 已被占用，可以在同一个根级 `.env` 里额外加上：

```env
WEB_HOST=127.0.0.1
WEB_PORT=8080
```

### 方式 C：已有 OpenResty / Nginx 反代

如果你服务器上已经有 OpenResty、Nginx、宝塔反代或其他网关，推荐这样部署：

- 项目自己的 `nginx` 容器只监听 `127.0.0.1:8080`
- 公网 `80/443` 仍然由你现有的 OpenResty / Nginx 接管
- OpenResty / Nginx 把站点域名反代到 `http://127.0.0.1:8080`
- XBT Tracker 的 `2710/tcp` 和 `6881/udp` 保持 Docker 直接暴露，并在安全组 / 防火墙放行

项目根目录 `.env`：

```env
WEB_HOST=127.0.0.1
WEB_PORT=8080
```

OpenResty 站点配置示例：

```nginx
server {
    listen 80;
    server_name pt.example.com;

    client_max_body_size 20m;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

同样的 HTTP 反代示例文件也放在 `docker/openresty/subtitlegroupdiversionsite.conf.example`。

`6881/udp` 不需要在 OpenResty 里反代，`docker-compose.yml` 已经默认暴露：

```yaml
"${TRACKER_UDP_HOST:-0.0.0.0}:${TRACKER_UDP_PORT:-6881}:6881/udp"
```

只需要在服务器防火墙 / 云安全组放行 `6881/udp` 即可。

如果 OpenResty 已经配置 HTTPS，`backend/.env` 里的外部地址应该写 HTTPS 域名：

```env
APP_ENV=production
PUBLIC_WEB_BASE_URL=https://pt.example.com
CORS_ALLOWED_ORIGINS=https://pt.example.com
TRUSTED_HOSTS=pt.example.com
SESSION_COOKIE_SECURE=true
```

`TRACKER_BASE_URL` 仍然建议保留 tracker 端口，例如：

```env
TRACKER_BASE_URL=http://pt.example.com:2710/announce
```

### 环境变量配置

新环境先复制 `backend/.env.example`：

```bash
cp backend/.env.example backend/.env
```

服务器部署至少检查这几项：

| 变量 | 示例 | 说明 |
| --- | --- | --- |
| `APP_ENV` | `production` | 正式部署建议设为 `production`；如果密钥仍是默认值，后端会拒绝启动 |
| `SECRET_KEY` | 随机长字符串 | 后端会话与签名密钥，必须改 |
| `JWT_SECRET_KEY` | 随机长字符串 | 登录 JWT 签名密钥，必须改 |
| `PUBLIC_WEB_BASE_URL` | `https://pt.example.com` | 用户访问站点的外部地址 |
| `TRACKER_BASE_URL` | `http://pt.example.com:2710/announce` | 写入 `.torrent` 的 tracker announce 基础地址 |
| `CORS_ALLOWED_ORIGINS` | `https://pt.example.com` | 允许访问 API 的前端来源，多个值用英文逗号分隔 |
| `TRUSTED_HOSTS` | `pt.example.com` | 允许访问后端的 Host，开发环境可用 `*`，生产环境建议写域名或 IP |

已配置 HTTPS 反向代理的域名部署示例：

```env
APP_ENV=production
PUBLIC_WEB_BASE_URL=https://pt.example.com
TRACKER_BASE_URL=http://pt.example.com:2710/announce
CORS_ALLOWED_ORIGINS=https://pt.example.com
TRUSTED_HOSTS=pt.example.com
```

如果只使用当前 compose 默认暴露的 `80/tcp`，先把上面的 `https://` 改成 `http://`。

公网 IP 测试示例：

```env
APP_ENV=development
PUBLIC_WEB_BASE_URL=http://你的服务器IP
TRACKER_BASE_URL=http://你的服务器IP:2710/announce
CORS_ALLOWED_ORIGINS=http://你的服务器IP
TRUSTED_HOSTS=你的服务器IP
```

如果你把 `WEB_PORT` 改成了 `8080` 且没有外部反代，这里的站点地址也要带端口：

```env
PUBLIC_WEB_BASE_URL=http://你的服务器IP:8080
CORS_ALLOWED_ORIGINS=http://你的服务器IP:8080
```

通常保持默认的内部连接项：

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `DATABASE_URL` | `postgresql+psycopg2://ptuser:ptpass@postgres:5432/ptapp` | `postgres` 是 compose 内部服务名，不要改成公网域名 |
| `REDIS_URL` | `redis://redis:6379/0` | `redis` 是 compose 内部服务名 |
| `XBT_TRACKER_DB_DSN` | `mysql+pymysql://tracker:tracker-pass@tracker-db:3306/xbt` | `tracker-db` 是 compose 内部服务名 |
| `TORRENT_STORAGE_PATH` | `./data/torrents` | `.torrent` 原始文件保存目录 |
| `UPLOAD_STORAGE_PATH` | `./data/uploads` | 上传临时目录 |
| `TRACKER_IMPL` | `xbt` | 当前默认 tracker 实现 |
| `TRACKER_CREDENTIAL_MODE` | `xbt_path` | 当前按 `/<tracker_credential>/announce` 风格重写 announce |
| `TRACKER_SYNC_MODE` | `xbt_db` | 默认从 XBT 数据库同步统计 |
| `TRACKER_SYNC_INTERVAL_SECONDS` | `60` | 周期同步间隔；设为 `0` 可关闭周期同步 |
| `AUTO_CREATE_TABLES` | `true` | 当前 MVP 默认用启动时自动建表 |

按需调整的高级项：

| 变量 | 何时调整 |
| --- | --- |
| `APP_NAME` | 想改后端应用名时调整；前台站点名建议在管理页里改 |
| `JWT_EXPIRE_MINUTES` | 想调整登录有效期时调整 |
| `ALLOW_PUBLIC_TORRENT_LIST` | 想禁止游客查看种子列表时设为 `false` |
| `ALLOW_USER_REGISTRATION` | 想关闭公开注册时设为 `false` |
| `AUTH_RATE_LIMIT_*` | 想调整登录 / 注册限流窗口和次数时调整 |
| `SECURITY_HEADERS_ENABLED` | 默认建议保持 `true` |
| `HSTS_ENABLED` | 只有确认全站 HTTPS 后再设为 `true` |
| `SESSION_COOKIE_SECURE` | 生产 HTTPS 部署建议设为 `true` |
| `CONTENT_SECURITY_POLICY` | 只有验证过 `/internal-admin` 静态资源后再填写 |

### 启动与检查

```bash
docker compose up -d --build
docker compose ps
docker compose logs -f
```

默认会直接输出所有 Compose 服务日志；如果只想看某几个服务，可以在命令后追加服务名，例如 `docker compose logs -f backend nginx`。

启动后访问：

- 前台：`http://localhost`
- 健康检查：`http://localhost/api/health`
- 内部后台：`http://localhost/internal-admin`

部署在服务器时，把 `localhost` 换成公网 IP 或域名即可。

### 初始化账号

- 打开 `/register`
- 注册第一个账号
- 第一个注册用户会自动成为 `admin`

注册后建议检查：

- `/admin`
- `/profile`
- `/rss`
- `/upload`
- `/torrents`
- `/internal-admin`

### 数据持久化与备份

容器内数据已经挂载到项目根目录的 `data/` 下：

| 路径 | 用途 |
| --- | --- |
| `./data/postgres` | 站点主数据库 |
| `./data/tracker-db` | XBT Tracker 数据库 |
| `./data/torrents` | 上传后的 `.torrent` 原始文件 |
| `./data/uploads` | 上传临时目录 |

迁移机器或备份时，至少保留这些目录。

### 常用命令

```bash
docker compose logs -f
docker compose up -d --build
docker compose down
```

清空测试数据后重新开始：

```bash
docker compose down
rm -rf data/postgres data/tracker-db data/torrents data/uploads
docker compose up -d --build
```

注意：上面的 `rm -rf` 会删除现有数据库和已上传文件，只适合开发或测试环境。

### 常见问题

如果 `nginx` 启动失败并看到端口占用：

```text
failed to bind host port 0.0.0.0:80/tcp: address already in use
```

说明宿主机的 `80/tcp` 已经被其他服务占用。最简单的处理方式是在项目根目录 `.env` 改成只监听本机回环地址：

```env
WEB_HOST=127.0.0.1
WEB_PORT=8080
```

然后重启：

```bash
docker compose up -d
```

如果没有外部反代，访问地址改成 `http://你的服务器IP:8080`，并同步更新 `backend/.env` 里的 `PUBLIC_WEB_BASE_URL` 和 `CORS_ALLOWED_ORIGINS`。如果已有 OpenResty/Nginx，就让它反代到 `http://127.0.0.1:8080`，`backend/.env` 里继续写用户实际访问的域名。

如果第一次启动遇到类似错误：

```text
dependency failed to start: container subtitlegroupdiversionsite-postgres-1 is unhealthy
```

通常是 `data/postgres/pgdata` 里残留了旧初始化数据。开发测试环境可以清理后重试：

```bash
docker compose down
rm -rf data/postgres/pgdata
docker compose up -d --build
docker compose logs -f postgres
```

生产环境不要直接删除数据目录，先做备份并确认问题来源。

## GitHub Actions Docker 镜像构建

仓库已包含 `.github/workflows/docker-images.yml`，用于构建项目自建 Docker 镜像。

工作流触发方式：

- `pull_request`：只构建校验，不推送镜像
- `push` 到 `main`：构建并推送到 GHCR
- `push` tag `v*.*.*`：构建并推送到 GHCR
- `workflow_dispatch`：手动触发构建并推送到 GHCR

构建镜像：

- `ghcr.io/zzzwannasleep/subtitlegroupdiversionsite-backend:<tag>`
- `ghcr.io/zzzwannasleep/subtitlegroupdiversionsite-frontend:<tag>`
- `ghcr.io/zzzwannasleep/subtitlegroupdiversionsite-xbt-tracker:<tag>`

默认标签由分支名、版本 tag 和提交 SHA 生成，例如 `main`、`v1.0.0`、`sha-<commit>`。当前工作流只构建 `linux/amd64`，如果后续要支持 ARM 服务器，可以再扩展 `platforms`。

## 说明

- 当前实现更接近“可继续开发的基础骨架”，不是完整可用产品。
- 当前实现默认按 XBT 风格的 `/<tracker_credential>/announce` 重写下载出来的 `.torrent`。
- 站点侧 tracker sync 默认通过 `XBT_TRACKER_DB_DSN` 直连 `xbt_users / xbt_files` 拉取统计，并在手动 sync 时顺带回填缺失的 XBT 用户与种子记录。

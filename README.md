# Subtitle Group Diversion Site

> 更新说明：后端已经接入可选的 `Torrust Tracker` 支持，包含私有种子规范化、whitelist 同步和按用户改写下载 announce。启用后请查看 [docs/PRIVATE_TRACKER_INTEGRATION.md](docs/PRIVATE_TRACKER_INTEGRATION.md)，并执行 `python backend/manage.py sync_tracker_state` 补齐历史数据。

一个面向字幕组内部使用的轻量资源站，提供资源发布、浏览、RSS 订阅和 torrent 下载能力。

当前版本不再依赖旧的私有 Tracker / XBT 方案，发布页和编辑页统一为直接上传 `.torrent` 文件。

- 未启用 Tracker 时，下载接口会直接返回站内保存的 torrent。
- 启用可选的 `Torrust Tracker` 后，下载接口会按用户改写 announce，并可将种子规范化为 private torrent。

## 技术栈

- 前端：`Vue 3 + Vite + Pinia + Vue Router`
- 后端：`Django 5 + DRF + drf-spectacular`
- 数据库：`MySQL 8`
- 缓存：`Redis`
- 部署：`Docker Compose + Django 单容器入口`

## 当前能力

- 用户登录、注册、邀请码、权限控制
- 资源发布、编辑、隐藏、列表和详情
- 发布时直接上传 torrent，编辑时可直接替换 torrent
- RSS 订阅与公开下载链接
- 可选 Private Tracker：用户 passkey / announce 改写、whitelist 同步、历史数据补齐
- 公告、分类、标签、审计日志、站点设置
- Swagger / OpenAPI 文档

## 仓库结构

```text
frontend/   Vue 前端
backend/    Django 后端
deploy/     Docker Compose 与部署脚本
docs/       设计过程文档
```

## 本地开发

### 前端

```bash
cd frontend
npm ci
npm run dev
```

### 后端

```bash
Copy-Item backend/.env.example backend/.env
python -m pip install -r backend/requirements.txt
python backend/manage.py migrate
python backend/manage.py createsuperuser
python backend/manage.py runserver
```

默认情况下，后端可使用 `SQLite + LocMemCache` 本地启动；配置 `MYSQL_*` 和 `REDIS_URL` 后可切换到 `MySQL + Redis`。

## 生产部署

生产环境建议准备一台已安装 `Docker Engine` 与 `Docker Compose` 插件的服务器。当前支持两种部署方式，并且都使用同一份 [deploy/docker-compose.yml](deploy/docker-compose.yml)。

### 方式一：克隆仓库后部署

适合需要查看源码、自行构建镜像或按自己的代码版本发布的场景。

```bash
git clone https://github.com/zzzwannasleep/SubtitleGroupDiversionSite.git
cd SubtitleGroupDiversionSite
cp deploy/.env.example deploy/.env
# PowerShell: Copy-Item deploy/.env.example deploy/.env
```

先编辑 `deploy/.env`，至少确认这些配置已经改成你的生产值：

- `DJANGO_SECRET_KEY`
- `DJANGO_ALLOWED_HOSTS`
- `SITE_BASE_URL`
- `MYSQL_PASSWORD`
- `MYSQL_ROOT_PASSWORD`

构建本地镜像：

```bash
docker build -f backend/Dockerfile -t subtitle-group-diversion-site/backend:local .
```

然后把 `deploy/.env` 中的镜像配置改成：

```env
BACKEND_IMAGE=subtitle-group-diversion-site/backend:local
IMAGE_PULL_POLICY=never
```

最后启动服务并创建管理员账号：

```bash
docker compose --env-file deploy/.env -f deploy/docker-compose.yml up -d
docker compose --env-file deploy/.env -f deploy/docker-compose.yml exec backend python manage.py createsuperuser
```

如果想直接指定超级用户的用户名、邮箱和密码，也可以执行：

```bash
docker compose --env-file deploy/.env -f deploy/docker-compose.yml exec \
  -e DJANGO_SUPERUSER_USERNAME=admin \
  -e DJANGO_SUPERUSER_EMAIL=admin@example.com \
  -e DJANGO_SUPERUSER_PASSWORD=change-me \
  backend python manage.py createsuperuser --noinput
```

### 方式二：直接使用 `deploy/docker-compose.yml` 部署

适合只想拉取预构建镜像，不关心源码构建的场景。把 `deploy/` 目录整体复制到服务器后执行：

```bash
cd deploy
cp .env.example .env
# PowerShell: Copy-Item .env.example .env
docker compose up -d
docker compose exec backend python manage.py createsuperuser
```

如果想直接指定超级用户的用户名、邮箱和密码，也可以执行：

```bash
docker compose exec \
  -e DJANGO_SUPERUSER_USERNAME=admin \
  -e DJANGO_SUPERUSER_EMAIL=admin@example.com \
  -e DJANGO_SUPERUSER_PASSWORD=change-me \
  backend python manage.py createsuperuser --noinput
```

默认会直接拉取：

- `ghcr.io/zzzwannasleep/subtitlegroupdiversionsite/backend:latest`

如果是完整仓库部署，也可以直接运行 `sh deploy/scripts/init.sh` 完成首启。

默认 Compose 服务包括：

- `backend`
- `mysql`
- `redis`
- `tracker`（可选，通过 `--profile tracker` 启动）

### 可选：启用 Private Tracker

如果部署时需要 Private Tracker，推荐直接复用仓库内置的 Torrust 集成，而不是再额外拼一套站点逻辑。

先复制 tracker 配置文件：

```bash
cp deploy/tracker/tracker.example.toml deploy/tracker/tracker.toml
# PowerShell: Copy-Item deploy/tracker/tracker.example.toml deploy/tracker/tracker.toml
```

如果你是在服务器上只保留 `deploy/` 目录，则改为在 `deploy/` 目录内执行：

```bash
cp tracker/tracker.example.toml tracker/tracker.toml
# PowerShell: Copy-Item tracker/tracker.example.toml tracker/tracker.toml
```

然后在 `deploy/.env` 里至少补齐这些配置：

- `TRACKER_ENABLED=true`
- `TRACKER_ANNOUNCE_URL=http://你的域名或服务器IP:7070/announce`
- `TORRUST_API_URL=http://tracker:1212`
- `TORRUST_API_TOKEN=your-admin-token`

这里要特别区分：

- `TRACKER_ANNOUNCE_URL` 是写进用户下载到的 `.torrent` 里的外网地址，必须能被 BT 客户端访问
- `TORRUST_API_URL` 是 Django 容器访问 tracker 管理 API 的内网地址，Docker Compose 场景下应保持为 `http://tracker:1212`
- `deploy/tracker/tracker.toml` 需要保留 `[metadata]` 段，例如 `schema_version = "2.0.0"`

启动并补齐历史状态：

```bash
docker compose --env-file deploy/.env -f deploy/docker-compose.yml --profile tracker up -d
docker compose --env-file deploy/.env -f deploy/docker-compose.yml exec backend python manage.py migrate
docker compose --env-file deploy/.env -f deploy/docker-compose.yml exec backend python manage.py sync_tracker_state
```

如果当前就在 `deploy/` 目录内，则可直接执行：

```bash
docker compose --profile tracker up -d
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py sync_tracker_state
```

## 关键配置

- `SITE_BASE_URL`：站点基础地址，用于拼接 RSS 和下载链接
- `MYSQL_DATABASE` / `MYSQL_USER` / `MYSQL_PASSWORD` / `MYSQL_ROOT_PASSWORD`：MySQL 配置
- `REDIS_URL`：可选，启用 Redis 缓存与会话
- `HTTP_PORT`：站点对外端口，由 `backend` 容器直接提供前端、API、静态文件和下载
- `BACKEND_IMAGE`：可选，覆盖默认镜像地址；源码部署时可指向本地构建镜像
- `IMAGE_PULL_POLICY`：可选，默认 `always`；源码部署时建议改为 `never`
- `TRACKER_ENABLED`：是否启用可选的 Private Tracker 集成
- `TRACKER_ANNOUNCE_URL`：写入 torrent 的对外 announce 地址
- `TORRUST_API_URL` / `TORRUST_API_TOKEN`：Django 与 Torrust 管理 API 的连接配置
- `TRACKER_HTTP_PORT` / `TRACKER_UDP_PORT` / `TRACKER_API_PORT`：tracker 对外与管理端口映射
- `TRACKER_REQUIRE_AUTH_DOWNLOADS` / `TRACKER_FORCE_PRIVATE_TORRENTS`：是否要求登录下载、是否强制 private torrent

更多日志、备份与目录内执行方式见 [deploy/README.md](deploy/README.md)，Private Tracker 的接入背景与完整说明见 [docs/PRIVATE_TRACKER_INTEGRATION.md](docs/PRIVATE_TRACKER_INTEGRATION.md)。

## 验证

- 前端：`cd frontend && npm run build`
- 后端：`python -m compileall backend`

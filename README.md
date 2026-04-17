# Subtitle Group Diversion Site

一个面向字幕组内部使用的轻量资源站，提供资源发布、浏览、RSS 订阅和 torrent 下载能力。

当前版本已经移除私有 Tracker / XBT 依赖，发布页和编辑页都改为直接上传 `.torrent` 文件，下载接口也会直接返回站内保存的原始 torrent。

## 技术栈

- 前端：`Vue 3 + Vite + Pinia + Vue Router`
- 后端：`Django 5 + DRF + drf-spectacular`
- 数据库：`MySQL 8`
- 缓存：`Redis`
- 部署：`Docker Compose + Nginx`

## 当前能力

- 用户登录、注册、邀请码、权限控制
- 资源发布、编辑、隐藏、列表和详情
- 发布时直接上传 torrent，编辑时可直接替换 torrent
- RSS 订阅与基于 `passkey` 的下载鉴权
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
docker build -t subtitle-group-diversion-site/frontend:local ./frontend
docker build -t subtitle-group-diversion-site/backend:local ./backend
```

然后把 `deploy/.env` 中的镜像配置改成：

```env
FRONTEND_IMAGE=subtitle-group-diversion-site/frontend:local
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

- `ghcr.io/zzzwannasleep/subtitlegroupdiversionsite/frontend:latest`
- `ghcr.io/zzzwannasleep/subtitlegroupdiversionsite/backend:latest`

如果是完整仓库部署，也可以直接运行 `sh deploy/scripts/init.sh` 完成首启。

默认 Compose 服务包括：

- `frontend`
- `backend`
- `mysql`
- `redis`
- `nginx`

## 关键配置

- `SITE_BASE_URL`：站点基础地址，用于拼接 RSS 和下载链接
- `MYSQL_DATABASE` / `MYSQL_USER` / `MYSQL_PASSWORD` / `MYSQL_ROOT_PASSWORD`：MySQL 配置
- `REDIS_URL`：可选，启用 Redis 缓存与会话
- `HTTP_PORT`：Nginx 对外端口
- `FRONTEND_IMAGE` / `BACKEND_IMAGE`：可选，覆盖默认镜像地址；源码部署时可指向本地构建镜像
- `IMAGE_PULL_POLICY`：可选，默认 `always`；源码部署时建议改为 `never`

更多日志、备份与目录内执行方式见 [deploy/README.md](deploy/README.md)。

## 验证

- 前端：`cd frontend && npm run build`
- 后端：`python -m compileall backend`

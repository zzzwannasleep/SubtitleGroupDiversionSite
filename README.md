# Subtitle Group Diversion Site

一个给字幕组内部使用的轻量分流站点，目标是用尽量低的学习成本和部署复杂度，把下面这条链路打通：

1. 管理员建号和控权
2. 上传者发布资源与 torrent
3. 用户浏览、RSS 订阅、下载个性化种子
4. 下载器通过私有 Tracker 完成受控分流

这个项目不是完整 PT 社区，也不追求做种率、魔力值、论坛、邀请体系那一套。它更像一个“够用、顺手、便于维护”的内部资源站。

## 技术方案

- 前端：`Vue 3 + Vite + Pinia + Vue Router`
- 后端：`Django 5 + DRF + drf-spectacular`
- 数据库：`MySQL 8`
- 缓存：`Redis`
- Tracker：`XBT`
- 部署：`Docker Compose`
- 镜像分发：`GHCR`

## 当前能力

- Session 登录、登出、`/auth/me`
- 三角色权限：`admin / uploader / user`
- 资源上传、编辑、隐藏、列表、详情
- 私有 torrent 校验与文件列表解析
- 个性化 torrent 下载
- RSS 总览、全量、分类、标签订阅
- XBT 用户与白名单同步
- 审计日志、公告、后台管理接口
- Swagger / OpenAPI

## 仓库结构

```text
frontend/   Vue 前端
backend/    Django 后端
tracker/    XBT Tracker 镜像构建文件
deploy/     Docker Compose、Nginx 和部署补充文件
docs/       设计与部署规范
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

说明：

- 后端会自动读取 `backend/.env`
- 默认使用 `SQLite + LocMemCache`
- 配置 `MYSQL_DATABASE` 和 `REDIS_URL` 后可切到 `MySQL + Redis`

## 生产部署

直接把下面两段内容复制到服务器上就能部署，不需要自己再填镜像名，也不需要默认改 tag。

`deploy/docker-compose.yml` 内容：

```yaml
name: subtitle-group-diversion-site

services:
  frontend:
    image: ghcr.io/zzzwannasleep/subtitlegroupdiversionsite/frontend:latest
    pull_policy: always
    restart: unless-stopped
    expose:
      - "80"
    networks:
      - app_net

  backend:
    image: ghcr.io/zzzwannasleep/subtitlegroupdiversionsite/backend:latest
    pull_policy: always
    restart: unless-stopped
    env_file:
      - ./.env
    depends_on:
      mysql:
        condition: service_healthy
      redis:
        condition: service_healthy
    environment:
      DJANGO_SETTINGS_MODULE: config.settings.prod
      MYSQL_HOST: mysql
      MYSQL_PORT: "3306"
      REDIS_URL: redis://redis:6379/0
      XBT_SYNC_ENABLED: "true"
      XBT_SYNC_DATABASE_ALIAS: default
    expose:
      - "8000"
    volumes:
      - torrent_storage:/app/media
      - backend_static:/app/staticfiles
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/', timeout=3).read()"]
      interval: 30s
      timeout: 5s
      retries: 5
      start_period: 30s
    networks:
      - app_net

  mysql:
    image: mysql:8
    restart: unless-stopped
    env_file:
      - ./.env
    command:
      - --default-authentication-plugin=mysql_native_password
      - --character-set-server=utf8mb4
      - --collation-server=utf8mb4_unicode_ci
    volumes:
      - mysql_data:/var/lib/mysql
    healthcheck:
      test: ["CMD-SHELL", "mysqladmin ping -h 127.0.0.1 -uroot -p$$MYSQL_ROOT_PASSWORD --silent"]
      interval: 20s
      timeout: 5s
      retries: 10
      start_period: 30s
    networks:
      - app_net

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: ["redis-server", "--appendonly", "yes"]
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 20s
      timeout: 5s
      retries: 10
    networks:
      - app_net

  xbt:
    image: ghcr.io/zzzwannasleep/subtitlegroupdiversionsite/xbt:latest
    pull_policy: always
    restart: unless-stopped
    env_file:
      - ./.env
    depends_on:
      mysql:
        condition: service_healthy
    environment:
      MYSQL_HOST: mysql
      MYSQL_PORT: "3306"
    ports:
      - "${XBT_TRACKER_PORT:-2710}:${XBT_TRACKER_PORT:-2710}"
    networks:
      - app_net

  nginx:
    image: nginx:stable-alpine
    restart: unless-stopped
    depends_on:
      backend:
        condition: service_healthy
      frontend:
        condition: service_started
    ports:
      - "${HTTP_PORT:-80}:80"
    volumes:
      - ./nginx/default.conf:/etc/nginx/conf.d/default.conf:ro
      - backend_static:/var/www/static:ro
      - torrent_storage:/var/www/media:ro
      - nginx_logs:/var/log/nginx
    networks:
      - app_net

networks:
  app_net:
    driver: bridge

volumes:
  mysql_data:
  redis_data:
  torrent_storage:
  backend_static:
  nginx_logs:
```

`deploy/.env` 内容模板：

```dotenv
DJANGO_SECRET_KEY=change-me-before-production
DJANGO_ALLOWED_HOSTS=example.com,www.example.com
SITE_BASE_URL=https://example.com
TRACKER_ANNOUNCE_BASE_URL=http://example.com:2710
MYSQL_DATABASE=subtitle_group
MYSQL_USER=subtitle
MYSQL_PASSWORD=change-me
MYSQL_ROOT_PASSWORD=change-root-password

LOG_LEVEL=INFO
XBT_TRACKER_PORT=2710
HTTP_PORT=80
```

环境变量怎么填：

- `DJANGO_SECRET_KEY`：填一串足够长的随机字符串。
- `DJANGO_ALLOWED_HOSTS`：填你的站点域名，多个域名用逗号分隔。
- `SITE_BASE_URL`：填站点公网地址，例如 `https://example.com`。
- `TRACKER_ANNOUNCE_BASE_URL`：填 Tracker 公网地址，例如 `http://example.com:2710`。
- `MYSQL_DATABASE`：MySQL 数据库名。
- `MYSQL_USER`：MySQL 用户名。
- `MYSQL_PASSWORD`：MySQL 应用密码。
- `MYSQL_ROOT_PASSWORD`：MySQL root 密码。
- `LOG_LEVEL`：一般保持 `INFO` 就行。
- `XBT_TRACKER_PORT`：一般保持 `2710`。
- `HTTP_PORT`：一般保持 `80`；如果前面还有反代，可以改成别的端口。

启动命令：

```bash
docker compose --env-file deploy/.env -f deploy/docker-compose.yml up -d
```

首次启动时会自动完成：

- Django 数据库迁移
- Django 静态文件收集
- XBT 配置文件生成
- XBT 数据表结构导入

然后执行：

```bash
docker compose --env-file deploy/.env -f deploy/docker-compose.yml exec backend python manage.py createsuperuser
```

更多部署细节见：

- `deploy/README.md`
- `docs/docker-compose-deployment-spec.md`
- `docs/xbt-container-integration-spec.md`

## 镜像构建

仓库提供 3 个应用镜像：

- `frontend`
- `backend`
- `xbt`

对应工作流位于：

- `.github/workflows/build-images.yml`

工作流会在 `main` 和 `v*` tag 上构建并推送到 `ghcr.io`，同时支持手动触发。默认标签策略：

- `latest`（推送到 `main` 时）
- `main-<short_sha>`
- `v1.0.0`

## 关键约束

- 保持单体 Django 后端，不拆微服务
- 默认只保留一套主路径：`Vue + Django + XBT + MySQL + Redis`
- 环境变量尽量少
- 日志默认走 stdout/stderr
- 优先保证“简单可用”，而不是“架构看起来更炫”

## 文档入口

- `docs/subtitle-group-diversion-site-spec.md`
- `docs/backend-architecture-spec.md`
- `docs/database-xbt-mapping-spec.md`
- `docs/simplicity-usability-operability-rules.md`

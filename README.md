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

```bash
Copy-Item deploy/.env.example deploy/.env
docker compose --env-file deploy/.env -f deploy/docker-compose.yml up -d
docker compose --env-file deploy/.env -f deploy/docker-compose.yml exec backend python manage.py createsuperuser
```

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

## 验证

- 前端：`cd frontend && npm run build`
- 后端：`python -m compileall backend`

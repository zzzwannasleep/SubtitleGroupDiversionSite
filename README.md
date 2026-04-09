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

直接使用 `deploy/docker-compose.yml` 就可以部署，不再要求额外的 `.env` 文件或初始化脚本。

1. 打开 `deploy/docker-compose.yml`
2. 修改顶部这几个配置块里的示例值：
   - `x-site-env`
   - `x-db-env`
   - `x-xbt-env`
3. 执行：

```bash
docker compose -f deploy/docker-compose.yml up -d --build
```

首次启动时会自动完成：

- Django 数据库迁移
- Django 静态文件收集
- XBT 配置文件生成
- XBT 数据表结构导入

然后执行：

```bash
docker compose -f deploy/docker-compose.yml exec backend python manage.py createsuperuser
```

如果你改了 `XBT_TRACKER_PORT`，记得把 `deploy/docker-compose.yml` 里 `xbt.ports` 的端口映射一起改掉。

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

- `main-<short_sha>`
- `v1.0.0`

默认部署文档走本地 `docker compose build` 路径，GHCR 镜像主要用于 CI 分发与后续扩展。

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

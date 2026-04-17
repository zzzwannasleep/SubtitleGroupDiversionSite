# Deploy

生产部署使用 [docker-compose.yml](docker-compose.yml)。以下命令默认在 `deploy/` 目录下执行。

默认会启动：

- `frontend`
- `backend`
- `mysql`
- `redis`
- `nginx`

## 准备配置

先复制配置文件：

```bash
cp .env.example .env
# PowerShell: Copy-Item .env.example .env
```

至少确认这些配置已经改成你的生产值：

- `DJANGO_SECRET_KEY`
- `DJANGO_ALLOWED_HOSTS`
- `SITE_BASE_URL`
- `MYSQL_PASSWORD`
- `MYSQL_ROOT_PASSWORD`

## 方式一：源码部署

适合已经 `git clone` 整个仓库、需要自行构建镜像的场景。先在仓库根目录执行：

```bash
docker build -t subtitle-group-diversion-site/frontend:local ./frontend
docker build -t subtitle-group-diversion-site/backend:local ./backend
```

然后回到 `deploy/.env`，把镜像来源改成：

```env
FRONTEND_IMAGE=subtitle-group-diversion-site/frontend:local
BACKEND_IMAGE=subtitle-group-diversion-site/backend:local
IMAGE_PULL_POLICY=never
```

启动服务并创建管理员账号：

```bash
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

## 方式二：预构建镜像部署

适合只保留 `deploy/` 目录、直接拉取现成镜像的场景。默认会使用：

- `ghcr.io/zzzwannasleep/subtitlegroupdiversionsite/frontend:latest`
- `ghcr.io/zzzwannasleep/subtitlegroupdiversionsite/backend:latest`

启动服务：

```bash
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

如果希望按初始化顺序自动启动，也可以执行：

```bash
sh scripts/init.sh
```

## 查看日志

```bash
docker compose logs -f backend nginx mysql redis
```

## 备份

```bash
sh scripts/backup.sh
```

## 说明

- `backend` 与 `nginx` 共享 `/media` 和 `/staticfiles`
- 首次启动会自动执行数据库迁移与静态文件收集
- `FRONTEND_IMAGE` / `BACKEND_IMAGE` 可覆盖默认镜像地址，`IMAGE_PULL_POLICY=never` 可关闭拉取并改用本地镜像
- 当前部署方案不再包含私有 Tracker / XBT 服务

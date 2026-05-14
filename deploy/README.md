# Deploy

生产部署使用 [docker-compose.yml](docker-compose.yml)。以下命令默认都在 `deploy/` 目录下执行。

默认启动的服务：

- `backend`
- `mysql`
- `redis`

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

## Media 鐩綍鏄犲皠

榛樿鎯呭喌涓嬶紝`backend` 浼氱户缁娇鐢?Docker volume `torrent_storage:/app/media`銆?

濡傛灉浣犳兂鎶?`/media` 鐩存帴鏄犲皠鍒板崟鐙殑瀛樺偍鐩橈紝鍙互鍦?`deploy/.env` 閲屾坊鍔狅細

```env
MEDIA_VOLUME_SPEC=D:/subtitle-group-media:/app/media
```

Linux 渚嬪瓙锛?

```env
MEDIA_VOLUME_SPEC=/srv/subtitle-group-media:/app/media
```

鍙抽渶淇濈暀鍙冲渶鍚庣殑 `:/app/media` 涓嶅彉锛涘彧闇€鏇存崲宸﹁竟鐨勪富鏈虹洰褰曘€?

## 方式一：源码部署

适合已经 `git clone` 整个仓库、需要自己构建镜像的场景。先在仓库根目录执行：

```bash
docker build -f backend/Dockerfile -t subtitle-group-diversion-site/backend:local .
```

然后回到 `deploy/.env`，把镜像来源改成：

```env
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

- `zzzwannasleep111/subtitlegroupdiversionsite:latest`

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

## Torrust Tracker

当前仓库已经把 **Torrust 的后端对接逻辑接进去了**，但 **Torrust Tracker 本体仍然需要单独部署**。

这里已经在 `docker-compose.yml` 里提供了可选的 `tracker` 服务，通过 profile 启动，不会影响原来的纯分流站部署。

先准备 tracker 配置文件：

```bash
cp tracker/tracker.example.toml tracker/tracker.toml
# PowerShell: Copy-Item tracker/tracker.example.toml tracker/tracker.toml
```

然后在 `.env` 里至少补这些配置：

- `TRACKER_ENABLED=true`
- `TRACKER_ANNOUNCE_URL=http://你的域名或服务器IP:7070/announce`
- `TORRUST_API_URL=http://tracker:1212`
- `TORRUST_API_TOKEN=your-admin-token`
- `deploy/tracker/tracker.toml` 里要保留新版 Torrust 必需的 `[metadata]` 段，例如 `schema_version = "2.0.0"`

这里要特别注意：

- `.env` 每一行都必须是 `KEY=value`，不要在行首加空格，也不要写成 `KEY = value`
- `TRACKER_ANNOUNCE_URL` 是写进用户下载到的 `.torrent` 里的，必须是 **外部 BT 客户端也能访问到的地址**
- `TORRUST_API_URL` 才是 Django 容器访问 Torrust 管理 API 的 **容器内网地址**

启动方式：

```bash
docker compose --profile tracker up -d
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py sync_tracker_state
```

说明：

- HTTP announce 默认对外映射到 `7070`
- UDP announce 默认对外映射到 `6969/udp`
- 管理 API 默认只映射到宿主机 `127.0.0.1:1212`
- `tracker.toml` 默认就是 `private + listed` 模式
- `TRACKER_IMAGE` 默认是 `torrust/tracker:develop`，如果你想锁版本，建议在 `.env` 里改成你确认过的具体 tag

## 查看日志

```bash
docker compose logs -f backend mysql redis
docker compose --profile tracker logs -f tracker
```

## 备份

```bash
sh scripts/backup.sh
```

## 说明

- `backend` 容器会直接提供前端页面、`/api`、`/static` 和 `/media`
- 首次启动会自动执行数据库迁移与静态文件收集
- `BACKEND_IMAGE` 可覆盖默认镜像地址，`IMAGE_PULL_POLICY=never` 可关闭拉取并改用本地镜像
- 如果启用了 `tracker` profile，Django 会通过 `TORRUST_API_URL` 调用 Torrust 管理 API，并通过 `TRACKER_ANNOUNCE_URL` 生成用户下载到的 announce 地址

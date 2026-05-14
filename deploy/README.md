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

## Media 目录映射

默认情况下，`backend` 会继续使用 Docker volume `torrent_storage:/app/media`。

如果你想把 `/media` 直接映射到单独的存储盘，可以在 `deploy/.env` 里添加：

```env
MEDIA_VOLUME_SPEC=D:/subtitle-group-media:/app/media
```

Linux 例子：

```env
MEDIA_VOLUME_SPEC=/srv/subtitle-group-media:/app/media
```

推荐把“发布页服务器目录”使用的映射资源单独放到另一个目录，而不是继续复用 `/app/media`。这样站点内部文件就不会再写进你的资源映射目录。

```env
WEBSEED_LIBRARY_ROOT=/app/webseed-library
WEBSEED_LIBRARY_URL_PATH=/webseed/
WEBSEED_LIBRARY_VOLUME_SPEC=D:/subtitle-group-library:/app/webseed-library
```

Linux 例子：

```env
WEBSEED_LIBRARY_ROOT=/app/webseed-library
WEBSEED_LIBRARY_URL_PATH=/webseed/
WEBSEED_LIBRARY_VOLUME_SPEC=/srv/subtitle-group-library:/app/webseed-library
```

如果你希望这些直链走单独的公网域名、Nginx 或 CDN，可以额外配置：

```env
WEBSEED_LIBRARY_PUBLIC_URL=https://static.example.com/webseed
```

配置后：

- 发布页“服务器目录”生成的逐文件直链预览会使用这个资源目录
- 下载种子时写入的 webseed 根 URL 也会对应这个资源目录
- 站点内部的 `torrent_templates/`、`site/`、`release-webseeds/` 不会再写进你的资源映射目录

只需保留最后的 `:/app/media` 不变；只需更换左边的主机目录。

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

`sh scripts/init.sh` 现在会在 `TRACKER_ENABLED=true` 时自动启用 `tracker` profile，并在缺少 `tracker/tracker.toml` 时从示例文件自动生成一份。

## Torrust Tracker

当前仓库已经把 **Torrust 的后端对接逻辑接进去了**，但 **Torrust Tracker 本体仍然需要单独部署**。

这里已经在 `docker-compose.yml` 里提供了可选的 `tracker` 服务，通过 profile 启动，不会影响原来的纯分流站部署。

先准备 tracker 配置文件：

```bash
cp tracker/tracker.example.toml tracker/tracker.toml
# PowerShell: Copy-Item tracker/tracker.example.toml tracker/tracker.toml
```

然后按下面两种模式二选一。

### 模式 A：BT 客户端直连 Torrust

适合只需要 Private Tracker，不需要站内自动回填用户上传量、下载量、做种量等统计的场景。

```env
TRACKER_ENABLED=true
COMPOSE_PROFILES=tracker

TRACKER_ANNOUNCE_URL=http://你的域名或服务器IP:7070/announce
TRACKER_SCRAPE_URL=http://你的域名或服务器IP:7070/scrape

TORRUST_API_URL=http://tracker:1212
TORRUST_API_TOKEN=your-admin-token
```

### 模式 B：Django 代理 announce/scrape，并自动回填用户统计

如果你要启用站内“按用户名查询上传量、下载量、做种量、做种体积”等数据，推荐使用这一模式。

```env
TRACKER_ENABLED=true
COMPOSE_PROFILES=tracker
TRACKER_AUTH_MODE=per_user

TRACKER_ANNOUNCE_URL=https://你的站点域名/tracker/announce
TRACKER_INTERNAL_ANNOUNCE_URL=http://tracker:7070/announce

TRACKER_PUBLIC_SCRAPE_URL=https://你的站点域名/tracker/scrape
TRACKER_SCRAPE_URL=http://tracker:7070/scrape

TORRUST_API_URL=http://tracker:1212
TORRUST_API_TOKEN=your-admin-token
TRACKER_PEER_SNAPSHOT_STALE_SECONDS=900
```

同时把 `deploy/tracker/tracker.toml` 的这项改为 `true`：

```toml
[core.net]
on_reverse_proxy = true
```

这类自动回填是“announce 级近实时”，不是字节级实时：

- 用户统计会在 BT 客户端向 tracker 发 `announce` 时更新
- 默认示例 `tracker.toml` 的 announce 间隔是 `120` 秒
- `started`、`completed`、`stopped` 事件也会触发更新

这里要特别注意：

- `.env` 每一行都必须是 `KEY=value`，不要在行首加空格，也不要写成 `KEY = value`
- `TRACKER_ANNOUNCE_URL` / `TRACKER_PUBLIC_SCRAPE_URL` 是给外部 BT 客户端访问的公网地址
- `TRACKER_INTERNAL_ANNOUNCE_URL` / `TRACKER_SCRAPE_URL` 是 Django 转发到 Torrust 的容器内网地址，Docker Compose 下通常分别是 `http://tracker:7070/announce` 和 `http://tracker:7070/scrape`
- `TORRUST_API_URL` 是 Django 容器访问 Torrust 管理 API 的内网地址，Docker Compose 场景下应保持为 `http://tracker:1212`
- `deploy/tracker/tracker.toml` 里要保留新版 Torrust 必需的 `[metadata]` 段，例如 `schema_version = "2.0.0"`

启动方式：

```bash
docker compose --profile tracker up -d
```

如果把 `COMPOSE_PROFILES=tracker` 写进 `.env`，那么普通的 `docker compose up -d` 也会自动把 tracker 一起启动。后端容器首启会自动等待 Torrust API 就绪，并执行 `users + releases` 的 tracker 同步；默认不会把 `scrape` 放进启动阻塞里。

如果你使用的是完整仓库，也可以继续用：

```bash
sh scripts/init.sh
```

`sh scripts/init.sh` 会在 `TRACKER_ENABLED=true` 时自动启用 `tracker` profile、自动补 `tracker.toml`，并在代理模式缺少 `TRACKER_INTERNAL_ANNOUNCE_URL` 或 `on_reverse_proxy` 没有设为 `true` 时给出告警。

升级现有站点后，第一次启动新的 `backend` 容器会自动执行数据库迁移；如果你习惯手动执行，也可以补一次：

```bash
docker compose exec backend python manage.py migrate
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
- 如果启用了 `tracker` profile，Django 会通过 `TORRUST_API_URL` 调用 Torrust 管理 API，并通过 `TRACKER_ANNOUNCE_URL` 生成用户下载到的 announce 地址；当 `TRACKER_ANNOUNCE_URL` 指向 `/tracker/announce` 代理时，Django 还会在 announce/scrape 经过站内时近实时回填用户统计

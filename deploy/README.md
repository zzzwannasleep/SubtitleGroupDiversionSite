# Deploy

生产部署统一使用 [docker-compose.yml](docker-compose.yml)。以下命令默认都在 `deploy/` 目录下执行。

默认启动的服务：

- `backend`
- `mysql`
- `redis`

如果启用可选的 Torrust Tracker，还会额外启动：

- `tracker`

## 快速开始

先复制环境变量模板：

```bash
cp .env.example .env
# PowerShell: Copy-Item .env.example .env
```

至少要先改掉这些配置：

- `DJANGO_SECRET_KEY`
- `DJANGO_ALLOWED_HOSTS`
- `SITE_BASE_URL`
- `MYSQL_PASSWORD`
- `MYSQL_ROOT_PASSWORD`

然后选择下面两种部署方式之一：

1. 完整仓库部署：适合自己构建镜像、自己跟代码版本。
2. 仅 `deploy/` 目录部署：适合直接拉预构建镜像。

## 直链目录

如果你要用“服务器目录”模式或 qB 直链，只需要关心这一个目录：

- `/app/media/webseed`
  BT 直链资源目录。发布页预览、torrent 里的 `url-list`、qB / libtorrent 用的 `httpseeds`，都走这里。

当前 `docker-compose.yml` 已经直接把宿主机目录挂好了：

```yaml
backend:
  volumes:
    - ${SITE_MEDIA_STORAGE:-site_media}:/app/media
    - ${WEBSEED_LIBRARY_HOST_PATH:-./library}:/app/media/webseed
```

也就是说：

- 站点自己的媒体文件默认放在 Docker 卷 `site_media` 里，`site/`、`release-webseeds/`、`torrent_templates/` 等内部文件都走这里
- `deploy/library/`：发布页“服务器目录”模式默认使用的资源目录
- 发布页看到的是 `WEBSEED_LIBRARY_HOST_PATH` 指向目录的根本身，不需要在这个目录下面再建一层 `webseed/`
- 如果你从仓库根目录执行 `docker compose -f deploy/docker-compose.yml ...`，默认需要关心的宿主机目录也只有 `deploy/library/`

站点自己的媒体文件不会再写进 `WEBSEED_LIBRARY_HOST_PATH` 指向的映射目录；默认情况下你也不需要直接碰它们。

## 默认挂载

大多数部署不用再额外写环境变量，直接往这个目录放文件即可：

```text
deploy/library/
```

如果你就是想换到别的宿主机路径，直接在 `.env` 里指定 `WEBSEED_LIBRARY_HOST_PATH` 即可。比如：

```env
# Windows
WEBSEED_LIBRARY_HOST_PATH=D:/subtitle-group-data

# Linux
WEBSEED_LIBRARY_HOST_PATH=/srv/subtitle-group-data
```

改完以后，发布页“服务器目录”直接读取的就是这些目录本身：

- `D:/subtitle-group-data/`
- `/srv/subtitle-group-data/`

默认情况下：

- 容器内资源目录固定是 `/app/media/webseed`
- 站点内 webseed 访问路径固定是 `/webseed/`
- 站点内部媒体固定保存在 Docker 卷 `site_media`

如果这些直链不是由站点自己直接对外暴露，而是走你自己的 Nginx、反代、对象存储或 CDN，再额外配置：

```env
WEBSEED_LIBRARY_PUBLIC_URL=https://static.example.com/webseed
```

配置后会影响三处：

- 发布页“服务器目录”的逐文件直链预览
- 下载种子时写入的 `url-list`
- 下载种子时写入的 `httpseeds`

## qB 直链接入要求

如果你的目标是让 qBittorrent 真正走 HTTP 直链，而不是只把地址写进种子但实际不生效，部署时请确认下面几点：

1. `docker-compose.yml` 里把宿主机映射目录挂到 `/app/media/webseed` 后，这个映射目录根里的文件结构必须和 torrent 内容匹配。默认就是 `deploy/library/`。
2. 多文件 torrent 推荐选择和 `info.name` 对应的完整根目录；单文件 torrent 可以直接选择文件。
3. qB 所在机器必须能访问：
   - `WEBSEED_LIBRARY_PUBLIC_URL` 对应的静态文件地址，或者站点自己的 `/webseed/`
   - 站点的 `/api/httpseed/<infohash>/`
4. 如果站点前面有反向代理或 CDN，确保它们不会拦截 `Range`、查询参数、二进制流响应。
5. 默认 webseed 路径是 `/webseed/`；如果你自己改过这个前缀，外部反代规则也要一起改。

发布页现在会同时给出：

- `Torrent Webseed Root URL`：写入 `url-list` 的目录根地址
- `qB HTTP Seed URL`：写入 `httpseeds` 的基础接口地址，不是单文件直链
- 每个文件的解析后直链：用于核对文件级 URL 是否真的对上资源路径

其中 `qB HTTP Seed URL` 只需要保持基础地址正确即可。qB / libtorrent 在实际取 piece 时会自动追加 `info_hash`、`piece`、`ranges` 等查询参数，所以不要手工给它拼文件路径，也不要把它当成普通文件下载链接去验证。

建议发种前先点一次“生成直链预览”，确认地址和目录层级都对。

## 方式一：完整仓库部署

适合已经 `git clone` 整个仓库、需要自己构建镜像的场景。

先在仓库根目录执行：

```bash
docker build -f backend/Dockerfile -t subtitle-group-diversion-site/backend:local .
```

然后在 `deploy/.env` 里改成：

```env
BACKEND_IMAGE=subtitle-group-diversion-site/backend:local
IMAGE_PULL_POLICY=never
```

启动服务并创建管理员账号：

```bash
docker compose up -d
docker compose exec backend python manage.py createsuperuser
```

如果要直接指定管理员用户名、邮箱和密码：

```bash
docker compose exec \
  -e DJANGO_SUPERUSER_USERNAME=admin \
  -e DJANGO_SUPERUSER_EMAIL=admin@example.com \
  -e DJANGO_SUPERUSER_PASSWORD=change-me \
  backend python manage.py createsuperuser --noinput
```

## 方式二：仅 `deploy/` 目录部署

适合只保留 `deploy/` 目录、直接拉预构建镜像的场景。

默认镜像：

- `zzzwannasleep111/subtitlegroupdiversionsite:latest`

启动服务：

```bash
docker compose up -d
docker compose exec backend python manage.py createsuperuser
```

同样也支持无交互创建管理员：

```bash
docker compose exec \
  -e DJANGO_SUPERUSER_USERNAME=admin \
  -e DJANGO_SUPERUSER_EMAIL=admin@example.com \
  -e DJANGO_SUPERUSER_PASSWORD=change-me \
  backend python manage.py createsuperuser --noinput
```

如果希望按初始化顺序自动处理，也可以执行：

```bash
sh scripts/init.sh
```

## 升级现有部署

如果你之前已经上线，且以前把“服务器资源目录”直接映射到了 `/app/media`，这次升级建议按下面顺序操作：

1. 备份数据库、旧 `.env`、以及原来的媒体目录。
2. 更新代码或替换新的 `deploy/` 目录。
3. 打开新的 `docker-compose.yml`，确认 `backend.volumes` 里已经拆成“站点内部媒体存储”和“服务器映射目录”两条挂载。默认配置是：

```yaml
- ${SITE_MEDIA_STORAGE:-site_media}:/app/media
- ${WEBSEED_LIBRARY_HOST_PATH:-./library}:/app/media/webseed
```

4. 把真正的“服务器资源文件”直接放到映射目录根。默认就是 `deploy/library/`；如果你改成了别的宿主机目录，就直接放到那个目录本身，不要再套 `webseed/` 子目录。
5. 启动新容器：

```bash
docker compose up -d
```

6. 如需手动补一次迁移：

```bash
docker compose exec backend python manage.py migrate
```

7. 登录站点，到发布页测试一次“服务器目录 -> 生成直链预览”。

如果你升级后发现映射目录里还在长 `torrent_templates/`、`site/`、`release-webseeds/`，基本就是因为：

- 仍然把映射目录直接挂到了 `/app/media`
- 没有更新到新的 compose 文件

如果这些目录是旧部署已经写进去的历史文件，需要在服务器上把映射目录换成干净目录，或者手动清理一次；新配置不会再继续往里面写这些站点内部目录。

如果你旧部署里的站点内部媒体原本就放在宿主机目录（例如旧的 `deploy/data/`），升级时可以先临时加一行：

```env
SITE_MEDIA_STORAGE=./data
```

这样会先继续沿用旧目录，避免丢失已有的站点图标、背景图、已上传 torrent、站内托管的 webseed 文件。确认需要的数据已经迁走后，再去掉这一行，回到默认的 Docker 卷模式。

## 启用 Torrust Tracker

当前仓库已经内置了 Django 到 Torrust 的对接逻辑，但 Torrust Tracker 本体仍然需要单独启动。`docker-compose.yml` 里已经带了可选的 `tracker` 服务。

先准备配置文件：

```bash
cp tracker/tracker.example.toml tracker/tracker.toml
# PowerShell: Copy-Item tracker/tracker.example.toml tracker/tracker.toml
```

如果你用的是完整仓库，也可以在仓库根目录里复制：

```bash
cp deploy/tracker/tracker.example.toml deploy/tracker/tracker.toml
# PowerShell: Copy-Item deploy/tracker/tracker.example.toml deploy/tracker/tracker.toml
```

### 模式 A：BT 客户端直接连 Torrust

适合只需要基础 Private Tracker，不要求站内自动回填用户上传量、下载量、做种量等统计。

```env
TRACKER_ENABLED=true
COMPOSE_PROFILES=tracker

TRACKER_ANNOUNCE_URL=http://你的域名或服务器IP:7070/announce
TRACKER_SCRAPE_URL=http://你的域名或服务器IP:7070/scrape

TORRUST_API_URL=http://tracker:1212
TORRUST_API_TOKEN=your-admin-token
```

### 模式 B：Django 代理 announce / scrape，并自动回填用户统计

适合需要站内按用户统计上传、下载、做种等数据。

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

同时把 `tracker.toml` 里的这一项改成：

```toml
[core.net]
on_reverse_proxy = true
```

启动命令：

```bash
docker compose --profile tracker up -d
```

如果已经在 `.env` 里写了 `COMPOSE_PROFILES=tracker`，普通的 `docker compose up -d` 也会自动把 `tracker` 一起拉起。

更完整的 Tracker 接入背景见：

- [docs/PRIVATE_TRACKER_INTEGRATION.md](../docs/PRIVATE_TRACKER_INTEGRATION.md)

## 部署后验证

建议至少检查这几项：

1. `docker compose ps` 看服务都在运行。
2. 打开站点首页、后台、发布页，确认页面能正常访问。
3. 在发布页选择：
   - `1` 个 torrent
   - `1` 个服务器目录或文件
4. 点击“生成直链预览”，确认：
   - `Torrent Webseed Root URL` 正确
   - `qB HTTP Seed URL` 正确
   - 文件逐项直链正确
5. 下载生成后的种子，用 qB 测试是否能看到 webseed / http seed。

## 常见问题

### 1. 映射目录里还在自动创建新文件夹

说明运行时没有把资源目录挂到 `/app/media/webseed`，或者还在用旧的 compose 配置。

优先检查：

- `docker-compose.yml` 是否已更新
- `backend.volumes` 是否已经拆成“站点内部媒体存储”和 `/app/media/webseed` 两条挂载

### 2. 发布页不能生成直链预览

优先检查：

- 选择的资源层级是否和 torrent 结构一致
- 多文件 torrent 是否选择了完整根目录
- `/app/media/webseed` 对应目录里是否真的有对应文件

### 3. qB 不认直链或不走 HTTP

优先检查：

- `WEBSEED_LIBRARY_PUBLIC_URL` 或 `/webseed/` 是否能从 qB 所在机器直接访问
- `/api/httpseed/<infohash>/` 是否可访问
- 直接打开 `qB HTTP Seed URL` 如果提示缺少参数是正常现象；真正请求时 qB 会自动带上 `info_hash`、`piece`、`ranges`
- 反代/CDN 是否放行查询参数和二进制流
- 资源文件是否完整、路径是否和 torrent 一致

### 4. 只想用目录式 webseed，不想走 HTTP seed

当前下载种子会同时写 `url-list` 和 `httpseeds`，这是为了兼容 qB / libtorrent。一般不需要手工关闭。

## 日志

```bash
docker compose logs -f backend mysql redis
docker compose --profile tracker logs -f tracker
```

## 备份

```bash
sh scripts/backup.sh
```

## 补充说明

- `backend` 容器会直接提供前端页面、`/api`、`/static`、`/media`，以及新的 webseed 资源路径。
- 首次启动会自动执行数据库迁移和静态文件收集。
- `BACKEND_IMAGE` 可以覆盖默认镜像地址；源码部署时通常配合 `IMAGE_PULL_POLICY=never` 使用。
- Tracker 与 qB 直链是两套能力，是否启用 Tracker 不影响服务器目录直链本身。

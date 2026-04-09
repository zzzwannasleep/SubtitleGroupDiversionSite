# Deploy

`deploy/docker-compose.yml` 里的镜像已经固定为 `latest`，不需要再填镜像名或 tag。

你只需要准备 `deploy/.env`，然后启动：

```bash
docker compose --env-file deploy/.env -f deploy/docker-compose.yml up -d
```

默认镜像地址已经预填在 `deploy/docker-compose.yml` 里：

- `ghcr.io/zzzwannasleep/subtitlegroupdiversionsite/frontend`
- `ghcr.io/zzzwannasleep/subtitlegroupdiversionsite/backend`
- `ghcr.io/zzzwannasleep/subtitlegroupdiversionsite/xbt`

首次启动会自动完成：

- Django 数据库迁移
- Django 静态文件收集
- XBT 配置文件生成
- XBT 数据表结构导入

然后创建第一个管理员：

```bash
docker compose --env-file deploy/.env -f deploy/docker-compose.yml exec backend python manage.py createsuperuser
```

查看关键日志：

```bash
docker compose --env-file deploy/.env -f deploy/docker-compose.yml logs -f backend nginx xbt
```

数据库备份：

```bash
sh deploy/scripts/backup.sh
```

说明：

- 默认直接从 GHCR 拉取镜像，不需要本地构建。
- `backend` 和 `nginx` 共享 `/media` 与 `/static` 卷，容器更新后上传文件和静态文件仍会保留。
- `nginx` 访问日志输出到 `stdout`，错误日志输出到 `stderr`，可直接用 `docker logs` / `docker compose logs` 查看。
- `xbt` 入口脚本会输出启动、配置渲染、等待数据库与 schema 导入日志，便于排障。
- Compose 默认启用 `json-file` 日志轮转：单文件 `10m`，保留 `3` 份。
- 默认直接拉取 `latest`。

# Deploy

1. 复制 `deploy/.env.example` 为 `deploy/.env`
2. 按注释填写环境变量
3. 直接启动：

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

说明：

- 默认直接从 GHCR 拉取镜像，不需要本地构建。
- `backend` 和 `nginx` 共享 `/media` 与 `/static` 卷，容器更新后上传文件和静态文件仍会保留。
- 默认镜像 tag 指向当前已发布的 `main-f1de957`。如果后面要切其他版本，可在 `deploy/.env` 里加 `APP_IMAGE_TAG=...` 覆盖。

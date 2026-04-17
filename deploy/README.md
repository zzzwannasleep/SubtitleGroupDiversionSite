# Deploy

生产部署使用 `deploy/docker-compose.yml`，默认会启动：

- `frontend`
- `backend`
- `mysql`
- `redis`
- `nginx`

## 启动

```bash
Copy-Item deploy/.env.example deploy/.env
docker compose --env-file deploy/.env -f deploy/docker-compose.yml up -d
docker compose --env-file deploy/.env -f deploy/docker-compose.yml exec backend python manage.py createsuperuser
```

## 查看日志

```bash
docker compose --env-file deploy/.env -f deploy/docker-compose.yml logs -f backend nginx mysql redis
```

## 备份

```bash
sh deploy/scripts/backup.sh
```

## 说明

- `backend` 与 `nginx` 共享 `/media` 和 `/staticfiles`
- 首次启动会自动执行数据库迁移与静态文件收集
- 当前部署方案不再包含私有 Tracker / XBT 服务

# Backend

后端基于 `Django + DRF`，负责：

- 用户、邀请码、权限和审计日志
- 资源发布、编辑、隐藏和下载
- RSS 输出
- 站点设置、公告、分类、标签管理
- Swagger / OpenAPI

当前实现已移除私有 Tracker / XBT 同步逻辑，torrent 文件按上传内容原样保存，下载接口直接返回站内保存的 torrent。

## 本地启动

```bash
Copy-Item backend/.env.example backend/.env
python -m pip install -r backend/requirements.txt
python backend/manage.py migrate
python backend/manage.py createsuperuser
python backend/manage.py runserver
```

## 常用配置

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `SITE_BASE_URL`
- `MYSQL_DATABASE` / `MYSQL_USER` / `MYSQL_PASSWORD` / `MYSQL_HOST` / `MYSQL_PORT`
- `REDIS_URL`
- `LOG_LEVEL`

未配置 MySQL / Redis 时，可先用本地默认配置完成开发联调。

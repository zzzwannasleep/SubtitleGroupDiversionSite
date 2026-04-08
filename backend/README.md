# Subtitle Group Diversion Site Backend

基于 `Django + DRF` 的后端实现，覆盖：

- Session 登录与权限
- 用户、资源、公告、审计、站点设置
- RSS 输出
- 个性化 torrent 下载
- XBT 用户与白名单同步
- Swagger / OpenAPI

## 本地启动

1. 复制环境模板：`Copy-Item backend/.env.example backend/.env`
2. 按需修改 `backend/.env` 中的少量配置
3. 安装依赖：`python -m pip install -r backend/requirements.txt`
4. 迁移数据库：`python backend/manage.py migrate`
5. 创建管理员：`python backend/manage.py createsuperuser`
6. 启动服务：`python backend/manage.py runserver`

默认使用 `SQLite + LocMemCache`，配置 `MYSQL_DATABASE` 等变量后可切换到 `MySQL 8`。

后端会自动读取 `backend/.env`，不需要额外引入 `python-dotenv` 或手动导出环境变量。

## 可选配置

- `REDIS_URL`：启用 Redis 作为 Django 缓存后端，用于 Session 缓存和限流共享状态。
- `SITE_BASE_URL`：站点基础地址，用于生成 RSS 与下载链接。
- `TRACKER_ANNOUNCE_BASE_URL`：个性化 torrent 注入的 announce 基础地址，默认跟随 `SITE_BASE_URL`。

# Subtitle Group Diversion Site Backend

基于 `Django + DRF` 的后端实现，覆盖：

- Session 登录与权限
- 用户、资源、公告、审计、站点设置
- RSS 输出
- 个性化 torrent 下载
- XBT 用户与白名单同步
- Swagger / OpenAPI

## 本地启动

1. 安装依赖：`python -m pip install -r backend/requirements.txt`
2. 迁移数据库：`python backend/manage.py migrate`
3. 创建管理员：`python backend/manage.py createsuperuser`
4. 启动服务：`python backend/manage.py runserver`

默认使用 `SQLite`，配置 `MYSQL_DATABASE` 等变量后可切换到 `MySQL 8`。

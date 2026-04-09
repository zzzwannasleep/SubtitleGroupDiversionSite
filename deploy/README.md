# Deploy

直接编辑 `deploy/docker-compose.yml` 顶部的示例值，然后执行：

```bash
docker compose -f deploy/docker-compose.yml up -d --build
```

首次启动会自动完成这些事情：

- Django 数据库迁移
- Django 静态文件收集
- XBT 配置文件生成
- XBT 数据表结构导入

初始化完成后，创建第一个管理员：

```bash
docker compose -f deploy/docker-compose.yml exec backend python manage.py createsuperuser
```

说明：

- 默认部署直接本地构建 `frontend`、`backend`、`xbt` 三个容器镜像。
- `backend` 和 `nginx` 共享 `/media` 与 `/static` 卷，容器更新后上传文件和静态文件仍会保留。
- 如果你修改了 `XBT_TRACKER_PORT`，记得把 `xbt.ports` 里的端口映射一起改掉。

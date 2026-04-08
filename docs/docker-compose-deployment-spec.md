# Docker Compose 部署文档

## 1. 文档目标

这份文档专门定义：

- 生产环境如何用 `Docker Compose` 部署整套系统
- 各容器的职责与镜像来源
- 最小环境变量集合
- 数据卷与网络规划
- 日志查看方式
- 更新与回滚方式

目标是让部署流程尽量收敛为：

1. 配置少量环境变量
2. `docker compose pull`
3. `docker compose up -d`

## 2. 当前结论

当前推荐部署形态：

- `frontend`：前端静态站点
- `backend`：Django + DRF
- `mysql`：MySQL 8
- `redis`：Redis
- `xbt`：独立 Tracker 容器
- `nginx`：统一入口

生产环境原则：

- `frontend`、`backend`、`xbt` 使用预构建镜像
- 服务器不做本地 `build`
- 通过 `GHCR` 拉取镜像

## 3. 推荐目录结构

```text
deploy/
  docker-compose.yml
  .env.example
  nginx/
    default.conf
  xbt/
    xbt_tracker.conf
  scripts/
    init.sh
    backup.sh
```

说明：

- `docker-compose.yml`：生产编排文件
- `.env.example`：最小环境变量模板
- `nginx/`：Nginx 配置
- `xbt/`：XBT 配置文件
- `scripts/`：初始化和备份脚本

## 4. 镜像策略

### 4.1 应用镜像

推荐：

- `ghcr.io/<owner>/<repo>/frontend:<tag>`
- `ghcr.io/<owner>/<repo>/backend:<tag>`
- `ghcr.io/<owner>/<repo>/xbt:<tag>`

### 4.2 基础镜像

推荐：

- `mysql:8`
- `redis:7-alpine`
- `nginx:stable-alpine`

### 4.3 标签策略

推荐：

- 测试环境：`main-<short_sha>`
- 正式环境：`v1.0.0`
- 不把 `latest` 作为生产固定标签

## 5. 服务职责

### 5.1 `frontend`

职责：

- 提供 Vue 构建后的静态文件

要求：

- 不承载业务逻辑
- 日志主要由 Nginx 入口层负责

### 5.2 `backend`

职责：

- Django API
- RSS
- 下载
- 后台接口
- XBT 同步
- Swagger UI

要求：

- 输出标准日志
- 依赖 `mysql` 和 `redis`

### 5.3 `mysql`

职责：

- 保存主站业务数据
- 保存 XBT 使用的数据表

要求：

- 使用持久化卷
- 做备份

### 5.4 `redis`

职责：

- 缓存
- 限流
- 后续异步任务基础

### 5.5 `xbt`

职责：

- 独立承担 announce / scrape

要求：

- 独立容器
- 连接同一个 `mysql`
- 输出标准日志

### 5.6 `nginx`

职责：

- 对外统一入口
- HTTPS
- 反向代理
- 静态资源与安全头

## 6. 网络与端口建议

建议至少使用一个内部网络：

- `app_net`

推荐访问关系：

- `nginx -> frontend`
- `nginx -> backend`
- `backend -> mysql`
- `backend -> redis`
- `backend -> xbt`（如有状态检查或内部联动）
- `xbt -> mysql`

端口原则：

- `frontend` 不直接暴露到公网
- `backend` 不直接暴露到公网
- `mysql` 不直接暴露到公网
- `redis` 不直接暴露到公网
- `nginx` 暴露 `80/443`
- `xbt` 暴露 tracker 所需端口

## 7. 数据卷建议

必须至少保留这些卷：

- `mysql_data`
- `redis_data`（可选，但建议保留）
- `torrent_storage`
- `nginx_logs`（如需要文件备份）

说明：

- 应用日志仍以 stdout/stderr 为主
- 卷主要用于数据库、数据文件和必要配置

## 8. 最小环境变量集合

目标：

- MVP 必填环境变量尽量控制在 `10` 个以内

推荐最小集合：

- `DJANGO_SECRET_KEY`
- `DJANGO_ALLOWED_HOSTS`
- `SITE_BASE_URL`
- `MYSQL_DATABASE`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_ROOT_PASSWORD`
- `XBT_TRACKER_PORT`

可选环境变量：

- `DJANGO_DEBUG=false`
- `LOG_LEVEL=INFO`

尽量不要额外暴露的变量：

- `MYSQL_HOST`
- `MYSQL_PORT`
- `REDIS_HOST`
- `REDIS_PORT`

原因：

- 在同一套 Compose 中，这些值可以直接写死为服务名和默认端口

## 9. Compose 文件原则

### 9.1 生产环境优先使用 `image`

生产环境：

- 使用 `image:`
- 不使用 `build:`

本地开发环境：

- 如有需要，单独提供 `docker-compose.dev.yml`

### 9.2 不把业务配置全塞进 Compose

Compose 中适合放：

- 镜像
- 端口
- 卷
- 网络
- 最少环境变量

不适合放：

- 复杂业务开关
- 大段应用配置
- 大量只在个别场景用的参数

## 10. XBT 配置挂载建议

建议：

- 使用单独配置文件挂载到 `xbt` 容器

例如：

- `deploy/xbt/xbt_tracker.conf`

配置要求：

- 关闭匿名 announce
- 关闭 auto register
- 数据库连接明确
- 端口明确

原则：

- XBT 的主要运行配置放配置文件
- 机密值可通过环境变量或模板注入

## 11. 日志要求

所有容器必须满足：

- 可通过 `docker logs <service>` 查看日志
- 可通过 `docker compose logs -f` 查看日志

重点检查：

- `backend`
- `xbt`
- `nginx`
- `mysql`
- `redis`

最低要求：

- 启动日志可见
- 错误日志可见
- 配置错误可见

## 12. 初始化流程

推荐初始化步骤：

1. 复制 `deploy/.env.example` 为 `deploy/.env`
2. 修改少量必要变量
3. 执行 `docker compose pull`
4. 执行 `docker compose up -d`
5. 执行数据库迁移
6. 创建管理员账户
7. 验证 `backend`、`xbt`、`nginx` 日志

## 13. 更新流程

推荐更新步骤：

1. GitHub Actions 完成新镜像构建
2. 服务器进入部署目录
3. 执行 `docker compose pull`
4. 执行 `docker compose up -d`
5. 查看日志
6. 验证首页、登录、下载、XBT announce

## 14. 回滚流程

推荐思路：

1. 将 Compose 中镜像 tag 切回旧版本
2. 执行 `docker compose pull`
3. 执行 `docker compose up -d`

要求：

- 使用明确 tag
- 不依赖 `latest` 做生产回滚

## 15. 健康检查建议

建议为以下服务增加健康检查：

- `backend`
- `mysql`
- `redis`

`xbt` 如健康检查不方便，至少保证：

- 端口监听正常
- 日志可见

## 16. MVP 验收标准

满足以下条件即可视为部署方案可用：

- `docker compose pull && docker compose up -d` 可拉起整套服务
- 必填环境变量数量受控
- 主站可正常访问
- Swagger UI 可访问
- XBT 可正常工作
- 所有关键容器日志可见
- 更新与回滚路径清楚

## 17. 当前结论

部署方案正式收敛为：

- 一套 `Docker Compose`
- 六个核心容器
- `frontend/backend/xbt` 使用 GHCR 镜像
- 生产环境不在服务器本地构建
- 少量环境变量 + 标准日志输出 + 明确更新流程

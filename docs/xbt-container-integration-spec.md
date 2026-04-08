# XBT 容器化与集成文档

## 1. 文档目标

这份文档专门定义：

- `XBT` 如何容器化
- `XBT` 如何在 `Docker Compose` 中部署
- `XBT` 与主站如何集成
- `XBT` 与 `MySQL` 如何连接
- `XBT` 日志如何输出
- `XBT` 镜像如何构建与更新

目标是让 `XBT` 既保持独立服务边界，又不把部署搞复杂。

整套 Compose 部署方式与环境变量策略，见：

- `docs/database-xbt-mapping-spec.md`
- `docs/docker-compose-deployment-spec.md`

## 2. 当前结论

当前推荐方案正式收敛为：

- `XBT` 独立一个容器
- 但仍纳入同一套 `Docker Compose`
- 不单独拆服务器
- 使用 `MySQL 8`
- 主站负责同步 `xbt_users` 和 `xbt_files`
- `XBT` 只负责 announce / scrape

一句话定义：

`XBT 单独一个容器部署，但仍属于同一套 Compose 编排。`

## 3. 为什么这样设计

这样设计的好处：

- `XBT` 和主站边界清楚
- Docker 编排仍然简单
- 部署步骤少
- 网络拓扑简单
- 数据库连接简单
- 日志和排障更方便

不建议 MVP 就做成：

- 单独一台机器部署 `XBT`
- 单独一套网络
- 单独一套数据库

原因：

- 环境变量会变多
- 防火墙和端口复杂度会上升
- 主站和 `XBT` 的联调成本更高
- 不符合当前“简单、易部署”的目标

## 4. Compose 中的服务定位

推荐生产环境容器如下：

- `frontend`
- `backend`
- `mysql`
- `redis`
- `xbt`
- `nginx`

这里 `xbt` 的定位是：

- 独立服务
- 独立镜像
- 独立容器
- 统一被 `docker compose` 编排

## 5. XBT 容器职责边界

`xbt` 容器只负责：

- `announce`
- `scrape`（如启用）
- 基于数据库中的白名单和用户信息做 Tracker 工作

`xbt` 容器不负责：

- 用户后台
- 资源后台
- RSS
- torrent 文件下载
- 页面渲染
- 管理界面

这些都由主站承担。

## 6. XBT 与主站的关系

主站负责：

- 生成用户 `passkey` / `torrent_pass`
- 资源发布
- 解析 torrent
- 生成 `infohash`
- 下载时注入 announce
- 同步 `xbt_users`
- 同步 `xbt_files`

`XBT` 负责：

- 接收下载器 announce 请求
- 校验用户是否允许
- 校验 torrent 是否在白名单
- 返回 peers

## 7. XBT 与 MySQL 的关系

推荐做法：

- `XBT` 与主站共享同一个 `MySQL 8` 实例

推荐原因：

- 部署简单
- 集成简单
- 数据同步路径短
- 对当前规模足够

注意：

- 共享同一个 MySQL 实例，不代表和主站完全共用所有表
- `XBT` 需要的表按其规范维护
- 主站自己的业务表继续由 Django 管理

## 8. 推荐网络拓扑

在同一套 `docker compose` 下，推荐：

- `backend` 与 `xbt` 在同一内部网络
- `mysql` 对 `backend` 与 `xbt` 可访问
- `xbt` 暴露给下载器需要的端口
- `backend` 不直接承担 tracker 流量

简化理解：

- 浏览器流量走 `nginx -> frontend/backend`
- 下载器 tracker 流量走 `xbt`

## 9. 推荐配置方式

### 9.1 总原则

- 尽量少环境变量
- 能用默认值就用默认值
- `xbt` 配置尽量集中在少量文件和少量 Compose 变量里

### 9.2 XBT 需要关注的最小配置

至少需要明确：

- `MySQL` 地址
- `MySQL` 用户名
- `MySQL` 密码
- `MySQL` 数据库名
- `listen` 端口
- `anonymous_announce = false`
- `auto_register = false`

说明：

- 关闭匿名 announce，确保只允许已登记用户
- 关闭自动注册，确保只追踪白名单 torrent

### 9.3 环境变量建议

建议控制为极少数：

- `XBT_DB_HOST`
- `XBT_DB_PORT`
- `XBT_DB_NAME`
- `XBT_DB_USER`
- `XBT_DB_PASSWORD`
- `XBT_TRACKER_PORT`

能在容器内固定的值，就不要再拆成额外环境变量。

## 10. XBT 镜像策略

### 10.1 当前建议

建议：

- `frontend`、`backend`、`xbt` 都拥有独立镜像

推荐镜像命名：

- `ghcr.io/<owner>/<repo>/frontend:<tag>`
- `ghcr.io/<owner>/<repo>/backend:<tag>`
- `ghcr.io/<owner>/<repo>/xbt:<tag>`

### 10.2 为什么 XBT 也建议独立镜像

原因：

- 版本边界清楚
- 更新和回滚方便
- 与主站镜像分离
- 更容易统一走 GitHub Actions 构建流程

### 10.3 推荐标签策略

- `latest`：开发或测试环境
- `main-<short_sha>`：主分支持续构建
- `v1.0.0`：正式发布版本

## 11. GitHub Actions 构建建议

推荐：

- 为 `xbt` 单独写一个镜像构建 job
- 推送到 `ghcr.io`

建议触发方式：

- push 到 `main`
- 手动 workflow dispatch
- release tag

推荐流程：

1. 拉取代码
2. 构建 `xbt` 镜像
3. 打 tag
4. 推送到 `ghcr.io`

## 12. Docker Compose 使用建议

### 12.1 生产环境

生产环境推荐：

- Compose 使用 `image`
- 不在服务器本地 `build`

推荐流程：

1. `docker compose pull`
2. `docker compose up -d`

### 12.2 本地开发环境

本地开发可选：

- 主站本地 `build`
- `xbt` 如不常改，可直接用已发布镜像

### 12.3 版本更新

推荐更新顺序：

1. 推送 GitHub
2. Actions 生成新镜像
3. 服务器 `docker compose pull`
4. 服务器 `docker compose up -d`
5. 检查日志与健康状态

## 13. XBT 日志输出要求

`XBT` 容器必须满足：

- 标准输出可见
- 可以通过 `docker logs xbt` 查看
- 可以通过 `docker compose logs -f xbt` 查看

必须至少可见的日志类型：

- 启动日志
- 配置加载失败
- 数据库连接失败
- 关键运行异常

如果 `XBT` 默认更倾向文件日志，建议：

- 在容器入口脚本中转发到 stdout/stderr

## 14. XBT 数据同步要求

主站必须同步到 `XBT` 的核心数据：

- 用户 `torrent_pass`
- 用户禁用状态
- 允许下载的 `infohash`

建议触发同步的时机：

- 创建用户
- 禁用/启用用户
- 重置 `passkey`
- 发布资源
- 隐藏资源
- 手动全量同步

## 15. 故障处理建议

常见故障方向：

- `xbt` 容器未启动
- `xbt` 端口未监听
- `xbt` 无法连接 MySQL
- 主站未成功同步 `xbt_users`
- 主站未成功同步 `xbt_files`
- 下载器使用了旧的 `passkey`

建议排查顺序：

1. 看 `xbt` 容器日志
2. 看 `backend` 同步日志
3. 看 MySQL 连接状态
4. 检查对应用户和 `infohash` 是否已写入 XBT 表

## 16. MVP 验收标准

满足以下条件即可视为 `XBT` 部署方案可用：

- `xbt` 能以独立容器运行
- `xbt` 被纳入同一套 `docker compose`
- 主站可同步用户与 torrent 白名单
- 下载器可通过 `XBT` announce 正常拿到 peers
- `xbt` 日志可通过 Docker 标准日志查看
- 更新时可通过 `docker compose pull && docker compose up -d` 完成

## 17. 当前结论

当前项目中，`XBT` 的最终推荐部署方式是：

- 单独一个容器
- 同一套 Compose 编排
- 同一套 MySQL 实例
- 主站负责同步
- 镜像可独立发布与更新

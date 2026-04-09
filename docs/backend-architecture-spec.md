# 后端架构设计文档

## 1. 文档目标

这份文档专门用于定义后端部分的：

- 技术栈与运行边界
- Django 项目结构
- 模块划分
- 认证与权限模型
- API 设计风格
- XBT 同步机制
- 文件与 torrent 处理
- 日志与错误处理
- 后端测试策略

目标是让后端开发时不再反复讨论：

- 应用应该怎么拆
- 哪些逻辑放 View，哪些放 Service
- 权限放在哪里校验
- XBT 怎么同步
- 日志怎么打

项目级“必须简单易用、低复杂度、低部署成本”的硬约束，见：

- `docs/simplicity-usability-operability-rules.md`

`XBT` 的容器化、Compose 编排、日志与镜像策略，见：

- `docs/database-xbt-mapping-spec.md`
- `docs/xbt-container-integration-spec.md`
- `docs/docker-compose-deployment-spec.md`

## 2. 当前技术结论

当前后端技术路线正式收敛为：

- 语言：`Python`
- Web 框架：`Django 5`
- API 框架：`Django REST Framework`
- API 文档：`drf-spectacular + Swagger UI`
- 数据库：`MySQL 8`
- 缓存：`Redis`
- Tracker：`XBT`
- 部署：`Docker Compose`

当前设计前提：

- 不自己写 Tracker
- 主站负责用户、资源、RSS、下载、后台、同步
- `XBT` 独立负责 announce / scrape
- 用户规模大约 `200` 人

## 3. 后端职责边界

主站后端负责：

- 登录、登出、当前用户信息
- `admin / uploader / user` 权限模型
- 用户管理
- 资源发布与维护
- RSS 输出
- 个性化 torrent 下载
- 下载日志
- XBT 用户与白名单同步
- 后台管理接口
- 审计日志
- OpenAPI Schema 与 Swagger UI

主站后端不负责：

- 自己实现 BitTorrent Tracker announce
- 自己实现 scrape
- 做种率、魔力值、考核
- 高精度上传下载量结算

## 4. Django 项目结构建议

建议后端按“项目层 + 业务应用层 + 公共基础层”拆分。

推荐结构：

```text
backend/
  manage.py
  config/
    __init__.py
    settings/
      __init__.py
      base.py
      local.py
      prod.py
    urls.py
    wsgi.py
    asgi.py
  apps/
    authx/
    users/
    releases/
    rss/
    downloads/
    tracker_sync/
    announcements/
    audit/
    api_docs/
    common/
  tests/
  requirements/
```

拆分原则：

- `config/` 只放项目级配置
- `apps/` 每个应用负责单一业务领域
- `common/` 放公共工具，不承载具体业务

## 5. 推荐应用模块划分

### 5.1 `authx`

职责：

- 登录
- 登出
- 修改密码
- 当前用户信息 `/auth/me`
- 会话相关逻辑

不要承载：

- 用户资料管理
- 用户后台管理

### 5.2 `users`

职责：

- 用户模型扩展
- 用户角色
- 用户状态
- 管理员创建用户
- 禁用/启用用户
- 重置 `passkey`

### 5.3 `releases`

职责：

- 资源模型
- 分类与标签
- 资源发布
- 资源编辑
- 资源隐藏
- 资源列表与详情
- torrent 基础信息解析

### 5.4 `rss`

职责：

- 全量 RSS
- 分类 RSS
- 标签 RSS
- RSS Token / passkey 校验

### 5.5 `downloads`

职责：

- 个性化 torrent 下载
- 下载日志记录
- 下载权限校验

### 5.6 `tracker_sync`

职责：

- `xbt_users` 同步
- `xbt_files` 白名单同步
- 禁用状态同步
- `passkey` / `torrent_pass` 联动
- 同步失败记录
- 手动与自动同步入口

### 5.7 `announcements`

职责：

- 站点公告
- 公告上下线

### 5.8 `audit`

职责：

- 审计日志记录
- 关键操作查询

### 5.9 `api_docs`

职责：

- OpenAPI Schema
- Swagger UI 页面

### 5.10 `common`

职责：

- 通用异常
- 分页基类
- 权限工具
- 日志工具
- 公共 mixin / serializer 基类

## 6. 数据模型与所有权建议

建议各应用负责的主要模型如下。

`users`：

- `User`
- `UserProfile`（如果需要扩展）

`releases`：

- `Category`
- `Tag`
- `Release`
- `ReleaseFile`

`downloads`：

- `DownloadLog`

`tracker_sync`：

- `TrackerSyncLog`
- `TrackerSyncTask`（如需持久化任务状态）

`announcements`：

- `Announcement`

`audit`：

- `AuditLog`

说明：

- 不建议一开始就把所有表都塞进一个 app
- Django app 应与业务边界一致，而不是按技术类型乱拆

## 7. 认证设计

## 7.1 首选方案

首选：

- `Django Session Authentication`

原因：

- 站点本身是内部系统
- 有前台和后台
- 浏览器使用为主
- Django 对 Session 支持最成熟

### 7.2 API 配合方式

建议：

- 前端登录后拿 Session Cookie
- 应用启动时请求 `/auth/me`
- 前端根据返回结果决定菜单和权限

### 7.3 可选增强

二期可选：

- 为内部脚本补充 Token 认证
- 为自动化工具补充 API Key

MVP 不建议：

- 一开始就把 Session、JWT、API Key 全都做上

## 8. 权限设计

### 8.1 角色

固定 3 类角色：

- `admin`
- `uploader`
- `user`

### 8.2 权限校验层级

后端权限必须至少做 3 层：

- 路由级
- 视图级
- 对象级

### 8.3 典型权限规则

`user`：

- 可查看资源
- 可下载资源
- 可访问 RSS
- 不可上传
- 不可访问后台

`uploader`：

- 拥有 `user` 全部权限
- 可上传资源
- 可编辑自己发布的资源
- 不可访问后台
- 不可编辑他人资源

`admin`：

- 可访问全部业务
- 可管理用户
- 可管理分类标签
- 可管理公告
- 可触发 XBT 同步

### 8.4 实现建议

建议用 DRF Permission Classes + Service 层检查组合实现。

例如：

- `IsAuthenticated`
- `IsAdminUser`
- `IsUploaderOrAdmin`
- `IsReleaseOwnerOrAdmin`

原则：

- 角色权限放 Permission Class
- 对象归属权限放对象级判断
- 不要把全部权限逻辑散落在 Serializer 和 View 里

## 9. API 设计风格

### 9.1 总体原则

- URL 简洁稳定
- REST 风格优先
- 特殊动作使用 action 接口
- 返回格式统一

### 9.2 建议接口分组

当前实现状态（截至 `2026-04-09`）：

- 以下分组中的核心接口均已在当前仓库落地
- 主站业务接口统一挂在 `/api` 前缀下；RSS Feed 使用 `/rss` 前缀

`auth`

- [x] `/auth/login`
- [x] `/auth/logout`
- [x] `/auth/change-password`
- [x] `/auth/me`

`releases`

- [x] `/releases`
- [x] `/releases/{id}`
- [x] `/releases/{id}/download`

`rss`

- [x] `/rss/all`
- [x] `/rss/category/{slug}`
- [x] `/rss/tag/{slug}`

`admin-users`

- [x] `/admin/users`
- [x] `/admin/users/{id}`
- [x] `/admin/users/{id}/disable`
- [x] `/admin/users/{id}/reset-passkey`

`tracker-sync`

- [x] `/admin/tracker-sync/overview`
- [x] `/admin/tracker-sync/logs`
- [x] `/admin/tracker-sync/users/{id}`
- [x] `/admin/tracker-sync/releases/{id}`
- [x] `/admin/tracker-sync/full`
- [x] `/admin/tracker-sync/logs/{id}/retry`

### 9.3 返回格式建议

建议 API 响应尽量统一。

成功响应：

```json
{
  "success": true,
  "data": {},
  "message": "ok"
}
```

错误响应：

```json
{
  "success": false,
  "code": "permission_denied",
  "message": "You do not have permission to perform this action."
}
```

### 9.4 分页建议

列表接口建议统一分页格式。

```json
{
  "count": 120,
  "next": null,
  "previous": null,
  "results": []
}
```

## 10. Service 层设计

建议不要把所有业务都堆在 ViewSet 里。

推荐分层：

- `View / ViewSet`: 接参数、鉴权、调 Service、返回响应
- `Serializer`: 输入输出校验与序列化
- `Service`: 承担核心业务逻辑
- `Repository / ORM`: 直接读写数据库

推荐 Service：

- `UserService`
- `ReleaseService`
- `RssService`
- `TorrentService`
- `DownloadService`
- `TrackerSyncService`
- `AuditService`

适合放进 Service 的逻辑：

- 发布资源时解析 torrent
- 下载时注入 announce/passkey
- 用户禁用后同步 XBT
- 重置 `passkey` 后失效旧访问凭证

不建议放进 View 的逻辑：

- 多表事务处理
- 多步骤同步
- 审计写入
- XBT 同步重试

## 11. torrent 与下载处理

### 11.1 基础策略

建议保存“基础 torrent 模板”，下载时动态注入 announce 地址。

流程：

1. 上传者上传 `.torrent`
2. 服务端解析并校验
3. 保存原始模板
4. 用户点击下载
5. 服务端生成带个人 `passkey` 的 torrent
6. 写下载日志
7. 返回文件

### 11.2 校验内容

上传时建议校验：

- 是否是合法 torrent
- 是否包含 `private=1`
- `infohash` 是否重复
- 文件列表是否可解析

### 11.3 下载安全

下载接口必须检查：

- 是否登录
- 用户是否禁用
- 资源是否存在
- 资源是否允许下载

## 12. RSS 设计

### 12.1 输出方式

建议使用 DRF + Django 原生 Response 或 XML 输出工具。

### 12.2 访问控制

支持：

- token
- passkey

建议首期：

- 优先 passkey 或专门 RSS token

### 12.3 风险控制

- 访问频率限制
- 用户禁用后立即失效
- 不在日志中打印完整 token

## 13. XBT 集成设计

### 13.1 集成目标

主站需要把以下信息与 `XBT` 对齐：

- 用户 `torrent_pass`
- 用户禁用状态
- 允许下载的 torrent / `infohash`

### 13.2 推荐方式

首选建议：

- 主站直接写 `XBT` 所使用的 `MySQL` 表

原因：

- 系统规模不大
- 架构简单
- 运维最省事

### 13.3 推荐同步场景

这些动作发生时应触发同步：

- 新建用户
- 禁用/启用用户
- 重置 `passkey`
- 发布资源
- 隐藏资源
- 手动全量同步

### 13.4 同步策略

建议同时提供：

- 保存后同步
- 后台手动重试
- 全量补偿同步

### 13.5 失败处理

同步失败时：

- 记录错误日志
- 记录同步失败表
- 后台可重试

### 13.6 审计要求

以下动作建议都写审计日志：

- 管理员重置 `passkey`
- 管理员禁用用户
- 发布资源后同步到 XBT
- 手动触发全量同步

## 14. API 文档设计

建议：

- `/api/schema/`
- `/api/swagger/`

Swagger UI 应覆盖：

- 登录相关
- 当前用户
- 资源列表
- 上传
- 下载
- RSS
- 用户管理
- XBT 同步

要求：

- 每个接口都要有清晰 summary
- 上传接口要标明 `multipart/form-data`
- 角色权限要在接口说明中体现

## 15. 日志与错误处理

### 15.1 基本要求

后端容器必须把日志输出到标准输出。

必须至少输出：

- 服务启动日志
- 请求异常日志
- 认证失败日志
- 上传失败日志
- 下载失败日志
- XBT 同步失败日志

### 15.2 日志级别

建议至少支持：

- `DEBUG`
- `INFO`
- `WARNING`
- `ERROR`

### 15.3 错误处理建议

统一错误处理：

- 参数校验错误
- 未登录
- 无权限
- 资源不存在
- 第三方依赖异常

建议：

- 对外返回统一错误格式
- 对内打印完整错误日志

## 16. 缓存与异步任务

### 16.1 Redis 用途

建议用于：

- Session 相关缓存
- 限流
- 短期热点缓存
- 后续异步任务队列

### 16.2 异步任务

MVP 可以先不强依赖任务队列。

但这些动作适合后续异步化：

- 全量 XBT 同步
- 批量重试同步
- 资源统计聚合

如果需要队列，推荐：

- `Celery + Redis`

## 17. 测试策略

建议至少覆盖：

- 登录/登出
- `/auth/me`
- 角色权限
- 上传资源
- torrent 校验
- 下载种子
- RSS 输出
- 用户禁用
- `passkey` 重置
- XBT 同步

测试层次建议：

- 单元测试：Service 和权限工具
- 接口测试：DRF API
- 集成测试：与 `MySQL` / `Redis` / XBT 表同步

## 18. 推荐后端目录细化

```text
backend/
  apps/
    authx/
      api/
      services/
      tests/
    users/
      api/
      services/
      tests/
    releases/
      api/
      services/
      tests/
    downloads/
      api/
      services/
      tests/
    rss/
      api/
      services/
      tests/
    tracker_sync/
      api/
      services/
      tests/
    common/
      permissions/
      exceptions/
      logging/
      utils/
```

## 19. 推荐实现顺序

### 阶段 1

- Django 项目初始化
- 用户模型与角色
- 登录/登出
- `/auth/me`
- Swagger UI

### 阶段 2

- 分类/标签
- 资源列表/详情
- 上传与 torrent 解析
- 下载日志

### 阶段 3

- RSS
- 用户管理
- 公告管理
- 审计日志

### 阶段 4

- XBT 同步
- `passkey` 重置联动
- 手动全量同步
- 同步失败重试

### 阶段 5

- 日志加固
- 错误处理加固
- 限流
- 备份与运维完善

### 当前进度（截至 `2026-04-09`）

- [x] 阶段 1：Django 项目初始化、用户模型与角色、登录/登出、`/auth/me`、Swagger UI
- [x] 阶段 2：分类/标签、资源列表/详情、上传与 torrent 解析、下载日志
- [x] 阶段 3：RSS、用户管理、公告管理、审计日志
- [x] 阶段 4：XBT 同步、`passkey` 重置联动、手动全量同步、失败日志与手动重试入口、同步概览接口
- [x] 阶段 5（已完成部分）：日志加固、错误处理加固、登录 / RSS / 下载限流、Swagger / OpenAPI 契约校验
- [ ] 阶段 5（剩余部分）：备份、部署侧日志补强与运维完善

## 20. 后端验收标准

- 登录、登出、当前用户接口可用
- 三角色权限可正确工作
- 上传资源后可生成可下载条目
- 下载时可返回个性化 torrent
- RSS 输出正常
- 用户禁用后下载与 RSS 失效
- XBT 同步可用
- Swagger UI 可展示全部核心接口
- 后端容器日志可通过 Docker 标准日志查看

## 21. 当前结论

后端实现建议正式收敛为：

- `Django + DRF` 作为主站后端
- `MySQL 8` 作为主数据库
- `Redis` 做缓存和后续队列基础
- `XBT` 作为独立 Tracker
- 主站负责“用户/资源/RSS/下载/XBT 同步/后台/API 文档”

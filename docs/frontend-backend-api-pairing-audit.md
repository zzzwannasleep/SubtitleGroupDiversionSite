# 前后端 API 配对审计

更新时间：2026-04-09

## 1. 结论

当前项目本轮已把审计中列出的主要前端缺口补齐。

当前状态更准确地说是：

- **SPA 页面层面的阻塞 API 已完成配对**
- **已可以开始关闭“默认 mock 优先”策略，进入真实 API 联调阶段**

已经基本配上的核心主链路有：

- 登录 / 登出 / 当前用户
- 资源列表 / 详情 / 上传 / 编辑 / 下载
- 分类 / 标签 / 公告
- RSS 总览页
- 我的账户 / 我的下载 / `API Token`
- 后台仪表盘 / 用户列表 / 用户详情编辑 / 单用户 XBT 同步
- 后台资源列表 / 资源级 XBT 同步详情
- 后台 XBT 同步总览 / 失败日志 / 按日志重试
- 后台分类 / 标签 / 公告 / 设置

仍待收口的部分，主要集中在：

- 真实 `Django/DRF` API 联调验证
- 联调中发现的问题修正与回归验证

## 2. 审计边界

本次审计按“`Vue SPA` 是否已经真正接上 `Django/DRF` 接口”来判断。

不直接算作“前端未配对缺陷”的内容有两类：

- 主要供 RSS 客户端 / 下载器直接访问的接口
- 主要供 Swagger / Schema / ReDoc 使用的文档接口

本次审计当前结论调整为：

- **阻塞项已补齐，可以开始默认使用真实 API 进行联调**
- 如联调过程中需要临时回退，仍可保留显式 `mock` 开关作为兜底

## 3. 本轮已补齐的阻塞 API

这一组在上一版审计中属于 `P0 / P1`。截至本次更新，前端已全部补齐。

| API | 后端状态 | 前端状态 | 问题说明 |
|---|---|---|---|
| `GET /api/me/api-token/` | 已实现 | 已接入 | “我的账户”页已提供 API Token 展示入口 |
| `POST /api/me/api-token/` | 已实现 | 已接入 | “我的账户”页已提供 API Token 重置交互 |
| `PUT /api/admin/users/{id}/` | 已实现 | 已接入 | 管理端用户详情页已支持完整更新用户基础信息 |
| `PATCH /api/admin/users/{id}/` | 已实现 | 已接入 | 管理端用户详情页已支持局部更新用户基础信息 |
| `GET /api/admin/tracker-sync/overview/` | 已实现 | 已接入 | 后台 XBT 页面已展示总览、失败统计与失败日志 |
| `GET /api/admin/tracker-sync/users/{id}/` | 已实现 | 已接入 | 管理员已可查看单用户 XBT 同步详情 |
| `POST /api/admin/tracker-sync/users/{id}/` | 已实现 | 已接入 | 管理员已可从用户详情页手动触发该用户同步 |
| `POST /api/admin/tracker-sync/logs/{id}/retry/` | 已实现 | 已接入 | 后台 XBT 页面已支持按失败日志重试 |
| `GET /api/admin/tracker-sync/releases/{id}/` | 已实现 | 已接入 | 后台资源列表已提供资源级 XBT 同步详情入口 |
| `POST /api/admin/tracker-sync/releases/{id}/` | 已实现 | 已接入 | 管理员已可对单个资源手动触发同步 |

## 4. 本轮已补齐的完整消费项

这部分在上一版审计中属于“接口已接，但前端没有消费完整输出”。截至本次更新，闭环已补齐。

| API | 当前接入情况 | 未消费内容 | 影响 |
|---|---|---|---|
| `GET /api/admin/tracker-sync/logs/` | 前端已消费完整输出 | 无 | 页面已支持根据日志跳转到用户/资源，并支持按日志重试 |
| `GET /api/admin/users/{id}/` | 前端已消费完整输出 | 无 | 页面已形成“查看详情 + 编辑资料 + 手动同步”的闭环 |

## 5. 已实现但当前不作为收口条件的兼容接口

项目仍处于试验阶段、尚未正式投入使用，因此这类兼容接口当前**不作为前后端收口条件**。
后端可以保留，前端不需要额外补接。

| API | 说明 | 当前前端替代路径 |
|---|---|---|
| `POST /api/admin/users/{id}/disable/` | 显式禁用兼容接口 | 前端使用 `POST /api/admin/users/{id}/status/` |
| `POST /api/admin/users/{id}/enable/` | 显式启用兼容接口 | 前端使用 `POST /api/admin/users/{id}/status/` |
| `POST /api/releases/{id}/hide/` | 旧版隐藏兼容接口 | 前端使用 `POST /api/releases/{id}/visibility/` |

## 6. 不纳入 SPA 未配对缺陷的接口

这类接口不是给 `Vue SPA` 页面直接消费的，不能简单算成“前端没接”。

| API | 原因 |
|---|---|
| `GET /rss/all`、`GET /rss/category/{slug}`、`GET /rss/tag/{slug}`、`GET /rss/{token}/all`、`GET /rss/{token}/category/{slug}`、`GET /rss/{token}/tag/{slug}` | RSS Feed 主要供下载器 / RSS 客户端直接访问，前端页面通过 `/api/rss/overview/` 暴露这些地址 |
| `GET /api/schema/`、`GET /api/swagger/`、`GET /api/docs/` | 文档 / 调试接口，不属于业务页面直连范围 |

## 7. 与默认 Mock 相关的当前判断

当前前端仍然保留 `mock` 回退逻辑，但默认策略已经可以切换为真实 API 联调。在这种状态下：

- 第 3 节中原本的阻塞 API 已补齐
- 现在可以把默认数据源切到 `api`
- 下一步应立即做一轮真实 API 联调
- 如联调中遇到阻塞，可临时使用显式 `mock` 开关回退

## 8. 建议的收口顺序

原建议顺序中的前端补齐项已完成。当前建议收口为：

1. 把默认数据源切到真实 `api`
2. 做一轮真实 `Django/DRF` API 联调
3. 修复联调中发现的权限、字段、状态流转或错误处理问题
4. 完成回归验证后，再决定是否删除前端 `mock` 兜底代码

## 9. 本次审计依据

- 已对 `frontend/src/services`、`frontend/src/views` 与 `backend/apps/*/urls.py`、`views.py` 做逐项核对
- `frontend` 在本轮补齐后再次执行 `npm run build` 通过
- `backend` 执行 `python manage.py test` 通过，`43/43` 全部通过

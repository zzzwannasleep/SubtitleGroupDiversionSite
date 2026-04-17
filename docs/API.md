# Subtitle Group Diversion Site API

本文件面向“其他项目接入当前站点后端 API”的场景，内容基于当前代码和 OpenAPI schema 整理，版本对应 `0.1.0`。

本文档只覆盖当前推荐使用的接口，不包含已经从 Swagger / ReDoc 中隐藏的兼容旧接口。

## 1. 基础信息

| 项目 | 说明 |
| --- | --- |
| 站点基地址 | `https://your-domain.example` |
| 业务 API 前缀 | `/api` |
| RSS 前缀 | `/rss` |
| OpenAPI Schema | `GET /api/schema/` |
| Swagger UI | `GET /api/swagger/` |
| ReDoc | `GET /api/docs/` |
| 响应编码 | `application/json; charset=utf-8` |
| 时间格式 | ISO 8601，例如 `2026-04-17T22:03:43+08:00` |

建议外部项目优先把本文档当作人工接入手册，同时保留对 `/api/schema/` 的机器读取能力。

## 2. 认证与权限

### 2.1 支持的认证方式

| 方式 | 说明 | 适用场景 |
| --- | --- | --- |
| Session Cookie | 登录成功后由服务端写入 `sessionid` Cookie | 浏览器、同域前端 |
| `Authorization: Token <api_token>` | 用户 API Token 认证 | 服务对服务调用 |
| `Authorization: Bearer <api_token>` | 与上面等价 | 服务对服务调用 |
| `X-API-Key: <api_token>` | 与上面等价 | 不方便改 `Authorization` 的客户端 |

### 2.2 角色与访问控制

| 角色 | 值 | 说明 |
| --- | --- | --- |
| 管理员 | `admin` | 可访问全部后台接口 |
| 上传者 | `uploader` | 可创建资源；可编辑自己发布的资源 |
| 普通用户 | `user` | 可访问前台和个人相关接口 |

| 用户状态 | 值 | 说明 |
| --- | --- | --- |
| 正常 | `active` | 可正常访问需登录接口 |
| 禁用 | `disabled` | 会被拒绝访问需登录接口 |

### 2.3 当前对外公开的匿名接口

以下接口不要求登录：

- `POST /api/auth/login/`
- `POST /api/auth/register/`
- `GET /api/site-settings/`
- `GET /api/releases/{release_id}/download/`
- `GET /api/rss/overview/`
- `GET /rss/all`
- `GET /rss/category/{slug}`
- `GET /rss/tag/{slug}`

除上面这些接口外，其余 `/api/*` 接口默认都要求“已登录且状态为 `active`”。

## 3. 通用响应格式

### 3.1 成功响应

```json
{
  "success": true,
  "data": {},
  "message": "ok"
}
```

### 3.2 分页响应

只有资源列表类接口使用分页，分页参数为 `page` 与 `pageSize`。

```json
{
  "success": true,
  "data": {
    "count": 125,
    "next": "https://your-domain.example/api/releases/?page=2&pageSize=10",
    "previous": null,
    "page": 1,
    "pageSize": 10,
    "results": []
  },
  "message": "ok"
}
```

### 3.3 失败响应

```json
{
  "success": false,
  "code": "validation_error",
  "message": "参数校验失败。",
  "errors": {
    "password": [
      "密码不能为空。"
    ]
  }
}
```

### 3.4 常见错误码

| code | 说明 |
| --- | --- |
| `validation_error` | 参数校验失败 |
| `throttled` | 被限流 |
| `authentication_failed` | 用户名、密码或 Token 不正确 |
| `not_authenticated` | 未登录 |
| `permission_denied` | 已登录但无权限 |
| `data_conflict` | 数据已存在或状态冲突 |
| `business_error` | 业务规则不满足 |
| `server_error` | 服务端内部错误 |

### 3.5 限流

| 范围 | 频率 |
| --- | --- |
| 登录 / 注册 | `10/minute` |
| RSS | `120/hour` |
| torrent 下载 | `240/hour` |

## 4. 枚举值

### 4.1 资源状态

| 值 | 说明 |
| --- | --- |
| `draft` | 草稿 |
| `published` | 已发布 |
| `hidden` | 已隐藏 |

### 4.2 公告状态

| 值 | 说明 |
| --- | --- |
| `online` | 上线 |
| `draft` | 草稿 |
| `offline` | 下线 |

### 4.3 公告可见范围

| 值 | 说明 |
| --- | --- |
| `all` | 全部用户 |
| `uploader` | 上传者与管理员 |
| `admin` | 仅管理员 |

### 4.4 主题模式

| 值 | 说明 |
| --- | --- |
| `system` | 跟随系统 |
| `light` | 浅色 |
| `dark` | 深色 |

### 4.5 登录页背景模式

| 值 | 说明 |
| --- | --- |
| `api` | 从外部图片地址加载 |
| `file` | 使用上传文件 |
| `css` | 使用 CSS 背景值 |

## 5. 接口总览

## 5.1 Auth

| 方法 | 路径 | 鉴权 | 说明 | 请求体 | `data` |
| --- | --- | --- | --- | --- | --- |
| `POST` | `/api/auth/login/` | 匿名 | 登录并建立 Session | `LoginRequest` | `CurrentUser` |
| `POST` | `/api/auth/register/` | 匿名 | 注册普通用户 | `RegisterRequest` | `CurrentUser` |
| `POST` | `/api/auth/logout/` | 已登录 | 退出登录 | 无 | `null` |
| `GET` | `/api/auth/me/` | 已登录 | 获取当前登录用户 | 无 | `CurrentUser` |
| `POST` | `/api/auth/change-password/` | 已登录 | 修改密码 | `ChangePasswordRequest` | `null` |

## 5.2 Site

| 方法 | 路径 | 鉴权 | 说明 | 请求体 | `data` |
| --- | --- | --- | --- | --- | --- |
| `GET` | `/api/site-settings/` | 匿名 | 获取公开站点设置 | 无 | `SiteSettingRead` |
| `GET` | `/api/announcements/visible/` | 已登录 | 获取当前用户可见公告 | 无 | `Announcement[]` |

## 5.3 Releases

| 方法 | 路径 | 鉴权 | 说明 | 请求体 | `data` |
| --- | --- | --- | --- | --- | --- |
| `GET` | `/api/categories/` | 已登录 | 获取分类列表 | 无 | `Category[]` |
| `GET` | `/api/tags/` | 已登录 | 获取标签列表 | 无 | `Tag[]` |
| `GET` | `/api/releases/` | 已登录 | 获取已发布资源分页列表 | 无 | `Paginated<Release>` |
| `POST` | `/api/releases/` | `admin` / `uploader` | 创建资源 | `ReleaseWriteRequest` | `Release` |
| `GET` | `/api/releases/{release_id}/` | 已登录 | 获取资源详情 | 无 | `Release` |
| `PUT` | `/api/releases/{release_id}/` | `admin` 或资源所有者 | 全量更新资源 | `ReleaseWriteRequest` | `Release` |
| `PATCH` | `/api/releases/{release_id}/` | `admin` 或资源所有者 | 部分更新资源 | `ReleaseWriteRequest` | `Release` |
| `GET` | `/api/me/releases/` | 已登录 | 获取我的发布 | 无 | `Release[]` |

`GET /api/releases/` 查询参数：

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `q` | string | 资源关键字，匹配标题 / 副标题 / 描述 |
| `category` | string | 分类 slug |
| `tag` | string | 标签 slug |
| `sort` | string | `latest` / `downloads` / `completions` |
| `page` | int | 页码，从 1 开始 |
| `pageSize` | int | 每页数量，默认 10，最大 100 |

说明：

- 普通列表只返回 `published` 资源。
- 资源详情接口对 `hidden` / `draft` 资源做权限控制，仅管理员或资源所有者可见。
- 创建资源时必须上传 `torrentFile`。
- 更新资源时 `torrentFile` 可选；如果重新上传，会重建文件列表与 `infohash`。

## 5.4 Downloads

| 方法 | 路径 | 鉴权 | 说明 | 请求体 | 返回 |
| --- | --- | --- | --- | --- | --- |
| `GET` | `/api/releases/{release_id}/download/` | 匿名可用 | 下载 `.torrent` 文件 | 无 | `application/x-bittorrent` 二进制 |
| `GET` | `/api/me/downloads/` | 已登录 | 获取当前用户下载记录 | 无 | `DownloadLog[]` |

说明：

- 下载接口仅允许下载 `published` 资源。
- 已登录用户会按用户维度记录下载日志；匿名访问会按 IP 记录。

## 5.5 RSS

| 方法 | 路径 | 鉴权 | 说明 | 返回 |
| --- | --- | --- | --- | --- |
| `GET` | `/api/rss/overview/` | 匿名 | 获取 RSS 概览与入口地址 | `RssOverviewData` |
| `GET` | `/rss/all` | 匿名 | 全站已发布资源 RSS | `application/rss+xml` |
| `GET` | `/rss/category/{slug}` | 匿名 | 指定分类 RSS | `application/rss+xml` |
| `GET` | `/rss/tag/{slug}` | 匿名 | 指定标签 RSS | `application/rss+xml` |

建议外部项目优先读取 `/api/rss/overview/`，而不是手工拼接 RSS 地址。

## 5.6 Profile

| 方法 | 路径 | 鉴权 | 说明 | 请求体 | `data` |
| --- | --- | --- | --- | --- | --- |
| `GET` | `/api/me/theme/` | 已登录 | 获取当前用户主题设置 | 无 | `SelfTheme` |
| `PUT` | `/api/me/theme/` | 已登录 | 更新当前用户主题设置 | `SelfThemeRequest` | `SelfTheme` |
| `GET` | `/api/me/api-token/` | 已登录 | 获取当前用户 API Token | 无 | `SelfApiToken` |
| `POST` | `/api/me/api-token/` | 已登录 | 重置当前用户 API Token | 无 | `SelfApiToken` |

## 5.7 Admin Dashboard

| 方法 | 路径 | 鉴权 | 说明 | `data` |
| --- | --- | --- | --- | --- |
| `GET` | `/api/admin/dashboard/` | `admin` | 获取后台仪表盘概览 | `AdminDashboardData` |

## 5.8 Admin Users

| 方法 | 路径 | 鉴权 | 说明 | 请求体 | `data` |
| --- | --- | --- | --- | --- | --- |
| `GET` | `/api/admin/users/` | `admin` | 获取用户列表 | 无 | `AdminUser[]` |
| `POST` | `/api/admin/users/` | `admin` | 创建用户 | `CreateUserRequest` | `AdminUserCreate` |
| `GET` | `/api/admin/users/{user_id}/` | `admin` | 获取用户详情 | 无 | `AdminUser` |
| `PUT` | `/api/admin/users/{user_id}/` | `admin` | 更新用户基础信息 | `UpdateUserRequest` | `AdminUser` |
| `PATCH` | `/api/admin/users/{user_id}/` | `admin` | 部分更新用户基础信息 | `UpdateUserRequest` | `AdminUser` |
| `POST` | `/api/admin/users/{user_id}/status/` | `admin` | 更新用户状态 | `ChangeUserStatusRequest` | `AdminUser` |

`GET /api/admin/users/` 查询参数：

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `q` | string | 搜索用户名、显示名、邮箱、角色 |
| `role` | string | `admin` / `uploader` / `user` |
| `status` | string | `active` / `disabled` |

## 5.9 Admin Invite Codes

| 方法 | 路径 | 鉴权 | 说明 | 请求体 | `data` |
| --- | --- | --- | --- | --- | --- |
| `GET` | `/api/admin/invite-codes/` | `admin` | 获取邀请码列表 | 无 | `InviteCode[]` |
| `POST` | `/api/admin/invite-codes/` | `admin` | 批量生成邀请码 | `CreateInviteCodesRequest` | `InviteCode[]` |
| `POST` | `/api/admin/invite-codes/{invite_code_id}/revoke/` | `admin` | 停用邀请码 | 无 | `InviteCode` |

## 5.10 Admin Releases

| 方法 | 路径 | 鉴权 | 说明 | 请求体 | `data` |
| --- | --- | --- | --- | --- | --- |
| `GET` | `/api/admin/releases/` | `admin` | 获取后台资源列表 | 无 | `Paginated<Release>` |
| `POST` | `/api/releases/{release_id}/visibility/` | `admin` | 切换资源为发布或隐藏 | `ReleaseVisibilityRequest` | `Release` |

`GET /api/admin/releases/` 查询参数：

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `status` | string | `all` / `draft` / `published` / `hidden` |
| `page` | int | 页码 |
| `pageSize` | int | 每页数量 |

## 5.11 Admin Taxonomy

| 方法 | 路径 | 鉴权 | 说明 | 请求体 | `data` |
| --- | --- | --- | --- | --- | --- |
| `GET` | `/api/admin/categories/` | `admin` | 获取后台分类列表 | 无 | `Category[]` |
| `POST` | `/api/admin/categories/` | `admin` | 创建或更新分类 | `CategorySaveRequest` | `Category` |
| `GET` | `/api/admin/tags/` | `admin` | 获取后台标签列表 | 无 | `Tag[]` |
| `POST` | `/api/admin/tags/` | `admin` | 创建或更新标签 | `TagSaveRequest` | `Tag` |

说明：

- `POST /api/admin/categories/` 与 `POST /api/admin/tags/` 都是“保存”语义。
- 当请求体带 `id` 时更新对应对象；不带 `id` 时创建。

## 5.12 Admin Site

| 方法 | 路径 | 鉴权 | 说明 | 请求体 | `data` |
| --- | --- | --- | --- | --- | --- |
| `GET` | `/api/admin/announcements/` | `admin` | 获取后台公告列表 | 无 | `Announcement[]` |
| `POST` | `/api/admin/announcements/` | `admin` | 创建或更新公告 | `AnnouncementSaveRequest` | `Announcement` |
| `GET` | `/api/admin/settings/` | `admin` | 获取站点设置 | 无 | `SiteSettingRead` |
| `PUT` | `/api/admin/settings/` | `admin` | 更新站点设置 | `SiteSettingWriteRequest` | `SiteSettingRead` |

说明：

- `POST /api/admin/announcements/` 带 `id` 为更新，不带 `id` 为创建。
- 更新站点设置时，若涉及文件上传，推荐使用 `multipart/form-data`。

## 5.13 Admin Audit

| 方法 | 路径 | 鉴权 | 说明 | 请求体 | `data` |
| --- | --- | --- | --- | --- | --- |
| `GET` | `/api/admin/audit-logs/` | `admin` | 获取审计日志 | 无 | `AuditLog[]` |

`GET /api/admin/audit-logs/` 查询参数：

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `q` | string | 搜索操作人、动作、对象类型、对象名称、详情 |
| `targetType` | string | 按对象类型筛选 |
| `limit` | int | 默认 100，最大 200 |

## 6. 请求模型

## 6.1 LoginRequest

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `username` | string | 是 | 用户名 |
| `password` | string | 是 | 密码 |

## 6.2 RegisterRequest

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `username` | string | 是 | 用户名，最大 150 字符 |
| `displayName` | string | 是 | 显示名称，最大 100 字符 |
| `email` | string | 是 | 邮箱 |
| `password` | string | 是 | 密码 |
| `confirmPassword` | string | 是 | 二次确认密码 |
| `inviteCode` | string | 否 | 当站点关闭公开注册时必填 |

## 6.3 ChangePasswordRequest

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `currentPassword` | string | 是 | 当前密码 |
| `nextPassword` | string | 是 | 新密码，至少 8 位 |

## 6.4 ReleaseWriteRequest

推荐使用 `multipart/form-data`。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `title` | string | 否 | 资源标题；创建时可留空，后端会自动推断 |
| `subtitle` | string | 否 | 副标题 |
| `description` | string | 否 | 描述 |
| `categorySlug` | string | 否 | 分类 slug；创建时可省略，后端会取第一个启用分类 |
| `tagSlugs` | string[] | 否 | 标签 slug 数组 |
| `torrentFile` | file | 创建时是 | `.torrent` 文件 |
| `status` | string | 否 | `draft` / `published` / `hidden` |

说明：

- 创建资源时，如果 `title` 为空，会按 `metadata.name` 或文件名自动生成。
- 同一 `infohash` 不允许重复发布。

## 6.5 ReleaseVisibilityRequest

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `status` | string | 是 | `published` 或 `hidden` |

## 6.6 SelfThemeRequest

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `mode` | string | 是 | `system` / `light` / `dark` |
| `customCss` | string | 否 | 自定义主题 CSS |

## 6.7 CreateUserRequest

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `username` | string | 是 | 用户名 |
| `displayName` | string | 是 | 显示名 |
| `email` | string | 是 | 邮箱 |
| `role` | string | 是 | `admin` / `uploader` / `user` |
| `password` | string | 否 | 不传时，后端可生成初始密码并在响应返回 |

## 6.8 UpdateUserRequest

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `displayName` | string | 否 | 显示名 |
| `email` | string | 否 | 邮箱 |
| `role` | string | 否 | `admin` / `uploader` / `user` |

至少传一个字段。

## 6.9 ChangeUserStatusRequest

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `nextStatus` | string | 是 | `active` / `disabled` |

## 6.10 CreateInviteCodesRequest

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `count` | int | 否 | 生成数量，默认 1，范围 1 到 20 |
| `note` | string | 否 | 备注 |
| `expiresAt` | string | 否 | 过期时间，ISO 8601，可为 `null` |

## 6.11 CategorySaveRequest

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | int | 否 | 带 `id` 为更新，不带为创建 |
| `name` | string | 是 | 分类名称 |
| `slug` | string | 是 | 分类 slug |
| `sortOrder` | int | 否 | 排序值，默认由后端处理 |
| `isActive` | bool | 否 | 是否启用 |

## 6.12 TagSaveRequest

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | int | 否 | 带 `id` 为更新，不带为创建 |
| `name` | string | 是 | 标签名称 |
| `slug` | string | 是 | 标签 slug |

## 6.13 AnnouncementSaveRequest

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | int | 否 | 带 `id` 为更新，不带为创建 |
| `title` | string | 是 | 公告标题 |
| `content` | string | 是 | 公告正文 |
| `status` | string | 是 | `online` / `draft` / `offline` |
| `audience` | string | 是 | `all` / `uploader` / `admin` |

## 6.14 SiteSettingWriteRequest

推荐使用 `multipart/form-data`。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `siteName` | string | 否 | 站点名称 |
| `siteDescription` | string | 否 | 站点描述 |
| `loginNotice` | string | 否 | 登录页提示 |
| `loginPageCss` | string | 否 | 登录页附加 CSS |
| `allowPublicRegistration` | bool | 否 | 是否允许公开注册 |
| `rssBasePath` | string | 否 | RSS 基础路径展示值 |
| `downloadNotice` | string | 否 | 下载提示 |
| `siteIconUrl` | string | 否 | 站点图标 URL |
| `siteIconFile` | file | 否 | 站点图标上传文件 |
| `clearSiteIconFile` | bool | 否 | 清空已上传图标文件 |
| `loginBackgroundType` | string | 否 | `api` / `file` / `css` |
| `loginBackgroundApiUrl` | string | 否 | 背景图 API / URL |
| `loginBackgroundFile` | file | 否 | 背景图上传文件 |
| `clearLoginBackgroundFile` | bool | 否 | 清空已上传背景文件 |
| `loginBackgroundCss` | string | 否 | CSS 背景值 |

规则：

- 当 `loginBackgroundType=api` 时，必须提供 `loginBackgroundApiUrl`。
- 当 `loginBackgroundType=file` 时，必须已有文件或本次上传 `loginBackgroundFile`。
- 当 `loginBackgroundType=css` 时，必须提供 `loginBackgroundCss`。

## 7. 响应数据模型

## 7.1 CurrentUser

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | int | 用户 ID |
| `username` | string | 用户名 |
| `displayName` | string | 显示名 |
| `role` | string | `admin` / `uploader` / `user` |
| `email` | string | 邮箱 |
| `status` | string | `active` / `disabled` |
| `lastLoginAt` | string | 最近登录时间 |
| `joinedAt` | string | 注册时间 |

## 7.2 Category

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | int | 分类 ID |
| `name` | string | 分类名称 |
| `slug` | string | 分类 slug |
| `sortOrder` | int | 排序值 |
| `isActive` | bool | 是否启用 |

## 7.3 Tag

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | int | 标签 ID |
| `name` | string | 标签名 |
| `slug` | string | 标签 slug |

## 7.4 ReleaseFile

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `path` | string | 文件路径 |
| `sizeBytes` | int | 文件大小 |

## 7.5 Release

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | int | 资源 ID |
| `title` | string | 标题 |
| `subtitle` | string | 副标题 |
| `description` | string | 描述 |
| `category` | `Category` | 分类对象 |
| `tags` | `Tag[]` | 标签数组 |
| `status` | string | `draft` / `published` / `hidden` |
| `sizeBytes` | int | 总大小 |
| `infohash` | string | torrent infohash |
| `coverImageUrl` | string | 封面图 URL，可能为空 |
| `publishedAt` | string | 发布时间 |
| `updatedAt` | string | 更新时间 |
| `createdBy` | object | `id` / `username` / `displayName` / `role` |
| `files` | `ReleaseFile[]` | 文件列表 |
| `downloadCount` | int | 下载次数 |
| `completionCount` | int | 完成次数 |
| `activePeers` | int | 活跃 peers |

## 7.6 DownloadLog

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | int | 下载记录 ID |
| `releaseId` | int | 资源 ID |
| `releaseTitle` | string | 资源标题 |
| `downloadedAt` | string | 下载时间 |
| `downloaderId` | int \| null | 下载者 ID，匿名时为 `null` |
| `downloaderName` | string | 下载者显示名，匿名时为“匿名访问” |

## 7.7 Announcement

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | int | 公告 ID |
| `title` | string | 标题 |
| `content` | string | 内容 |
| `status` | string | `online` / `draft` / `offline` |
| `audience` | string | `all` / `uploader` / `admin` |
| `updatedAt` | string | 更新时间 |

## 7.8 SiteSettingRead

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `siteName` | string | 站点名称 |
| `siteDescription` | string | 站点描述 |
| `loginNotice` | string | 登录页提示 |
| `loginPageCss` | string | 登录页附加 CSS |
| `allowPublicRegistration` | bool | 是否允许公开注册 |
| `rssBasePath` | string | RSS 基础路径展示值 |
| `downloadNotice` | string | 下载提示 |
| `siteIconUrl` | string | 手工配置的图标 URL |
| `siteIconFileUrl` | string | 已上传图标文件 URL |
| `siteIconResolvedUrl` | string | 最终可直接使用的图标 URL |
| `loginBackgroundType` | string | `api` / `file` / `css` |
| `loginBackgroundApiUrl` | string | 背景图 URL |
| `loginBackgroundFileUrl` | string | 背景图文件 URL |
| `loginBackgroundResolvedUrl` | string | 最终背景图 URL |
| `loginBackgroundCss` | string | CSS 背景值 |

## 7.9 SelfTheme

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `mode` | string | `system` / `light` / `dark` |
| `customCss` | string | 自定义 CSS |

## 7.10 SelfApiToken

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `apiToken` | string | 当前用户 API Token |

## 7.11 AdminDashboardData

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `stats.userCount` | int | 用户总数 |
| `stats.releaseCount` | int | 资源总数 |
| `stats.activeReleaseCount` | int | 已发布资源数 |
| `stats.draftReleaseCount` | int | 草稿资源数 |
| `stats.activeAnnouncementCount` | int | 在线公告数 |
| `latestUsers` | `AdminUser[]` | 最新用户 |
| `latestReleases` | `Release[]` | 最新资源 |

## 7.12 AdminUser

`AdminUser` 继承 `CurrentUser`，并额外包含：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `createdReleaseCount` | int | 用户已发布资源数 |

`AdminUserCreate` 在此基础上额外可能返回：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `initialPassword` | string \| null | 服务端自动生成的初始密码 |

## 7.13 InviteCode

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | int | 邀请码 ID |
| `code` | string | 邀请码，例如 `ABCD-EFGH-IJKL` |
| `note` | string | 备注 |
| `status` | string | `available` / `used` / `revoked` / `expired` |
| `isActive` | bool | 是否仍处于启用状态 |
| `createdByName` | string | 创建人显示名 |
| `usedByName` | string \| null | 使用人显示名 |
| `createdAt` | string | 创建时间 |
| `usedAt` | string \| null | 使用时间 |
| `expiresAt` | string \| null | 过期时间 |
| `canRevoke` | bool | 是否还能停用 |

## 7.14 AuditLog

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | int | 日志 ID |
| `actorName` | string | 操作人 |
| `action` | string | 动作 |
| `targetType` | string | 对象类型 |
| `targetName` | string | 对象名称 |
| `createdAt` | string | 发生时间 |
| `detail` | string | 详细说明 |

## 7.15 RssOverviewData

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `generalFeed` | string | 全站 RSS 地址 |
| `recentReleaseTitles` | string[] | 最近发布资源标题列表 |

## 8. 对接示例

### 8.1 使用 API Token 调用

```bash
curl -X GET "https://your-domain.example/api/releases/" \
  -H "Authorization: Bearer YOUR_API_TOKEN"
```

### 8.2 登录并保留 Cookie

```bash
curl -X POST "https://your-domain.example/api/auth/login/" \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{
    "username": "alice",
    "password": "your-password"
  }'
```

### 8.3 上传资源

```bash
curl -X POST "https://your-domain.example/api/releases/" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -F "title=Example Release" \
  -F "description=Uploaded from another service" \
  -F "categorySlug=movie" \
  -F "tagSlugs=1080p" \
  -F "tagSlugs=webdl" \
  -F "status=published" \
  -F "torrentFile=@example.torrent"
```

### 8.4 切换资源可见性

```bash
curl -X POST "https://your-domain.example/api/releases/123/visibility/" \
  -H "Authorization: Bearer ADMIN_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "hidden"
  }'
```

## 9. 备注

- 如果外部项目只需要“读站点、读资源、下载、RSS”，通常不必接入后台接口。
- 如果外部项目是管理端，建议优先使用 Token 鉴权，而不是依赖浏览器 Session。
- 若要自动同步接口变更，建议定期拉取 `/api/schema/` 做校验；本文档更适合人工阅读与业务接入。

# 前端页面与权限设计文档

## 1. 文档目标

这份文档专门用于定义前端部分的：

- 页面拆分
- 路由结构
- 布局方式
- 菜单与导航
- 页面权限
- 组件级权限
- 页面状态与异常页

目标是让前端开发时不再反复讨论“这个页面放哪”“谁能看到什么”“无权限时跳哪”，直接按统一规则实现。

前端视觉、组件风格、背景、卡片和组件库规范，见：

- `docs/frontend-style-system-spec.md`

后端接口、认证、权限、XBT 同步与日志规范，见：

- `docs/backend-architecture-spec.md`

项目级“必须简单易用、低复杂度、低部署成本”的硬约束，见：

- `docs/simplicity-usability-operability-rules.md`

## 2. 技术前提

当前前端默认技术路线：

- `Vue 3`
- `Vite`
- `Vue Router`
- `Pinia`
- `TailwindCSS`

当前后端默认技术路线：

- `Django + Django REST Framework`
- `Session` 登录态为主
- `/auth/me` 返回当前登录用户信息

当前角色模型：

- `admin`
- `uploader`
- `user`

当前站点定位：

- 内部字幕组分流站
- 非公开注册
- 前端主要承载浏览、上传、账户、后台管理
- Tracker 由 `XBT` 独立承担

## 3. 设计原则

- `简单`: 页面不要做成传统 PT 站那种信息密度过高的风格
- `统一`: 同类型页面尽量复用同一布局和同一状态组件
- `权限清晰`: 用户一眼能看出自己能做什么
- `减少误操作`: 没权限的功能不应该到处露出
- `后端为准`: 前端做权限体验，后端做权限裁决

## 4. 前端整体分层

建议把前端分成 4 个访问层。

### 4.1 游客层

适用对象：

- 未登录用户

页面：

- 登录页
- 404 页面

特点：

- 页面极少
- 不显示业务导航
- 只负责进入系统

### 4.2 登录用户层

适用对象：

- `user`
- `uploader`
- `admin`

页面：

- 首页
- 资源列表
- 资源详情
- 分类页
- 标签页
- RSS 页
- 我的账户
- 我的下载

特点：

- 所有登录用户共享同一套前台布局
- 页面以“浏览、筛选、下载”为核心

### 4.3 上传者层

适用对象：

- `uploader`
- `admin`

页面：

- 上传资源
- 我的发布
- 编辑我发布的资源

特点：

- 仍属于前台，不混进后台管理区
- 避免上传者误认为自己拥有后台权限

### 4.4 管理层

适用对象：

- `admin`

页面：

- 后台首页
- 用户管理
- 资源管理
- 分类标签管理
- 公告管理
- XBT 同步
- 审计日志
- 系统设置

特点：

- 与前台视觉上明显区分
- 强调管理和操作确认

## 5. 布局设计

全站建议只保留 3 套布局。

### 5.1 `AuthLayout`

用途：

- 登录页

结构：

- 居中卡片
- Logo / 站点名
- 登录表单
- 登录错误提示

要求：

- 尽量简洁
- 不显示业务菜单
- 支持键盘回车登录

### 5.2 `SiteLayout`

用途：

- 所有前台页面
- 包含普通用户和上传者页面

结构：

- 顶部导航栏
- 公告区
- 页面主内容区
- 页脚

导航建议：

- 左侧：站点名、首页、资源、RSS
- 右侧：上传资源、我的发布、我的账户、退出登录

响应式建议：

- 桌面端使用顶部导航
- 移动端折叠为抽屉菜单

### 5.3 `AdminLayout`

用途：

- 所有 `/admin/**` 页面

结构：

- 左侧固定侧边栏
- 顶部工具栏
- 主内容区

顶部工具栏建议：

- 当前管理员信息
- 快速返回前台
- 退出登录

侧边栏建议：

- 仪表盘
- 用户管理
- 资源管理
- 分类管理
- 标签管理
- 公告管理
- XBT 同步
- 审计日志
- 系统设置

## 6. 推荐路由结构

建议使用下面的路由树。

```text
/login
/403
/404
/
/releases
/releases/:id
/categories/:slug
/tags/:slug
/rss
/me
/me/downloads
/upload
/my/releases
/my/releases/:id/edit
/admin
/admin/users
/admin/users/:id
/admin/releases
/admin/categories
/admin/tags
/admin/announcements
/admin/tracker-sync
/admin/audit-logs
/admin/settings
```

建议路由命名：

- `login`
- `forbidden`
- `not-found`
- `home`
- `release-list`
- `release-detail`
- `category-detail`
- `tag-detail`
- `rss`
- `me`
- `my-downloads`
- `upload`
- `my-releases`
- `my-release-edit`
- `admin-dashboard`
- `admin-users`
- `admin-user-detail`
- `admin-releases`
- `admin-categories`
- `admin-tags`
- `admin-announcements`
- `admin-tracker-sync`
- `admin-audit-logs`
- `admin-settings`

## 7. 页面清单与职责

### 7.1 登录页 `/login`

布局：

- `AuthLayout`

可访问角色：

- 未登录用户

核心模块：

- 用户名输入框
- 密码输入框
- 登录按钮
- 错误提示

行为：

- 登录成功后跳转首页
- 如有原始目标地址，跳回原页面
- 已登录用户访问该页时直接跳首页

### 7.2 首页 `/`

布局：

- `SiteLayout`

可访问角色：

- `user`
- `uploader`
- `admin`

核心模块：

- 最新资源列表
- 分类快捷入口
- 标签筛选
- 站点公告
- 搜索入口

主要动作：

- 进入详情页
- 快速下载
- 筛选资源

### 7.3 资源列表页 `/releases`

布局：

- `SiteLayout`

可访问角色：

- 全部登录用户

核心模块：

- 搜索栏
- 分类筛选
- 标签筛选
- 排序
- 列表表格或卡片
- 分页

主要动作：

- 查看详情
- 下载种子

### 7.4 资源详情页 `/releases/:id`

布局：

- `SiteLayout`

可访问角色：

- 全部登录用户

核心模块：

- 标题与副标题
- 资源简介
- 文件列表
- 标签与分类
- 下载按钮
- 发布者信息

角色动作差异：

- `user`: 下载
- `uploader`: 下载，若为自己发布则可编辑
- `admin`: 下载、编辑、隐藏、后台查看

### 7.5 分类页 `/categories/:slug`

布局：

- `SiteLayout`

可访问角色：

- 全部登录用户

核心模块：

- 当前分类标题
- 分类下资源列表
- 过滤与排序

### 7.6 标签页 `/tags/:slug`

布局：

- `SiteLayout`

可访问角色：

- 全部登录用户

核心模块：

- 当前标签标题
- 标签下资源列表

### 7.7 RSS 页 `/rss`

布局：

- `SiteLayout`

可访问角色：

- 全部登录用户

核心模块：

- 通用 RSS 地址
- 分类 RSS 地址
- 标签 RSS 地址
- 一键复制按钮
- 风险提示

主要动作：

- 复制地址
- 查看使用说明

### 7.8 我的账户页 `/me`

布局：

- `SiteLayout`

可访问角色：

- 全部登录用户

核心模块：

- 用户基础信息
- 角色显示
- 上次登录时间
- RSS 信息
- `passkey` 状态
- 修改密码
- 重置 `passkey`

### 7.9 我的下载页 `/me/downloads`

布局：

- `SiteLayout`

可访问角色：

- 全部登录用户

核心模块：

- 下载时间
- 资源名
- 资源链接
- 重新下载按钮

### 7.10 上传页 `/upload`

布局：

- `SiteLayout`

可访问角色：

- `uploader`
- `admin`

核心模块：

- 标题
- 副标题
- 分类
- 标签
- 简介
- torrent 上传
- 提交按钮

主要动作：

- 发布资源
- 保存草稿

### 7.11 我的发布页 `/my/releases`

布局：

- `SiteLayout`

可访问角色：

- `uploader`
- `admin`

核心模块：

- 我发布的资源列表
- 状态筛选
- 编辑入口

### 7.12 编辑资源页 `/my/releases/:id/edit`

布局：

- `SiteLayout`

可访问角色：

- `uploader`
- `admin`

权限规则：

- `uploader` 只能编辑自己发布的资源
- `admin` 可以编辑任意资源

### 7.13 后台首页 `/admin`

布局：

- `AdminLayout`

可访问角色：

- `admin`

核心模块：

- 用户数
- 资源数
- 最近操作
- XBT 同步状态
- 系统异常提示

### 7.14 用户管理 `/admin/users`

布局：

- `AdminLayout`

可访问角色：

- `admin`

核心模块：

- 用户列表
- 搜索
- 状态筛选
- 角色筛选
- 创建用户按钮

### 7.15 用户详情 `/admin/users/:id`

布局：

- `AdminLayout`

可访问角色：

- `admin`

核心模块：

- 用户基础信息
- 角色
- 状态
- `passkey`
- 最近登录
- 操作按钮

主要动作：

- 禁用 / 启用
- 重置密码
- 重置 `passkey`
- 触发 XBT 同步

### 7.16 资源管理 `/admin/releases`

布局：

- `AdminLayout`

可访问角色：

- `admin`

核心模块：

- 资源列表
- 状态筛选
- 发布者筛选
- 编辑入口
- 隐藏/恢复入口

### 7.17 分类与标签管理

路由：

- `/admin/categories`
- `/admin/tags`

布局：

- `AdminLayout`

可访问角色：

- `admin`

核心模块：

- 列表
- 新建
- 编辑
- 启用/停用

### 7.18 公告管理 `/admin/announcements`

布局：

- `AdminLayout`

可访问角色：

- `admin`

核心模块：

- 公告列表
- 新建公告
- 编辑公告
- 上下线控制

### 7.19 XBT 同步页 `/admin/tracker-sync`

布局：

- `AdminLayout`

可访问角色：

- `admin`

核心模块：

- 最近同步记录
- 同步失败记录
- 手动全量同步
- 单项重试

### 7.20 审计日志 `/admin/audit-logs`

布局：

- `AdminLayout`

可访问角色：

- `admin`

核心模块：

- 操作人
- 操作对象
- 动作
- 时间
- 详情展开

### 7.21 系统设置 `/admin/settings`

布局：

- `AdminLayout`

可访问角色：

- `admin`

核心模块：

- 站点基础设置
- 登录相关设置
- RSS 设置
- 下载设置

### 7.22 异常页

页面：

- `/403`
- `/404`
- `/500`

用途：

- 明确区分“未登录”“无权限”“不存在”“系统错误”

## 8. 菜单与导航规则

### 8.1 顶部导航

未登录：

- 登录

`user`：

- 首页
- 资源
- RSS
- 我的账户
- 我的下载

`uploader`：

- 首页
- 资源
- RSS
- 上传资源
- 我的发布
- 我的账户
- 我的下载

`admin`：

- 首页
- 资源
- RSS
- 上传资源
- 我的发布
- 后台管理
- 我的账户
- 我的下载

### 8.2 后台侧边栏

仅 `admin` 可见：

- 仪表盘
- 用户管理
- 资源管理
- 分类管理
- 标签管理
- 公告管理
- XBT 同步
- 审计日志
- 系统设置

## 9. 权限设计

### 9.1 路由权限矩阵

| 页面类型 | user | uploader | admin |
|---|---|---|---|
| 首页/列表/详情/RSS/我的账户/我的下载 | Yes | Yes | Yes |
| 上传资源 | No | Yes | Yes |
| 我的发布 | No | Yes | Yes |
| 编辑自己发布的资源 | No | Yes | Yes |
| `/admin/**` | No | No | Yes |

### 9.2 页面级权限

建议通过路由 `meta` 统一控制：

- `requiresAuth`
- `guestOnly`
- `roles`
- `title`

示例：

```ts
{
  path: '/upload',
  name: 'upload',
  component: () => import('@/views/upload/UploadView.vue'),
  meta: {
    requiresAuth: true,
    roles: ['admin', 'uploader'],
    title: '上传资源',
  },
}
```

### 9.3 组件级权限

组件级权限用于控制按钮和局部区域显示。

建议使用统一工具：

- `hasRole(user, roles)`
- `canEditRelease(user, release)`
- `canManageAdmin(user)`

典型场景：

- 详情页是否显示“编辑”
- 列表页是否显示“上传资源”
- 管理页是否显示“禁用用户”

### 9.4 权限处理原则

- 没权限的页面不让进入
- 没权限的按钮默认不显示
- 即使按钮误显示，后端接口仍必须拒绝
- `admin` 拥有全部页面权限
- `uploader` 不拥有后台权限

## 10. 前端鉴权流程

### 10.1 登录态初始化

应用启动时建议流程：

1. 读取本地基础状态
2. 请求 `/auth/me`
3. 获取当前用户、角色、状态
4. 决定菜单和可访问路由

### 10.2 路由守卫

建议在 `router.beforeEach` 中统一处理：

1. 页面是否需要登录
2. 当前是否已登录
3. 是否满足角色要求
4. 是否需要跳转 `/login`
5. 是否需要跳转 `/403`

### 10.3 推荐跳转规则

- 未登录访问业务页：跳 `/login`
- 已登录访问 `/login`：跳 `/`
- 已登录但无权限：跳 `/403`
- 资源不存在：跳 `/404`
- 接口异常：显示页内错误态或 `/500`

## 11. 页面状态设计

每个页面都要统一处理以下状态：

- `loading`
- `empty`
- `error`
- `forbidden`
- `not_found`

建议抽公共组件：

- `AppLoading`
- `AppEmpty`
- `AppError`
- `AppForbidden`
- `AppNotFound`

列表页额外建议：

- 首次加载 skeleton
- 筛选为空时显示空状态
- 请求失败时可直接重试

详情页额外建议：

- 加载失败区分 403 / 404 / 500
- 权限不足时不要显示空白页

## 12. 前端 Store 设计

建议至少拆出以下 Store：

- `authStore`
- `uiStore`
- `releaseFilterStore`

### 12.1 `authStore`

建议保存：

- `currentUser`
- `role`
- `isAuthenticated`
- `isBootstrapped`

建议方法：

- `fetchMe()`
- `login()`
- `logout()`
- `resetPasskey()`

### 12.2 `uiStore`

建议保存：

- 侧边栏展开状态
- 全局 loading
- 当前主题或界面模式

### 12.3 `releaseFilterStore`

建议保存：

- 当前搜索词
- 当前分类
- 当前标签
- 当前排序
- 当前分页

## 13. 推荐前端目录结构

```text
src/
  layouts/
    AuthLayout.vue
    SiteLayout.vue
    AdminLayout.vue
  router/
    index.ts
    guards.ts
    routes.ts
  stores/
    auth.ts
    ui.ts
    releaseFilters.ts
  views/
    auth/
      LoginView.vue
    site/
      HomeView.vue
      ReleaseListView.vue
      ReleaseDetailView.vue
      CategoryView.vue
      TagView.vue
      RssView.vue
      MeView.vue
      MyDownloadsView.vue
    upload/
      UploadView.vue
      MyReleasesView.vue
      EditMyReleaseView.vue
    admin/
      AdminDashboardView.vue
      AdminUsersView.vue
      AdminUserDetailView.vue
      AdminReleasesView.vue
      AdminCategoriesView.vue
      AdminTagsView.vue
      AdminAnnouncementsView.vue
      AdminTrackerSyncView.vue
      AdminAuditLogsView.vue
      AdminSettingsView.vue
    system/
      ForbiddenView.vue
      NotFoundView.vue
      ErrorView.vue
  components/
    common/
    navigation/
    release/
    admin/
  services/
    api.ts
    auth.ts
    releases.ts
    rss.ts
    trackerSync.ts
  composables/
    useAuth.ts
    usePermissions.ts
    usePagination.ts
  utils/
    permissions.ts
    route-meta.ts
  types/
    auth.ts
    release.ts
    user.ts
```

## 14. 推荐实现顺序

### 阶段 1

- 搭建 `Vue Router`
- 搭建 `Pinia`
- 实现 3 套布局
- 实现登录态初始化
- 实现路由守卫
- 实现 `/403` `/404`

### 阶段 2

- 实现首页
- 实现资源列表
- 实现资源详情
- 实现顶部导航
- 实现统一状态组件

### 阶段 3

- 实现 RSS
- 实现我的账户
- 实现我的下载
- 实现上传页
- 实现我的发布

### 阶段 4

- 实现后台首页
- 实现后台侧边栏
- 实现用户管理
- 实现资源管理
- 实现 XBT 同步页

## 15. 前端验收标准

- 未登录用户只能看到登录页与异常页
- 不同角色登录后，顶部导航与可访问页面正确变化
- `uploader` 可上传并管理自己的资源
- `admin` 可访问全部后台页面
- 无权限访问后台时会进入 `/403`
- 页面空状态、错误状态、加载状态统一
- 移动端导航可正常展开与收起

## 16. 当前结论

前端实现建议收敛为：

- 一个 `Vue SPA`
- 三套布局：`AuthLayout`、`SiteLayout`、`AdminLayout`
- 四层访问区域：游客、登录用户、上传者、管理层
- 双层权限控制：路由权限 + 组件权限
- 所有后台页面仅 `admin` 可见
- 所有上传相关页面仅 `uploader` 和 `admin` 可见

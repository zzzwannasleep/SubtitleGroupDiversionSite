# 字幕组内部分流站点重设计方案

## 1. 项目目标

### 1.1 背景
现有需求是做一个给字幕组内部使用的分流站点，机制参考 PT，但不引入 PT 站常见的大量运营规则和复杂门槛。站点只聚焦三个核心能力：

1. `RSS 浏览与订阅`
2. `站内浏览与下载种子`
3. `多用户 Private Tracker`

这个站点不是公开站，也不是完整 PT 社区，不需要论坛、求种、魔力值、考核、保种等级、复杂做种率规则等功能。

### 1.2 建设目标

- 让字幕组成员可以快速看到最新资源
- 让不同角色的用户以最少学习成本完成上传、浏览、订阅、下载
- 通过 Private Tracker 保证资源在站内受控流转
- 让管理员能够低成本地维护用户和内容
- 用简单清晰的架构支持后续扩展

### 1.3 核心设计原则

- 项目级“易用、低复杂度、低部署成本”硬约束见：
- `docs/simplicity-usability-operability-rules.md`

- `极简`: 只做必须功能，避免 PT 站“全家桶”
- `好上手`: 页面和流程尽量接近普通资源站
- `权限清楚`: 只保留 `admin`、`uploader`、`user` 三类角色
- `私有可控`: 所有种子下载、RSS、Tracker 行为都与用户身份绑定
- `先做 MVP`: 优先保证上传、浏览、RSS、下载、追踪闭环可用

## 2. 功能边界

### 2.1 本期必须实现

- 用户登录与权限控制
- 管理员创建和管理用户
- 上传者发布种子与资源信息
- 用户浏览资源列表与详情
- 用户下载带个人 `passkey` 的种子文件
- 用户获取个人 RSS 地址
- Tracker `announce` 能识别用户和种子
- 站点可记录基本下载/完成/活跃信息

### 2.2 明确不做

- 做种率、上传下载比、魔力值、H&R、考核系统
- 论坛、评论区、求种区、站内私信
- 邀请体系、公开注册
- 复杂的审核流与多级权限
- 自动刮削海报、自动识别媒体库的重型媒体管理功能
- Magnet 外链聚合、公开搜索引擎收录

### 2.3 可作为二期增强

- 资源订阅规则管理
- Telegram / 邮件 / Webhook 通知
- 批量上传与模板化发布
- 标签体系增强
- 审计报表和运营统计面板
- 上传者草稿箱与发布审批

## 3. 用户角色与权限

### 3.1 `admin`

职责：

- 管理系统配置
- 创建、禁用、重置用户
- 分配角色
- 管理分类、标签、站点公告
- 查看所有资源与基本 Tracker 统计
- 处理违规资源、下架资源、重置用户 `passkey`

权限：

- 完整后台访问权限
- 查看和编辑所有资源
- 下载任意资源
- 查看所有用户活动日志
- 控制 RSS、Tracker、站点配置开关

### 3.2 `uploader`

职责：

- 上传种子
- 维护自己发布的资源信息
- 管理自己发布资源的标题、分类、标签、简介、截图

权限：

- 登录前台
- 访问上传页
- 编辑自己发布的资源
- 查看自己资源的下载/完成统计
- 下载站内资源
- 使用自己的 RSS

限制：

- 不能管理用户
- 不能编辑他人资源
- 不能改系统配置

### 3.3 `user`

职责：

- 浏览站内资源
- 订阅 RSS
- 下载种子
- 参与分流

权限：

- 登录前台
- 浏览列表、详情
- 获取个人 RSS 地址
- 下载带个人 `passkey` 的种子文件
- 查看自己的基础下载历史

限制：

- 不能上传资源
- 不能访问后台管理
- 不能查看他人数据

## 4. 核心业务流程

### 4.1 管理员创建账号

1. 管理员进入后台创建用户
2. 设置用户名、显示名、邮箱或内部标识
3. 指定角色为 `uploader` 或 `user`
4. 系统生成初始密码或发送重置链接
5. 用户首次登录后修改密码

说明：

- 不开放公开注册
- 内部站点建议采用“管理员建号”模式
- 如需进一步收紧，可以只允许内网/VPN 访问

### 4.2 上传者发布资源

1. 上传者进入“发布资源”页面
2. 填写标题、副标题、分类、标签、简介
3. 上传 `.torrent` 文件
4. 系统解析 torrent，校验 `infohash`、文件列表、`private` 标记
5. 系统创建资源记录并保存基础 torrent
6. 资源进入已发布状态
7. 资源出现在首页列表、分类页、RSS 中

建议：

- 上传表单要尽量短
- 常用字段提供模板化输入
- 支持“复制上一条配置”作为二期功能

### 4.3 用户浏览与下载

1. 用户登录站点
2. 在首页或分类页浏览最新资源
3. 进入详情页查看文件信息、标签、发布时间、发布者
4. 点击下载
5. 系统将当前用户的 `passkey` 注入 torrent 的 announce 地址
6. 浏览器下载个性化种子文件
7. 用户在下载器中打开后开始做种/下载

### 4.4 RSS 订阅

1. 用户在“RSS 订阅”页面获取自己的专属地址
2. 可选择全部资源 RSS 或按分类/标签筛选
3. 用户把地址加入下载器或阅读器
4. 新资源发布后 RSS 自动可见
5. RSS 条目中的下载链接同样绑定用户身份

### 4.5 Tracker 交互

1. 下载器使用用户专属 announce 地址访问 Tracker
2. Tracker 根据 `passkey` 识别用户身份
3. Tracker 根据 `infohash` 识别种子
4. 记录 `started`、`completed`、`stopped`、定期 `announce`
5. 返回 peer 列表

最小实现目标：

- 能鉴权
- 能返回 peers
- 能记录活跃状态和完成次数

不必首期实现：

- 复杂速率统计
- 精确上传下载量结算
- 做种率奖惩

## 5. 页面与信息架构

### 5.1 页面结构总览

- 登录页
- 首页 / 最新资源页
- 分类页
- 资源详情页
- RSS 订阅页
- 我的账户页
- 我的下载历史页
- 上传资源页（仅 `uploader` / `admin`）
- 后台用户管理页（仅 `admin`）
- 后台资源管理页（仅 `admin`）
- 后台系统设置页（仅 `admin`）

### 5.2 首页 / 最新资源页

目标：

- 一进入站点就能看到最近更新
- 减少学习成本，让用户像浏览普通资源站一样上手

建议模块：

- 顶部导航
- 站点公告
- 最新资源列表
- 分类筛选
- 标签筛选
- 搜索框
- RSS 快捷入口

资源列表字段建议：

- 标题
- 副标题或版本说明
- 分类
- 标签
- 大小
- 发布时间
- 发布者
- 下载按钮

### 5.3 资源详情页

建议展示：

- 标题与副标题
- 简介
- 截图或海报
- 文件大小
- 文件列表
- 分类与标签
- 发布时间
- 发布者
- 下载按钮
- RSS 相关入口

可选展示：

- 完成次数
- 当前活跃 peer 数
- 最近更新时间

### 5.4 RSS 订阅页

建议功能：

- 显示“我的通用 RSS 地址”
- 显示按分类筛选后的 RSS 地址
- 显示按标签筛选后的 RSS 地址
- 一键复制地址
- 提示“地址包含个人身份，请勿外传”

建议额外提供：

- 最近 RSS 更新记录预览
- RSS 使用说明

### 5.5 上传资源页

表单建议字段：

- 标题
- 副标题
- 分类
- 标签
- 简介
- 截图链接或上传
- torrent 文件
- 是否置顶或推荐（仅管理员）

交互要求：

- 上传前校验 torrent 是否为 private
- 重复 `infohash` 给出提示
- 字段错误提示尽量清晰

### 5.6 我的账户页

建议展示：

- 用户名
- 角色
- 账户状态
- 上次登录时间
- RSS 地址
- `passkey` 状态
- 重置密码
- 重置 `passkey` 按钮

注意：

- 重置 `passkey` 后，旧 RSS 与旧 torrent 将全部失效

### 5.7 后台管理页

后台模块建议：

- 用户管理
- 资源管理
- 分类标签管理
- 站点公告管理
- Tracker 基本监控
- 系统设置
- 审计日志

### 5.8 前端页面分层建议

前端页面、路由、布局与权限的详细设计，见：

- `docs/frontend-page-permission-spec.md`

前端建议做成一个 `Vue` 单页应用，但按“访问区域”拆成 4 层：

- `游客层`: 只包含登录页和 404 页面
- `登录用户层`: 所有已登录用户都可访问的前台页面
- `上传者层`: `uploader` 和 `admin` 可访问的上传与维护页面
- `管理层`: 只有 `admin` 可访问的后台页面

这样做的好处：

- 页面边界清楚
- 路由守卫简单
- 菜单显示逻辑清楚
- 后续加页面时不容易乱

### 5.9 推荐页面清单

建议首期页面收敛为下面这些。

游客层：

- `/login` 登录页
- `/404` 页面不存在

登录用户层：

- `/` 首页 / 最新资源
- `/releases` 资源列表页
- `/releases/:id` 资源详情页
- `/categories/:slug` 分类列表页
- `/tags/:slug` 标签列表页
- `/rss` RSS 页面
- `/me` 我的账户页
- `/me/downloads` 我的下载记录页

上传者层：

- `/upload` 上传资源页
- `/my/releases` 我发布的资源列表
- `/my/releases/:id/edit` 编辑我发布的资源

管理层：

- `/admin` 后台首页
- `/admin/users` 用户列表
- `/admin/users/:id` 用户详情
- `/admin/releases` 资源管理
- `/admin/categories` 分类管理
- `/admin/tags` 标签管理
- `/admin/announcements` 公告管理
- `/admin/tracker-sync` XBT 同步状态页
- `/admin/audit-logs` 审计日志页
- `/admin/settings` 系统设置页

补充页面：

- `/403` 无权限页面
- `/500` 系统错误页

### 5.10 布局建议

建议统一用 3 套布局，不要每个页面自己拼导航。

`AuthLayout`：

- 用于 `/login`
- 居中表单布局
- 背景可简洁，突出登录框

`SiteLayout`：

- 用于前台普通页面
- 顶部导航 + 主内容区
- 移动端用抽屉菜单

`AdminLayout`：

- 用于 `/admin/**`
- 左侧导航 + 顶部工具栏 + 主内容区
- 明确和前台区分视觉层级

建议：

- `/upload` 和 `/my/releases` 仍然使用 `SiteLayout`
- 不要把上传者页面混进 `AdminLayout`
- 这样 `uploader` 不会误以为自己进入后台

### 5.11 菜单与导航规则

顶部导航建议按角色动态显示。

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

后台侧边栏仅 `admin` 可见：

- 仪表盘
- 用户管理
- 资源管理
- 分类管理
- 标签管理
- 公告管理
- XBT 同步
- 审计日志
- 系统设置

### 5.12 页面权限矩阵

建议前端直接固化一份最小权限矩阵。

所有人都不能访问：

- 未登录用户不能访问除 `/login` 之外的业务页面

`user` 可访问：

- 首页
- 列表页
- 详情页
- RSS 页面
- 我的账户
- 我的下载

`user` 不可访问：

- 上传页
- 我的发布
- 所有 `/admin/**`

`uploader` 可访问：

- `user` 的全部页面
- 上传页
- 我的发布
- 编辑自己发布的资源

`uploader` 不可访问：

- 所有 `/admin/**`
- 编辑他人资源

`admin` 可访问：

- 全部前台页面
- 上传页
- 我的发布
- 所有 `/admin/**`

### 5.13 前端鉴权与路由守卫

前端建议不要把权限逻辑散落在每个页面里，而是统一收口到：

- `auth store`
- `route meta`
- `router.beforeEach`

推荐做法：

- 登录成功后调用 `/auth/me`
- 前端在 `Pinia` 中保存当前用户信息
- 路由通过 `meta.requiresAuth`、`meta.roles` 控制访问
- 未登录访问受保护页面时，跳转到 `/login`
- 已登录但无权限时，跳转到 `/403`

建议路由元信息：

- `requiresAuth: true | false`
- `roles: ['admin']`
- `roles: ['admin', 'uploader']`
- `guestOnly: true`
- `title`

推荐逻辑：

- `guestOnly` 页面已登录后跳回首页
- `requiresAuth` 页面未登录则跳登录
- 配置了 `roles` 但当前角色不在其中，则跳 `/403`

### 5.14 页面级权限与组件级权限

前端权限不要只做路由守卫，还要做组件级控制。

例如在资源详情页：

- `user` 能看到下载按钮
- `uploader` 能看到“编辑我发布的资源”按钮，但仅限自己发布的资源
- `admin` 能看到“编辑”“隐藏”“后台查看”按钮

例如在资源列表页：

- `user` 不显示“上传资源”
- `uploader` 显示“上传资源”
- `admin` 显示“上传资源”和“后台管理”

原则：

- 路由权限控制“能不能进页面”
- 组件权限控制“页面里能看到什么按钮”
- 后端接口权限仍然必须保留，不依赖前端防护

### 5.15 页面状态设计

每个列表页和详情页都建议统一处理这些状态：

- `loading`
- `empty`
- `error`
- `forbidden`
- `not_found`

建议统一组件：

- `AppLoading`
- `AppEmpty`
- `AppError`
- `AppForbidden`
- `AppNotFound`

这样做的好处：

- 风格统一
- 页面开发速度快
- 后期维护容易

### 5.16 推荐前端目录结构

建议目录按“布局、页面、模块、权限”拆分。

- `src/layouts/`
- `src/router/`
- `src/stores/`
- `src/views/auth/`
- `src/views/site/`
- `src/views/upload/`
- `src/views/admin/`
- `src/components/common/`
- `src/components/release/`
- `src/components/admin/`
- `src/composables/`
- `src/services/`
- `src/types/`
- `src/utils/`

权限相关建议单独抽出来：

- `src/router/guards.ts`
- `src/utils/permissions.ts`
- `src/stores/auth.ts`

## 6. 数据模型设计

以下为推荐最小数据模型，适合先做 MVP。

### 6.1 `users`

字段建议：

- `id`
- `username`
- `display_name`
- `email`
- `password_hash`
- `role` (`admin` / `uploader` / `user`)
- `status` (`active` / `disabled`)
- `passkey`
- `last_login_at`
- `created_at`
- `updated_at`

说明：

- `passkey` 为每个用户唯一
- `passkey` 同时用于 tracker 和 RSS 个性化访问

### 6.2 `categories`

字段建议：

- `id`
- `name`
- `slug`
- `sort_order`
- `is_active`

### 6.3 `tags`

字段建议：

- `id`
- `name`
- `slug`

### 6.4 `releases`

字段建议：

- `id`
- `title`
- `subtitle`
- `description`
- `category_id`
- `created_by`
- `status` (`draft` / `published` / `hidden`)
- `cover_image_url`
- `size_bytes`
- `infohash`
- `torrent_storage_path`
- `published_at`
- `created_at`
- `updated_at`

说明：

- `torrent_storage_path` 保存基础 torrent 文件
- 用户下载时动态生成带个人 announce 的 torrent

### 6.5 `release_tags`

字段建议：

- `release_id`
- `tag_id`

### 6.6 `release_files`

字段建议：

- `id`
- `release_id`
- `file_path`
- `file_size`

说明：

- 由解析 torrent 时自动写入

### 6.7 `downloads`

字段建议：

- `id`
- `user_id`
- `release_id`
- `downloaded_at`
- `ip_address`
- `user_agent`

说明：

- 记录谁下载过哪个个性化 torrent
- 方便问题排查和简单审计

### 6.8 `tracker_peers`

字段建议：

- `id`
- `user_id`
- `release_id`
- `peer_id`
- `ip_address`
- `port`
- `left_bytes`
- `uploaded_bytes`
- `downloaded_bytes`
- `event`
- `last_announce_at`
- `is_seeder`

说明：

- 如果首期不做精确统计，也可以保留字段但只做基础记录

### 6.9 `rss_tokens`

如果 `passkey` 直接兼作 RSS 访问令牌，这张表可以省略。

如果希望更安全，可以拆分为：

- `id`
- `user_id`
- `token`
- `type`
- `created_at`
- `revoked_at`

### 6.10 `audit_logs`

字段建议：

- `id`
- `actor_user_id`
- `action`
- `target_type`
- `target_id`
- `payload_json`
- `created_at`

用途：

- 记录后台改用户、删资源、重置 passkey 等关键操作

## 7. Tracker 机制建议

### 7.1 目标

做一个“够用”的私有 Tracker，而不是完整 PT 规则引擎。

### 7.2 最小能力

- 识别用户身份
- 校验种子是否合法
- 返回 peer 列表
- 记录活跃时间
- 记录完成事件

### 7.3 推荐规则

- 所有 torrent 必须设置 `private=1`
- 所有下载链接必须登录后访问
- 所有下载出的 torrent 都带用户专属 announce 地址
- `passkey` 泄露后可由管理员或用户手动重置
- 被禁用用户的 announce 请求直接拒绝

### 7.4 首期不建议实现的复杂点

- 严格上传下载量计算
- 防作弊规则
- 多 Tracker 集群
- 复杂 scrape 兼容
- IPv6 / 多网卡 / 多实例高可用设计

### 7.5 简化建议

如果首期想尽快落地，可以采用下面策略：

- `announce` 实现为唯一关键接口
- `scrape` 可以先不开放，或者只返回最小信息
- peer 列表允许先做“小规模内部分发”版本
- 只记录必要日志，不做重运营数据

### 7.6 开源 Tracker 复用建议

既然“不自己从零写 Tracker”，那么更合理的方案是：

- 站点主程序负责用户、资源、RSS、下载种子
- Tracker 使用独立开源项目
- 站点只负责把“允许的 torrent / 用户 passkey / 禁用状态”同步给 Tracker

这样可以显著降低复杂度。

推荐优先看下面几类方案。

#### 方案 A：`Torrust Tracker`

项目：

- `https://github.com/torrust/torrust-tracker`
- `https://torrust.com/torrent-tracker`

优点：

- 明确支持 `Private & Whitelisted mode`
- 支持 `UDP`、`HTTP`、`TLS`
- 有 `Tracker Management API`
- 有 Docker 运行方式
- 项目仍在活跃开发
- 整体工程化程度较高，文档也相对完整

缺点：

- 当前持久化主打 `SQLite3 / MySQL`
- 官方路线图里才提到后续支持 `PostgreSQL`
- 许可证是 `AGPL-3.0`

适合场景：

- 想要一个现代、独立、可容器化部署的 Tracker
- 希望站点和 Tracker 服务解耦
- 可以接受 AGPL 许可证

结论：

- 这是目前最值得优先评估的独立 Tracker 候选

#### 方案 B：`Mochi`

项目：

- `https://github.com/sot-tech/mochi`

优点：

- 是 Chihaya 的增强分支
- 支持 `PostgreSQL`、`KeyDB`、`LMDB`
- 支持 `BittorrentV2`
- 明确提到目标之一是做 `semi-private tracker`
- 发布相对较新
- `BSD-2-Clause` 许可证更宽松

缺点：

- 社区规模明显小于 Torrust / Chihaya
- 更偏“可改造的 tracker 核心”，不是开箱即用的完整私有站方案
- 你仍然需要自己对接用户 `passkey`、允许列表、状态同步

适合场景：

- 你很在意 `PostgreSQL` 兼容
- 能接受“拿现成核心 + 做一定二改集成”
- 想避免 AGPL

结论：

- 如果你非常想要 `PostgreSQL`，它是一个值得认真看的候选

#### 方案 C：`XBT Tracker`

项目：

- `https://github.com/OlafvdSpek/xbt`
- `https://xbtt.sourceforge.net/tracker/`

优点：

- 老牌高性能纯 Tracker
- 明确支持私有站常见的 `torrent_pass` / `passkey` 模式
- 可关闭匿名 announce，只允许 `xbt_users` 表中的用户
- 可关闭自动注册，只追踪 `xbt_files` 表中的白名单 torrent
- 使用 `MySQL`，对传统私有站模式很友好
- 主站与 Tracker 分离的架构很自然

缺点：

- 工程化和文档风格较老
- 更偏传统部署，不如现代项目那样开箱即用
- 没有我目前看到的现代管理 API 体验
- 许可证是 `GPL-3.0`

适合场景：

- 用户规模不大
- 接受 `MySQL`
- 希望主站自己做，Tracker 用老牌成熟方案
- 可以接受“主站同步表数据到 Tracker”这种集成方式

结论：

- 如果用户规模在几百人以内，且接受 `MySQL`，它会成为非常现实的候选

#### 方案 D：`opentracker`

项目：

- `https://erdgeist.org/arts/software/opentracker/`

优点：

- 非常轻量
- 资源占用低
- 支持白名单模式
- 2025-01-01 发布了 `v1.0`
- 已支持同一 Tracker 返回 IPv4 / IPv6 peers

缺点：

- 更偏底层和极简
- 白名单控制主要基于 access list 文件
- 对“用户 passkey + 站点账号体系 + 管理后台联动”不够友好
- 二改和运维体验没有现代项目顺手

适合场景：

- 只想要一个极简高性能 Tracker
- 不介意通过文件或额外脚本管理允许列表

结论：

- 适合极简部署，不太适合你这个“站点账号体系绑定”的方案

#### 方案 E：`Chihaya`

项目：

- `https://github.com/chihaya/chihaya`

优点：

- 中间件和存储扩展思路清楚
- 支持 HTTP / UDP
- 支持 Redis 高可用
- 适合嵌入已有生产环境

缺点：

- 官方仓库最新 release 显示为 `2017-06-09`
- 更像“给开发者做二次集成的 tracker 框架”
- 如果做私有站，你仍要补很多自己的权限逻辑

补充：

- 有第三方项目 `https://github.com/mrd0ll4r/chihaya-privtrak-middleware`
- 但它自己明确说明“不负责检查用户是否允许 announce，也不检查 infohash 是否白名单”

结论：

- 不是不能用，但对于这个项目来说不如 `Torrust Tracker` 或 `Mochi` 直接

#### 不建议作为本项目主方案的“整站框架”

下面这类项目更像“完整 PT 站系统”，不太符合本项目“只做 RSS / 浏览 / 下载 / 多用户 private tracker”的轻量目标：

- `UNIT3D`: `https://github.com/HDInnovations/UNIT3D`
- `Gazelle`: `https://whatcd.github.io/Gazelle/`
- `Trackarr`: `https://github.com/florianjs/trackarr`

原因：

- 功能普遍偏重
- 带较多社区化功能和规则
- 技术路线不一定与你的既定前后端选型一致
- 二次裁剪的工作量可能不比“主站自己做 + 外挂独立 Tracker”更小

### 7.7 推荐决策

结合你目前的目标，我建议按这个优先级判断：

1. `XBT Tracker`：如果用户规模大约在 `200` 人以内，接受 `MySQL`，并且希望采用老牌稳定的纯 Tracker
2. `Torrust Tracker`：如果你更看重现代化、Docker 友好、私有和白名单模式、管理 API
3. `Mochi`：如果你后续又重新偏向 `PostgreSQL`，并愿意接受一定程度的二次集成
4. `opentracker`：如果你只追求极简高性能，不在意账号体系联动体验

当前最现实的实施方式建议为：

1. 主站自己做：用户、权限、资源、RSS、下载种子
2. Tracker 直接采用现成项目
3. 主站在用户下载 torrent 时注入对应 announce 地址
4. 主站通过配置、白名单、API 或同步脚本，把 torrent / passkey / 用户状态同步给 Tracker

按你现在补充的条件：

- 分流人员最多约 `200` 人
- `MySQL` 完全可接受
- 不想自己写 Tracker

那么推荐会进一步收敛为：

1. `XBT Tracker + MySQL`
2. `Torrust Tracker + MySQL`

其中：

- 如果你更重视“老牌、直接、贴近传统私有站接法”，优先 `XBT`
- 如果你更重视“现代化部署体验和后续扩展”，优先 `Torrust`

## 8. RSS 设计建议

### 8.1 RSS 类型

建议首期提供三类：

- 全量最新资源 RSS
- 按分类 RSS
- 按标签 RSS

### 8.2 访问方式

推荐格式：

- `/rss/all?token=xxx`
- `/rss/category/{slug}?token=xxx`
- `/rss/tag/{slug}?token=xxx`

或使用 path 风格：

- `/rss/{token}/all`
- `/rss/{token}/category/{slug}`

### 8.3 RSS 条目字段

每条建议包含：

- 标题
- 发布时间
- 描述摘要
- 分类
- 下载链接
- `guid`

### 8.4 安全要求

- RSS 地址与用户绑定
- 支持手动重置 RSS Token 或 `passkey`
- 对高频访问做简单限流
- 页面明确提醒“RSS 地址不要分享”

## 9. 下载种子设计

### 9.1 推荐策略

站内不直接把“原始上传 torrent”暴露给用户，而是：

1. 保存一个基础 torrent 模板
2. 用户点击下载时，服务端动态注入该用户的 announce 地址
3. 返回一个专属 torrent 文件

这样做的好处：

- 可以与用户身份绑定
- 方便封禁与追踪
- 旧 `passkey` 失效后，旧 torrent 同步失效

### 9.2 下载接口建议

- `GET /releases/{id}/download`

行为：

- 校验登录态
- 校验资源状态
- 记录下载日志
- 返回个性化 torrent 文件

### 9.3 文件存储建议

可选方案：

- 本地磁盘存储
- 对象存储（S3 / MinIO）

对于内部站点首期：

- 本地磁盘即可
- 后期若迁移方便，再切对象存储

## 10. 权限与安全设计

### 10.1 认证

- 账号密码登录
- 密码哈希使用安全算法
- 登录态使用服务端 Session 或安全 JWT

### 10.2 授权

- 基于角色的简单 RBAC
- 页面级和接口级同时鉴权

### 10.3 安全控制

- 全站 HTTPS
- 登录限流
- 下载接口限流
- RSS 限流
- Tracker announce 基础限流
- 关键操作写审计日志

### 10.4 内部站点额外建议

- 只允许管理员建号
- 可选内网/VPN 白名单
- 可选只允许特定邮箱域

## 11. 推荐技术方案

后端架构、模块拆分、认证权限、XBT 集成、日志与测试的详细设计，见：

- `docs/backend-architecture-spec.md`
- `docs/database-xbt-mapping-spec.md`
- `docs/docker-compose-deployment-spec.md`
- `docs/xbt-container-integration-spec.md`

### 11.1 整体建议

根据当前需求和你的偏好，推荐采用：

- 前端：`Vue 3 + Vite + TailwindCSS`
- 后端：`Python + Django`
- 数据库：`MySQL 8`
- 缓存：`Redis`
- 部署：`Docker Compose`
- 反向代理：`Nginx` 或 `Caddy`
- Tracker：`XBT`

推荐架构为“前后端分离 + 独立 Tracker 服务”的模式，原因是：

- 前端交互和样式可以做得更轻快
- 主站后端可以专注在权限、资源、RSS、下载、后台管理
- Tracker 已交给 `XBT`，主站不需要自己扛 announce 热路径
- Django 非常适合内部系统、后台管理和角色权限模型
- 结构仍然足够简单，不会演变成一堆微服务
- Docker 化后，本地开发和线上部署都更容易统一

建议首期保持以下边界：

- 一个 `frontend` 容器
- 一个 `backend` 容器
- 一个 `mysql` 容器
- 一个 `redis` 容器
- 一个 `xbt` 容器
- 一个 `nginx` 容器

这样已经足够支撑内部字幕组站点，不需要一开始就拆微服务或上 Kubernetes。

### 11.2 推荐技术栈

推荐首选组合：

- 前端：`Vue 3`
- 构建工具：`Vite`
- 样式：`TailwindCSS`
- 状态管理：`Pinia`
- 路由：`Vue Router`
- 后端框架：`Django 5 + Django REST Framework`
- API 文档：`drf-spectacular + Swagger UI`
- 认证：`Django Auth + Session`，必要时补充 Token
- ORM：`Django ORM`
- 任务队列：`Celery` 或 `Django-Q`（二期可选）
- 数据库：`MySQL 8`
- 缓存与短期状态：`Redis`
- 反向代理：`Nginx` 或 `Caddy`
- 容器编排：`Docker Compose`
- 文件存储：本地磁盘起步，后续可切 `MinIO`

推荐原因：

- `Django` 自带成熟的认证、权限、管理后台和 ORM
- `DRF` 很适合统一输出 API，方便前端和管理工具接入
- `drf-spectacular + Swagger UI` 可以直接生成类似你希望的 API 展示页
- `Vue + TailwindCSS` 很适合快速搭建后台和资源列表类页面
- `MySQL 8` 在这种规模下完全够用，尤其适合与 `XBT` 这类 Tracker 搭配
- `Redis` 很适合做登录会话、限流、热点缓存、短期 peer 状态缓存
- `Docker Compose` 很适合单机或小规模服务器部署

建议后端模块拆分：

- `auth`: 登录、权限、用户管理
- `release`: 资源、分类、标签、上传
- `rss`: RSS 输出与鉴权
- `torrent`: torrent 解析、announce 注入、下载
- `tracker_sync`: 同步 `XBT` 用户、`passkey`、torrent 白名单、禁用状态
- `audit`: 审计日志
- `api_docs`: OpenAPI schema 与 Swagger UI

建议前端模块拆分：

- `site`: 首页、列表、详情、RSS、我的账户
- `upload`: 上传资源页
- `admin`: 用户管理、资源管理、分类标签、公告、日志

### 11.3 如果团队更偏前端

如果你们团队有人熟悉 Dart，也可以考虑：

- 后端：`Dart + Shelf` 或 `Dart Frog`
- 前端：`Vue 3 + TailwindCSS`
- 数据库：`MySQL 8` 或 `PostgreSQL`

但当前项目我更推荐 `Python + Django` 作为首选，原因是：

- 你已经决定不自己写 Tracker，而是接 `XBT`
- 主站的核心复杂度转移到了“后台、权限、上传、RSS、下载、同步”
- Django 在内部系统、管理后台、角色权限、API 文档上更省时
- `Dart` 做后台不是不能做，但这类后台系统生态还是不如 Django 成熟

如果你提到 `C`，从性能角度当然很强，但不建议作为这个项目的主后端语言，原因是：

- 开发效率低
- 安全成本高
- Web 框架和后台基础设施生态弱
- 维护难度明显高于 `Python` 和 `Rust`

结论：

- `Python + Django` 是首选
- `Rust` 可以作为有明确性能热点时的局部增强方案
- `Dart` 可以作为团队偏好型备选
- `C` 不建议作为站点主后端

### 11.4 数据库建议

数据库这里不建议为了“先进”而盲目追新，更重要的是“稳定、成熟、并发能力强、运维方便”。

对于这个项目，数据库不需要“最先进”，而需要“最顺手、最稳定、最适合当前 Tracker 方案”。

在你现在给出的约束下：

- 分流人员最多约 `200` 人
- 不需要超大规模横向扩展
- 直接采用 `MySQL 8`

那么推荐改为：

- 主库：`MySQL 8`
- 缓存：`Redis`

为什么这样更合适：

- 这类站点真正的大流量在 P2P 传输，不在站点数据库
- 数据库主要承载的是用户、资源元数据、下载日志、Tracker 基础记录
- `200` 人规模下，`MySQL 8` 完全够用
- 如果 Tracker 选 `XBT`，用 `MySQL` 会明显减少集成复杂度
- 如果站点和 Tracker 都能围绕同类数据库工作，运维会更省心

补充建议：

- 如果你后续选择 `Torrust`，也可以继续使用 `MySQL`
- 如果后续改用 `Mochi`，再评估是否切到 `PostgreSQL`
- 现在没必要为了“未来可能会大”而先把数据库复杂化

推荐索引思路：

- `users(username)` 唯一索引
- `users(passkey)` 唯一索引
- `releases(infohash)` 唯一索引
- `releases(status, published_at)` 复合索引
- `downloads(user_id, downloaded_at)` 索引
- `tracker_peers(release_id, last_announce_at)` 索引
- `tracker_peers(user_id, release_id)` 索引

如果后期 Tracker 压力明显升高，可以这样增强：

- 高频在线 peer 状态先放 `Redis`
- 定时批量刷回主库
- 对 `tracker_peers` / `downloads` 做按月分区
- 把统计报表单独做物化视图或离线聚合

这一步通常已经足够，不需要一开始就上 `TiDB`、`CockroachDB`、`ScyllaDB` 之类更重的方案。

当前推荐结论：

- 如果 Tracker 选 `XBT`：优先 `MySQL`
- 如果 Tracker 选 `Torrust`：优先 `MySQL`
- 如果 Tracker 选 `Mochi`：再考虑 `PostgreSQL`

### 11.5 Docker 部署建议

推荐首期部署形态：

- `frontend`: Vue 构建产物 + Nginx 静态服务
- `backend`: Django API 服务
- `mysql`: 主数据库
- `redis`: 缓存和限流
- `xbt`: 独立 Tracker 服务
- `nginx`: 统一入口、HTTPS、反代、下载头处理

建议目录结构：

- `frontend/`
- `backend/`
- `tracker/`
- `deploy/docker-compose.yml`
- `deploy/nginx/`
- `deploy/env/`

建议容器职责：

- 前端容器只负责静态资源
- 后端容器负责 API、RSS、下载、后台管理和 XBT 同步
- XBT 容器只负责 Tracker announce / scrape
- Nginx 负责 HTTPS、反代、限流、基础安全头
- MySQL 和 Redis 做独立持久化卷

上线时建议至少配置：

- `mysql` 数据卷
- torrent 文件存储卷
- 日志卷
- 环境变量文件
- 自动重启策略
- 定时备份任务

### 11.6 API 文档页面建议

如果你希望站点提供一个“展示全部 API 并支持在线调试”的页面，推荐直接使用：

- `Django REST Framework`
- `drf-spectacular`
- `Swagger UI`

推荐路由：

- `/api/schema/`: 输出 OpenAPI Schema
- `/api/swagger/`: Swagger UI 页面
- `/api/docs/`: 可选，后续如需 ReDoc 再补

建议展示的接口分组：

- `auth`: 登录、登出、修改密码、当前用户
- `releases`: 列表、详情、上传、编辑、隐藏
- `rss`: 全量 RSS、分类 RSS、标签 RSS
- `downloads`: 下载个性化 torrent
- `admin-users`: 用户管理、禁用、重置 passkey
- `tracker-sync`: 同步 XBT 用户和 torrent 白名单

这样做的好处：

- 前端对接时能直接看到接口定义
- 后台联调更快
- 文件上传接口也可以在 Swagger UI 中调试
- 后续如果开放给内部脚本使用，也有统一文档入口

### 11.7 日志输出建议

Docker 部署后，日志的最低要求不是“做得多漂亮”，而是：

- 每个容器都必须稳定输出日志
- 默认可以通过 `docker logs` 直接看到日志
- 出问题时能快速区分是 `backend`、`xbt`、`nginx`、`mysql`、`redis` 还是 `frontend`

首期最低标准：

- 所有服务优先输出到 `stdout` / `stderr`
- 不依赖只写容器内文件的方式
- `docker compose logs -f` 能直接看到完整日志
- 每条日志至少包含时间、服务名、级别、核心消息

推荐日志策略：

- `backend(Django)`: 使用 Python `logging`，默认输出到标准输出
- `nginx`: `access_log` 指向 stdout，`error_log` 指向 stderr
- `frontend`: 仅静态站点时主要依赖 Nginx 访问日志和错误日志
- `xbt`: 如果程序原生支持 stdout/stderr，直接输出；如果默认写文件，则在容器入口脚本中转发到 stdout
- `mysql`: 使用官方容器默认日志输出方式，确保启动失败、连接失败、崩溃信息能被 `docker logs` 捕获
- `redis`: 使用官方容器默认日志输出方式，确保启动和连接类错误可见

日志级别建议：

- 首期至少支持 `INFO` 和 `ERROR`
- 如能区分 `DEBUG` / `INFO` / `WARN` / `ERROR` 更好
- 生产环境默认 `INFO`
- 本地开发环境默认 `DEBUG`

建议记录的关键日志：

- 用户登录、登出、登录失败
- 资源上传成功、上传失败、torrent 校验失败
- RSS 请求异常
- 下载 torrent 成功、下载失败、权限拒绝
- `XBT` 同步成功、同步失败、重试
- 管理员禁用用户、重置 `passkey`
- Nginx `4xx` / `5xx`
- 容器启动失败、数据库连接失败、Redis 连接失败

不建议的方式：

- 只写容器内部临时文件，不输出到 stdout
- 多个服务混用同一个无前缀日志文件
- 日志里输出明文密码、完整 token、完整 passkey

二期增强建议：

- 增加 JSON 结构化日志
- 增加请求 ID / trace ID
- 对接 Loki、ELK 或其他日志聚合系统
- 增加后台日志检索页或错误告警

### 11.8 镜像构建与分发建议

考虑到部署便利性，推荐默认采用：

- `GitHub Actions` 负责构建镜像
- 镜像推送到 `GitHub Container Registry (ghcr.io)`
- 服务器上的 `docker compose` 直接使用固定镜像地址

推荐原因：

- 服务器不需要再本地构建镜像
- 部署机器依赖更少
- 版本更清楚，回滚更方便
- 更符合“少步骤、少环境差异”的目标

推荐镜像来源：

- `ghcr.io/<owner>/<repo>/frontend:<tag>`
- `ghcr.io/<owner>/<repo>/backend:<tag>`

推荐标签策略：

- `latest`：仅用于开发或测试环境
- `main-<short_sha>`：用于日常构建
- `v1.0.0`：用于正式版本发布

推荐 Compose 用法：

- 生产环境优先使用 `image`
- 本地开发环境才使用 `build`

示例思路：

- `docker-compose.yml` 里直接写 `image`
- 如需本地开发，再额外提供 `docker-compose.dev.yml`

这样可以避免：

- 服务器本地还要装完整构建环境
- 因为本地 Dockerfile 或缓存差异导致部署结果不一致
- 部署文档变得过长

当前项目推荐做法：

1. 推送代码到 GitHub
2. GitHub Actions 自动构建 `frontend` 与 `backend` 镜像
3. 推送到 `ghcr.io`
4. 服务器执行 `docker compose pull`
5. 服务器执行 `docker compose up -d`

注意：

- `mysql`、`redis`、`nginx`、`xbt` 通常可以继续使用现成镜像或本地少量定制镜像
- 主要需要进入 GitHub 镜像构建流程的是 `frontend` 与 `backend`

## 12. 接口草案

### 12.1 认证接口

- `POST /auth/login`
- `POST /auth/logout`
- `POST /auth/change-password`

### 12.2 资源接口

- `GET /releases`
- `GET /releases/{id}`
- `POST /releases` (`uploader` / `admin`)
- `PUT /releases/{id}` (`owner` / `admin`)
- `POST /releases/{id}/hide` (`admin`)
- `GET /releases/{id}/download`

### 12.3 RSS 接口

- `GET /rss/all`
- `GET /rss/category/{slug}`
- `GET /rss/tag/{slug}`

说明：

- 可以走 session，也可以走 token/passkey
- 更推荐 token/passkey 形式，方便下载器使用

### 12.4 用户管理接口

- `GET /admin/users`
- `POST /admin/users`
- `PUT /admin/users/{id}`
- `POST /admin/users/{id}/disable`
- `POST /admin/users/{id}/reset-passkey`

### 12.5 XBT 集成接口

主站不自己实现 Tracker 的 `announce` / `scrape`，这部分由 `XBT` 独立承担。

主站需要的接口更偏向“同步与管理”：

- `POST /admin/tracker-sync/users/{id}`
- `POST /admin/tracker-sync/releases/{id}`
- `POST /admin/tracker-sync/full`
- `POST /admin/tracker-sync/users/{id}/disable`

说明：

- 用于把用户 `passkey`、禁用状态同步到 `XBT`
- 用于把允许下载的 torrent / `infohash` 同步到 `XBT`
- 可以做成后台手动触发，也可以在保存后自动触发

### 12.6 API 文档接口

- `GET /api/schema/`
- `GET /api/swagger/`

说明：

- `/api/schema/` 提供 OpenAPI Schema
- `/api/swagger/` 提供 Swagger UI 页面

## 13. MVP 开发范围

### 13.1 MVP 必须闭环

MVP 上线前必须打通以下闭环：

1. 管理员能创建用户
2. 上传者能上传资源和 torrent
3. 用户能浏览资源列表和详情
4. 用户能获取个人 RSS
5. 用户能下载个性化 torrent
6. Tracker 能识别用户并返回 peers

### 13.2 MVP 页面清单

- 登录页
- 首页/最新资源页
- 资源详情页
- RSS 页面
- 我的账户页
- 上传页
- 后台用户管理页
- 后台资源管理页

## 14. 任务清单

说明：

- 截至 `2026-04-08`，本轮同时标记已完成的后端能力与前端页面骨架进度
- 当前前端页面、权限、布局与导航已在 `frontend/` 中落地，并通过本地构建验证
- 前端当前仍基于 `Mock` 服务层，真实 `Django/DRF` 接口接入待后续继续推进

### 14.1 产品与设计

- [x] 明确站点名称、Logo、主色调
- [ ] 明确资源分类体系
- [ ] 明确资源标题命名规范
- [x] 明确上传表单字段
- [x] 明确首页列表展示字段
- [ ] 输出低保真页面草图
- [x] 定义管理员后台导航结构

### 14.2 账户与权限

- [x] 实现登录/登出
- [x] 实现密码修改
- [x] 实现三角色权限中间件
- [x] 实现管理员创建用户
- [x] 实现用户禁用/启用
- [x] 实现 `passkey` 生成与重置
- [x] 实现账户状态页

### 14.3 资源管理

- [x] 实现资源列表接口
- [x] 实现资源详情接口
- [x] 实现分类筛选接口
- [x] 实现标签筛选接口
- [x] 实现关键词搜索接口
- [x] 实现上传资源表单
- [x] 实现 torrent 文件校验
- [x] 实现文件列表解析
- [x] 实现重复 `infohash` 校验
- [x] 实现资源编辑与隐藏

### 14.4 前端页面与权限

- [x] 搭建 `Vue Router`
- [x] 搭建 `Pinia`
- [x] 实现 `AuthLayout`
- [x] 实现 `SiteLayout`
- [x] 实现 `AdminLayout`
- [x] 实现前台顶部导航
- [x] 实现后台侧边导航
- [x] 实现路由守卫
- [x] 实现基于角色的菜单显示
- [x] 实现页面级权限控制
- [x] 实现组件级按钮权限控制
- [x] 实现 `/403` 页面
- [x] 实现 `/404` 页面
- [x] 实现统一的 `loading / empty / error` 状态组件
- [x] 实现登录态初始化与 `/auth/me` 同步

### 14.5 RSS 模块

- [x] 实现全量 RSS
- [x] 实现分类 RSS
- [x] 实现标签 RSS
- [x] 实现 RSS Token / `passkey` 鉴权（当前为 `passkey`）
- [x] 实现 RSS 页面与复制入口
- [ ] 实现 RSS 访问限流

### 14.6 下载模块

- [x] 实现个性化 torrent 下载接口
- [x] 实现下载日志记录
- [x] 实现下载权限校验
- [x] 实现基础 torrent 存储
- [x] 实现 announce 地址动态注入

### 14.7 XBT 集成模块

- [x] 设计主站与 `XBT` 的同步策略
- [x] 实现用户 `passkey` / `torrent_pass` 生成规则
- [x] 实现 `xbt_users` 同步
- [x] 实现 `xbt_files` 白名单同步
- [x] 实现禁用用户状态同步
- [x] 实现资源发布后自动同步到 `XBT`
- [x] 实现 `passkey` 重置后的 `XBT` 同步
- [x] 实现同步失败日志与手动重试入口

### 14.8 后台管理

- [x] 实现用户列表接口
- [x] 实现用户详情接口
- [x] 实现资源管理接口
- [x] 实现分类管理接口
- [x] 实现标签管理接口
- [x] 实现公告管理接口
- [x] 实现审计日志接口

### 14.9 工程与部署

- [x] 初始化项目结构
- [x] 初始化 `frontend` 与 `backend` 目录
- [ ] 配置开发环境
- [x] 配置数据库迁移
- [ ] 配置 Redis
- [x] 配置文件存储目录
- [ ] 配置环境变量模板
- [ ] 提供尽量开箱即用的 `.env.example`
- [ ] 控制 MVP 必填环境变量数量
- [ ] 编写 `docker-compose.yml`
- [ ] 编写 GitHub Actions 镜像构建工作流
- [ ] 配置镜像推送到 `ghcr.io`
- [ ] 约定 `frontend` / `backend` 镜像标签策略
- [ ] 编写前端 Dockerfile
- [ ] 编写后端 Dockerfile
- [ ] 编写 `XBT` 容器与配置文件
- [x] 配置 `Django REST Framework`
- [x] 配置 `drf-spectacular`
- [x] 配置 Swagger UI 路由
- [ ] 配置 Nginx 反代
- [ ] 配置 HTTPS
- [x] 配置 Django 标准输出日志
- [ ] 配置 Nginx access/error 标准输出日志
- [ ] 配置 `XBT` 日志输出到 Docker 标准日志
- [ ] 验证 `mysql` / `redis` 容器日志可通过 `docker logs` 查看
- [ ] 配置容器日志前缀与基础级别
- [ ] 配置日志与错误监控
- [ ] 验证 `docker compose up -d` 能按文档拉起整套服务
- [ ] 验证 `docker compose pull && docker compose up -d` 可完成更新
- [ ] 配置备份策略

### 14.10 测试与验收

- [x] 编写登录权限测试
- [x] 编写资源上传测试
- [x] 编写 RSS 输出测试
- [x] 编写下载接口测试
- [ ] 编写 `XBT` 同步测试
- [ ] 编写 `passkey` 重置测试
- [ ] 编写后台权限测试
- [ ] 编写 API Schema / Swagger 页面测试
- [ ] 验证所有容器在 Docker 中都有可读日志输出
- [ ] 做一次完整上线前走查

## 15. 开发阶段建议

### 阶段 1：基础框架

目标：

- 跑起项目
- 完成用户模型、角色权限、Django 基础后台

建议交付：

- 登录
- 用户管理
- 分类/标签模型
- Django Admin 基础配置
- Swagger UI 基础页面
- Vue 路由骨架
- 三套布局骨架
- 路由权限守卫
- 基础页面框架

### 阶段 2：资源发布与浏览

目标：

- 完成资源上传、列表、详情

建议交付：

- 上传页
- 列表页
- 详情页
- 菜单权限控制
- 组件级按钮权限控制
- 搜索和筛选

### 阶段 3：RSS 与下载闭环

目标：

- 让用户能完成“看见资源 -> 订阅 -> 下载”

建议交付：

- RSS 页面
- RSS 输出
- 个性化 torrent 下载

### 阶段 4：XBT 集成 MVP

目标：

- 让下载器真正能够接入并完成内部分流

建议交付：

- `xbt_users` 同步
- `xbt_files` 同步
- `passkey` / `torrent_pass` 联动
- 用户禁用联动

### 阶段 5：上线加固

目标：

- 做安全、日志、备份、监控

建议交付：

- 限流
- 审计日志
- 错误监控
- 备份方案

## 16. MVP 验收标准

满足以下条件即可视为 MVP 可上线：

- 管理员可创建三类用户并正常登录
- 上传者可发布资源并成功展示在列表中
- 用户可查看详情并下载专属 torrent
- 用户可获取自己的 RSS 并在下载器中正常使用
- 下载器可通过 `XBT` 的 announce 接口拿到 peers
- 禁用用户后其 RSS、下载和 Tracker 都会失效
- 所有 Docker 容器都能通过标准日志输出关键运行信息

## 17. 风险与注意事项

### 17.1 产品风险

- 如果一开始把 PT 规则做复杂，会明显拖慢开发
- 如果上传字段设计过多，上传者会觉得繁琐
- 如果权限边界不清，后续维护成本会变高

### 17.2 技术风险

- Tracker 协议处理需要认真做参数校验
- 动态生成 torrent 时要保证 announce 注入稳定
- `passkey` 泄露会导致身份冒用，因此必须支持重置

### 17.3 运维风险

- 内部站点也需要 HTTPS
- 文件和数据库要做备份
- 如果容器不输出标准日志，问题排查成本会非常高
- 日志中不要明文暴露敏感 token

## 18. 建议的下一步

建议按照下面顺序继续推进：

1. 先确认这份文档中的功能边界是否符合你们字幕组实际流程
2. 确认技术栈，优先决定是否采用 `Django + DRF + Vue + XBT + MySQL + Redis + Docker`
3. 先画出 6 个核心页面低保真图
4. 然后按“阶段 1 -> 阶段 4”推进 MVP
5. Tracker 不做复杂规则，先保证可用

---

如果后续要正式开工，这份文档可以直接继续拆成：

- `产品需求文档 PRD`
- `数据库设计文档`
- `API 文档`
- `前端页面任务单`
- `后端开发任务单`

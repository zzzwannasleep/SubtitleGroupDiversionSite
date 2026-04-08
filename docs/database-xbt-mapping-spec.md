# 数据库与 XBT 字段映射文档

## 1. 文档目标

这份文档专门定义：

- 主站数据库与 `XBT` 相关表的关系
- 哪些字段由 Django 主站维护
- 哪些字段由 `XBT` 维护
- 什么时候同步
- 同步失败如何补偿

目标是避免后续开发时出现这些混乱：

- 主站和 `XBT` 都改同一份字段
- 不清楚哪个字段是谁的事实来源
- `passkey`、`torrent_pass`、`infohash` 各用各的
- 用户禁用或资源隐藏后，`XBT` 没有同步失效

## 2. 设计前提

当前方案前提：

- 主站：`Django + DRF + MySQL 8`
- Tracker：`XBT`
- `XBT` 独立一个容器
- 主站与 `XBT` 使用同一个 `MySQL` 实例
- 主站负责同步用户和 torrent 白名单

## 3. 信息来源与边界

基于 `XBT` 官方文档，我们可以明确确认：

- `XBT` 使用 `MySQL`
- `XBT` 读取 `xbt_tracker.conf` 和 `xbt_config`
- `anonymous_announce=0` 时，用户必须存在于 `xbt_users`
- `xbt_users.torrent_pass` 是 32 字符的唯一标识
- announce URL 中会携带同样的 `torrent_pass`
- `auto_register=0` 时，torrent 必须存在于 `xbt_files`
- 官方文档给出了向 `xbt_files` 写入 `info_hash / mtime / ctime` 的示例

基于这些官方信息，当前文档采用以下策略：

- 对 `xbt_users.torrent_pass`
- 对 `xbt_files.info_hash / flags / mtime / ctime`

做明确映射设计。

对于 `xbt_tracker.sql` 中其他字段：

- 本文只做“推荐映射与所有权约定”
- 最终上线前应以实际打包进镜像的 `xbt_tracker.sql` 为准再次核对

这是一个明确的工程约束。

## 4. 主站数据库事实来源

以下数据以主站数据库为唯一事实来源：

- 用户账号
- 用户角色
- 用户状态
- 用户 `passkey`
- 资源标题、副标题、简介
- 分类与标签
- 资源是否发布/隐藏
- 资源原始 torrent 文件
- 资源 `infohash`
- 下载日志
- 审计日志

换句话说：

- `XBT` 不是用户中心
- `XBT` 不是资源中心
- `XBT` 只是 Tracker 执行层

## 5. XBT 数据库事实来源

以下数据可以视为由 `XBT` 主导或运行期维护：

- 当前 seeders / leechers
- completed 统计
- announce 运行记录
- 用户-种子运行期关系

这些数据可以由主站读取，但不建议主站把自己变成它们的主写入方。

## 6. 主站表与 XBT 表关系总览

建议核心映射如下。

主站表：

- `users`
- `releases`
- `downloads`
- `audit_logs`

XBT 表：

- `xbt_users`
- `xbt_files`
- `xbt_files_users`
- `xbt_announce_log`

推荐关系理解：

- `users` <-> `xbt_users`
- `releases` <-> `xbt_files`
- `users + releases` <-> `xbt_files_users`

## 7. 用户映射

### 7.1 主站用户字段

主站 `users` 建议保留：

- `id`
- `username`
- `role`
- `status`
- `passkey`
- `created_at`
- `updated_at`

其中对接 `XBT` 最关键的是：

- `id`
- `status`
- `passkey`

### 7.2 XBT 用户关键字段

根据 `XBT` 官方文档，当前我们明确依赖：

- `xbt_users.torrent_pass`

推荐同时在你们实际版本的 `xbt_tracker.sql` 中核对：

- 用户主键字段
- 用户启用/禁用相关字段
- 汇总上传下载字段

这里的工程建议是：

- 主站保存 `passkey`
- 默认将 `passkey` 作为 `torrent_pass` 写入 `xbt_users`

### 7.3 映射规则

推荐映射：

- `users.id` -> `xbt_users` 的用户主键字段
- `users.passkey` -> `xbt_users.torrent_pass`
- `users.status=active` -> `xbt_users` 中为可用状态
- `users.status=disabled` -> `xbt_users` 中为禁用状态或直接移除访问能力

这里有一个明确选择：

- 不再额外生成第二套 tracker pass
- 主站 `passkey` 就是 `XBT` 用的 `torrent_pass`

这样可以减少复杂度。

### 7.4 用户同步触发时机

这些时机必须同步 `xbt_users`：

- 新建用户
- 禁用用户
- 启用用户
- 重置 `passkey`
- 手动全量同步

## 8. 资源映射

### 8.1 主站资源字段

主站 `releases` 里，与 `XBT` 对接最关键的是：

- `id`
- `infohash`
- `status`
- `published_at`
- `created_at`

### 8.2 XBT 资源关键字段

根据 `XBT` 官方文档，当前明确依赖：

- `xbt_files.info_hash`
- `xbt_files.flags`
- `xbt_files.mtime`
- `xbt_files.ctime`

官方文档示例说明：

- 新增 torrent 时向 `xbt_files` 写入 `info_hash, mtime, ctime`
- 删除 torrent 时更新 `flags = 1`

### 8.3 映射规则

推荐映射：

- `releases.infohash` -> `xbt_files.info_hash`
- 资源首次发布 -> 向 `xbt_files` 插入记录
- 资源隐藏/禁用 -> 对应 `xbt_files.flags = 1`
- 资源重新启用 -> 重新写入或恢复白名单状态

### 8.4 时间字段建议

推荐：

- `xbt_files.ctime` 使用资源首次进入白名单的时间
- `xbt_files.mtime` 使用最近一次同步更新时间

这里我明确说明：

- 这是结合官方示例做出的实现建议
- 最终以实际 `XBT` 版本行为为准

## 9. 下载与运行期关系映射

### 9.1 主站下载日志

主站 `downloads` 负责：

- 记录谁下载了哪个个性化 torrent
- 记录下载时间
- 记录 IP / UA（如需要）

### 9.2 XBT 运行期关系

`xbt_files_users` 和 `xbt_announce_log` 更偏运行期统计。

建议：

- 主站不把它们作为主事实来源
- 主站如需展示统计，可读取它们或做聚合
- 不建议在 MVP 主站中直接写这些运行期统计表

原因：

- 这部分更适合由 `XBT` 自己维护
- 否则主站会和 Tracker 形成职责冲突

## 10. 同步方向与单向原则

建议坚持：

- 主站 -> XBT 为主同步方向

具体来说：

- 用户数据由主站推送到 `xbt_users`
- torrent 白名单由主站推送到 `xbt_files`

不建议：

- 由 `XBT` 反向覆盖主站用户状态
- 由 `XBT` 反向决定资源是否可见

读取方向可以是双向：

- 主站可以读取 `XBT` 的统计信息用于展示

但写入方向应主要保持单向：

- 主站写入
- XBT 运行

## 11. 同步动作明细

### 11.1 新建用户

动作：

1. 主站创建 `users`
2. 生成 32 字符 `passkey`
3. 写入 `xbt_users`
4. 写审计日志

### 11.2 禁用用户

动作：

1. 主站将 `users.status` 设为 `disabled`
2. 同步 `xbt_users`
3. 使旧 torrent / RSS 失效
4. 写审计日志

### 11.3 重置 passkey

动作：

1. 主站生成新 `passkey`
2. 更新 `users.passkey`
3. 同步 `xbt_users.torrent_pass`
4. 旧 RSS 与旧 torrent 失效
5. 写审计日志

### 11.4 发布资源

动作：

1. 主站解析 torrent
2. 得到 `infohash`
3. 创建 `releases`
4. 写入 `xbt_files`
5. 写审计日志

### 11.5 隐藏资源

动作：

1. 主站将 `releases.status` 标记为 `hidden`
2. 更新 `xbt_files` 白名单状态
3. 写审计日志

## 12. 推荐字段生成规则

### 12.1 `passkey`

建议：

- 使用 32 位十六进制字符串

原因：

- `XBT` 官方文档明确提到 `torrent_pass` 为 32 字符

### 12.2 `infohash`

建议：

- 使用 torrent 标准 `info_hash`
- 数据库存储时统一大小写与编码策略

推荐：

- 在主站统一存 hex 字符串
- 写入 `XBT` 时按所需格式转换

这里明确说明：

- 是否以 binary(20) 还是 hex 字符串写入 `XBT`，必须根据实际 `xbt_tracker.sql` 核对
- 这一步在实现前必须再次确认

## 13. 删除与失效策略

推荐规则：

- 用户禁用：立即失效，不做软忽略
- `passkey` 重置：立即失效旧值
- 资源隐藏：立即从白名单移除或标记删除

推荐不要做：

- 延迟很久才同步
- 用户禁用后旧 torrent 还能继续用
- 资源隐藏后 tracker 仍继续放行

## 14. 同步失败处理

推荐：

- 所有同步动作必须记录结果
- 同步失败写 `TrackerSyncLog`
- 后台可按用户或资源手动重试
- 提供全量补偿同步

最低要求：

- 不能静默失败
- 不能失败后毫无记录

## 15. 数据库事务建议

推荐处理方式：

- 主站本地事务先提交业务数据
- 然后执行 `XBT` 同步
- 同步失败则写失败记录并可重试

不建议：

- 为了强一致把所有动作硬绑成一个跨系统大事务

原因：

- 主站与 `XBT` 的集成更适合“最终一致 + 可重试”

## 16. 后台展示建议

后台 `XBT 同步页` 建议展示：

- 最近同步成功记录
- 最近同步失败记录
- 按用户重试
- 按资源重试
- 全量同步按钮

用户详情页建议展示：

- 当前 `passkey`
- 最近同步状态
- 最近同步时间

资源详情页建议展示：

- `infohash`
- 当前白名单状态
- 最近同步状态

## 17. 上线前核对清单

上线前必须核对：

- 你们打包的 `XBT` 版本对应的 `xbt_tracker.sql`
- `xbt_users` 的实际主键与状态字段
- `xbt_files.info_hash` 的实际存储格式
- `flags=1` 在你们实际版本中的删除/失效语义
- `torrent_pass` 是否只接受 32 字符格式

这一步非常重要。

## 18. MVP 验收标准

满足以下条件即可视为映射方案可用：

- 主站 `passkey` 能正确写入 `xbt_users`
- 发布资源后 `infohash` 能进入 `xbt_files`
- 禁用用户后 `XBT` 不再允许其 announce
- 隐藏资源后 `XBT` 不再放行该 torrent
- 重置 `passkey` 后旧 torrent 失效
- 所有同步失败都有日志和重试入口

## 19. 当前结论

当前推荐映射方案正式收敛为：

- 主站 `users.passkey` 直接作为 `XBT` 的 `torrent_pass`
- 主站 `releases.infohash` 直接映射到 `xbt_files.info_hash`
- 主站负责写 `xbt_users` 和 `xbt_files`
- `XBT` 自己维护运行期统计表
- 同步采取“主站写入 + XBT执行 + 失败可重试”的模式

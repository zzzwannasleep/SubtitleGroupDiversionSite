# Private Tracker 接入建议

## 结论

这个项目不适合再套一个“整站型 PT 程序”进去，更适合保留现有 `Django + Vue` 站点，只补一个 **Tracker 内核**。

主推方案：**Torrust Tracker**

备选方案：`Chihaya`、`webtorrent/bittorrent-tracker`

不推荐作为当前项目的首选：`UNIT3D`、`Ocelot`

## 当前仓库已实现

当前代码已经落地了这几项：

- 可选 `Torrust Tracker` 配置开关
- 上传时把新种子规范化为 private torrent
- 下载时按用户或共享 key 重写 `announce`
- 发布、隐藏、替换种子时同步 whitelist
- `sync_tracker_state` 管理命令：补齐历史用户 key，并把历史种子规范化后同步到 tracker

## 现在是什么状态

已经完成的是：

- **后端业务接入已经完成**
- Django 这边已经支持：
  - 给用户分配 tracker key
  - 上传时把种子转成 private
  - 下载时改写 announce
  - 发布/隐藏资源时同步 Torrust whitelist

你还需要部署的是：

- **Torrust Tracker 本体服务**

所以现在不是“还没接完”，而是：

- 后端已经接好了
- Tracker 作为独立服务运行

这是正常架构，不是少做了一半。

## 推荐部署方式

推荐直接用当前仓库里的 `deploy/docker-compose.yml` 启一个额外的 `tracker` 服务。

建议顺序：

1. 复制 `deploy/.env.example` 为 `deploy/.env`
2. 复制 `deploy/tracker/tracker.example.toml` 为 `deploy/tracker/tracker.toml`
3. 在 `deploy/.env` 里开启 tracker 相关配置
4. 执行 `docker compose --profile tracker up -d`
5. 执行 `docker compose exec backend python manage.py migrate`
6. 执行 `docker compose exec backend python manage.py sync_tracker_state`

这样现有站点就会正式和 Torrust 连起来。

部署时要特别区分两个地址：

- `TRACKER_ANNOUNCE_URL`
  这是写进用户下载到的 `.torrent` 里的地址，必须填公网可访问地址，例如 `http://example.com:7070/announce`
- `TORRUST_API_URL`
  这是 Django 容器访问 Torrust 管理 API 的内网地址，Docker Compose 场景下应填 `http://tracker:1212`

## 为什么你的项目更适合“补 Tracker 内核”

你现在这个仓库其实已经有 PT 站的大半个外壳：

- 用户、角色、邀请码：`backend/apps/users/models.py`
- 资源发布、分类、标签、上传 torrent：`backend/apps/releases/models.py`
- 下载日志：`backend/apps/downloads/models.py`
- RSS、后台、审计日志、站点设置：`backend/apps/rss/`、`backend/apps/audit/`、`backend/apps/announcements/`

而真正缺的是这些能力：

- `announce` / `scrape`
- 每用户 passkey 或 tracker key
- infohash 白名单
- 做种/下载完成统计回流
- 下载时按用户动态改写 `.torrent`

仓库里还有很明显的“以前接过 tracker，后来拆掉了”的痕迹：

- `User.passkey` 已删除，只保留 `api_token`：`backend/apps/users/models.py`
- 下载接口现在直接回原始 `.torrent`：`backend/apps/downloads/services.py`
- 测试里明确断言不再暴露 `passkey / trackerSync / xbt*`：`backend/tests/test_api.py`

所以最省成本的路线不是迁站，而是把 tracker 能力重新嵌回当前后端。

## 候选项目对比

### 1. Torrust Tracker

推荐指数：**最高**

适合原因：

- 它本身就是“现代 private tracker 内核”，不是整站社区程序。
- 官方文档明确支持：
  - `Private and Whitelisted mode`
  - 内置 REST API
  - 认证 key
  - whitelist 持久化
  - `SQLite / MySQL / PostgreSQL`
- 你的项目本来就有 MySQL、Django 后台和发布流，正好可以让 Django 负责用户与业务，Torrust 只负责 tracker 协议层。

最适合你的接法：

1. Django 继续做主站和权限中心。
2. Torrust 单独跑成一个 tracker 服务。
3. 发布资源时把 `infohash` 同步到 Torrust whitelist。
4. 用户下载种子时，Django 动态生成带用户 key 的 `announce` 地址。
5. 前台展示的做种数/完成数，通过 scrape 或 API 定时回写到 `releases.active_peers` 和 `releases.completion_count`。

优点：

- 和现有架构重叠最少。
- 自带 whitelist / key / API / 持久化，少造轮子。
- 近一年仍然活跃，适合后续继续改。

注意点：

- 文档里写的是“time-bound keys”，默认思路更像“可过期认证 key”而不是经典永久 passkey。
- 这不影响接入，但我们需要在 Django 里决定策略：
  - 要么给每个用户发超长有效期 key
  - 要么保留固定 `tracker_passkey`，再同步成 Torrust key
  - 要么下载时按需续签

### 2. Chihaya

推荐指数：**第二**

适合原因：

- 官方 README 明说它是给“接入已有生产环境”的。
- 有 middleware hooks，适合做私有 tracker 的鉴权和扩展。
- Go 写的，多协议、高性能、业界常见。

为什么排第二：

- 它更像“可插拔 tracker 框架”，不是现成的 private-tracker 业务内核。
- 你需要自己写更多中间层，把 Django 用户、passkey、白名单、统计同步接进去。
- GitHub 页面显示 stable release 很老，接入时要更谨慎评估你准备跟 release 还是自己盯源码。

适合什么场景：

- 你更看重高性能和长期自定义。
- 你愿意接受多写一些 Go 侧中间件。

### 3. webtorrent/bittorrent-tracker

推荐指数：**第三**

适合原因：

- 文档直接提供 `filter(infoHash, params, cb)`，允许异步查数据库或外部系统。
- README 还直接提到可以按 secret key 做 private tracker。
- 改造门槛低，代码容易读，Node 生态也轻。

为什么不是第一：

- 它更偏“简单 tracker server/library”，不是完整 private tracker 内核。
- 从 README 暴露出来的能力看，私有站常见的 whitelist/persistence/accounting 仍然需要你自己补很多业务。

适合什么场景：

- 你想先很快做一个可跑的私有 tracker。
- 你接受后面再慢慢补白名单、持久化和统计。

### 4. UNIT3D

推荐指数：**不建议作为本项目首选**

原因不是它不好，而是它和你现有项目**重叠太多**：

- 它本身就是完整 private tracker 站点。
- 技术栈是 `Laravel + Livewire + AlpineJS`，和你现在的 `Django + Vue` 不同。
- 如果接它，实质上更像“迁站”或“双后台并存”，不是“接入”。

只有在这种情况下才建议考虑它：

- 你打算放弃当前站点，整体迁到成熟 PT 平台。

### 5. Ocelot

推荐指数：**不建议**

原因：

- 它是 Gazelle 生态里的 C++ tracker。
- 官方 README 直接要求 Gazelle 那套表结构，比如 `xbt_files_users`、`xbt_snatched`。
- 对你这个 Django 项目来说，耦合太重，改起来也最痛苦。

## 建议采用的架构

### 角色划分

- `Django`：用户、权限、邀请码、资源发布、管理后台、下载授权
- `Torrust`：announce、scrape、peer 统计、whitelist、tracker key
- `Vue`：展示站内统计、个人下载页、后续个人做种页

### 最小可行版本

第一阶段只做这些：

1. 新增用户 tracker 字段
2. 发布/隐藏资源时同步 whitelist
3. 下载 torrent 时动态改写 announce URL
4. 开启 HTTP/HTTPS tracker
5. 定时 scrape 更新 `active_peers` / `completion_count`

这样就已经是能用的 PrivateTracker 了。

### 建议新增的数据

建议在 `User` 上新增：

- `tracker_passkey`
- `tracker_key_expires_at`（如果决定使用可过期 key）
- `tracker_enabled`

建议新增一张同步表，避免把 tracker 状态全塞进 `Release`：

- `TrackerTorrentSync`
  - `release`
  - `infohash`
  - `is_whitelisted`
  - `last_whitelist_sync_at`
  - `last_scrape_at`
  - `last_scrape_seeders`
  - `last_scrape_leechers`
  - `last_scrape_completed`

## 代码层落点

### 1. 用户模型

文件：`backend/apps/users/models.py`

要做的事：

- 增加 `tracker_passkey` 或等价字段
- 用户创建时自动生成
- 禁用用户时让 tracker key 失效

### 2. 下载逻辑

文件：`backend/apps/downloads/services.py`

现在的 `build_download_torrent()` 是“读原始 torrent 然后原样返回”。

这里需要改成：

1. 读取原始 torrent
2. 为当前用户拿到 tracker key / passkey
3. 把 `announce` 改成类似：
   - `https://tracker.example.com/announce/<key>`
4. 如果要更严谨，也同步覆盖 `announce-list`
5. 返回改写后的 torrent

### 3. 发布与隐藏

文件：`backend/apps/releases/services.py`

在这些动作里补同步：

- `create_release()`
- `update_release()` 中更换 torrent 时
- `set_visibility()`

规则建议：

- `published` -> 加入 whitelist
- `hidden` / `draft` -> 从 whitelist 移除
- infohash 改变 -> 先删旧的，再加新的

### 4. 统计回流

可新建：

- `backend/apps/tracker/`

里面放：

- Tracker API client
- Torrent 重写工具
- whitelist sync service
- scrape sync job

## 真实开发顺序

建议按这个顺序改，风险最低：

1. 先引入 Torrust，单独用 Docker 跑起来
2. 在 Django 里加 tracker 配置和 API client
3. 给用户加 `tracker_passkey`
4. 先打通“下载时改写 torrent”
5. 再打通“发布/隐藏 -> whitelist 同步”
6. 最后补 scrape 定时同步和前台统计展示

## 我对这个仓库的明确建议

如果目标是：

- 尽量保留现有站
- 改动集中在后端
- 后续你自己还能继续魔改

那就选：

**Torrust Tracker + 当前 Django 站点继续做主业务**

不要选：

- `UNIT3D`，因为它会把你带到迁站路线
- `Ocelot`，因为它会把你带到 Gazelle/XBT 风格强耦合路线

如果你想要的是“我先帮你把第一步直接做掉”，下一步最适合落代码的是：

1. 先在项目里加 `apps/tracker/` 和 tracker 配置
2. 给 `User` 补 `tracker_passkey`
3. 把下载接口改成“按用户重写 torrent 的 announce”

这三步做完，你这个站就从“资源分流站”真正迈进 PrivateTracker 了。

## 参考来源

- Torrust Tracker GitHub: https://github.com/torrust/torrust-tracker
- Torrust Tracker docs.rs: https://docs.rs/torrust-tracker
- Chihaya GitHub: https://github.com/chihaya/chihaya
- webtorrent/bittorrent-tracker GitHub: https://github.com/webtorrent/bittorrent-tracker
- UNIT3D GitHub: https://github.com/HDInnovations/UNIT3D
- Ocelot GitHub: https://github.com/WhatCD/Ocelot

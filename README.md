# PT Platform

基于 `FastAPI + Vue 3 + Tailwind CSS + PostgreSQL + Redis + external tracker` 的私有种子分发站点骨架，当前默认 tracker 方案为 `XBT Tracker`。

## 前端翻译说明

如果你要翻译现有前端文本，直接修改下面这些语言包文件：

- `frontend/src/locales/en-US.ts`
- `frontend/src/locales/zh-CN.ts`

这些文件是当前前端页面文案的主要来源，包含：

- 页面标题
- 导航文字
- 登录 / 注册 / Profile / RSS / 上传 / 管理页等界面文案
- 按钮、表单标签、占位符、空状态提示

规则：

- 修改已有翻译：直接改对应语言包里的 key。
- 新增一种语言：
  1. 把新语言文件放到 `frontend/src/locales/` 下，文件名建议直接用 locale code，例如 `ja-JP.ts`、`fr-FR.ts`。
  2. 在 `frontend/src/locales/index.ts` 里新增 `import`。
  3. 把新的 locale code 加到 `LocaleCode` 类型。
  4. 把新语言加到 `SUPPORTED_LOCALES`，这样语言切换器里才能看到。
  5. 把新语言加到 `LOCALE_MESSAGES`，这样 `t("...")` 才能真正读取到这份语言包。
- 前端组件里不要再直接硬编码文案，统一通过 `t("...")` 读取。
- 路由标题也是多语言驱动的，对应关系在 `frontend/src/router/index.ts` 的 `titleKey`。

补充说明：

- 当前语言选择保存在 `frontend/src/stores/locale.ts`。
- 默认语言可以通过 `VITE_DEFAULT_LOCALE` 配置。
- 后端直接返回的错误信息，以及数据库里的分类名、种子名这类内容，不会被这些前端语言包自动翻译。
- 也就是说，想“多放一份语言”，不是覆盖原文件，而是新增一个 `frontend/src/locales/<你的语言代码>.ts` 文件，再去 `frontend/src/locales/index.ts` 注册。

## 当前状态

当前仓库已经完成第一批基础骨架：

- `backend/`：FastAPI 后端基础结构、用户模型、认证、种子列表/详情接口、分类接口、管理接口骨架
- `frontend/`：Vue 3 + Vite + Tailwind CSS 前端骨架、路由、Pinia、基础页面与 AppShell
- `docker-compose.yml`：Postgres / Redis / Backend / Frontend / XBT Tracker / XBT tracker-db / Nginx 组合
- `pt_platform_implementation_spec.md`：英文 spec
- `pt_platform_implementation_spec.zh-CN.md`：中文 spec

## 已实现

- 注册 / 登录 / `/api/auth/me`
- 首个注册用户自动成为 `admin`
- 默认分类自动初始化
- `.torrent` 上传、基础解析、原始文件保存、`torrents / torrent_files` 落库
- 种子列表页与详情页基础接口
- 下载时按可配置 credential 策略重写 `announce`
- RSS XML 输出与 RSS 下载端点
- SQLAdmin 内部后台接入，管理员可通过 `/internal-admin` 登录
- 管理员接口补充分类管理、种子可见性/Free 状态调整、手动 tracker sync
- 保留 Alembic 配置；当前默认部署路径以 `AUTO_CREATE_TABLES=true` 自动建表为主
- 用户 Profile 基础接口
- 前端登录 / 注册 / 列表 / 详情 / 上传 / Profile / RSS 页面骨架
- 基础响应式布局、路由守卫、页面切换动画、外观偏好本地存储

## 尚未完成

- XBT 的真实部署、announce 验证与统计回读需要第一次实际 `docker compose` 验证
- 只有在 XBT 不合适时，才切回 Torrust 备选方案
- 更完整的上传校验、NFO/MediaInfo 处理与生产级错误处理
- 更完整的后台前端化管理页与操作审计

## Docker 部署

当前仓库最省事的方式是直接使用 `docker compose`。这也是当前最适合“快速跑通全流程”的方案。

### 部署前准备

确保机器上已经安装：

- Docker
- Docker Compose

默认会用到这些端口：

- `80/tcp`：站点入口
- `2710/tcp`：XBT Tracker HTTP announce
- `6881/udp`：XBT Tracker UDP

### 1. 准备配置

检查 `backend/.env`。如果你是新环境，也可以先参考 `backend/.env.example`。

至少建议修改这些值：

- `SECRET_KEY`
- `JWT_SECRET_KEY`
- `APP_NAME`
- `PUBLIC_WEB_BASE_URL`
- `TRACKER_BASE_URL`
- `CORS_ALLOWED_ORIGINS`

常见示例：

- 本机预览：
  - `PUBLIC_WEB_BASE_URL=http://localhost`
  - `TRACKER_BASE_URL=http://localhost:2710/announce`
- 用域名部署：
  - `PUBLIC_WEB_BASE_URL=https://pt.example.com`
  - `TRACKER_BASE_URL=http://pt.example.com:2710/announce`
  - `CORS_ALLOWED_ORIGINS=https://pt.example.com`

说明：

- 当前默认部署路径不要求你手工执行数据库迁移命令。
- 只要 `AUTO_CREATE_TABLES=true`，后端启动时会自动补齐缺少的表。
- 新增的 `site_settings` 这类表也会走这条路径自动创建。

### 2. 启动服务

在项目根目录执行：

```bash
docker compose up -d --build
```

### 3. 访问站点

启动后可以访问：

- 前台：`http://localhost`
- 健康检查：`http://localhost/api/health`
- 内部后台：`http://localhost/internal-admin`

如果你部署在服务器，把 `localhost` 换成你的公网 IP 或域名即可。

### 4. 初始化账号

- 打开 `/register`
- 注册第一个账号
- 第一个注册用户会自动成为 `admin`

注册后，建议按这个顺序检查：

1. `/admin`
2. `/profile`
3. `/rss`
4. `/upload`
5. `/torrents`
6. `/internal-admin`

### 5. 持久化数据目录

当前 compose 会把这些目录挂载到宿主机：

- `./data/postgres`
- `./data/tracker-db`
- `./data/torrents`
- `./data/uploads`

如果你要迁移机器或备份，至少要保留这些目录。

### 6. 常用命令

查看日志：

```bash
docker compose logs -f backend frontend nginx tracker
```

重建并重启：

```bash
docker compose up -d --build
```

停止服务：

```bash
docker compose down
```

清空开发数据后重新开始：

注意：下面这一步会删除现有数据库和已上传文件。

```bash
docker compose down
rm -rf data/postgres data/tracker-db data/torrents data/uploads
docker compose up -d --build
```

### 7. 部署注意事项

- 当前 compose 已经包含 `Postgres + Redis + XBT Tracker + tracker-db + backend + frontend + nginx`。
- BT 客户端实际使用的 announce 地址来自 `TRACKER_BASE_URL`，不是 Nginx 的 `/api` 入口。
- 如果你之前使用过旧数据，旧用户的 `tracker_credential` 可能与当前 XBT 方案不兼容，最稳妥的做法是直接从空数据重新开始。
- 如果你只是想快速验证站点流程，优先用一套全新数据启动。

## 说明

- 当前实现更接近“可继续开发的基础骨架”，不是完整可用产品。
- 当前实现默认按 XBT 风格的 `/<tracker_credential>/announce` 重写下载出来的 `.torrent`。
- 站点侧 tracker sync 默认通过 `XBT_TRACKER_DB_DSN` 直连 `xbt_users / xbt_files` 拉取统计，并在手动 sync 时顺带回填缺失的 XBT 用户与种子记录。

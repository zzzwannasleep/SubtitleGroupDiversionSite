# PT Platform

基于 `FastAPI + Vue 3 + Tailwind CSS + PostgreSQL + Redis + external tracker` 的私有种子分发站点骨架，当前默认 tracker 方案为 `XBT Tracker`。

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
- Alembic 配置与首个初始迁移，后端容器启动时自动执行 `upgrade head`
- 用户 Profile 基础接口
- 前端登录 / 注册 / 列表 / 详情 / 上传 / Profile / RSS 页面骨架
- 基础响应式布局、路由守卫、页面切换动画、外观偏好本地存储

## 尚未完成

- XBT 的真实部署、announce 验证与统计回读需要第一次实际 `docker compose` 验证
- 只有在 XBT 不合适时，才切回 Torrust 备选方案
- 更完整的上传校验、NFO/MediaInfo 处理与生产级错误处理
- 更完整的后台前端化管理页与操作审计

## 快速开始

1. 检查 `backend/.env`
2. 构建并启动服务：

```bash
docker compose up --build
```

注意：

- 当前 compose 已经切到 `XBT Tracker + tracker-db`。
- 本地 BT 客户端 announce 默认走 `http://localhost:2710/<tracker_credential>/announce`，不再通过 Nginx 反代。
- 如果你之前已经注册过用户，旧用户的 `tracker_credential` 可能还是 64 字符；XBT 默认 `torrent_pass` 使用 32 字符私有凭证，新环境建议直接重建开发数据。

如果是本地直接运行后端而不是走 Docker，先执行：

```bash
cd backend
alembic -c alembic.ini upgrade head
```

3. 打开：

- 前台：`http://localhost`
- 后端健康检查：`http://localhost/api/health`
- 内部后台：`http://localhost/internal-admin`

## 说明

- 当前实现更接近“可继续开发的基础骨架”，不是完整可用产品。
- 当前实现默认按 XBT 风格的 `/<tracker_credential>/announce` 重写下载出来的 `.torrent`。
- 站点侧 tracker sync 默认通过 `XBT_TRACKER_DB_DSN` 直连 `xbt_users / xbt_files` 拉取统计，并在手动 sync 时顺带回填缺失的 XBT 用户与种子记录。

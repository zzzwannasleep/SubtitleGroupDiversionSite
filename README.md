# PT Platform

基于 `FastAPI + Vue 3 + Tailwind CSS + PostgreSQL + Redis + Trunker` 的私有种子分发站点骨架。

## 当前状态

当前仓库已经完成第一批基础骨架：

- `backend/`：FastAPI 后端基础结构、用户模型、认证、种子列表/详情接口、分类接口、管理接口骨架
- `frontend/`：Vue 3 + Vite + Tailwind CSS 前端骨架、路由、Pinia、基础页面与 AppShell
- `docker-compose.yml`：Postgres / Redis / Backend / Frontend / Trunker / Nginx 组合
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

- Trunker 真实统计 endpoint 与每用户凭证格式 PoC 收口
- 更完整的上传校验、NFO/MediaInfo 处理与生产级错误处理
- 更完整的后台前端化管理页与操作审计

## 快速开始

1. 检查 `backend/.env`
2. 构建并启动服务：

```bash
docker compose up --build
```

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
- 由于 `Trunker` 每用户凭证格式与统计同步方式还需要 PoC，当前下载重写能力采用可配置的抽象策略，后续需要按 PoC 结果再收口。

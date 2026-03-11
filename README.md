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
- 种子列表页与详情页基础接口
- 用户 Profile 基础接口
- 前端登录 / 注册 / 列表 / 详情 / 上传 / Profile / RSS 页面骨架
- 基础响应式布局、路由守卫、页面切换动画、外观偏好本地存储

## 尚未完成

- 真正的种子上传逻辑
- `.torrent` 解析
- 下载时重写 tracker credential
- RSS XML 输出
- Trunker 统计同步
- SQLAdmin 接入
- Alembic 迁移

## 快速开始

1. 检查 `backend/.env`
2. 构建并启动服务：

```bash
docker compose up --build
```

3. 打开：

- 前台：`http://localhost`
- 后端健康检查：`http://localhost/api/health`

## 说明

- 当前实现更接近“可继续开发的基础骨架”，不是完整可用产品。
- 由于 `Trunker` 每用户凭证格式与统计同步方式还需要 PoC，相关下载与同步逻辑暂时保留为占位实现。

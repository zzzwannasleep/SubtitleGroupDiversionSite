# 前端样式系统设计文档

## 1. 文档目标

这份文档用于统一前端视觉和组件风格，避免后续开发出现：

- 每个页面背景不一样
- 卡片结构不统一
- 按钮样式混乱
- 表单、表格、弹窗各写各的
- 引入多个组件库导致风格冲突

这份文档重点解决：

- 背景怎么做
- 卡片怎么做
- 组件库怎么选
- 全站色彩、圆角、边框、阴影怎么统一
- 前台和后台在同一站点里怎么保持一致又有区分

项目级“必须简单易用、低复杂度、低部署成本”的硬约束，见：

- `docs/simplicity-usability-operability-rules.md`

## 2. 当前结论

前端样式建议现在就定下来，不要等页面做完再补。

当前推荐方案：

- 样式基础：`TailwindCSS`
- 基础组件方案：`shadcn-vue`
- 图标方案：`Lucide`
- 页面风格：`浅色主题优先`
- 深色模式：`不进入 MVP`

不推荐在当前项目里把 `Element Plus` 或 `Vuetify` 作为主组件库。

原因：

- 这个项目已经明确使用 `TailwindCSS`
- 我们还要自己定义站点视觉风格
- 重型组件库会带入很强的默认设计语言
- 后续想改出“自己的样子”会更麻烦

## 3. 组件库选择建议

### 3.1 推荐主方案

推荐：

- `TailwindCSS + shadcn-vue`

推荐原因：

- `shadcn-vue` 官方把自己定位为“设计系统的基础”，强调 `Open Code`
- 它不是传统那种完全封闭的组件库，更适合拿来做自己的组件系统
- 组件风格和 `TailwindCSS` 结合自然
- 适合你这种需要“统一风格但不想被组件库绑死”的项目

适合本项目用它来承载的组件：

- Button
- Input
- Select
- Dialog
- Drawer
- Dropdown Menu
- Tabs
- Pagination
- Tooltip
- Table
- Skeleton
- Empty State

### 3.2 可补充方案

如果极少数组件 `shadcn-vue` 不够顺手，可以考虑：

- 原生 HTML + TailwindCSS 自己封装
- 少量 `Headless UI` 组件

原则：

- 优先“自己系统内统一”
- 不要混 2 套重型视觉组件库

### 3.3 不推荐主用方案

不推荐：

- 全站主用 `Element Plus`
- 全站主用 `Vuetify`

原因：

- `Element Plus` 官方组件很多、上手快，确实适合后台系统
- `Vuetify` 也很完整
- 但它们都会带来明显的默认视觉风格
- 这会和我们已经决定的 `TailwindCSS` 自定义路线冲突

结论：

- `TailwindCSS` 负责视觉基础
- `shadcn-vue` 负责基础组件
- 项目内再封装一层 `App*` 组件做统一样式

## 4. 视觉方向

### 4.1 整体气质

建议方向：

- 简洁
- 信息清晰
- 稍偏工具型
- 不做花哨动效
- 不做夸张渐变和玻璃态

这不是公开社区产品，更像内部工作站点，所以视觉重点不是“炫”，而是：

- 清楚
- 稳定
- 好扫读
- 长时间使用不累

### 4.2 主题策略

MVP 建议只做：

- `浅色主题`

暂不做：

- 深色主题
- 多主题切换
- 品牌皮肤切换

原因：

- 先把页面和权限做稳定
- 少一套主题就少一倍维护成本

## 5. 设计 Token 建议

建议统一为少量基础 Token，不要到处写散。

### 5.1 色彩

建议主色体系：

- 主色：蓝色系
- 中性色：Slate/Zinc
- 成功：绿色
- 警告：橙色/黄色
- 危险：红色

推荐语义色：

- `primary`: `blue-600`
- `primary-hover`: `blue-700`
- `surface`: `white`
- `surface-muted`: `slate-50`
- `page-bg`: `slate-100`
- `border`: `slate-200`
- `text-primary`: `slate-900`
- `text-secondary`: `slate-500`
- `success`: `green-600`
- `warning`: `amber-600`
- `danger`: `red-600`

### 5.2 字体

建议使用系统字体优先，不额外引入重字体依赖。

建议字体栈：

- `Inter`
- `PingFang SC`
- `Microsoft YaHei`
- `Noto Sans SC`
- `sans-serif`

建议：

- 正文 14px / 16px 为主
- 中文界面避免字号过小
- 标题层级清晰，不超过 4 级

### 5.3 圆角

建议统一只用 3 档圆角：

- 小圆角：`rounded-md`
- 标准圆角：`rounded-xl`
- 大圆角：`rounded-2xl`

推荐：

- 输入框、按钮：`rounded-md`
- 卡片：`rounded-xl`
- 弹窗：`rounded-2xl`

### 5.4 阴影

建议只用轻阴影，不做重投影。

推荐：

- 默认卡片：`shadow-sm`
- 弹窗：`shadow-xl`
- 悬浮菜单：`shadow-md`

### 5.5 间距

建议主间距单位以 `4 / 6 / 8` 为主，不要太碎。

推荐：

- 页面外边距：`px-4 md:px-6 lg:px-8`
- 卡片内边距：`p-4` 或 `p-6`
- 表单字段间距：`space-y-4`
- 模块块间距：`space-y-6` 或 `space-y-8`

## 6. 背景设计

### 6.1 全站背景

建议：

- 全站基础背景使用浅灰色
- 内容区域卡片用白色

推荐：

- 页面背景：`bg-slate-100`
- 主内容卡片：`bg-white`
- 次级区块：`bg-slate-50`

不要做：

- 大面积纯黑背景
- 强渐变背景
- 带噪点的复杂纹理背景

### 6.2 前台页面背景

前台页面建议：

- 顶部导航白色
- 页面主体浅灰
- 资源列表、详情、RSS 等模块都放在白色卡片中

这样浏览资源时可读性更好。

### 6.3 后台页面背景

后台建议和前台保持同一主题，但层级更明显。

推荐：

- 主内容区：`bg-slate-100`
- 左侧侧边栏：`bg-slate-950 text-slate-100`
- 内容卡片：`bg-white`

这样能做到：

- 仍然是同一个站
- 但用户一眼能区分“前台”和“后台”

## 7. 卡片结构设计

卡片是这个项目最重要的视觉容器，必须统一。

### 7.1 标准卡片

推荐结构：

- Header
- Body
- Footer（可选）

推荐样式：

- `rounded-xl`
- `border border-slate-200`
- `bg-white`
- `shadow-sm`

### 7.2 Header 规范

Header 建议包含：

- 标题
- 副标题或说明
- 右上操作区

推荐：

- 标题偏左
- 操作按钮偏右
- Header 与 Body 之间留足距离

### 7.3 Body 规范

Body 建议只放内容本体，不要塞太多操作按钮。

例如：

- 列表
- 表单
- 详情信息
- 文件列表

### 7.4 Footer 规范

Footer 只在这些场景下出现：

- 表单提交区
- 分页区
- 二次确认区

不建议每张卡都硬加 Footer。

## 8. 组件视觉规范

### 8.1 按钮

建议统一 4 类按钮：

- `Primary`
- `Secondary`
- `Ghost`
- `Danger`

规则：

- 一个区块里只保留一个主按钮
- 删除、禁用、重置类操作统一用危险色
- 纯文字跳转用 `Ghost` 或链接样式

### 8.2 输入框

规则：

- 高度统一
- 标签在上方
- 错误提示在下方
- 必填项标识统一

不建议：

- 一会儿左标签一会儿上标签
- 一个表单里混多种尺寸

### 8.3 选择器

统一用一套：

- Select
- Multi Select
- Tag Input

不要：

- 某些页面原生 select
- 某些页面组件库 select
- 某些页面自定义下拉

### 8.4 表格

后台管理页面建议大量使用表格，但要控制密度。

推荐：

- 表头浅灰背景
- 行 hover 高亮
- 单元格左右留白充足
- 操作列固定在右侧

不要：

- 过细边框
- 过密行高

### 8.5 标签与状态徽标

建议统一标签与状态组件：

- 分类标签
- 状态标签
- 角色标签

示例：

- `Published`
- `Hidden`
- `Active`
- `Disabled`
- `Admin`
- `Uploader`

### 8.6 弹窗

弹窗只用于：

- 删除确认
- 禁用确认
- 重置 `passkey`
- 重要提示

不建议：

- 把复杂页面内容硬塞进小弹窗

### 8.7 空状态与错误状态

全站统一做：

- 空状态
- 无权限状态
- 加载状态
- 错误状态

风格建议：

- 图标 + 标题 + 说明 + 操作按钮

## 9. 页面模式建议

### 9.1 首页 / 列表页

建议模式：

- 筛选条卡片
- 资源列表卡片
- 分页区

### 9.2 详情页

建议模式：

- 标题信息卡片
- 资源介绍卡片
- 文件列表卡片
- 操作侧栏或顶部操作区

### 9.3 上传页

建议模式：

- 单列大表单
- 分步骤感知，但不必做真正 Stepper
- 提交按钮固定在底部操作区

### 9.4 后台列表页

建议模式：

- 页面标题区
- 筛选和搜索工具条
- 表格卡片
- 批量操作或分页区

## 10. 图标与插图建议

推荐：

- 全站使用同一套线性图标
- 图标尺寸统一
- 不混实心图标和线性图标

建议使用：

- `Lucide`

原因：

- 官方强调图标“Beautiful & consistent”
- 支持 Vue
- 可自定义大小、颜色、描边粗细
- 适合后台和工具类站点

## 11. 响应式规则

MVP 至少保证：

- 桌面端可用
- 平板端可用
- 手机端可登录、浏览、下载、看 RSS

不要求：

- 手机端后台管理做到桌面级体验

建议：

- 前台页面优先响应式适配
- 后台页面手机端允许降级，但不能完全不可用

## 12. 实现规则

建议实现时遵守下面的约束。

### 12.1 组件封装层级

推荐分 3 层：

- `ui` 层：基础组件
- `app` 层：项目封装组件
- `page` 层：页面组合组件

例如：

- `ui/button`
- `ui/dialog`
- `app/AppCard`
- `app/AppPageHeader`
- `app/AppStatusBadge`

### 12.2 样式来源

推荐优先级：

1. 设计 Token
2. `ui` 组件基础样式
3. `app` 项目组件样式
4. 页面局部样式

不建议：

- 页面里到处写很长的临时 class
- 同一个按钮在不同页面直接复制出不同版本

### 12.3 不混库原则

禁止：

- `shadcn-vue` 和 `Element Plus` 混用做主要组件
- `shadcn-vue` 和 `Vuetify` 混用做主要组件

原因：

- 视觉语言不一致
- 状态样式不一致
- 表单体验不一致
- 后期维护成本会明显变高

## 13. MVP 样式范围

截至 `2026-04-08` 已完成：

- [x] 背景
- [x] 导航栏
- [x] 卡片
- [x] 按钮
- [x] 输入框
- [x] 选择器
- [x] 表格
- [x] 标签
- [ ] 弹窗
- [x] 空状态 / 错误状态 / 加载状态

暂时不必做：

- 深色模式
- 动态主题切换
- 复杂动效系统
- 营销型插画体系

## 14. 推荐交付物

建议把样式系统最终落成以下内容：

- [x] `tailwind.config`
- [x] `src/styles/tokens.css`
- [x] `src/styles/base.css`
- [x] `src/components/ui/`
- [x] `src/components/app/`
- [ ] 一份组件展示页或 Storybook（可二期）

当前已补齐：

- [x] 统一状态组件：`AppLoading`、`AppEmpty`、`AppError`、`AppForbidden`、`AppNotFound`
- [x] 统一页内反馈组件：`AppAlert`
- [x] 统一状态徽标与语义标签：`AppStatusBadge`
- [x] 前台/后台导航的统一 Lucide 图标与浅色主题视觉

## 15. 当前结论

当前前端视觉方案建议正式收敛为：

- 基础样式：`TailwindCSS`
- 基础组件：`shadcn-vue`
- 图标：`Lucide`
- 风格：浅色、简洁、工具型
- 容器：白色卡片 + 浅灰背景
- 前后台统一体系、不同布局
- MVP 先统一基础样式，不做深色模式

## 16. 参考资料

- shadcn-vue: https://www.shadcn-vue.com/docs/introduction.html
- shadcn-vue docs: https://www.shadcn-vue.com/docs
- Headless UI: https://headlessui.com/
- Element Plus overview: https://element-plus.org/en-US/component/overview.html
- Element Plus quick start: https://element-plus.org/en-US/guide/quickstart
- Vuetify: https://docs.genio.dev/en/
- Lucide: https://lucide.dev/

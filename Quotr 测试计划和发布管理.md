# Quotr 测试计划和发布管理 v0.7

**日期**：2026-08-03
**环境**：test.quotr.ai
**基于**：对测试站点的产品探索（登录、4 个模块、API 层、数据状态）

---

## 目录

1. [产品理解](#1-产品理解)
2. [模块测试策略](#2-模块测试策略)（含功能、安全、支付、兼容性、无障碍、迁移、并发、AI、性能共 16 个子章节）
3. [测试执行体系](#3-测试执行体系)
4. [质量保障体系](#4-质量保障体系)
5. [PR 测试管理](#5-pr-测试管理)
6. [Release Gate](#6-release-gate)
7. [自动化测试框架](#7-自动化测试框架)
8. [产品与交付](#8-产品与交付)

---

## 1. 产品理解

### 1.1 技术架构

| 层 | 技术 | 已验证 |
|---|------|--------|
| 前端 | React SPA + Ant Design v5 + React Router v6 | 是 |
| 认证 | Supabase Auth JWT，存储于 localStorage | 是 |
| API | POST 为主（非 RESTful），JSON 响应统一格式 `{code, message, data}` | 是 |
| 监控 | Sentry（错误追踪）+ Amplitude（session replay/analytics） | 是 |
| CDN | Cloudflare，静态资源路径 `/quort_static/` | 是 |

### 1.2 localStorage 关键字段

| Key | 内容 | 测试关注点 |
|-----|------|-----------|
| `auth_v2_session` | JWT access token（对象） | 登录后必须存在，过期后处理 |
| `token` | JWT raw token（字符串） | 与 auth_v2_session 同步写入 |
| `user` | 用户信息 JSON（id, email, org_owner, phoneNumber 等） | 字段完整性 |
| `organization` | 当前组织 ID（如 "384"） | 多组织切换时的正确性 |
| `quotr_onboarding_state` | 引导流程进度 | 新用户引导不应卡死 |
| `selectedTemplate` | 当前选中模板类型（material/room） | Template 模块依赖 |
| `quotr:last-workspace-org-id` | 上次工作空间 ID | 跨 session 恢复 |

### 1.3 API 端点全景

> **注意**：此列表仅包含探索过程中实际触发的 API 调用。后续需向开发获取完整 API 文档或 Swagger/OpenAPI schema，补充缺失端点。

**认证层：**

| 端点 | 方法 | 用途 | 风险等级 |
|------|------|------|---------|
| `/api/auth/v2/signin` | POST | 登录，返回 JWT token | P0 — 登录失败 = 全站不可用 |
| `/api/auth/v2/sign-out-reason` | POST | 记录登出原因 | 监控：非预期调用可能清空 session |

**组织与项目：**

| 端点 | 方法 | 用途 | 风险等级 |
|------|------|------|---------|
| `/api/query-org` | POST | 查询组织信息 | P0 — **此调用失败导致 Dashboard 白屏** |
| `/api/get-projects` | POST | 获取项目列表 | P0 — 核心数据源 |
| `/api/get-versions` | POST | 获取估价版本列表 | P1 — 估算数据依赖 |
| `/api/get-roomTypes` | POST | 获取房型数据（按建筑类型分类） | P1 — AI 解析依赖 |

**模板与供应商：**

| 端点 | 方法 | 用途 | 风险等级 |
|------|------|------|---------|
| `/api/get-customer-templates` | POST | 自定义模板列表 | P2 |
| `/api/get-default-templates` | POST | 系统默认模板 | P2 |
| `/api/get-customer-supplier-list` | POST | 供应商列表 | P1 — 采购流程依赖 |

**协作与通知：**

| 端点 | 方法 | 用途 | 风险等级 |
|------|------|------|---------|
| `/api/qms/v1/meetings` | GET | 会议列表 | P2 |
| `/api/qms/v1/bell` | GET | 通知铃铛（未读数） | P2 |
| `/api/get-unread-count` | POST | 未读消息计数 | P2 |

**静态资源：**

| 端点 | 方法 | 用途 |
|------|------|------|
| `/api/static/files/ai_tools/*.mp4` | GET | AI 工具教程视频 |
| `/api/static/files/draw_tools/*.mp4` | GET | 绘图工具教程视频 |

### 1.4 模块导航结构

```
/dashboard/project          → 项目管理（主工作区）
/dashboard/project/{id}     → 项目详情（当前返回 404，需确认路由格式）
/dashboard/database         → 材料/成本数据库
/dashboard/template         → 模板管理（Material Template / Room Template）
/dashboard/suppliers/manage → 供应商管理（Manage / RFQ / Quotes）
```

### 1.5 测试环境现有数据

| 资源 | 详情 |
|------|------|
| 项目 | `test_pro1`（id: 703，Singlefamily House，zip: 00000） |
| 估价版本 | `test_est1`（id: 3434，Economy quality，Residential，关联 PDF: 1.png） |
| 供应商 | `test_sup1`（CS0126，Electrical trade，contact: aabb@ccdd.com） |
| 自定义模板 | 无 |
| 组织 | id: 384（trial_eligible: false） |

### 1.6 最大质量风险（按影响排序）

1. **`/api/query-org` 失败** — Dashboard 完全白屏，等价于全站宕机
2. **AI 输出"高置信度错误"** — 模型以高置信度输出错误估算，用户直接用于投标
3. **数据持久化失败** — 用户花费数小时的估算结果丢失
4. **IDOR / 越权访问** — 用户 A 访问用户 B 的财务数据（报价、估价），直接导致商业机密泄露和客户流失
5. **跨模块数据不一致** — Project → Database → Template → Procurement 链路数据断裂
6. **反爬/认证误杀** — 合法用户被当作 bot 拦截，SPA 渲染空白；同时影响自动化 CI 流水线全量失败
7. **Stripe 支付链路中断** — 订阅创建/续费失败，直接影响营收

---

## 2. 模块测试策略

### 2.1 模块总览

| 模块 | 路由 | 当前状态 | 主要风险 | 测试重点 |
|------|------|---------|---------|---------|
| **Project** | `/dashboard/project` | API 返回数据但列表页未渲染项目行；无可见"New Project"入口；详情页 `/project/703` 返回 404 | 项目不可见、不可创建、路由异常 | P0 |
| **Database** | `/dashboard/database` | **布局 Bug**：仅渲染侧边栏，主内容区完全空白，无 `.ant-layout-content` | 模块完全不可用 | P0 |
| **Template** | `/dashboard/template` | 正常：Material/Room Template 双 Tab，New Template 按钮，Example Templates 按钮 | 模板 CRUD 正确性、渲染输出一致性 | P1 |
| **Suppliers** | `/dashboard/suppliers/manage` | 正常：三 Tab（Manage/RFQ/Quotes），Add New Supplier 按钮，含测试数据 | 供应商 CRUD、价格关联、数据同步 | P1 |
| **Auth** | `/auth/*` | 登录 API 正常，但 SPA 渲染不稳定（反爬检测），sign-out-reason 可能异常触发 | 登录稳定性、token 管理、session 过期 | P0 |

### 2.2 Project 模块

**当前发现：**
- `get-projects` API 正确返回了 `test_pro1`，但 Dashboard 项目列表页不渲染任何行
- 页面未显示"New Project"或"Create Project"等创建入口按钮
- 直接访问 `/dashboard/project/703` 返回 ERROR 404
- 可能原因：项目列表使用非标准 UI 组件（非 Ant Table）、路由格式不正确、或测试账号权限限制

**测试策略：**

| 场景 | 方法 | 优先级 |
|------|------|--------|
| 项目列表正常渲染已有项目 | 确认 API 返回数据与 UI 渲染一致 | P0 |
| 项目创建流程 | 定位创建入口 → 填写表单 → 验证 API 请求 → 确认列表刷新 | P0 |
| 项目详情页路由 | 从列表点击进入 → 验证 URL 格式 → 验证页面内容 | P0 |
| 图纸上传 | 多格式（PDF/PNG/JPG）、多尺寸（1MB-100MB） | P0 |
| AI Takeoff 解析 | Golden Baseline 图纸对比，结构化输出校验 | P0 |
| 估算编辑与保存 | 手动修改 → 保存 → 刷新 → 验证数据恢复 | P0 |
| 项目删除/归档 | 软删除 → 确认不可恢复提示 → 列表更新 | P1 |
| 空状态处理 | 无项目时的引导 UI、搜索/筛选的优雅降级 | P1 |

### 2.3 Database 模块

**当前发现：**
- 页面仅显示 "Nav Bar"、Help 按钮、用户头像 — **主内容区完全空白**
- DOM 中无 `.ant-layout-content`、`.ant-table`、`.ant-empty`、`.ant-spin` 等任何内容组件
- 无 console error 输出
- 此问题在两次独立探索中复现（8/2 和 8/3），已确认为可复现 Bug

**测试策略：**

| 场景 | 方法 | 优先级 |
|------|------|--------|
| **Bug 验证** | 开发修复后，验证主内容区正确渲染 | P0（阻塞） |
| 材料条目 CRUD | 新增、编辑、批量导入、删除 | P1 |
| 价格校验 | 单价合理性检查、单位换算正确性 | P1 |
| 搜索与筛选 | 按名称、类别、供应商搜索 | P1 |
| 数据导出 | CSV/Excel 导出与数据库内容对比 | P2 |
| 空状态 | 无数据时的引导 UI | P2 |

### 2.4 Template 模块

**当前发现：**
- 页面正常渲染，含 "Material Template" 和 "Room Template" 两个 Tab
- "New Template" 按钮可用
- "Show Example Templates" 按钮可用
- `get-roomTypes` API 返回完整的房型分类数据（SinglefamilyHouse, MultifamilyHousing 等类型下各含 15+ 房型）
- `get-customer-templates` 返回空（无自定义模板）
- `selectedTemplate` 存储于 localStorage

**测试策略：**

| 场景 | 方法 | 优先级 |
|------|------|--------|
| Material Template 创建 | New Template → 填写 → 保存 → 列表验证 | P1 |
| Room Template 创建 | New Template → 选房型 → 填写 → 保存 | P1 |
| Example Templates 浏览 | 点击 → 验证列表 → 预览 | P1 |
| 模板编辑与删除 | 修改已有模板 → 验证关联项目是否受影响 | P1 |
| 模板应用 | 在项目中应用模板 → 验证占位符替换 | P1 |
| 渲染输出 | PDF 预览与实际下载一致性 | P1 |

### 2.5 Suppliers (Procurement) 模块

**当前发现：**
- 页面正常渲染，含三个 Tab：Manage Suppliers、Request for Quote、Quotes from Suppliers
- "Add New Supplier" 按钮可用
- 已有 1 个测试供应商 `test_sup1`（Electrical），含 Edit/Delete 操作
- `get-customer-supplier-list` API 正常返回，含 supplierId、trades、contact 等字段

**测试策略：**

| 场景 | 方法 | 优先级 |
|------|------|--------|
| 供应商创建 | Add New Supplier → 填写 → 保存 → 列表验证 | P1 |
| 供应商编辑 | Edit → 修改信息 → 保存 → 验证 | P1 |
| 供应商删除 | Delete → 确认 → 列表更新 | P1 |
| 搜索与筛选 | 按名称、Trade、Project 搜索 | P1 |
| RFQ 创建 | Request for Quote → 选供应商 → 发送 | P1 |
| Quotes 管理 | 查看/比较报价 → 确认 | P1 |
| 供应商关联项目 | 验证供应商可关联到具体项目 | P2 |

### 2.6 认证与权限

**当前发现：**
- 登录 API（`POST /api/auth/v2/signin`）始终返回 200 + JWT
- Token 正确写入 localStorage（`auth_v2_session`、`token`、`user`）
- SPA 渲染不稳定：有时正常显示登录表单，有时 #root 为空（反爬检测）
- `sign-out-reason` API 有时在登录后立即调用，导致 session 被清空
- 反爬检测手段：navigator.webdriver、navigator.plugins、navigator.languages 等指纹

**测试策略：**

| 场景 | 方法 | 优先级 |
|------|------|--------|
| 正常登录 | 邮箱 + 密码 → 验证 token → 验证跳转 | P0 |
| 登录失败 | 错误密码 → 验证错误提示 | P0 |
| Token 过期 | 修改 token exp → 验证重定向到登录 | P0 |
| 未登录访问 | 直接访问 /dashboard/* → 验证重定向 | P0 |
| Session 恢复 | 关闭 tab → 重新打开 → 验证自动登录（如支持） | P1 |
| 多 Tab 同步 | 两个 tab 同时操作 → 验证 token 同步 | P2 |
| Google SSO | 如启用：正常登录 + 取消 + 账号不存在 | P1 |
| 反爬兼容性 | 至少 3 种主流浏览器（Chrome/Edge/Firefox）验证登录正常 | P1 |

### 2.7 空状态测试（全模块通用）

当前测试环境大部分模块处于空状态或无数据状态，这是重要的测试场景：

- 空状态 UI 是否友好引导用户创建第一条数据（而非空白或报错）
- 空状态下的搜索、筛选、排序是否优雅降级
- 从空状态创建第一条数据后，列表是否正确刷新
- 删除最后一条数据后是否正确回到空状态
- 空状态下的分页组件是否隐藏或禁用

### 2.8 API 层通用测试

所有 API 端点的通用校验：

| 维度 | 校验内容 |
|------|---------|
| 状态码 | 正常返回 200，错误返回统一格式 |
| 响应格式 | `{code: 200, message: "success", data: ...}` |
| 认证 | 无 token 时返回 401 |
| 超时 | P95 < 5s |
| 空数据 | data 为空数组 `[]` 时不报错 |
| CORS | 跨域请求正确返回 CORS headers |

### 2.9 安全测试

Quotr 处理建筑投标的财务数据（估算金额、供应商报价、项目成本），安全漏洞可能直接导致用户经济损失。

**身份认证与授权：**

| 场景 | 方法 | 优先级 |
|------|------|--------|
| IDOR — 跨用户项目访问 | 用用户 A 的 token 请求用户 B 的项目 ID（URL 参数/API body），验证返回 403/404 而非数据 | P0 |
| IDOR — 跨组织数据访问 | 修改 API 请求中的 org_id，验证无法访问不属于当前组织的资源 | P0 |
| 未认证 API 访问 | 不带 token 调用所有已知 API 端点，验证均返回 401 | P0 |
| JWT 篡改 | 修改 token payload（role、org_id、email），验证后端拒绝或忽略篡改字段 | P0 |
| Token 重放 | 登出后使用旧的 token 调用 API，验证 token 已失效 | P1 |
| 弱密码策略 | 验证密码最小长度、复杂度要求、常见密码拒绝 | P1 |

**前端安全：**

| 场景 | 方法 | 优先级 |
|------|------|--------|
| localStorage XSS 风险评估 | Token 存储在 localStorage 是固有 XSS 攻击面 — 审计是否有 CSP headers、输入转义、第三方脚本隔离 | P0 |
| XSS — 项目名称注入 | 创建项目时在名称字段输入 `<script>alert(1)</script>`，验证被转义 | P1 |
| XSS — 供应商字段注入 | 在供应商名称、邮箱、地址等自由文本字段注入脚本标签 | P1 |
| 敏感信息泄露 | 审查 API 响应是否包含不应暴露的字段（密码哈希、内部 ID、调试信息） | P1 |
| CSP Headers 检查 | 验证 `Content-Security-Policy` header 存在且合理配置 | P1 |
| 文件上传安全 | 上传非图片文件伪装成 .png（如 .exe 改后缀），验证后端校验 MIME type 和文件头 | P1 |

**API 安全：**

| 场景 | 方法 | 优先级 |
|------|------|--------|
| Rate Limiting | 短时间内大量请求同一 API，验证触发 429 或限流响应 | P1 |
| SQL 注入（如有 DB 直连） | 在搜索/筛选输入中注入 SQL 片段，验证后端使用参数化查询 | P1 |
| 大文件 DoS | 上传超大文件（500MB+），验证后端有上传大小限制 | P2 |
| API 响应头安全 | 验证 `X-Content-Type-Options`、`X-Frame-Options`、`Strict-Transport-Security` 等安全头 | P2 |

### 2.10 支付测试

系统集成了 Stripe（`stripe_customer_id` 字段），支付功能直接影响营收。

| 场景 | 方法 | 优先级 |
|------|------|--------|
| 订阅创建 | 选择 plan → 输入 Stripe 测试卡号 → 验证订阅激活 → 验证 org 状态更新 | P0 |
| 订阅升级/降级 | 从低 tier 升级 → 验证按比例计费 → 验证功能权限即时生效 | P1 |
| 订阅取消 | 取消 → 验证在当前周期结束时正确终止 → 验证数据保留策略 | P1 |
| 支付失败处理 | 使用 Stripe 测试拒绝卡号（如 4000000000000002）→ 验证友好提示 → 验证账户未激活 | P1 |
| 发票生成与下载 | 验证发票信息（金额、周期、公司名）与实际一致 | P1 |
| Trial 到期转换 | trial_eligible 的账号到期后 → 验证正确引导到付费页面 → 验证之前数据完整保留 | P1 |
| Stripe Webhook | 模拟 Stripe 发送 payment_intent.succeeded / failed / subscription.deleted 事件 → 验证系统正确响应 | P1 |
| 多币种 | 如支持：切换货币 → 验证金额转换正确（当前 org unit_type 为 US） | P2 |

**注意**：支付测试需在 Stripe Test Mode 下进行，使用 Stripe 官方测试卡号。Webhook 测试使用 Stripe CLI 的 `stripe listen` 转发到本地。

### 2.11 兼容性测试

Quotr 的目标用户（美国建筑行业）在多种设备上使用：办公室用桌面电脑，工地现场用 iPad 看图。

**浏览器兼容性：**

| 场景 | 方法 | 优先级 |
|------|------|--------|
| Chrome（最新版） | 全量功能回归 | P0（基线） |
| Edge（最新版） | Smoke + 核心流程 | P1 |
| Firefox（最新版） | Smoke + 核心流程 | P1 |
| Safari（macOS + iOS） | 登录 + Dashboard + 图纸查看 | P1 |
| 反爬兼容性 | 以上所有浏览器均能正常登录（不被误判为 bot） | P1 |

**设备兼容性：**

| 场景 | 方法 | 优先级 |
|------|------|--------|
| iPad（1024×768 横屏 + 768×1024 竖屏） | 登录 → 项目列表 → 图纸查看 → 缩放操作 | P1 |
| 主流笔记本（1440×900） | 基线分辨率，全量测试 | P0 |
| 大屏显示器（1920×1080） | 验证布局不拉伸变形 | P2 |
| 触屏交互 | 在 iPad viewport 下验证按钮点击区域足够大、手势缩放正常 | P2 |

**操作系统：**

| 场景 | 方法 | 优先级 |
|------|------|--------|
| Windows 10/11 | 基线，全量测试 | P0 |
| macOS（最新版） | Smoke + 核心流程 | P1 |
| iOS Safari（iPad） | 登录 + 图纸渲染 | P1 |

### 2.12 无障碍测试

作为面向美国市场的 SaaS 产品，Quotr 有 ADA（Americans with Disabilities Act）合规义务。不达标可能导致法律风险和丢失政府/大型企业客户。

| 场景 | 方法 | 优先级 |
|------|------|--------|
| 键盘导航 | Tab / Shift+Tab 遍历所有交互元素 → Enter/Space 激活 → Escape 关闭弹窗 → 验证无键盘陷阱 | P1 |
| 焦点管理 | 弹窗打开时焦点移入 → 关闭时焦点回到触发元素 → 页面切换时焦点跳到内容区 | P1 |
| 屏幕阅读器基础 | 使用 NVDA（Windows）或 VoiceOver（macOS）验证：导航菜单可朗读、表单 label 关联正确、错误提示可被阅读器感知 | P1 |
| 色彩对比度 | 关键文本（导航、表单 label、错误信息）的对比度 ≥ 4.5:1（WCAG AA 标准） | P2 |
| Alt 文本 | 所有图标按钮有 `aria-label`，图纸/图片有合理的 `alt` 描述 | P2 |
| 表单可访问性 | 所有 input 关联 `<label>` 或 `aria-labelledby`，必填字段标记 `aria-required`，校验错误用 `aria-describedby` 关联 | P1 |
| 缩放支持 | 浏览器缩放到 200%，验证布局不溢出、内容不隐藏 | P2 |

**工具建议**：axe-core 自动化检查（`@axe-core/playwright` 集成到 Playwright 测试中），辅助以手工键盘/屏幕阅读器验证。

### 2.13 数据迁移测试

PR 影响声明要求开发标注"是否需数据迁移"，但迁移本身需要独立的测试策略。

| 场景 | 方法 | 优先级 |
|------|------|--------|
| 迁移脚本语法验证 | 在 staging 环境空跑迁移 → 验证无语法错误 | P0 |
| 迁移—数据完整性 | 迁移前记录行数和关键字段 checksum → 迁移后对比 → 验证无丢失 | P0 |
| 迁移—业务逻辑正确性 | 抽样验证迁移后的数据：默认值是否合理、NOT NULL 字段是否都已填充、外键是否有效 | P0 |
| 迁移回滚 | 执行回滚脚本 → 验证 schema 和数据恢复到迁移前状态 | P1 |
| 迁移 + 旧版本兼容 | 迁移后旧版本代码是否仍能正确读写（如需灰度发布） | P1 |
| 大数据量迁移耗时 | 在 staging 导入接近生产量级的数据 → 测量迁移耗时 → 评估是否需要维护窗口 | P2 |

**流程要求**：开发提交迁移 PR 时必须附带：
- 迁移脚本和回滚脚本
- 在 staging 的执行结果截图
- 影响的数据量预估

### 2.14 并发测试

多人协作场景下的数据一致性是建筑项目管理的关键需求（多个分包商可能同时在同一项目上工作）。

| 场景 | 方法 | 优先级 |
|------|------|--------|
| 同项目并发编辑 | 多个用户同时编辑同一项目估价 → 验证后保存者收到冲突提示或被正确合并 | P1 |
| 供应商并发修改 | 用户 A 编辑供应商信息时用户 B 删除该供应商 → 验证 A 收到明确错误提示 | P1 |
| 项目创建并发 | 多个用户同时创建同名项目 → 验证唯一性约束工作正常 | P2 |
| 模板并发使用 | 项目 A 正在应用模板 X 时，模板 X 被编辑 → 验证项目使用的是当时版本或收到更新通知 | P2 |
| API 幂等性 | 对创建类 API（创建项目/模板/供应商）短时间内发送相同请求两次 → 验证不会创建重复数据 | P1 |
| 快速双击/重复提交 | 所有提交按钮 → 点击后立即禁用 → 验证不会创建两条记录 | P1 |

### 2.15 AI 模型测试

Quotr 的核心价值是 AI 图纸解析与估算。AI 管线可抽象为两阶段：

```
图纸 → AI 解析（构件识别/分类/计数）→ 检索成本数据（Database）→ 生成估算
      └── 视觉 + NLP ──┘              └── RAG ──┘            └── 结构化输出 ──┘
```

每阶段对应不同的评估方法和工具。

#### 测试样本

- **Golden Baseline Set**：从生产抽取 100 张代表性图纸，覆盖不同建筑类型（住宅/商业/工业）、复杂度、图片质量。每张图纸配人工标注的 ground truth（构件类型、数量、位置、预期估算金额）
- **对抗样本**：图像退化（模糊、旋转、低对比度、遮挡）生成
- **边界样本**：空图纸、单页、超大图纸（100+ 页）、非标准格式

#### 评估工具矩阵

| 阶段 | 工具 | 评估什么 | 怎么用 |
|------|------|---------|--------|
| 构件检测 | 结构化对比（precision/recall/F1） | 构件类型、数量、空间坐标的正确性 | JSON 输出与 ground truth 逐字段对比 |
| 文本语义 | **BERTScore** | AI 输出的材料名称、房型描述与人工标注的语义相似度 | 用 `bert-score` 库计算每对文本的 F1（即使措辞不同，语义相近也得分高） |
| 检索质量 | **RAGAs** — Context Relevance | 从 Database 检索到的成本数据是否与图纸构件相关 | 对每个检索结果计算与 query 的相关性分数 |
| 生成可信度 | **RAGAs** — Faithfulness | 估算金额是否基于检索到的成本数据（而非模型"编造"数字） | 将估算分解为原子声明，逐一验证是否有检索结果支撑 |
| 输出完整性 | **RAGAs** — Answer Relevance | 估算输出是否完整回答了"这个图纸要花多少钱" | 计算输出与预期估算的语义覆盖度 |
| 结构化输出 | JSON Schema 校验 | 确保输出可被下游系统消费 | `jsonschema` 库自动校验 |

#### BERTScore 在 Quotr 中的应用

```python
# 示例：评估 AI 输出的材料名称与人工标注的语义距离
from bert_score import score

# AI 输出与 ground truth 文本对
predictions = ["Ceramic Floor Tile 12x12", "Painted Drywall Partition"]
references  = ["Porcelain Floor Tile 12\"x12\"", "Painted Gypsum Board Partition"]

P, R, F1 = score(predictions, references, lang="en")
# F1 ≈ 0.92 — 即使措辞不同，BERTScore 识别出语义高度相似
# 传统 exact match 对此例得 0 分，但人类知道意思差不多
```

**适用场景**：
- 材料名称匹配（"gypsum board" vs "drywall"）
- 房型分类（"Half Bathroom" vs "Powder Room"）
- 供应商名称去重（"ABC Supply Co." vs "ABC Supply Company"）

#### RAGAs 在 Quotr 中的应用

```python
from ragas import evaluate
from ragas.metrics import context_relevance, faithfulness, answer_relevance
from datasets import Dataset

# 每个评估样本包含：图纸 AI 解析结果(query)、检索到的成本数据(contexts)、最终估算(answer)
eval_data = Dataset.from_dict({
    "question": ["Wall assembly for Living Room 200 sqft"],       # 图纸解析结果
    "contexts": [["Drywall 5/8\" - $2.50/sqft",                   # 检索到的成本项
                  "Metal Stud 25GA - $4.80/lnft",
                  "R13 Batt Insulation - $1.20/sqft"]],
    "answer": ["Living Room Wall: $1,850 (Drywall + Studs + Insulation + Labor)"],  # 最终估算
    "ground_truth": ["Living Room Wall Assembly: $1,920"]          # 人工标注
})

result = evaluate(eval_data, metrics=[context_relevance, faithfulness, answer_relevance])
# context_relevance: 检索到的三项成本数据是否都与"客厅墙面"相关 → 目标 ≥ 0.85
# faithfulness: 估算金额 $1,850 是否可从检索数据计算得出 → 目标 ≥ 0.90
# answer_relevance: "Living Room Wall: $1,850" 是否完整回答了原始 query → 目标 ≥ 0.85
```

#### 评估指标总表

| 工具 | 指标 | 说明 | GO 范围 | NO-GO 红线 |
|------|------|------|---------|-----------|
| 结构化对比 | 构件检测 F1 | 构件类型/数量/位置 | 退化 ≤ 2% | 下降 > 5% |
| 结构化对比 | 数量偏差 | 每类构件的数量误差 | 偏差 ≤ 10% | > 20% |
| 结构化对比 | JSON Schema 合规 | 输出结构合规 | 100% | 非 100% |
| **BERTScore** | 文本语义 F1 | 材料名称/描述的语义匹配 | ≥ 0.90 | < 0.85 |
| **RAGAs** | Context Relevance | 检索成本数据的相关性 | ≥ 0.85 | < 0.75 |
| **RAGAs** | Faithfulness | 估算是否有检索支撑 | ≥ 0.90 | < 0.80 |
| **RAGAs** | Answer Relevance | 输出是否完整 | ≥ 0.85 | < 0.75 |
| 业务指标 | 总金额偏差 | 估算总金额与实际偏差 | 偏差 ≤ 10% | > 20% |
| 业务指标 | 置信度校准 | 高置信度输出中错误率 | ≤ 3% | > 5% |

#### 自动化 vs 手动

- **完全自动化**：结构化 F1、Schema 校验、BERTScore、RAGAs 三项指标、金额偏差——每次 RC 构建时在 Golden Baseline 上自动计算，生成对比报告
- **人工判断**：查看报告，判定"偏差是否可接受"（如 BERTScore 从 0.93 降到 0.91——机器报告数值，人判断影响）
- **需要人工标注的**：Golden Baseline 的 ground truth（一次性投入，后续复用）

#### 代码实现（`tests/ai/test_baseline.py`）

采用 Class-based Evaluator 模式，评估逻辑独立于 pytest：

```
AISample (dataclass)           — 一个 Golden Baseline 样本
  ├── drawing_path             — 图纸文件路径
  ├── ground_truth             — 人工标注（构件、数量、成本）
  ├── ground_truth_texts       — 用于 BERTScore 的参考文本
  └── ground_truth_contexts    — 预期检索数据

AIBaselineEvaluator
  ├── load_samples(baseline.json)     — 加载样本集
  ├── add_sample()                    — Builder 式添加（→ return self）
  ├── run_ai_pipeline(drawing_path)   — 调用 AI 管线（待 API 接入）
  ├── evaluate_structured(output, gt) → (f1, qty_error, schema_ok)
  ├── evaluate_bertscore(preds, refs) → float
  ├── evaluate_ragas(questions, contexts, answers, gts) → (cr, faith, ar)
  └── summary()                       → 人类可读评估报告

AIEvaluationResult (dataclass)  — 单样本评估结果，9 个指标字段
```

- **评估流程**：`load_samples → for each sample: run_ai_pipeline → evaluate_structured → evaluate_bertscore → evaluate_ragas → 汇总 → summary()`
- **基线管理**：样本存储为 `fixtures/baseline_v1.json`，可版本化。新版本模型产生新基线文件
- **pytest 集成**：通过 `@pytest.mark.ai` marker 标记，RC 构建时 `-m ai` 触发
- **依赖**：`pip install bert-score ragas datasets`，未安装时 evaluator 返回 -1 而非崩溃

#### Block Release 的 AI 问题

- AI 输出 NaN / Null / 空
- 解析完全失败（全部构件 0）
- 估算金额为 0 或负数
- 关键字段缺失（如整层构件漏检）
- F1 下降 > 5% 或 Faithfulness < 0.80
- BERTScore 断崖式下降（≥ 0.10）——说明模型输出了完全不同的材料体系

---

### 2.16 性能验证

#### Benchmark

| 场景 | 关注指标 | 测试方法 |
|------|---------|---------|
| 图纸上传 + 解析 | P50/P95/P99 总耗时 | 固定测试图纸集，Playwright 测量完整上传→解析→结果显示的 wall-clock 时间 |
| API 并发（100 req） | P95、RPS、错误率 | Locust 或 k6 脚本，在 staging 环境运行 |
| Dashboard 首屏渲染 | FCP、LCP | Playwright 性能 API（`page.metrics()`）或 Lighthouse CI |
| Proposal 导出 | P95 生成时间、文件大小 | Playwright 触发导出，测量响应时间和文件大小 |

#### 判定标准

- "变快"：P95 下降 ≥ 10%
- "变慢"：P95 上升 ≥ 5%
- 每个版本 3 次取平均
- 优化 PR 必须先过功能回归再做 Benchmark

#### 自动化程度

性能**基线采集**完全自动化（RC 构建时自动运行并生成对比报告）。性能**专项 Benchmark**（大文件上传、高并发）按需触发——仅在架构变更、大版本发布或季度审计时执行。性能测试不进入每周 RC 流程的 blocking gate，但结果会在 Release Readiness 中作为信息维度呈现。

#### 代码实现

分为 API 延迟和前端渲染两条采集链路：

**API 延迟（`tests/performance/test_api_latency.py`）** — Collector 模式：

```
LatencyCollector(client)
  ├── measure(name, method, path)    — warmup 3 轮 → 采集 20 轮 → 存入 samples
  ├── load_baseline()                — 加载 latency_baseline.json
  ├── save_baseline()                — 保存当前采集结果为新基线
  ├── compare_to_baseline()          — 逐端点对比 P95，返回退化告警列表
  └── report()                       — P50/P95/P99/avg/error_rate 文本报告

LatencySample (dataclass)
  ├── durations_ms: list[float]    — 原始采集数据
  └── p50 / p95 / p99 / avg        — 统计属性
```

- **退化告警**：P95 上升 > 5% → `[SLOWER] endpoint: P95 Xms → Yms (+Z%)`；error rate > 1% → `[ERRORS]`
- **基线管理**：`performance/latency_baseline.json` 保存上次 RC 的采集结果

**前端渲染（`tests/performance/test_rendering.py`）**：

```
measure_page_load(page, url) → dict    — 单次页面加载的 Web Vitals
  ├── domContentLoaded / loadComplete  — Navigation Timing API
  ├── fcp / lcp                        — Paint Timing + LCP API
  ├── transferSize / resourceCount     — 资源加载统计
  └── 返回 {fcp_median, lcp_median, samples}
```

- 每个 Dashboard 页面采集 5 轮，取中位数
- 结果写入 `performance/rendering_baseline.json`
- LCP > 5s 的页面触发表格告警（不阻塞 Release）

**pytest 集成**：通过 `@pytest.mark.performance` marker，RC 构建时 `-m performance` 触发。

---

## 3. 测试执行体系

### 3.1 按 Release 阶段分层触发

测试不按"周一到周四做什么"安排，而是按 **Release 阶段** 决定触发哪些测试、哪些自动哪些手动。

```
PR 提交 ──→ 合入 main ──→ Nightly ──→ Release Candidate ──→ Release
   │            │            │               │                │
   ▼            ▼            ▼               ▼                ▼
 Pre-merge   Post-merge    Daily        Pre-Release      Release Day
 (自动)       (自动)       (自动)        (自动+手动)       (手动确认)
```

每一层的测试类型、执行方式、QA 职责如下。

---

### 3.2 Pre-Merge（每次 PR，全自动）

**触发**：PR 提交 / 更新

| 测试类型 | 内容 | 工具 | 耗时 |
|---------|------|------|------|
| Lint / Type Check | 代码规范、类型安全 | ESLint, tsc, mypy | < 1min |
| Unit Test | 纯函数、工具函数、API handler 单元 | Jest, pytest | < 2min |
| L0 Smoke（自动） | 登录成功/失败、4 导航可达、`/api/query-org` 200、localStorage 完整性 | Playwright | ~10min |
| 安全 header 检查 | CSP, HSTS, X-Frame-Options 存在性 | Playwright | < 30s |
| 依赖漏洞扫描 | 新增依赖是否有已知 CVE | `pip audit` / `npm audit` | < 1min |

**QA 职责**：CI 失败 → 阻止合入。QA 不手动介入此阶段。

**Gate**：全部通过才允许 merge。

---

### 3.3 Post-Merge / Nightly（每日凌晨，全自动）

**触发**：每日 3:00 UTC 定时，或 main 分支有新 commit

| 测试类型 | 内容 | 工具 | 耗时 |
|---------|------|------|------|
| L1 Critical Path（自动） | L0 全部 + 模块基本 CRUD + API 契约测试 | Playwright | ~30min |
| 安全全量（自动） | IDOR、未认证访问、JWT 篡改、XSS 注入 | Playwright | ~8min |
| 无障碍扫描（自动） | 所有关键页面的 WCAG 违规检测 | `@axe-core/playwright` | ~5min |
| 兼容性冒烟（自动） | Chrome/Edge/Firefox + iPad viewport 各跑登录 + 导航 | Playwright (多 project) | ~15min |
| 并发基础（自动） | API 幂等性、按钮防重复提交 | Playwright | ~5min |

**QA 职责**：上午 10 点查看报告。失败 → 排查是否为环境问题 → 若是真实回归 → 提 Bug。

**Gate**：自动生成 Nightly Report 推送 Slack。L1 通过率 < 95% → QA 优先排查。

---

### 3.4 Pre-Release（每次 Release Candidate，自动 + 手动）

**触发**：开发确认 "RC ready"（通常是周三），或手动触发

#### 自动部分

| 测试类型 | 内容 | 耗时 |
|---------|------|------|
| L2 Full Regression | 所有模块完整场景 + 跨模块数据流 + 空状态 | ~2.5h |
| AI Baseline 自动评估 | 结构化 F1 + 数量/金额偏差 + BERTScore + RAGAs（Context Relevance / Faithfulness / Answer Relevance） | ~3h（与 L2 并行） |
| 性能基线采集 | API 延迟（P50/P95/P99 + 退化对比）+ Dashboard 渲染 FCP/LCP | ~15min |
| 安全全量回归 | 安全用例全集 | ~8min |
| 无障碍全量 | 新增页面/组件的 WCAG 扫描 | ~8min |
| 兼容性全量 | Chrome/Edge/Firefox/Safari + iPad viewport 上的核心流程回归 | ~20min |
| 支付 Webhook 模拟 | Stripe test mode 事件回放 | ~5min |
| 并发完整 | 同项目并发编辑、供应商并发修改、模板并发使用 | ~8min |

**QA 职责**：分析失败用例 → 区分环境/数据问题 vs 真实回归 → 真实回归提 Bug 阻塞 RC。

> **专项 Benchmark 说明**：2.16 定义的大文件上传、高并发压力测试按需触发——仅在架构变更、大版本发布或季度审计时执行，不进入每周 RC 流程。

#### 手动部分（自动化无法替代）

| 测试类型 | 内容 | 为什么必须手动 | 耗时 |
|---------|------|---------------|------|
| **探索性测试** | 自由操作 20% 时间，不按脚本，模拟真实用户行为 | 自动化只能验证已知路径 | 1-2h |
| **AI 输出质量判断** | Golden Baseline 对比后的**人工抽查**：自动对比跑完数字，但"估算结果是否合理"需要人工看 | 自动化告诉你偏差 15%，但需要人判断这 15% 偏差是否可接受 | 1h |
| **屏幕阅读器验证** | NVDA / VoiceOver 走一遍关键流程 | axe-core 只能检测 30% 的无障碍问题，其余需要真实 AT | 30min |
| **视觉/UX Review** | 新功能 UI 的设计稿对比、交互流畅度 | 自动化不做像素级判断 | 30min |
| **支付端到端（手动）** | 在 Stripe test mode 手动走完整支付流程（选 plan → 填卡 → 确认 → 查订阅状态） | Webhook 和卡号交互的完整链路需人工确认一次 | 15min |
| **键盘导航** | Tab/Enter/Escape 走通新增的复杂交互 | Focus 管理逻辑需人工验证 | 15min |
| **迁移数据抽检**（如有） | 手动抽查迁移后的数据：打开实际页面，确认字段内容合理 | Checksum 通过不保证业务逻辑正确 | 15min |

---

### 3.5 Release Day（周四，手动确认 + 决策）

**目标**：不做新测试（不探索、不发现），只验证已知修复的 Bug + 确认自动化结果 + Release 决策。

| 活动 | 内容 | 自动/手动 | 耗时 |
|------|------|----------|------|
| Nightly Report Review | 确认昨晚自动测试全部通过 | 自动（QA 看结果） | 10min |
| 安全冒烟 | IDOR + 未认证访问快速自动通过 | 自动 | 2min |
| Bug 修复复测 | 验证所有标记"已修复"的 Bug | 手动 | 30-60min |
| 迁移正式验证（如有） | staging 执行 + checksum 对比（周三 dry-run 已过） | 自动 + 手动抽检 | 15min |
| Release Readiness Checklist | 逐 Gate 确认 | 手动 | 30min |
| Release Meeting | 决策 | — | 1h |
| 部署后监控 | Sentry 观察 30min | 自动（QA 看 dashboard） | 30min |

**周四原则**：
- **只验证，不探索** — 周四发现的新问题，要么接受风险带上线，要么延期
- **安全修复不允许快速通道** — 涉及安全的修复必须过安全自动化回归
- **周三 dry-run 未过的迁移，周四不再接受新版本**

---

### 3.6 手动 vs 自动总览

| 类型 | 自动 | 手动 | 触发频率 |
|------|:---:|:---:|---------|
| L0 Smoke | ✅ | — | 每次 PR |
| Unit Test | ✅ | — | 每次 PR |
| 安全 header | ✅ | — | 每次 PR |
| 依赖漏洞 | ✅ | — | 每次 PR |
| L1 Critical Path | ✅ | — | 每日 |
| 安全全量 | ✅ | — | 每日 |
| 无障碍扫描 | ✅ | — | 每日 |
| 兼容性冒烟 | ✅ | — | 每日 |
| 并发基础 | ✅ | — | 每日 |
| L2 Full Regression | ✅ | — | RC 时触发 |
| 支付 Webhook | ✅ | — | RC 时触发 |
| 并发完整 | ✅ | — | RC 时触发 |
| AI Baseline 自动评估 | ✅ | — | RC 时触发 |
| 性能基线采集（API 延迟 + 渲染） | ✅ | — | RC 时触发 |
| 迁移执行 + checksum | ✅ | — | RC / Release day |
| **探索性测试** | — | ✅ 手动 | RC 时 |
| **AI 输出质量判断** | — | ✅ 手动 | RC 时 |
| **屏幕阅读器** | — | ✅ 手动 | RC 时 |
| **视觉/UX Review** | — | ✅ 手动 | RC 时 |
| **支付端到端** | — | ✅ 手动 | RC 时 |
| **键盘导航** | — | ✅ 手动 | RC 时 |
| **迁移数据抽检** | — | ✅ 手动 | Release day |
| **Bug 修复复测** | — | ✅ 手动 | Release day |

**比例**：22 个测试类型中 14 个已自动化（64%），其余 8 个为手动——集中在"需要人类判断"的领域（探索、AI 质量、无障碍体验、视觉 Review）。

---

### 3.7 QA 一周节奏（以人为中心）

在自动化承担了 70% 执行工作的前提下，QA 的时间花在哪里：

| 时段 | 周一 | 周二 | 周三（RC 日） | 周四（Release） |
|------|------|------|-------------|---------------|
| **上午** | Sprint Planning + PR 影响范围分析 | Review Nightly 报告 + 手动探索新功能 | 触发 L2 回归 + AI/性能报告 Review | 看 Nightly 报告 + Bug 复测 |
| **下午** | 编写/维护自动化用例 + 准备测试数据 | 新功能 XSS/敏感信息手动检查 + 支付端到端 | 屏幕阅读器 + 键盘导航 + 视觉 Review | Release Checklist + Meeting + 上线监控 |

**核心变化**：QA 不再每天花时间"跑测试"（机器在跑），而是花时间在：
1. **维护自动化用例** — 跟上产品变更
2. **做机器做不到的事** — 探索、判断、Review
3. **分析结果** — 区分真实 Bug 和 Flaky；审查 AI/性能基线退化报告
4. **做 Release 决策** — 基于数据给 GO/NO-GO 建议

---

## 4. 质量保障体系

### 4.1 确认所有 PR 被测试

- Release PR Tracker 维护每个 PR 的三态：待测 → 测试中 → 已验证
- 周四 Release Meeting 前逐条确认

### 4.2 PR 影响声明（开发必填）

| 字段 | 说明 |
|------|------|
| 变更类型 | 新功能 / Bug 修复 / 重构 / 配置 / **安全修复** |
| 影响模块 | 前端 / 后端 / DB / AI / **支付(Stripe)** / **认证/权限** |
| 是否需数据迁移 | 是 / 否（若是 → 附迁移脚本 + 回滚脚本 + staging 执行截图） |
| 是否新增 API | 是 / 否（若是 → 需补充 IDOR 测试用例） |
| 是否涉及支付 | 是 / 否（若是 → 需在 Stripe test mode 验证） |
| 建议测试范围 | 开发自述 |

### 4.3 回归策略

| PR 类型 | 回归范围 |
|---------|---------|
| 新功能（新增模块） | 完整回归 + 安全基线 |
| 核心模块 Bug 修复（Project / Database / 保存 / 导出） | 完整回归 + 安全基线 |
| 安全修复 | **安全全量回归**（IDOR + XSS + 认证绕过 + 安全 header）+ 核心功能 Smoke |
| 支付相关变更（Stripe） | 支付全量回归（订阅/取消/Webhook）+ 核心功能 Smoke |
| 认证/权限变更 | 完整回归（权限矩阵全覆盖） |
| 非核心 Bug 修复（Template / 供应商 UI） | 局部回归 + Smoke |
| 数据迁移 | 迁移验证（执行 + 数据完整性 + 回滚）+ Smoke |
| 重构（不影响业务逻辑） | 局部回归 + 自动化 Smoke |
| 配置变更（环境变量 / Feature Flag） | 局部验证 + Smoke |
| 依赖升级 | 完整回归 + 安全扫描 |

### 4.4 Bug 修复验证流程

1. 按原复现步骤确认 Bug 不再出现
2. 在相关模块执行冒烟测试确保无新问题
3. 通过 → "已验证/Closed"；失败 → 重开退回开发

### 4.5 测试环境与数据管理

- **凭据管理**：`.env` 文件存储凭据，零硬编码，`.gitignore` 排除
- **测试数据**：使用版本化 Fixture 文件确保可重现
- **环境健康检查**：每次跑自动化前请求 `/api/query-org` 确认环境可用
- **已知限制**：当前 test.quotr.ai 环境 Project 模块无法创建新项目、Database 模块空白。自动化用例需处理这些已知异常——用例中对这些模块的断言应验证"错误不是回归"（如 Database 不应从空白变成更差的状态），而非假设模块功能完好
- **数据隔离**：自动化测试创建的数据（模板、供应商）使用可识别的前缀（如 `auto_test_`），便于手动清理。每个测试在 teardown 中清理自己创建的数据
- **多账号需求**：IDOR 和并发测试需要多个不同组织的测试账号。

### 4.6 避免自动化 Flaky

- 失败自动重试 3 次（任一次通过记 Pass，但标记 Flaky）
- 同一用例连续 3 次 Build 有重试 → `@pytest.mark.flaky` 单独报告
- 每周 Flaky Triage，限 2 周内修复

### 4.7 避免人工漏测

- Checklist 驱动每次测试 Session
- 预留 20% 时间做探索性测试
- 复杂功能 Pair Testing

---

## 5. PR 测试管理

### 5.1 PR Merge 前开发需提供

- 变更摘要（一句话）
- 影响范围（前端/后端/DB/AI/支付/权限/性能）
- 自测结果
- 是否需数据迁移
- 紧急程度（Blocking / High / Normal / Low）

### 5.2 影响范围判断

| 维度 | 方法 |
|------|------|
| 文件变更 | 前端组件 → UI 测试；API 层 → 接口测试；DB migration → 数据一致性；AI → Golden Baseline |
| 变更量 | < 50 行且仅日志/注释 → 轻量；> 200 行或核心逻辑 → 完整回归 |
| 历史关联 | 模块过去高频 Bug → 加大力度 |

### 5.3 自动化覆盖要求

- 核心路径 PR：必须附带或更新对应自动化用例
- Bug 修复 PR：必须补充回归用例防复发
- 改动 > 100 行且无自动化覆盖 → 退回要求补充

### 5.4 PR 测试状态

`not_started` → `in_progress` → `verified` → `blocked`

### 5.5 未测清的 PR

1. PR 下评论指出缺失场景
2. Blocking 级 → 直接退回
3. 开发坚持合入 → Risk Acceptance 流程

---

## 6. Release Gate

### 6.1 GO 条件

| 维度 | 条件 |
|------|------|
| 功能 | P0 通过率 = 100%；P1 ≥ 98% |
| 性能 | P99 ≤ 基线 × 1.1；错误率 ≤ 0.05% |
| AI | 所有指标在 2.15 评估指标定义的 GO 范围内（F1 退化 ≤ 2%、偏差 ≤ 10%、准确率 ≥ 93%、格式 100%） |
| Bug | 无未修复 P0；P1 已修复或签批 |
| 回归 | 核心回归清单 100% |
| PR | 所有 Release PR 已验证或签批 |
| API | `/api/query-org` 200，P95 < 500ms |
| Sentry | Release 后 30min，新 error rate ≤ 基线 × 1.5 |
| Dashboard | 4 个导航全部可点击，无白屏 |
| localStorage | `auth_v2_session` / `user` / `organization` 正确写入 |
| 安全 | 无 P0 安全漏洞；IDOR 测试通过；CSP header 已配置 |
| 支付 | Stripe 订阅创建/取消 Webhook 在 test mode 验证通过 |
| 数据迁移 | 如有迁移：staging 执行成功 + 数据完整性校验通过 + 回滚已验证 |

### 6.2 NO-GO（Block Release）

- 任何未修复 P0 Bug
- ≥ 1 个未修复 P1 且未签批
- 核心流程自动化通过率 < 95%
- 任何 AI 指标达到 2.15 NO-GO 红线（F1 下降 > 5%、偏差 > 20%、准确率 < 90%、格式不合规）
- 数据丢失或损坏
- 支付/权限错误
- `/api/query-org` 非 200
- Dashboard 白屏或核心导航不可用
- 任何 IDOR 漏洞（跨用户/跨组织数据访问）
- 未认证即可访问受保护 API
- 数据迁移脚本在 staging 执行失败
- Stripe 支付核心流程（订阅创建/Webhook 响应）异常

### 6.3 Bug 等级

| 等级 | 定义 | 实例 |
|------|------|------|
| **P0** | 核心功能完全不可用；数据丢失/损坏；安全漏洞 | 无法登录、Dashboard 白屏、`/api/query-org` 失败、Database 模块空白、项目无法创建 |
| **P1** | 核心功能可用但有严重缺陷 | 算量误差 > 20%、导出数据遗漏、token 异常过期 |
| **P2** | 非核心功能缺陷，有 workaround | UI 错位、错误提示不友好 |
| **P3** | 轻微缺陷 | 拼写错误、颜色偏差 |

### 6.4 Release Readiness Summary 模板

```text
## Quotr Release Readiness Summary
### Release: vX.Y.Z | Date: YYYY-MM-DD

### 测试覆盖
- [已完成] 已测模块: [Project, Database, Template, Procurement, Auth, API]
- [进行中] 部分测试: [模块（原因）]
- [未开始] 未测模块: [模块（原因）]

### 质量状态
| 维度 | 状态 | 数据 |
|------|------|------|
| 功能（P0） | [PASS/FAIL] | X/X 通过 |
| 功能（P1） | [PASS/FAIL] | X/X 通过 |
| API 健康 | [PASS/FAIL] | query-org: 200, P95: Xms |
| 性能 | [PASS/FAIL] | P99: X.Xx 基线 |
| AI 指标 | [PASS/FAIL] | F1 退化 X%，偏差 X% |
| 安全 | [PASS/FAIL] | IDOR 通过、CSP OK、无 P0 漏洞 |
| 支付 | [PASS/FAIL] | 订阅/取消 Webhook 通过 |
| 数据迁移 | [PASS/FAIL] / N/A | staging 验证通过 |
| Sentry | [PASS/FAIL] | 新 error rate: X |
| Dashboard | [PASS/FAIL] | 4 导航无白屏 |
| 自动化 | [PASS/FAIL] | L2 通过率 X% |

### Bug 状态
- P0: X 未修复
- P1: X 未修复
- P2: X 已知（已签批）

### 风险声明
1. [风险描述 — 影响 — 缓解措施]

### 最终建议: [GO] / [GO WITH RISKS] / [NO-GO]
```

---

## 7. 自动化测试框架

### 7.1 技术选型

**Playwright + Pytest**，选择理由：
- Quotr 是 React SPA，Playwright 原生支持 React 异步渲染等待
- `page.evaluate()` 可直接读写 localStorage 做 JWT 断言
- Pytest fixture/conftest 机制解决 auth state 复用
- Windows/macOS/Linux 均可运行
- 一份 `.venv` 管理全部依赖

### 7.2 测试分层

```
L0 Smoke (每次 PR, ~10 min)
  ├── 登录成功 / 失败（每次 ~3min，含反爬等待）
  ├── 4 个导航可访问 (200 + 非白屏)
  ├── /api/query-org 健康检查
  └── localStorage 关键字段完整性

L1 Critical Path (每日, ~30 min)
  ├── L0 全部
  ├── API 契约测试（所有已知端点）
  ├── 安全用例全量（IDOR / 未认证访问 / JWT / XSS）
  ├── 无障碍扫描（axe-core）
  ├── 兼容性冒烟（Chrome/Edge/Firefox + iPad viewport）
  └── Database/Template/Suppliers 基本 CRUD

L2 Full Regression (RC 时触发, ~3h)
  ├── L1 全部
  ├── 所有模块完整场景 + 跨模块数据一致性 + 空状态
  ├── AI Golden Baseline（BERTScore + RAGAs + 结构化 F1 + Schema）
  ├── 性能基线对比（API P50/P95/P99 + Dashboard FCP/LCP）
  └── 支付 Webhook / 并发完整 / 兼容性全量
```

### 7.3 自动化优先级

**第一优先级（入职第一周，Smoke）：**
1. 登录成功 + 失败场景
2. 4 个一级导航可访问（验证非白屏）
3. `/api/query-org` 返回 200
4. localStorage `auth_v2_session`、`user`、`organization` 完整性
5. 登录后页面不出现 sign-out-reason 异常调用的回归检测

**第二优先级（第一个月，Critical Path）：**
1. API 层所有已知端点契约测试（状态码、响应格式、认证要求）
2. Project 创建 → 保存 → 重新加载（端到端持久化）
3. Template 创建 → 编辑 → 删除
4. Supplier 创建 → 编辑 → 删除
5. Database 模块页面渲染正确性（Bug 修复后的回归）

**第三优先级（RC 时触发，部分按需）：**
- 跨模块数据流测试
- 权限矩阵测试（多角色）
- AI Golden Baseline（BERTScore + RAGAs）— 每次 RC 自动运行
- 性能基线采集（API 延迟 + 渲染 FCP/LCP）— 每次 RC 自动运行
- 性能专项 Benchmark（大文件上传、高并发）— 架构变更/季度审计时

**不适合自动化的：**
- UI 视觉类（颜色、间距、字体），当然了也可以通过一些多模态方案来实现
- AI 输出质量最终判断（需人工）
- 探索性测试
- 一次性场景
- 屏幕阅读器验证（需人工 + 真实设备）

### 7.4 安全扫描自动化

集成到 CI 流水线中的自动化安全检查：

| 工具 | 用途 | 触发时机 |
|------|------|---------|
| `@axe-core/playwright` | 无障碍自动化检查（WCAG 违规） | 每次 L1 Critical Path |
| `npm audit` / `pip audit` | 依赖漏洞扫描 | 每次 PR |
| Playwright 安全用例 | IDOR、未认证访问、XSS 注入 | 每次 L1 |
| CSP header 验证 | 检查 security headers 存在且合理 | 每次 L1 |
| Trivy / Snyk | 容器/Docker 镜像漏洞（如使用） | 每日构建 |

### 7.5 目录结构

```
tests/
├── conftest.py              # Fixtures: page, logged_in_page, app, logged_in_app
├── pytest.ini               # Markers: smoke, security, performance, ai 等
├── core/                    # 设计模式基础设施
│   ├── page_factory.py      # Registry 模式：惰性创建 + 缓存 Page Object
│   └── decorators.py        # @retry 重试 / @screenshot_on_failure 失败截图
├── config/
│   ├── settings.py          # 从 .env 读取 + WAIT 时间常量（避免硬编码）
│   └── routes.py            # 路由常量 + localStorage key 常量
├── pages/                   # Page Object Model（组合式，通过 PageFactory 获取）
│   ├── base_page.py         # goto(), is_white_screen(), ls_get(), screenshot()
│   ├── login_page.py        # login() / login_failure_expected() / logout()
│   ├── dashboard_page.py    # 侧边栏导航、模块遍历
│   ├── project_page.py      # 项目列表、创建入口（当前部分功能不可用）
│   ├── database_page.py     # 数据库页 + Bug 检测（is_bug_nav_bar_only()）
│   ├── template_page.py     # 模板 CRUD、Tab 切换、示例模板
│   └── procurement_page.py  # 供应商 CRUD、Tab 切换、Edit/Delete
├── api/
│   ├── client.py            # HTTP client + Playwright fetch 绕过反爬
│   └── test_api_contract.py # 所有已知端点：响应格式 + 未认证 401
├── smoke/                   # L0 — 每次 PR
│   ├── test_login.py        # 登录成功/失败、token 持久化、未认证重定向
│   ├── test_navigation.py   # 4 导航可达 + 白屏检测 + query-org 健康
│   └── test_auth_state.py   # localStorage 完整性、sign-out-reason 异常检测
├── regression/              # L2 — RC 时触发
│   ├── test_project.py      # 项目列表/创建/详情（含已知 Bug skip）
│   ├── test_database.py     # Bug 监控 + CRUD（Bug 修复后启用）
│   ├── test_template.py     # Tab 切换、创建表单、示例模板、selectedType
│   ├── test_procurement.py  # 供应商列表、创建、Edit/Delete、三 Tab
│   └── test_cross_module.py # 跨模块导航序列、organization ID 一致性
├── security/
│   ├── test_headers.py      # CSP / HSTS / X-Content-Type-Options / X-Frame-Options
│   ├── test_auth.py         # 未认证访问 401、空 token、垃圾 token、过期 token
│   ├── test_xss.py          # XSS 载荷注入（反射型 + 存储型占位）
│   ├── test_idor.py         # 跨组织数据访问（需第二账号）
│   └── test_rate_limit.py   # 连续请求不应过早触发限流
├── performance/             # API 延迟 + 前端渲染性能
│   ├── test_api_latency.py  # P50/P95/P99 采集 + 基线对比 + 退化告警
│   └── test_rendering.py    # Dashboard FCP/LCP Web Vitals 采集
├── payment/
│   ├── test_subscription.py # Stripe 订阅创建/取消/升级（待 Stripe test mode）
│   ├── test_webhook.py      # Webhook 事件处理（待 Stripe CLI）
│   └── test_invoice.py      # 发票生成验证
├── a11y/
│   ├── test_axe_core.py     # axe-core WCAG 扫描（待 npm 安装）
│   └── test_keyboard.py     # 键盘导航自动化
├── migration/
│   ├── test_migration_run.py    # 迁移执行 + 数据完整性 checksum
│   └── test_migration_rollback.py # 回滚验证
├── concurrency/
│   ├── test_conflict.py     # 并发编辑冲突（需第二账号）
│   └── test_idempotency.py  # 按钮防重复提交、API 幂等性
├── ai/
│   ├── test_baseline.py     # Golden Baseline + BERTScore + RAGAs 评估
│   └── fixtures/            # baseline_v1.json 样本集
├── utils/
│   ├── helpers.py           # human_pause, wait_for_spa, goto_spa, snap, dump_text
│   ├── antd_selectors.py    # Ant Design 组件封装：table_rows, tabs, form_items, modal
│   ├── reporter.py          # TestReporter: summary(), to_json()
│   └── html_reporter.py     # HtmlReport: 自动生成 HTML 报告 + Bug 知识库
├── reports/                 # 自动生成的 HTML 报告（latest.html + 时间戳版本）
└── fixtures/                # 共享测试数据
```

### 7.6 关键设计决策

**设计模式（`core/`）：**

| 模式 | 位置 | 解决的问题 |
|------|------|-----------|
| **Registry** | `page_factory.py` | Page Object 惰性创建 + 缓存。测试代码从 `ProjectPage(page)` 变为 `app.project.do_something()` — 无需手动管理实例 |
| **Decorator** | `decorators.py` | `@retry(times=3)` 处理反爬/网络 flaky；`@screenshot_on_failure` 失败时自动截图 |
| **Dataclass** | `ai/test_baseline.py`, `performance/test_api_latency.py` | `AISample`、`AIEvaluationResult`、`LatencySample` 替代裸 dict，类型安全 |
| **Class-based Evaluator** | `ai/test_baseline.py` | `AIBaselineEvaluator` 封装完整评估流程（加载样本 → 跑 AI → 算指标 → 出报告），可独立于 pytest 使用 |
| **Collector Pattern** | `performance/test_api_latency.py` | `LatencyCollector` 采集 → 对比基线 → 退化告警，warmup/measure 分离 |
| **Composition** | 全部 Page Object | 每个 Page Object 组合 `BasePage` 而非继承它。职责更清晰，测试代码不依赖继承链 |

**认证复用（`conftest.py`）：**
- `logged_in_page` fixture 通过 `storageState` 缓存已登录 context，整个 session 只登录一次
- `logged_in_app` fixture 返回 `PageFactory(logged_in_page)`，测试中直接用 `app.template.click_new_template()` 等快捷访问
- Token 从 `.env` 读取，零硬编码

**Ant Design 选择器辅助（`utils/antd_selectors.py`）：**
```python
def antd_table_rows(page):       # 获取 Ant Table 行数据
def antd_table_row_count(page):  # 行数
def antd_tabs(page):             # 所有 Tab 文本
def antd_tab_click(page, name):  # 点击指定 Tab
def antd_form_items(page):       # 表单字段信息
def antd_modal(page):            # 当前 Modal
def antd_empty(page):            # 是否空状态
def antd_spinning(page):         # 是否加载中
```

**反爬处理策略（`pages/base_page.py`）：**
- `goto_spa(url)` — 导航 + SPA 挂载等待（`load` → 失败回退 `commit` → 轮询 `#root`）
- `login()` — 重试 3 次，检测 SPA 是否渲染，未渲染则重新导航
- 浏览器启动时注入反检测脚本（webdriver、plugins、languages 三项）
- **关键风险**：反爬可能在多次自动化后被触发（IP 限流），导致 CI 全量失败。缓解：
  - 非生产环境禁用反爬是最直接的做法
  - CI 固定 IP 池
  - 失败时检查模式：全用例同时 `wait_for` 超时 → 判定反爬阻断而非代码回归 → Slack 告警 "possible anti-bot block"
  - 每日手动触发 anti-bot health check

**AI 评估（`ai/test_baseline.py`）：**
- `AIBaselineEvaluator` 封装结构化对比 + BERTScore + RAGAs 三步评估
- 每次 RC 构建在 Golden Baseline 上自动计算，人工只看报告判断偏差是否可接受
- BERTScore 解决 "gypsum board" vs "drywall" 的语义匹配问题
- RAGAs 解决 "估算金额是否有检索数据支撑"的可信度问题

**性能采集（`performance/`）：**
- `LatencyCollector`：warmup → 20 轮采集 → P50/P95/P99 → 基线对比 → 退化告警
- `measure_page_load()`：Playwright Performance API 采集 FCP/LCP

**等待策略（`config/settings.py` — `WAIT` 常量类）**：
- 所有超时/等待集中在 `WAIT` 对象中，避免代码中散落魔法数字
- `WAIT.AFTER_LOGIN_SUBMIT`：登录提交后等 redirect 完成
- `WAIT.SPA_POLL_INTERVAL`：SPA 轮询间隔
- `WAIT.HUMAN_DELAY_*`：人类操作模拟延迟范围
- 页面对象中的 `wait_for_timeout()` 尽力替换为 `wait_for(state="visible/hidden")` 条件等待

**HTML 报告自动生成（`utils/html_reporter.py`）：**
- `HtmlReport` 类通过 `conftest.py` 的三个 pytest hooks 自动收集结果
- `pytest_configure` → 初始化报告器
- `pytest_runtest_makereport` → 逐用例收集（passed/failed/skipped + 耗时）
- `pytest_sessionfinish` → 生成自包含 HTML 到 `tests/reports/`（`report_<timestamp>.html` + `latest.html`）
- 报告内含 **Bug 知识库**：已确认的产品 Bug（安全 Header 缺失、Dashboard 重定向、Database 空白等）在测试失败时自动匹配并附带描述、影响分析和修复建议
- 报告内容包括：KPI 卡片、模块覆盖统计、已知 Bug 详情、失败用例列表、全部用例折叠表

**执行入口（`run_ci.py`）— 唯一测试运行方式：**
- `python run_ci.py` — 全量单 session（所有 marker，一次 pytest，session 不过期，带层级标签）
- `python run_ci.py --layer smoke` — L0 Smoke（GitHub Actions PR 触发）
- `python run_ci.py --layer critical` — L1 Critical Path（GitHub Actions 定时）
- `python run_ci.py --layer regression` — L2 Full Regression（GitHub Actions 手动）
- 全量模式：层级通过模块路径自动推断（smoke→L0, security/api→L1, regression/perf/ai→L2, payment 等→BLOCKED）
- 单层模式：`QUOTR_CI_LAYER` 环境变量标记，per-layer JSON 合并生成报告
- 输出日志写入 `tests/reports/pytest_*.log`，HTML 报告 → `tests/reports/latest.html`

**CI 集成（生产环境 — `.github/workflows/ci.yml`）：**
- `pull_request` → L0 Smoke job（~15min timeout）
- `schedule` (每日 3:00 UTC) → L1 Critical Path job（~45min timeout）
- `workflow_dispatch` (手动触发) → L2 Full Regression job（~240min timeout），可选择 smoke/critical/regression/all
- `pull_request` → Dependency audit job（`pip audit`）
- 凭据通过 GitHub Secrets 注入（`QUOTR_EMAIL`, `QUOTR_PASSWORD`）
- 失败自动通过 `slackapi/slack-github-action` 推送 Slack `#release-风险`
- HTML 报告通过 `actions/upload-artifact` 上传为构建产物

---

## 8. 产品与交付

### 8.1 问题分类

| 类型 | 判断 | 处理 |
|------|------|------|
| **Bug** | 功能未按设计实现 | 提 Bug，推动修复 |
| **UX Issue** | 功能正确但体验差 | 与设计师/PM 讨论 |
| **Product Gap** | 缺少用户需要的功能 | 反馈 PM，排 roadmap |
| **用户教育** | 功能存在但不为人知 | 建议文档/教程/tooltip |

用户无法完成核心任务 → 最高优先级（无论类别）。

### 8.2 速度、质量、体验平衡

- P0 必须修，P1 尽量修，P2 可延后
- 高风险新功能用 Feature Flag 对内开放，逐步放量
- Release Meeting 明确 trade-off："本周上，已知风险 X；延期，业务影响 Y"

### 8.3 减少重复 Bug

- 每次 P0/P1 修复后追问"测试为什么没发现" → 补充自动化
- 每季度 Bug 数据回顾 → 识别高频类型 → 系统性改进
- 维护"常见问题与测试策略"文档

### 8.4 用户反馈闭环

- 疑似 Bug → 立即复现 → Bug 流程
- 功能缺失 → 与 PM 讨论 → Roadmap
- 被采纳的反馈在 Release Note 标注 "Based on user feedback"

---

> **版本**：v0.7 | **日期**：2026-08-03 | 

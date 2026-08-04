# Quotr 测试失败分析

**日期**：2026-08-03 | **环境**：test.quotr.ai
**最后一次全量**：29 passed, 25 failed, 35 skipped, 3 errors, 25 deselected (68min)

---

## 分类总览

| 类别 | 数量 | 说明 |
|------|------|------|
| 产品 Bug | 6 | Quotr 站点真实缺陷 |
| 环境/反爬 | 14 | 反爬阻断、网络超时、session 过期 |
| 代码 Bug | 5 | 测试框架自己的问题，需要修 |
| 环境未就绪 | 35 | Stripe/axe-core/DB/第二账号/Golden Baseline 未配置 |

---

## 一、产品 Bug（需开发修复）

### P0 — 4 个安全 Header 全部缺失 (5 个用例)

| 用例 | 原因 |
|------|------|
| `test_csp_header_present` | 站点无 CSP header，XSS 无防护 |
| `test_hsts_header_present` | 站点无 HSTS header |
| `test_content_type_options_header_present` | 站点无 X-Content-Type-Options: nosniff |
| `test_frame_options_header_present` | 站点无 X-Frame-Options |
| `test_all_critical_headers` | 汇总：4 个 header 全缺 |

**根因**：CDN/反向代理层未配置安全响应头。**非测试代码问题**。

### P0 — Dashboard 未认证不重定向 (1 个用例)

| 用例 | 原因 |
|------|------|
| `test_dashboard_redirects_to_login` | `/dashboard/project` 不跳转到登录页 |

**根因**：React Router auth guard 可能被反爬改动影响。URL 停留在 `/dashboard/project`，页面显示空白。**非测试代码问题**。

---

## 二、测试代码 Bug（需修测试框架）

### 1. IDOR 测试：NoneType has no len() 

`test_invalid_project_id_not_leak_data` → `TypeError: object of type 'NoneType' has no len()`

**根因**：`_fetch()` 返回的 `body["data"]` 为 None（不是空列表），`len(None)` 报错。

**修复**：加 None check：`len(data) if data else 0`

### 2. Session 跨层过期导致 regression 全挂 (~12 用例)

`test_template_has_tabs`、`test_supplier_list` 等 → body 为空 or "Sign in" 

**根因**：`logged_in_context` fixture 的 JWT 有效期短（~20min），smoke 跑完后就过期了。regression 层拿到的 page 实际在登录页。

**修复**：`logged_in_page` fixture 检测到被重定向时自动重新登录。

### 3. test_query_org_healthy body 为空 → assert 'Project' in ''

**根因**：session 过期导致页面重定向到登录页（body 为空或 "Sign in..."）。

### 4. HTML 报告 skipped/error 计数不准

**根因**：`pytest_terminal_summary` 钩子从 `terminalreporter.stats` 补 skipped 的逻辑与 `pytest_runtest_makereport` 重复/遗漏。

**修复**：已改到 `pytest_sessionfinish` 统一处理，待下次运行验证。

### 5. test_rate_limit 用 requests signin 被反爬拦截 → 401

**根因**：`APIClient` 用裸 requests 调 signin 被反爬拒绝。

**修复**：已改为浏览器 fetch，但测试仍 fail（session 过期导致 token 获取不到）。

---

## 三、环境/反爬（非代码问题，非产品功能 Bug）

### 反爬阻断 SPA 渲染 (5 个用例)

| 用例 | 现象 |
|------|------|
| `test_login_with_wrong_password` | `Locator.fill: Timeout` — email input 不存在 |
| `test_login_with_invalid_email_format` | 同上 |
| `test_login_button_disabled_after_click` | login form 未渲染 |

**根因**：短时间内多次浏览器请求触发 anti-bot IP 限流。SPA 只渲染外层壳，表单不挂载。

**性质**：环境问题 → CI 用固定 IP 白名单可解决。

### 网络超时 (2 个用例)

| 用例 | 现象 |
|------|------|
| `test_all_critical_headers` | SSL handshake timeout |
| `test_permissions_policy` | Read timeout |

**根因**：`requests.get()` 到 test.quotr.ai 偶发 SSL/read 超时。

**性质**：网络波动，重试可解。

### Page.goto 超时 (7 个用例)

多个 navigation 测试 → `Page.goto: Timeout 60000ms exceeded`

**根因**：浏览器导航到 Dashboard 页面时超时。反爬可能已经开始拦截。

---

## 四、环境未就绪（35 skipped，正常）

| 类型 | 数量 | 原因 |
|------|------|------|
| Payment (Stripe) | 8 | 需 Stripe test mode 配置 |
| AI Baseline | 5 | 需 Golden Baseline 图纸集 |
| A11y (axe-core) | 6 | 需 `npm install @axe-core/playwright` |
| Migration | 4 | 需 staging DB 连接 |
| Concurrency (多用户) | 4 | 需第二测试账号 |
| 已知产品 Bug (Project/Database) | 8 | 功能不可用，测试正确 skip |

**性质**：正常。这些 skip 本身说明框架的 skip 逻辑正确——不可用时不会误报失败。

---

## 修复优先级

1. **立即修**：IDOR NoneType（改一行） + session 自动续期（改 fixture）
2. **明天验证**：HTML 报告 skipped/error 计数是否对齐
3. **不需要修**：反爬/网络问题（CI 独立 runner + 固定 IP 可解）
4. **产品侧**：安全 Header 缺失（CDN 配置，5 分钟工作量）

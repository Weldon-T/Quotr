# Quotr Test Framework

Playwright + Pytest 自动化测试框架，覆盖 Quotr 测试站点 (test.quotr.ai)。

## 运行

```bash
# 全量测试（单 session，~90min）
python run_ci.py

# 按层级（GitHub Actions 触发）
python run_ci.py --layer smoke       # L0 Smoke
python run_ci.py --layer critical    # L1 Critical Path
python run_ci.py --layer regression  # L2 Full Regression
```

## 结构

```
tests/
├── smoke/        L0 — 每次 PR（登录/导航/localStorage）
├── security/     安全（Header/认证/XSS/IDOR）
├── regression/   L2 — RC 触发（Template/Procurement/跨模块）
├── api/          API 契约（响应格式/认证要求）
├── payment/      Stripe 支付（待 test mode）
├── a11y/         无障碍（待 axe-core）
├── ai/           AI Golden Baseline（BERTScore + RAGAs）
├── performance/  API 延迟 + 渲染性能
├── concurrency/  并发冲突
├── migration/    数据迁移
├── pages/        Page Object Model
├── core/         Registry / Decorator 设计模式
├── utils/        HTML 报告生成 / Ant Design 选择器
└── config/       路由常量 / 配置
```


## 报告

`tests/reports/latest.html` — 自包含 HTML，含 KPI / 层级 / 模块 / Bug / 全部用例详情。

`tests/reports/analysis.txt` — 最新全量运行的分析摘要。

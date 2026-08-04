"""HTML 测试报告生成器。

架构（无全局状态，无跨层污染）：

  直接模式（本地 pytest）:
    pytest → hooks 收集 → pytest_sessionfinish 生成 HTML

  CI 分层模式（run_ci.py）:
    pytest L0 → hooks 收集 → 写入 ci_layer_L0-smoke.json
    pytest L1 → hooks 收集 → 写入 ci_layer_L1-security.json
    pytest L2 → hooks 收集 → 写入 ci_layer_L2-regression.json
    run_ci.py → HtmlReport.from_layer_files() → 合并生成统一 HTML
"""
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Optional

REPORT_DIR = Path("tests/reports")
REPORT_DIR.mkdir(exist_ok=True)


# ---- Bug 知识库 ----
BUG_KB = {
    "test_csp_header_present": {
        "id": "BUG-001", "title": "Content-Security-Policy header 缺失", "severity": "P0", "module": "Security",
        "description": "HTTP 响应缺少 CSP header，站点无 XSS 防护。Quotr 将 JWT 存储于 localStorage，XSS 可导致 token 泄露。",
        "fix": "在 Cloudflare/CDN 层添加 Content-Security-Policy 响应头。",
    },
    "test_hsts_header_present": {
        "id": "BUG-001", "title": "Strict-Transport-Security header 缺失", "severity": "P0", "module": "Security",
        "description": "缺少 HSTS header，无法强制 HTTPS，存在中间人攻击风险。",
        "fix": "添加 Strict-Transport-Security: max-age=31536000; includeSubDomains",
    },
    "test_content_type_options_header_present": {
        "id": "BUG-001", "title": "X-Content-Type-Options header 缺失", "severity": "P0", "module": "Security",
        "description": "缺少 nosniff 指令，浏览器可能进行 MIME 类型嗅探。",
        "fix": "添加 X-Content-Type-Options: nosniff",
    },
    "test_frame_options_header_present": {
        "id": "BUG-001", "title": "X-Frame-Options header 缺失", "severity": "P0", "module": "Security",
        "description": "站点可被嵌入 iframe，存在 Clickjacking 攻击风险。",
        "fix": "添加 X-Frame-Options: DENY 或 SAMEORIGIN",
    },
    "test_dashboard_redirects_to_login": {
        "id": "BUG-002", "title": "未认证用户访问 Dashboard 不强制重定向", "severity": "P0", "module": "Auth",
        "description": "未登录状态下访问 /dashboard/project，页面停留不重定向到登录页。可能是反爬改动的副作用。",
        "fix": "检查 React Router auth guard 逻辑。",
    },
    "test_query_org_healthy": {
        "id": "BUG-003", "title": "Dashboard 白屏或 query-org 异常", "severity": "P0", "module": "Dashboard",
        "description": "/api/query-org 是 Dashboard 加载的第一个 API，失败会导致整个 Dashboard 白屏。",
        "fix": "优先排查 query-org 返回值和 SPA 渲染逻辑。",
    },
    "test_database_bug_not_regressed": {
        "id": "BUG-004", "title": "Database 模块主内容区空白", "severity": "P0", "module": "Database",
        "description": "/dashboard/database 仅渲染侧边栏，主内容区无任何 DOM 元素。无 console error。",
        "fix": "检查 React Router 中 Database 路由注册和 Suspense/lazy 配置。",
    },
}


class HtmlReport:
    """收集一次 pytest session 的结果并生成 HTML 报告。"""

    def __init__(self):
        self._start = time.time()
        self.results: list[dict] = []
        self.bugs: dict[str, dict] = {}
        self._bug_ids: set[str] = set()
        self._layer: str = ""

    def set_layer(self, name: str):
        self._layer = name

    # ---- Hook 接口 ----

    def add_result(self, nodeid: str, outcome: str, duration: float = 0, phase: str = "", layer: str = ""):
        # 去重：同一个 nodeid 只记录一次，call 阶段结果覆盖 setup 阶段
        for r in self.results:
            if r["nodeid"] == nodeid:
                r["outcome"] = outcome
                r["duration"] = duration
                r["phase"] = phase
                if layer:
                    r["layer"] = layer
                return
        self.results.append({
            "nodeid": nodeid, "outcome": outcome, "duration": duration,
            "phase": phase, "layer": layer or self._layer,
        })
        # 匹配已知 Bug
        test_name = nodeid.split("::")[-1]
        if outcome in ("failed", "error") and test_name in BUG_KB:
            info = BUG_KB[test_name]
            bid = info["id"]
            if bid not in self._bug_ids:
                self._bug_ids.add(bid)
                self.bugs[bid] = dict(info)

    # ---- 统计 ----

    @property
    def total(self) -> int: return len(self.results)

    @property
    def passed(self) -> int: return sum(1 for r in self.results if r["outcome"] == "passed")

    @property
    def failed(self) -> int: return sum(1 for r in self.results if r["outcome"] == "failed")

    @property
    def skipped(self) -> int: return sum(1 for r in self.results if r["outcome"] == "skipped")

    @property
    def errors(self) -> int: return sum(1 for r in self.results if r["outcome"] == "error")

    @property
    def blocked(self) -> int:
        return sum(1 for r in self.results if r["outcome"] == "skipped" and any(
            kw in r.get("nodeid", "") for kw in ["payment", "a11y", "migration", "stripe", "axe", "baseline"]
        ))

    def pass_rate(self) -> float:
        t = self.total
        return self.passed / t * 100 if t > 0 else 100

    def layer_stats(self) -> list[dict]:
        layers: dict[str, dict] = {}
        for r in self.results:
            name = r.get("layer", "") or "—"
            if name not in layers:
                layers[name] = {"passed": 0, "failed": 0, "skipped": 0, "error": 0, "blocked": 0, "total": 0}
            layers[name][r["outcome"]] = layers[name].get(r["outcome"], 0) + 1
            layers[name]["total"] += 1
        return [{"name": k, **v} for k, v in sorted(layers.items())]

    def module_stats(self) -> list[dict]:
        modules: dict[str, dict] = {}
        for r in self.results:
            parts = r["nodeid"].split("::")[0].replace("tests/", "").split("/")
            mod = parts[0] if parts[0] else "root"
            if mod not in modules:
                modules[mod] = {"passed": 0, "failed": 0, "skipped": 0, "error": 0, "total": 0}
            modules[mod][r["outcome"]] = modules[mod].get(r["outcome"], 0) + 1
            modules[mod]["total"] += 1
        return [{"name": k, **v} for k, v in sorted(modules.items())]

    # ---- 持久化 ----

    def save_layer_json(self):
        """CI 模式：写入当前层的 JSON 文件。不清除内存状态。"""
        if not self._layer:
            return
        path = REPORT_DIR / f"ci_layer_{self._layer}.json"
        path.write_text(json.dumps({"results": self.results, "layer": self._layer}, ensure_ascii=False, indent=2))

    @classmethod
    def from_layer_files(cls) -> "HtmlReport":
        """CI 模式：读取所有 per-layer JSON，合并为一个 HtmlReport。"""
        merged = cls()
        merged._layer = "ALL"
        seen = set()
        for f in sorted(REPORT_DIR.glob("ci_layer_*.json")):
            data = json.loads(f.read_text())
            for r in data.get("results", []):
                nid = r["nodeid"]
                if nid not in seen:
                    seen.add(nid)
                    merged.results.append(r)
                    merged.add_result(nid, r["outcome"], r.get("duration", 0), r.get("phase", ""))
        return merged

    # ---- HTML 生成 ----

    def generate(self, path: str = None) -> Path:
        p = Path(path or (REPORT_DIR / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"))
        p.write_text(self._render(), encoding="utf-8")
        latest = REPORT_DIR / "latest.html"
        latest.write_text(self._render(), encoding="utf-8")
        return p

    def _render(self) -> str:
        stats = self.module_stats()
        layers = self.layer_stats()
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Quotr Test Report — {datetime.now().strftime('%Y-%m-%d %H:%M')}</title>
<style>
:root{{--pass:#22c55e;--fail:#ef4444;--skip:#f59e0b;--error:#f97316;--blocked:#6366f1;--bg:#0f172a;--card:#1e293b;--border:#334155;--text:#e2e8f0;--muted:#94a3b8}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:var(--bg);color:var(--text);line-height:1.6}}
.container{{max-width:1200px;margin:0 auto;padding:24px}}
h1{{font-size:28px;margin-bottom:4px}}h2{{font-size:20px;margin:32px 0 16px;padding-bottom:8px;border-bottom:2px solid var(--border)}}
.subtitle{{color:var(--muted);font-size:14px;margin-bottom:24px}}
.grid{{display:grid;gap:16px}}.grid4{{grid-template-columns:repeat(4,1fr)}}.grid5{{grid-template-columns:repeat(5,1fr)}}
@media(max-width:768px){{.grid4,.grid5{{grid-template-columns:1fr}}}}
.card{{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:20px}}
.stat-value{{font-size:36px;font-weight:700}}.stat-label{{font-size:13px;color:var(--muted);margin-top:4px}}
.pass{{color:var(--pass)}}.fail{{color:var(--fail)}}.skip{{color:var(--skip)}}.error{{color:var(--error)}}.blocked{{color:var(--blocked)}}
.badge{{display:inline-block;padding:2px 10px;border-radius:12px;font-size:12px;font-weight:600}}
.badge-p0{{background:#7f1d1d;color:#fca5a5}}.badge-p1{{background:#78350f;color:#fcd34d}}
table{{width:100%;border-collapse:collapse;font-size:14px}}
th,td{{padding:10px 14px;text-align:left;border-bottom:1px solid var(--border)}}
th{{color:var(--muted);font-weight:600;font-size:12px;text-transform:uppercase}}
tr:hover{{background:rgba(255,255,255,0.02)}}
.dot{{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px}}
.dot-p{{background:var(--pass)}}.dot-f{{background:var(--fail)}}.dot-s{{background:var(--skip)}}.dot-e{{background:var(--error)}}.dot-b{{background:var(--blocked)}}
details{{margin:8px 0}}details summary{{cursor:pointer;padding:10px 14px;background:var(--card);border:1px solid var(--border);border-radius:8px;font-weight:600}}
details .content{{padding:16px;border-left:2px solid var(--border);margin-left:14px}}
.bug-card{{border-left:4px solid var(--fail);padding:16px;margin:12px 0;background:var(--card);border-radius:0 8px 8px 0}}
.bug-card h4{{margin-bottom:8px}}.bug-card .meta{{font-size:12px;color:var(--muted);margin-bottom:8px}}
footer{{text-align:center;color:var(--muted);font-size:12px;margin-top:48px;padding:24px;border-top:1px solid var(--border)}}
</style>
</head>
<body>
<div class="container">
<h1>Quotr 测试报告</h1>
<p class="subtitle">环境：test.quotr.ai | {datetime.now().strftime('%Y-%m-%d %H:%M')} | Playwright + Pytest | 模式：{'CI 分层累积' if layers[0]['name'] != '—' else '完整单次'}</p>

<h2>执行摘要</h2>
<div class="grid grid5">
<div class="card"><div class="stat-value">{self.total}</div><div class="stat-label">总用例</div></div>
<div class="card"><div class="stat-value pass">{self.passed}</div><div class="stat-label">通过</div></div>
<div class="card"><div class="stat-value fail">{self.failed}</div><div class="stat-label">失败</div></div>
<div class="card"><div class="stat-value skip">{self.skipped}</div><div class="stat-label">跳过</div></div>
<div class="card"><div class="stat-value error">{self.errors}</div><div class="stat-label">错误</div></div>
</div>
<div class="grid grid5" style="margin-top:16px">
<div class="card"><div class="stat-value pass">{self.pass_rate():.0f}%</div><div class="stat-label">通过率</div></div>
<div class="card"><div class="stat-value">{len(self._bug_ids)}</div><div class="stat-label">产品 Bug</div></div>
<div class="card"><div class="stat-value blocked">{self.blocked}</div><div class="stat-label">阻塞 (Env)</div></div>
<div class="card"><div class="stat-value">{len(stats)}</div><div class="stat-label">模块</div></div>
<div class="card"><div class="stat-value">{datetime.now().strftime('%H:%M')}</div><div class="stat-label">生成时间</div></div>
</div>

<h2>模块覆盖</h2>
<table>
<tr><th>模块</th><th>用例</th><th>通过</th><th>失败</th><th>跳过</th><th>错误</th><th>通过率</th></tr>
{self._module_rows(stats)}
</table>

<h2>发现的 Bug{'（本次未触发）' if not self.bugs else ''}</h2>
{self._bug_cards()}

<h2>全部用例详情</h2>
<details><summary>查看全部 {self.total} 个用例</summary><div class="content"><table>
<tr><th>层级</th><th>模块</th><th>用例</th><th>结果</th><th>耗时</th></tr>
{self._all_rows()}
</table></div></details>

<footer>Quotr Test Report — Auto-generated — {datetime.now().isoformat()}</footer>
</div>
</body>
</html>"""

    def _module_rows(self, stats: list) -> str:
        rows = []
        for s in stats:
            t = s["total"]
            pct = f'{s["passed"]/t*100:.0f}%' if t > 0 else '—'
            rows.append(
                f'<tr><td><strong>{s["name"]}</strong></td><td>{t}</td>'
                f'<td><span class="dot dot-p"></span>{s["passed"]}</td>'
                f'<td><span class="dot dot-f"></span>{s["failed"]}</td>'
                f'<td><span class="dot dot-s"></span>{s["skipped"]}</td>'
                f'<td><span class="dot dot-e"></span>{s.get("error", 0)}</td>'
                f'<td>{pct}</td></tr>'
            )
        return "\n".join(rows) if rows else "<tr><td colspan='7'>无数据</td></tr>"

    def _all_rows(self) -> str:
        rows = []
        for r in self.results:
            icon = {"passed": "dot-p", "failed": "dot-f", "skipped": "dot-s", "error": "dot-e"}.get(r["outcome"], "")
            layer = r.get("layer", "—")
            parts = r["nodeid"].split("::")[0].replace("tests/", "").split("/")
            mod = parts[0] if parts else "root"
            rows.append(
                f'<tr><td>{layer}</td><td>{mod}</td><td style="font-size:12px">{r["nodeid"]}</td>'
                f'<td><span class="dot {icon}"></span>{r["outcome"]}</td>'
                f'<td>{r["duration"]:.1f}s</td></tr>'
            )
        return "\n".join(rows) if rows else "<tr><td colspan='5'>无数据</td></tr>"

    def _bug_cards(self) -> str:
        if not self.bugs:
            return "<p style='color:var(--pass)'>本次运行未触发已知产品 Bug。</p>"
        cards = []
        for bid, info in self.bugs.items():
            sev_class = "badge-p0" if info["severity"] == "P0" else "badge-p1"
            cards.append(
                f'<div class="bug-card">'
                f'<h4>{info["title"]} <span class="badge {sev_class}">{info["severity"]}</span></h4>'
                f'<div class="meta"><span>模块：{info["module"]}</span><span>ID：{info["id"]}</span></div>'
                f'<p>{info["description"]}</p><p><strong>修复：</strong>{info["fix"]}</p></div>'
            )
        return "\n".join(cards)

"""Performance: Dashboard 首屏渲染性能测试。

使用 Playwright Performance API 采集 FCP、LCP 等 Web Vitals。
"""
import json
import pytest
from pathlib import Path
from statistics import median

from tests.config.routes import PROJECT_LIST, DATABASE, TEMPLATE, SUPPLIERS

BASELINE_FILE = Path(__file__).parent / "rendering_baseline.json"
MEASURE_ROUNDS = 5

PAGE_ROUTES = {
    "Project": PROJECT_LIST,
    "Database": DATABASE,
    "Template": TEMPLATE,
    "Suppliers": SUPPLIERS,
}


def measure_page_load(page, url: str) -> dict:
    """测量单次页面加载的 Web Vitals。"""
    page.goto(url, wait_until="commit")
    page.wait_for_timeout(6000)  # 等 SPA 挂载

    metrics = page.evaluate("""() => {
        const nav = performance.getEntriesByType('navigation')[0];
        const paint = performance.getEntriesByType('paint');
        const fcp = paint.find(p => p.name === 'first-contentful-paint');
        const lcpEntry = performance.getEntriesByType('largest-contentful-paint').pop();
        return {
            domContentLoaded: nav.domContentLoadedEventEnd - nav.fetchStart,
            loadComplete: nav.loadEventEnd > 0 ? nav.loadEventEnd - nav.fetchStart : -1,
            fcp: fcp ? fcp.startTime : -1,
            lcp: lcpEntry ? lcpEntry.startTime : -1,
            transferSize: nav.transferSize || 0,
            resourceCount: performance.getEntriesByType('resource').length,
        };
    }""")

    # 确保是数值
    return {k: float(v) for k, v in metrics.items()}


@pytest.mark.performance
@pytest.mark.p2
class TestRenderingPerformance:

    def test_dashboard_pages_fcp_lcp(self, logged_in_app):
        """所有 Dashboard 页面的 FCP/LCP 采集。"""
        results = {}
        for name, route in PAGE_ROUTES.items():
            samples = []
            for _ in range(MEASURE_ROUNDS):
                metrics = measure_page_load(logged_in_app.page, f"https://test.quotr.ai{route}")
                samples.append(metrics)
            results[name] = {
                "fcp_median": median(s["fcp"] for s in samples if s["fcp"] > 0),
                "lcp_median": median(s["lcp"] for s in samples if s["lcp"] > 0),
                "samples": len(samples),
            }
        print("\nRendering Performance Report")
        print("-" * 40)
        for name, r in results.items():
            print(f"  {name}: FCP={r['fcp_median']:.0f}ms LCP={r['lcp_median']:.0f}ms (n={r['samples']})")
        BASELINE_FILE.parent.mkdir(exist_ok=True)
        BASELINE_FILE.write_text(json.dumps(results, indent=2, default=str))

    def test_no_page_exceeds_5s_lcp(self, logged_in_app):
        """所有页面的 LCP 不应超过 5 秒。"""
        slow_pages = []
        for name, route in PAGE_ROUTES.items():
            metrics = measure_page_load(logged_in_app.page, f"https://test.quotr.ai{route}")
            if metrics["lcp"] > 5000:
                slow_pages.append(f"{name}: LCP={metrics['lcp']:.0f}ms")
        assert not slow_pages, f"以下页面 LCP > 5s:\n" + "\n".join(slow_pages)

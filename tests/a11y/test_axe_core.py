"""Accessibility: axe-core 自动化扫描。

Inject axe.min.js into page, run accessibility audit on key pages.
"""
import pytest
from pathlib import Path

AXE_MIN_JS = Path("node_modules/axe-core/axe.min.js")


def _inject_axe(page) -> None:
    """Inject axe-core into the page."""
    js = AXE_MIN_JS.read_text(encoding="utf-8")
    page.evaluate(js)


def _run_axe(page) -> list[dict]:
    """Run axe-core and return violations list."""
    return page.evaluate("""
        async () => {
            const results = await axe.run(document);
            return results.violations;
        }
    """)


@pytest.mark.a11y
@pytest.mark.p1
class TestAxeCore:
    def test_login_page_no_critical_violations(self, page):
        """登录页无 critical WCAG 违规。"""
        page.goto("https://test.quotr.ai/auth/sign-in", wait_until="commit", timeout=30000)
        page.wait_for_timeout(5000)
        _inject_axe(page)
        violations = _run_axe(page)
        critical = [v for v in violations if v.get("impact") == "critical"]
        if critical:
            ids = [f"{v['id']}: {v['help']}" for v in critical]
            pytest.fail(f"Critical WCAG violations: {ids}")

    def test_login_page_no_serious_violations(self, page):
        """登录页无 serious 及以上 WCAG 违规。"""
        page.goto("https://test.quotr.ai/auth/sign-in", wait_until="commit", timeout=30000)
        page.wait_for_timeout(5000)
        _inject_axe(page)
        violations = _run_axe(page)
        bad = [v for v in violations if v.get("impact") in ("critical", "serious")]
        assert len(bad) == 0, f"Serious+ WCAG violations: {[v['id'] for v in bad]}"

    def test_dashboard_template_a11y(self, logged_in_app):
        """Template 页面通过基础 a11y 检查。"""
        logged_in_app.dashboard.go_template()
        _inject_axe(logged_in_app.page)
        violations = _run_axe(logged_in_app.page)
        critical = [v for v in violations if v.get("impact") in ("critical", "serious")]
        if critical:
            pytest.fail(f"Template serious+ WCAG: {[v['id'] for v in critical]}")

    def test_dashboard_suppliers_a11y(self, logged_in_app):
        """Suppliers 页面通过基础 a11y 检查。"""
        logged_in_app.dashboard.go_suppliers()
        _inject_axe(logged_in_app.page)
        violations = _run_axe(logged_in_app.page)
        critical = [v for v in violations if v.get("impact") in ("critical", "serious")]
        if critical:
            pytest.fail(f"Suppliers serious+ WCAG: {[v['id'] for v in critical]}")

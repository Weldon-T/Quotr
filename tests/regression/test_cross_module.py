"""L2 Regression: 跨模块数据流。"""
import pytest


@pytest.mark.regression
@pytest.mark.p1
class TestCrossModuleNavigation:
    def test_all_modules_accessible_in_sequence(self, logged_in_app):
        routes = [
            ("Project", "/dashboard/project"),
            ("Database", "/dashboard/database"),
            ("Template", "/dashboard/template"),
            ("Suppliers", "/dashboard/suppliers/manage"),
        ]
        for name, path in routes:
            logged_in_app.dashboard.goto(path)
            body_len = len(logged_in_app.dashboard.body_text)
            assert body_len > 20, f"{name} body 过短 ({body_len} chars)，可能白屏"

    def test_sidebar_navigation_works(self, logged_in_app):
        logged_in_app.dashboard.go_project()
        links = logged_in_app.dashboard.sidebar_links
        assert len(links) >= 4, f"侧边栏链接不足 4 个: {links}"


@pytest.mark.regression
@pytest.mark.p1
class TestDataIntegrity:
    def test_org_id_consistent_across_modules(self, logged_in_app):
        org_before = logged_in_app.page.evaluate("() => localStorage.getItem('organization')")
        for path in ["/dashboard/project", "/dashboard/template", "/dashboard/suppliers/manage"]:
            logged_in_app.dashboard.goto(path)
            org_now = logged_in_app.page.evaluate("() => localStorage.getItem('organization')")
            assert org_before == org_now, f"切换 {path} 后 org 从 {org_before} 变 {org_now}"

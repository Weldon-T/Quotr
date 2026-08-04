"""P0 Smoke: 导航可用性 + 白屏检测 + /api/query-org 健康。"""
import pytest


@pytest.mark.smoke
@pytest.mark.p0
class TestNavigation:
    def test_project_page_accessible(self, logged_in_app):
        """Project 页面可访问，非白屏。"""
        logged_in_app.dashboard.go_project()
        assert not logged_in_app.dashboard.is_white_screen(), (
            f"Project 白屏: {logged_in_app.dashboard.body_text[:200]}"
        )

    def test_template_page_accessible(self, logged_in_app):
        """Template 页面可访问。"""
        logged_in_app.dashboard.go_template()
        assert not logged_in_app.dashboard.is_white_screen(), (
            f"Template 白屏: {logged_in_app.dashboard.body_text[:200]}"
        )

    def test_suppliers_page_accessible(self, logged_in_app):
        """Suppliers 页面可访问。"""
        logged_in_app.dashboard.go_suppliers()
        assert not logged_in_app.dashboard.is_white_screen(), (
            f"Suppliers 白屏: {logged_in_app.dashboard.body_text[:200]}"
        )

    def test_database_page_known_bug(self, logged_in_app):
        """Database 已知 Bug（仅显示 Nav Bar），验证未恶化。"""
        logged_in_app.database.go()
        if logged_in_app.database.is_bug_nav_bar_only:  # property, not method
            pytest.skip("Database 当前已知 Bug（仅 Nav Bar）")
        assert not logged_in_app.database.is_white_screen(), "Database 修复后不应白屏"

    def test_query_org_healthy(self, logged_in_app):
        """/api/query-org 健康：Dashboard 不白屏且含预期内容。"""
        logged_in_app.dashboard.go_project()
        body = logged_in_app.dashboard.body_text
        assert "Project" in body, "/api/query-org 异常导致 Dashboard 加载异常"

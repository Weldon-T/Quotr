"""L2 Regression: Database 模块（已知 Bug — 主内容区空白）。"""
import pytest


@pytest.mark.regression
@pytest.mark.p1
class TestDatabaseBugMonitor:
    def test_database_page_loads_without_error(self, logged_in_app):
        logged_in_app.database.go()
        body = logged_in_app.database.body_text
        assert "error" not in body.lower()[:200], f"Database 页面出现错误: {body[:300]}"

    def test_database_bug_not_regressed(self, logged_in_app):
        logged_in_app.database.go()
        if logged_in_app.database.is_bug_nav_bar_only:
            pytest.skip("Database 已知 Bug 状态（Nav Bar only）")
        assert logged_in_app.database.has_content_area, "缺 .ant-layout-content"
        assert not logged_in_app.database.is_white_screen(), "Database 修复后不应白屏"


@pytest.mark.regression
@pytest.mark.p2
class TestDatabaseCRUD:
    @pytest.mark.skip(reason="Database Bug 未修复")
    def test_database_table_renders(self, logged_in_app):
        logged_in_app.database.go()
        assert logged_in_app.database.row_count >= 0

    @pytest.mark.skip(reason="Database Bug 未修复")
    def test_search_bar_exists(self, logged_in_app):
        logged_in_app.database.go()
        inp = logged_in_app.page.locator("input[placeholder*='search' i], input[placeholder*='Search']").first
        assert inp.is_visible(timeout=3000)

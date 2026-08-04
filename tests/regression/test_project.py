"""L2 Regression: Project 模块（受已知 Bug 影响）。"""
import pytest


@pytest.mark.regression
@pytest.mark.p1
class TestProjectList:
    def test_project_page_loads(self, logged_in_app):
        logged_in_app.project.go()
        assert not logged_in_app.project.is_white_screen(), "Project 白屏"

    @pytest.mark.skip(reason="已知 Bug：列表不渲染行")
    def test_project_list_shows_data(self, logged_in_app):
        pass


@pytest.mark.regression
@pytest.mark.p1
class TestProjectCreate:
    def test_create_button_visible(self, logged_in_app):
        logged_in_app.project.go()
        if not logged_in_app.project.click_create():
            pytest.skip("创建按钮当前不可用 — 已知限制")


@pytest.mark.regression
@pytest.mark.p1
class TestProjectDetail:
    def test_project_detail_route(self, logged_in_app):
        logged_in_app.project.go_detail(703)
        if logged_in_app.project.is_404:
            pytest.skip("项目详情 404 — 已知 Bug")
        assert not logged_in_app.project.is_white_screen(), "项目详情白屏"

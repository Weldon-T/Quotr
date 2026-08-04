"""L2 Regression: Template 模块。"""
import pytest


@pytest.mark.regression
@pytest.mark.p1
class TestTemplateNavigation:
    def test_template_page_loads(self, logged_in_app):
        logged_in_app.template.go()
        assert not logged_in_app.template.is_white_screen(), "Template 白屏"

    def test_template_has_tabs(self, logged_in_app):
        logged_in_app.template.go()
        tabs = logged_in_app.template.tab_names
        assert len(tabs) >= 2, f"期望 ≥2 Tab，实际: {tabs}"
        assert any("Material" in t for t in tabs), f"缺 Material Tab: {tabs}"
        assert any("Room" in t for t in tabs), f"缺 Room Tab: {tabs}"

    def test_can_switch_between_tabs(self, logged_in_app):
        logged_in_app.template.go()
        original = logged_in_app.template.selected_template_type
        tabs = logged_in_app.template.tab_names
        for tab in tabs:
            if "Room" in tab:
                logged_in_app.template.switch_tab(tab)
                break
        new_selection = logged_in_app.template.selected_template_type
        assert new_selection != original or len(tabs) <= 1, (
            f"切换 Tab 后 selectedTemplate 应变化: {original} → {new_selection}"
        )


@pytest.mark.regression
@pytest.mark.p1
class TestTemplateCreate:
    def test_new_template_button_opens_form(self, logged_in_app):
        logged_in_app.template.go()
        assert logged_in_app.template.click_new_template(), "New Template 按钮未找到"
        modal = logged_in_app.page.locator(".ant-modal, .ant-drawer").first
        assert modal.is_visible(timeout=5000), "创建 Modal/Drawer 未打开"
        logged_in_app.template.cancel_create()

    def test_example_templates_available(self, logged_in_app):
        logged_in_app.template.go()
        assert logged_in_app.template.click_show_examples(), "Show Example Templates 按钮未找到"


@pytest.mark.regression
@pytest.mark.p1
class TestTemplateSelectedType:
    def test_selected_template_persists(self, logged_in_app):
        logged_in_app.template.go()
        st = logged_in_app.template.selected_template_type
        assert st in ["material", "room"], f"selectedTemplate 异常: {st}"

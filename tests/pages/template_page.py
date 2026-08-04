"""Template Page — Material/Room Template 管理。

当前状态：正常渲染，两个 Tab，New Template 按钮可用。
"""
from playwright.sync_api import Page

from tests.config.routes import TEMPLATE
from tests.pages.base_page import BasePage
from tests.utils.antd_selectors import (
    antd_tabs,
    antd_tab_click,
    antd_form_items,
    antd_modal,
    antd_modal_confirm,
    antd_modal_close,
)


class TemplatePage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

    def go(self):
        self.goto(TEMPLATE)
        return self

    # ---- Tabs ----

    @property
    def tab_names(self) -> list[str]:
        return antd_tabs(self.page)

    def switch_tab(self, tab_name: str):
        antd_tab_click(self.page, tab_name)
        # 等待 Tab 内容出现（Ant Tabs 切换是即时的客户端渲染）
        self.page.locator(".ant-tabs-tabpane-active").first.wait_for(state="visible", timeout=5000)
        return self

    # ---- 创建 ----

    def click_new_template(self) -> bool:
        """点击 New Template 按钮，打开创建表单。"""
        for text in ["New Template", "Create Template", "Add Template"]:
            try:
                btn = self.page.locator(f"button:has-text('{text}')").first
                if btn.is_visible(timeout=2000):
                    btn.click()
                    # 等待 Modal 出现
                    self.page.locator(".ant-modal, .ant-drawer").first.wait_for(
                        state="visible", timeout=5000
                    )
                    return True
            except Exception:
                continue
        return False

    @property
    def create_form_fields(self) -> list[dict]:
        return antd_form_items(self.page)

    def submit_create(self):
        antd_modal_confirm(self.page)
        self.page.locator(".ant-modal, .ant-drawer").first.wait_for(
            state="hidden", timeout=5000
        )

    def cancel_create(self):
        antd_modal_close(self.page)

    # ---- 示例模板 ----

    def click_show_examples(self) -> bool:
        try:
            btn = self.page.locator("button:has-text('Example Templates')").first
            if btn.is_visible(timeout=2000):
                btn.click()
                # 等待示例列表出现
                self.page.locator(".ant-table, .ant-list, .ant-card").first.wait_for(
                    state="visible", timeout=5000
                )
                return True
        except Exception:
            pass
        return False

    # ---- 选择 ----

    @property
    def selected_template_type(self) -> str:
        return self.page.evaluate(
            "() => localStorage.getItem('selectedTemplate') || ''"
        )

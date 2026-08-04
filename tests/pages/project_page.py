"""Project Page — 项目列表、创建、详情。

注意：当前 test.quotr.ai 环境存在已知限制：
  1. 项目列表不渲染行（API 返回数据但 UI 不显示）
  2. 无可见 "New Project" 创建入口
  3. 项目详情路由 /dashboard/project/{id} 返回 404
"""
from playwright.sync_api import Page

from tests.config.routes import PROJECT_LIST
from tests.pages.base_page import BasePage
from tests.utils.antd_selectors import antd_table_rows, antd_table_row_count, antd_empty


class ProjectPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

    def go(self):
        self.goto(PROJECT_LIST)
        return self

    # ---- 列表 ----

    @property
    def row_count(self) -> int:
        return antd_table_row_count(self.page)

    @property
    def table_data(self) -> list[list[str]]:
        return antd_table_rows(self.page)

    @property
    def is_empty_state(self) -> bool:
        """检查是否显示空状态（Ant Empty 组件或引导提示）。"""
        return antd_empty(self.page)

    # ---- 创建 ----

    def click_create(self) -> bool:
        """尝试点击创建项目按钮。返回是否找到并点击。"""
        for text in ["New Project", "Create Project", "Add Project", "New", "Create"]:
            try:
                btn = self.page.locator(f"button:has-text('{text}')").first
                if btn.is_visible(timeout=2000):
                    btn.click()
                    self.page.locator(".ant-modal, .ant-drawer, .ant-form").first.wait_for(
                        state="visible", timeout=5000
                    )
                    return True
            except Exception:
                continue
        return False

    # ---- 详情 ----

    def go_detail(self, project_id: int):
        """导航到项目详情页（当前返回 404）。"""
        self.goto(f"/dashboard/project/{project_id}")
        return self

    @property
    def is_404(self) -> bool:
        return "404" in self.body_text or "not found" in self.body_text.lower()

    # ---- 创建表单（Modal/Drawer） ----

    @property
    def create_form_fields(self) -> list[dict]:
        """获取创建表单的字段信息。"""
        from tests.utils.antd_selectors import antd_form_items
        return antd_form_items(self.page)

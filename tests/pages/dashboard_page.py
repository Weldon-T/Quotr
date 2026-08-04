"""Dashboard Page — 侧边栏导航、模块切换。"""
from playwright.sync_api import Page

from tests.config.routes import PROJECT_LIST, DATABASE, TEMPLATE, SUPPLIERS
from tests.pages.base_page import BasePage
from tests.utils.helpers import wait_for_spa


class DashboardPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

    def go_project(self):
        self.goto(PROJECT_LIST)
        return self

    def go_database(self):
        self.goto(DATABASE)
        return self

    def go_template(self):
        self.goto(TEMPLATE)
        return self

    def go_suppliers(self):
        self.goto(SUPPLIERS)
        return self

    @property
    def sidebar_links(self) -> list[str]:
        """获取侧边栏中所有导航链接的文本。"""
        links = []
        for el in self.page.locator(".ant-menu-item a, nav a").all():
            try:
                text = el.inner_text().strip()
                if text:
                    links.append(text)
            except Exception:
                pass
        return links

    def navigate_to(self, module_name: str):
        """按模块名称点击侧边栏链接。"""
        link = self.page.locator(f"a:has-text('{module_name}')").first
        link.click()
        wait_for_spa(self.page)


def navigate_all_modules(page: Page) -> dict[str, dict]:
    """遍历 4 个一级模块，返回每个模块的状态（url, is_white_screen, body_length）。"""
    results = {}
    for name, path in [
        ("Project", PROJECT_LIST),
        ("Database", DATABASE),
        ("Template", TEMPLATE),
        ("Suppliers", SUPPLIERS),
    ]:
        dash = DashboardPage(page)
        dash.goto(path)
        results[name] = {
            "url": page.url,
            "is_white_screen": dash.is_white_screen(),
            "body_length": len(dash.body_text),
        }
    return results

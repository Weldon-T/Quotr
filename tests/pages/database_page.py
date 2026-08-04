"""Database Page — 材料/成本数据库。

注意：当前 test.quotr.ai 环境存在已知 Bug：
  主内容区完全空白，仅渲染侧边栏（"Nav Bar"）。
  DOM 中无 .ant-layout-content、.ant-table 等内容组件。
"""
from playwright.sync_api import Page

from tests.config.routes import DATABASE
from tests.pages.base_page import BasePage


class DatabasePage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

    def go(self):
        self.goto(DATABASE)
        return self

    # ---- Bug 检测 ----

    @property
    def has_content_area(self) -> bool:
        """检查主内容区是否存在。数据库 Bug 的特征就是缺少此元素。"""
        return self.page.evaluate(
            """() => {
                const el = document.querySelector('.ant-layout-content, main, [class*="content"]');
                return !!(el && el.offsetParent !== null);
            }"""
        )

    @property
    def content_html(self) -> str:
        """获取主内容区的 HTML 片段，用于 Bug 诊断。"""
        return self.page.evaluate(
            """() => {
                const root = document.getElementById('root');
                if (!root) return 'NO #ROOT';
                const main = root.querySelector('.ant-layout-content, main');
                return main ? main.innerHTML.substring(0, 1000) : root.innerHTML.substring(0, 1000);
            }"""
        )

    @property
    def is_bug_nav_bar_only(self) -> bool:
        """检测已知 Bug：仅显示 Nav Bar，无实际内容。"""
        text = self.body_text
        return len(text) < 50 or text.strip().startswith("Nav Bar")

    # ---- 正常功能（Bug 修复后启用） ----

    @property
    def row_count(self) -> int:
        from tests.utils.antd_selectors import antd_table_row_count
        return antd_table_row_count(self.page)

    @property
    def table_data(self) -> list[list[str]]:
        from tests.utils.antd_selectors import antd_table_rows
        return antd_table_rows(self.page)

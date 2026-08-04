"""Base Page — 所有 Page Object 的基类。

提供通用操作：导航、SPA 等待、反爬处理、白屏检测。
"""
from playwright.sync_api import Page

from tests.config.settings import BASE_URL, NAVIGATION_TIMEOUT, SPA_MOUNT_TIMEOUT
from tests.utils.helpers import wait_for_spa, human_pause, snap, dump_text


class BasePage:
    def __init__(self, page: Page):
        self.page = page
        self.base_url = BASE_URL

    # ---- 导航 ----

    def goto(self, path: str, wait="load"):
        """导航到指定路径，自动拼接 BASE_URL。"""
        url = f"{self.base_url}{path}"
        try:
            self.page.goto(url, wait_until=wait, timeout=NAVIGATION_TIMEOUT)
        except Exception:
            self.page.goto(url, wait_until="commit", timeout=NAVIGATION_TIMEOUT)
        wait_for_spa(self.page, max_wait=SPA_MOUNT_TIMEOUT)
        human_pause()
        return self

    # ---- 页面状态 ----

    @property
    def current_url(self) -> str:
        return self.page.url

    @property
    def title(self) -> str:
        return self.page.title()

    @property
    def body_text(self) -> str:
        return self.page.locator("body").inner_text().strip()

    def is_white_screen(self) -> bool:
        """检测 Dashboard 白屏：body 只含导航条文字但无实际内容。"""
        text = self.body_text
        # 白屏特征：body 文本极短（仅侧边栏），主内容区无内容
        words = text.split()
        if len(words) < 10:
            return True
        # 检查是否有实际内容（非导航文字）
        nav_keywords = {"Project", "Database", "Template", "Procurement", "Help", "Nav Bar"}
        remaining = [w for w in words if w not in nav_keywords]
        if len(remaining) <= 3:  # 只剩 email + 用户头像文字
            return True
        return False

    # ---- 截图 / 调试 ----

    def screenshot(self, name: str):
        return snap(self.page, name)

    def dump(self, max_lines=40):
        return dump_text(self.page, max_lines)

    # ---- localStorage ----

    def ls_exists(self, key: str) -> bool:
        return self.page.evaluate(f"() => !!localStorage.getItem('{key}')")

    def ls_get(self, key: str) -> str:
        return self.page.evaluate(f"() => localStorage.getItem('{key}')")

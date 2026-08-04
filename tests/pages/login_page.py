"""Login Page — 登录/登出操作。"""
from playwright.sync_api import Page, expect
from tests.config.settings import (
    BASE_URL, QUOTR_EMAIL, QUOTR_PASSWORD,
    NAVIGATION_TIMEOUT, SPA_MOUNT_TIMEOUT, ELEMENT_WAIT_TIMEOUT,
    LOGIN_RETRY_MAX, WAIT,
)
from tests.config.routes import SIGN_IN
from tests.utils.helpers import wait_for_spa, human_pause, goto_spa


class LoginPage:
    def __init__(self, page: Page):
        self.page = page

    def goto(self):
        """导航到登录页（含 landing 预热）。"""
        try:
            self.page.goto(BASE_URL, wait_until="load", timeout=NAVIGATION_TIMEOUT)
        except Exception:
            self.page.goto(BASE_URL, wait_until="commit", timeout=NAVIGATION_TIMEOUT)
        human_pause()
        goto_spa(self.page, f"{BASE_URL}{SIGN_IN}", wait="load", timeout=NAVIGATION_TIMEOUT)
        return self

    @property
    def is_form_visible(self) -> bool:
        try:
            self.page.locator("input[name='email']").first.wait_for(
                state="visible", timeout=ELEMENT_WAIT_TIMEOUT
            )
            return True
        except Exception:
            return False

    def fill_email(self, email: str = QUOTR_EMAIL):
        self.page.locator("input[name='email']").first.fill(email)
        return self

    def fill_password(self, password: str = QUOTR_PASSWORD):
        self.page.locator("input[type='password']").first.fill(password)
        return self

    def submit(self):
        """提交登录并等待结果（URL 变化或 token 写入）。"""
        self.page.locator("button[type='submit']").first.click()
        # 等待认证完成：要么 URL 变了，要么 token 写入了 localStorage
        try:
            self.page.wait_for_url("**/dashboard/**", timeout=WAIT.AFTER_LOGIN_SUBMIT)
        except Exception:
            pass
        # 如果没跳转，再给点时间等 token 写入
        self.page.wait_for_timeout(WAIT.AFTER_LOGIN_SUBMIT)
        return self

    def login(self, email: str = QUOTR_EMAIL, password: str = QUOTR_PASSWORD) -> bool:
        """完整登录流程，含重试。返回是否成功。"""
        for _ in range(LOGIN_RETRY_MAX):
            self.goto()
            if not self.is_form_visible:
                continue
            self.fill_email(email).fill_password(password).submit()
            if self.is_logged_in():
                wait_for_spa(self.page, max_wait=SPA_MOUNT_TIMEOUT)
                return True
        return False

    def login_failure_expected(self, email: str, password: str) -> str:
        """尝试登录，预期失败。返回页面文本。"""
        self.goto()
        self.fill_email(email).fill_password(password).submit()
        # 等待错误提示出现
        try:
            self.page.locator(".ant-form-item-explain-error, [class*='error'], [class*='alert']").first.wait_for(
                state="visible", timeout=5000
            )
        except Exception:
            pass
        return self.page.locator("body").inner_text()[:500]

    def is_logged_in(self) -> bool:
        return self.page.evaluate(
            "() => !!(localStorage.getItem('auth_v2_session') || localStorage.getItem('token'))"
        )

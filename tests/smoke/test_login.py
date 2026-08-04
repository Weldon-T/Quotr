"""P0 Smoke: 登录全场景 — 每次 PR 必跑。"""
import json
import pytest
from tests.config.settings import QUOTR_EMAIL, QUOTR_PASSWORD
from tests.core.decorators import retry


@pytest.mark.smoke
@pytest.mark.p0
class TestLoginSuccess:
    @retry(times=3, delay=2)
    def test_login_with_valid_credentials(self, app):
        """正常凭据登录 → localStorage 有 token。"""
        result = app.login.login()
        assert result, "正常凭据登录失败"
        assert app.login.is_logged_in(), "登录后 is_logged_in() 返回 False"


@pytest.mark.smoke
@pytest.mark.p0
class TestLoginFailure:
    def test_login_with_wrong_password(self, app):
        """错误密码 → 不写入 token，显示错误提示。"""
        body = app.login.login_failure_expected(QUOTR_EMAIL, "wrong-password-12345")
        assert not app.login.is_logged_in(), "错误密码不应写入 token"
        has_error = any(
            kw in body.lower()
            for kw in ["invalid", "wrong", "incorrect", "error", "failed"]
        )
        assert has_error, f"错误密码应显示错误提示: {body[:300]}"

    def test_login_with_invalid_email_format(self, app):
        """无效邮箱格式 → 前端校验或后端拒绝。"""
        app.login.login_failure_expected("not-an-email", QUOTR_PASSWORD)
        assert not app.login.is_logged_in(), "无效邮箱不应写入 token"


@pytest.mark.smoke
@pytest.mark.p0
class TestTokenPersistence:
    def test_token_in_localstorage_after_login(self, logged_in_app):
        """已登录 session: auth_v2_session 或 token 存在。"""
        has_token = logged_in_app.page.evaluate(
            "() => !!(localStorage.getItem('auth_v2_session') || localStorage.getItem('token'))"
        )
        assert has_token, "auth_v2_session 或 token 应在 localStorage 中"

    def test_user_info_in_localstorage(self, logged_in_app):
        """user 字段含 email 和 id。"""
        raw = logged_in_app.page.evaluate("() => localStorage.getItem('user')")
        assert raw, "localStorage 应包含 user"
        user = json.loads(raw)
        assert user.get("email"), "user 应包含 email"
        assert user.get("id"), "user 应包含 id"


@pytest.mark.smoke
@pytest.mark.p0
class TestUnauthenticatedRedirect:
    def test_dashboard_redirects_to_login(self, app):
        """未登录访问 /dashboard/project → 重定向到登录页。"""
        app.page.goto("https://test.quotr.ai/dashboard/project", wait_until="commit")
        app.page.wait_for_timeout(5000)
        is_redirected = (
            "/auth/" in app.page.url.lower()
            or "sign in" in app.page.locator("body").inner_text().lower()
        )
        assert is_redirected, f"未登录应重定向，实际 URL: {app.page.url}"

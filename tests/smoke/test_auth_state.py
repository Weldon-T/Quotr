"""P0 Smoke: localStorage 认证状态完整性 + sign-out-reason 异常检测。"""
import json
import pytest
from tests.config.routes import LS_REQUIRED_FIELDS, LS_AUTH_SESSION


@pytest.mark.smoke
@pytest.mark.p0
class TestAuthState:
    def test_all_required_ls_keys_exist(self, logged_in_app):
        """登录后所有关键 localStorage 字段存在。"""
        missing = []
        for key in LS_REQUIRED_FIELDS:
            exists = logged_in_app.page.evaluate(f"() => !!localStorage.getItem('{key}')")
            if not exists:
                missing.append(key)
        assert not missing, f"缺少 localStorage 字段: {missing}"

    def test_auth_session_is_valid_json(self, logged_in_app):
        """auth_v2_session 是合法 JSON（含 access_token）。"""
        raw = logged_in_app.page.evaluate(f"() => localStorage.getItem('{LS_AUTH_SESSION}')")
        assert raw, "auth_v2_session 不存在"
        data = json.loads(raw)
        assert "access_token" in data, f"auth_v2_session 缺少 access_token: {list(data.keys())}"

    def test_user_has_required_fields(self, logged_in_app):
        """user 含 id, email。"""
        raw = logged_in_app.page.evaluate("() => localStorage.getItem('user')")
        assert raw, "user 不存在"
        user = json.loads(raw)
        for field in ["id", "email"]:
            assert user.get(field), f"user 缺少字段: {field}"

    def test_organization_is_set(self, logged_in_app):
        """organization 为有效数字 ID。"""
        org = logged_in_app.page.evaluate("() => localStorage.getItem('organization')")
        assert org and org.isdigit(), f"organization 应为数字 ID，实际: {org}"


@pytest.mark.smoke
@pytest.mark.p0
class TestNoSignOutReason:
    def test_sign_out_reason_not_called_after_login(self, app):
        """登录后 sign-out-reason 不应异常触发（reason=None 表示被动登出）。"""
        sign_out_called = False

        def on_response(response):
            nonlocal sign_out_called
            if "/api/auth/v2/sign-out-reason" in response.url:
                try:
                    if response.json().get("reason") is None:
                        sign_out_called = True
                except Exception:
                    pass

        app.page.on("response", on_response)

        result = app.login.login()
        assert result, "登录应成功"
        assert not sign_out_called, (
            "sign-out-reason 在登录后异常调用（reason=None），session 可能已被清空"
        )

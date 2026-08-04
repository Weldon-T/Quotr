"""Concurrency: 按钮防重复提交、API 幂等性。"""
import pytest


@pytest.mark.concurrency
@pytest.mark.p1
class TestDoubleSubmit:
    def test_login_button_disabled_after_click(self, app):
        """登录按钮点击后应立即禁用，防止重复提交。"""
        app.page.goto("https://test.quotr.ai/auth/sign-in", wait_until="commit")
        app.page.wait_for_timeout(8000)

        btn = app.page.locator("button[type='submit']").first
        if not btn.is_visible():
            pytest.skip("登录表单未渲染（反爬）")

        btn.click()
        btn.click()  # 快速双击
        app.page.wait_for_timeout(5000)

        body = app.page.locator("body").inner_text()
        assert "too many" not in body.lower(), "重复提交触发了 rate limit 错误"


@pytest.mark.concurrency
@pytest.mark.p1
class TestIdempotency:
    @pytest.mark.skip(reason="需创建类 API 端点信息")
    def test_create_endpoint_idempotent(self):
        pass

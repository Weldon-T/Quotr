"""Security: XSS 注入测试。"""
import pytest


@pytest.mark.security
@pytest.mark.p1
class TestXSSInjection:
    def test_no_reflected_xss_in_login_page(self, app):
        """登录页 URL 参数中的 script 标签应被转义，不直接渲染。"""
        app.page.goto(
            "https://test.quotr.ai/auth/sign-in?redirect=%3Cscript%3Ealert(1)%3C%2Fscript%3E",
            wait_until="commit",
        )
        app.page.wait_for_timeout(5000)
        body = app.page.locator("body").inner_text()
        assert "<script>" not in body, "反射型 XSS: script 标签未转义"
        assert "alert(1)" not in body, "反射型 XSS: payload 出现在页面中"

    @pytest.mark.skip(reason="创建项目功能不可用")
    def test_xss_in_project_name(self, logged_in_app):
        pass

    @pytest.mark.skip(reason="创建供应商 API 未知")
    def test_xss_in_supplier_name(self, logged_in_app):
        pass

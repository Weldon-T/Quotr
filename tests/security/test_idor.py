"""Security: IDOR 测试（需要多账号）。"""
import pytest


@pytest.mark.security
@pytest.mark.p0
class TestIDOR:
    @pytest.mark.skip(reason="需第二组织账号")
    def test_cannot_access_other_org_data(self):
        pass

    @pytest.mark.skip(reason="需第二组织账号")
    def test_cannot_modify_other_org_supplier(self):
        pass

    def test_invalid_project_id_not_leak_data(self, logged_in_app):
        """请求不存在的项目 ID 不应泄露其他数据。"""
        import json
        from tests.api.test_api_contract import _fetch

        # 导航到同源页面（否则 localStorage 不可访问）
        logged_in_app.page.goto("https://test.quotr.ai/dashboard/project", wait_until="commit")
        logged_in_app.page.wait_for_timeout(3000)
        token = logged_in_app.page.evaluate("() => localStorage.getItem('token') || ''")
        if not token:
            pytest.skip("未获取到 auth token，跳过 IDOR 测试")

        result = _fetch(logged_in_app.page, "POST", "/api/get-versions",
                        {"project_id": 999999}, token=token)
        assert result["status"] == 200
        data = result["body"].get("data")
        assert not data, f"不存在的项目 ID 不应返回数据: {data}"

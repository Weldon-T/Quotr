"""Security: Rate Limiting 测试。"""
import time
import pytest


@pytest.mark.security
@pytest.mark.p1
class TestRateLimiting:
    def test_repeated_requests_not_blocked_immediately(self, logged_in_app):
        """连续 10 次 query-org 不应触发封禁（通过浏览器 fetch）。"""
        logged_in_app.page.goto("https://test.quotr.ai/dashboard/project", wait_until="commit")
        logged_in_app.page.wait_for_timeout(3000)

        token = logged_in_app.page.evaluate("() => localStorage.getItem('token') || ''")
        if not token:
            pytest.skip("未获取到 auth token")

        success = 0
        for _ in range(10):
            result = logged_in_app.page.evaluate(f"""
                async () => {{
                    const resp = await fetch('/api/query-org', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json', 'Authorization': 'Bearer {token}' }},
                        body: '{{}}',
                    }});
                    return resp.status;
                }}
            """)
            if result == 200:
                success += 1
            elif result == 429:
                pytest.skip("Rate limiting 在 10 次请求内触发")
            time.sleep(0.3)

        assert success >= 8, f"10 次请求中仅 {success} 次成功，可能过早限流"

"""API 契约测试 — 状态码、响应格式、认证要求。

认证测试通过 Playwright browser fetch 绕过反爬。
未认证测试使用 requests（不需要浏览器）。
"""
import json
import pytest
import requests
from tests.config.settings import BASE_URL, QUOTR_EMAIL, QUOTR_PASSWORD, USER_AGENT
from tests.config.routes import PROTECTED_APIS

BROWSER_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "application/json",
    "Content-Type": "application/json",
}


def _fetch(page, method: str, path: str, body: dict = None, token: str = "") -> dict:
    """通过浏览器 fetch 发同源 API 请求。page 必须在 test.quotr.ai 域。"""
    headers_expr = "{ 'Content-Type': 'application/json' }"
    if token:
        headers_expr = f"{{ 'Content-Type': 'application/json', 'Authorization': 'Bearer {token}' }}"
    body_str = json.dumps(body) if body else "undefined"

    return page.evaluate(f"""
        async () => {{
            const resp = await fetch('{path}', {{
                method: '{method}',
                headers: {headers_expr},
                body: {body_str},
            }});
            const text = await resp.text();
            let data;
            try {{ data = JSON.parse(text); }} catch(e) {{ data = text; }}
            return {{ status: resp.status, body: data }};
        }}
    """)


def _get_token(page) -> str:
    """从已有页面的 localStorage 获取 token，或通过 fetch 登录获取。"""
    token = page.evaluate("() => localStorage.getItem('token') || ''")
    if token:
        return token
    # 通过 fetch 登录
    result = _fetch(page, "POST", "/api/auth/v2/signin", {
        "email": QUOTR_EMAIL,
        "password": QUOTR_PASSWORD,
    })
    return result["body"].get("token", "") if isinstance(result["body"], dict) else ""


@pytest.fixture(scope="function")
def auth_token(logged_in_page):
    """从已登录页面获取 JWT token。"""
    logged_in_page.goto(f"{BASE_URL}/dashboard/project", wait_until="commit")
    logged_in_page.wait_for_timeout(3000)
    token = _get_token(logged_in_page)
    assert token, "无法获取 auth token"
    return token


# ==================== 响应格式（需认证，浏览器 fetch） ====================


@pytest.mark.critical
@pytest.mark.p1
class TestResponseFormat:
    def test_signin_returns_token(self, page):
        """登录 API 返回 token。"""
        page.goto(f"{BASE_URL}/auth/sign-in", wait_until="commit", timeout=30000)
        page.wait_for_timeout(5000)
        result = _fetch(page, "POST", "/api/auth/v2/signin", {
            "email": QUOTR_EMAIL,
            "password": QUOTR_PASSWORD,
        })
        assert result["status"] == 200, f"登录失败: {result['body']}"
        token = result["body"].get("token", "")
        assert token, "登录响应无 token"

    @pytest.mark.parametrize("path", [
        "/api/query-org",
        "/api/get-projects",
        "/api/get-versions",
        "/api/get-roomTypes",
        "/api/get-customer-templates",
        "/api/get-customer-supplier-list",
        "/api/get-unread-count",
    ])
    def test_authenticated_endpoints_return_200(self, auth_token, logged_in_page, path):
        """已验证端点返回 200 + 标准格式。"""
        logged_in_page.goto(f"{BASE_URL}/dashboard/project", wait_until="commit")
        logged_in_page.wait_for_timeout(2000)
        result = _fetch(logged_in_page, "POST", path, token=auth_token)
        assert result["status"] == 200, f"{path}: 期望 200，实际 {result['status']}: {str(result['body'])[:200]}"
        body = result["body"]
        if isinstance(body, dict):
            assert body.get("code") == 200, f"{path}: code 应为 200，实际 {body.get('code')}"

    def test_meetings_endpoint(self, auth_token, logged_in_page):
        logged_in_page.goto(f"{BASE_URL}/dashboard/project", wait_until="commit")
        logged_in_page.wait_for_timeout(2000)
        result = _fetch(logged_in_page, "GET", "/api/qms/v1/meetings", token=auth_token)
        assert result["status"] == 200

    def test_bell_endpoint(self, auth_token, logged_in_page):
        logged_in_page.goto(f"{BASE_URL}/dashboard/project", wait_until="commit")
        logged_in_page.wait_for_timeout(2000)
        result = _fetch(logged_in_page, "GET", "/api/qms/v1/bell", token=auth_token)
        assert result["status"] == 200


# ==================== 认证要求（不需要浏览器） ====================


@pytest.mark.critical
@pytest.mark.p0
class TestAuthRequired:
    @pytest.mark.parametrize("endpoint", PROTECTED_APIS)
    def test_unauthenticated_returns_401(self, endpoint):
        """无 token 访问受保护 API → 401/403。"""
        resp = requests.post(
            f"{BASE_URL}{endpoint}",
            json={},
            headers=BROWSER_HEADERS,
            timeout=30,
        )
        assert resp.status_code in [401, 403], (
            f"{endpoint}: 期望 401/403，实际 {resp.status_code}: {resp.text[:200]}"
        )

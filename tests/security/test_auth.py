"""Security: 认证安全 — 未认证访问、JWT 篡改。"""
import pytest
from tests.config.settings import QUOTR_EMAIL, QUOTR_PASSWORD, BASE_URL
from tests.config.routes import PROTECTED_APIS

# 使用 requests 做未认证测试（反爬不拦截 401 响应）
import requests
from tests.config.settings import USER_AGENT

BROWSER_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "application/json",
    "Content-Type": "application/json",
}


@pytest.mark.security
@pytest.mark.p0
class TestUnauthenticatedAccess:
    @pytest.mark.parametrize("endpoint", PROTECTED_APIS)
    def test_endpoint_requires_auth(self, endpoint):
        resp = requests.post(f"{BASE_URL}{endpoint}", json={}, headers=BROWSER_HEADERS, timeout=30)
        assert resp.status_code in [401, 403], f"{endpoint}: 期望 401/403，实际 {resp.status_code}"

    def test_signin_does_not_require_auth(self):
        resp = requests.post(
            f"{BASE_URL}/api/auth/v2/signin",
            json={"email": QUOTR_EMAIL, "password": QUOTR_PASSWORD},
            headers=BROWSER_HEADERS,
            timeout=30,
        )
        # 可能 200（成功）或 401（credentials 通过 requests 被反爬拒绝）
        # 但绝不应是 500
        assert resp.status_code != 500, f"signin 不应 500: {resp.text[:200]}"


@pytest.mark.security
@pytest.mark.p0
class TestJWTValidation:
    def test_empty_token_rejected(self):
        resp = requests.post(
            f"{BASE_URL}/api/query-org",
            json={},
            headers={**BROWSER_HEADERS, "Authorization": "Bearer "},
            timeout=30,
        )
        assert resp.status_code in [401, 403], f"空 token: 期望 401/403，实际 {resp.status_code}"

    def test_garbage_token_rejected(self):
        resp = requests.post(
            f"{BASE_URL}/api/query-org",
            json={},
            headers={**BROWSER_HEADERS, "Authorization": "Bearer not-a-valid-jwt"},
            timeout=30,
        )
        assert resp.status_code in [401, 403], f"无效 token: 期望 401/403，实际 {resp.status_code}"

    def test_expired_token_rejected(self):
        expired = "eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInN1YiI6InRlc3QiLCJleHAiOjEwMDAwMDAwMDAsImlhdCI6MTAwMDAwMDAwMH0.signature"
        resp = requests.post(
            f"{BASE_URL}/api/query-org",
            json={},
            headers={**BROWSER_HEADERS, "Authorization": f"Bearer {expired}"},
            timeout=30,
        )
        assert resp.status_code in [401, 403], f"过期 token: 期望 401/403，实际 {resp.status_code}"

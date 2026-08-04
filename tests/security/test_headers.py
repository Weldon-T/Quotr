"""Security: 安全响应头检查。

验证关键安全 headers 存在且合理配置。
"""
import pytest
import requests
from tests.config.settings import BASE_URL


SECURITY_HEADERS = [
    "Content-Security-Policy",
    "Strict-Transport-Security",
    "X-Content-Type-Options",
    "X-Frame-Options",
]

OPTIONAL_HEADERS = [
    "X-XSS-Protection",
    "Referrer-Policy",
    "Permissions-Policy",
]


@pytest.mark.security
@pytest.mark.p1
class TestSecurityHeaders:
    def test_csp_header_present(self):
        """CSP header 存在，防止 XSS。"""
        resp = requests.get(BASE_URL, timeout=30)
        csp = resp.headers.get("Content-Security-Policy", "")
        assert csp, "CSP header 缺失 — 站点缺少 XSS 防护"

    def test_hsts_header_present(self):
        """HSTS header 存在，强制 HTTPS。"""
        resp = requests.get(BASE_URL, timeout=30)
        hsts = resp.headers.get("Strict-Transport-Security", "")
        assert hsts, "HSTS header 缺失"

    def test_content_type_options_header_present(self):
        """X-Content-Type-Options: nosniff 防止 MIME 嗅探。"""
        resp = requests.get(BASE_URL, timeout=30)
        cto = resp.headers.get("X-Content-Type-Options", "")
        assert "nosniff" in cto.lower(), f"X-Content-Type-Options 应为 nosniff，实际: {cto}"

    def test_frame_options_header_present(self):
        """X-Frame-Options 防止 clickjacking。"""
        resp = requests.get(BASE_URL, timeout=30)
        xfo = resp.headers.get("X-Frame-Options", "")
        assert xfo, "X-Frame-Options header 缺失"

    def test_all_critical_headers(self):
        """一次性检查所有关键安全 headers。"""
        resp = requests.get(BASE_URL, timeout=30)
        missing = []
        for header in SECURITY_HEADERS:
            if header not in resp.headers:
                missing.append(header)
        assert not missing, f"缺失安全 headers: {missing}"


@pytest.mark.security
@pytest.mark.p2
class TestOptionalSecurityHeaders:
    def test_referrer_policy(self):
        resp = requests.get(BASE_URL, timeout=30)
        rp = resp.headers.get("Referrer-Policy", "")
        # 不强要求存在，但如果存在需要是合理的值
        if rp:
            valid = ["no-referrer", "strict-origin", "strict-origin-when-cross-origin", "same-origin"]
            assert any(v in rp for v in valid), f"Referrer-Policy 值异常: {rp}"

    def test_permissions_policy(self):
        resp = requests.get(BASE_URL, timeout=30)
        pp = resp.headers.get("Permissions-Policy", "")
        # 不强要求，记录即可
        if not pp:
            pytest.skip("Permissions-Policy 未设置（可选）")

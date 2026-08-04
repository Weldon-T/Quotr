"""API HTTP Client — 可带 JWT token 发请求，用于 API 契约测试。

注意：Quotr API 有反爬保护，裸 requests 可能被拒绝。
认证测试优先使用 Playwright browser context（通过 page.evaluate 发 fetch），
非认证测试（security headers 等）可以使用裸 requests。
"""
import requests
from tests.config.settings import BASE_URL, USER_AGENT

BROWSER_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Content-Type": "application/json",
    "Origin": BASE_URL,
    "Referer": f"{BASE_URL}/auth/sign-in",
}


class APIClient:
    def __init__(self, base_url: str = BASE_URL, token: str = None):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.session = requests.Session()
        self.session.headers.update(BROWSER_HEADERS)
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def post(self, path: str, json_data: dict = None, headers: dict = None) -> requests.Response:
        return self.session.post(self._url(path), json=json_data or {}, headers=headers or {})

    def get(self, path: str, headers: dict = None) -> requests.Response:
        return self.session.get(self._url(path), headers=headers or {})

    # ---- Playwright-native API calls (for auth-required tests) ----

    @staticmethod
    def playwright_post(page, path: str, json_data: dict = None) -> dict:
        """通过 Playwright page 发 fetch 请求，绕过反爬检测。返回 JSON body。"""
        import json
        body = json.dumps(json_data or {})
        result = page.evaluate(f"""
            async () => {{
                const resp = await fetch('{BASE_URL}{path}', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: '{body}',
                }});
                const data = await resp.json();
                return {{ status: resp.status, body: data }};
            }}
        """)
        return result

    @staticmethod
    def playwright_signin(page, email: str, password: str) -> dict:
        """通过 Playwright 加载的页面发 signin 请求。返回 {status, body}。"""
        token = page.evaluate(f"""
            async () => {{
                const resp = await fetch('{BASE_URL}/api/auth/v2/signin', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ email: '{email}', password: '{password}' }}),
                }});
                const data = await resp.json();
                return data.token || '';
            }}
        """)
        return token

    # ---- 认证相关 ----

    def signin(self, email: str, password: str) -> requests.Response:
        return self.post("/api/auth/v2/signin", {"email": email, "password": password})

    def query_org(self) -> requests.Response:
        return self.post("/api/query-org")

    def get_projects(self) -> requests.Response:
        return self.post("/api/get-projects")

    def get_versions(self) -> requests.Response:
        return self.post("/api/get-versions")

    def get_room_types(self) -> requests.Response:
        return self.post("/api/get-roomTypes")

    def get_customer_templates(self) -> requests.Response:
        return self.post("/api/get-customer-templates")

    def get_default_templates(self) -> requests.Response:
        return self.post("/api/get-default-templates")

    def get_supplier_list(self) -> requests.Response:
        return self.post("/api/get-customer-supplier-list")

    def get_meetings(self) -> requests.Response:
        return self.get("/api/qms/v1/meetings")

    def get_bell(self) -> requests.Response:
        return self.get("/api/qms/v1/bell")

    def get_unread_count(self) -> requests.Response:
        return self.post("/api/get-unread-count")

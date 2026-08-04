"""
Pytest fixtures — browser, auth-state caching, anti-bot injection, PageFactory.

Fixtures:
  page           — blank page, no auth
  app            — PageFactory(page), no auth
  logged_in_page — authenticated page (cached via storageState)
  logged_in_app  — PageFactory(logged_in_page), main fixture for most tests

Usage:
  def test_something(logged_in_app):
      logged_in_app.dashboard.go_project()
      assert not logged_in_app.dashboard.is_white_screen()
      token = logged_in_app.page.evaluate("() => localStorage.getItem('token')")
"""

import pytest
from tests.core.page_factory import PageFactory
from pathlib import Path
from playwright.sync_api import sync_playwright, Page, BrowserContext

from tests.config.settings import (
    BASE_URL,
    QUOTR_EMAIL,
    QUOTR_PASSWORD,
    VIEWPORT,
    USER_AGENT,
    NAVIGATION_TIMEOUT,
    SPA_MOUNT_TIMEOUT,
    ELEMENT_WAIT_TIMEOUT,
    LOGIN_RETRY_MAX,
    WAIT,
)
from tests.utils.helpers import wait_for_spa

AUTH_STATE_PATH = Path("tests/.auth_state.json")

# ---------- 反爬注入脚本 ----------
ANTI_BOT_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', { get: () => false });
Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
"""


def _create_context(browser, storage_state=None):
    """创建带反爬配置的 browser context。"""
    context = browser.new_context(
        viewport=VIEWPORT,
        user_agent=USER_AGENT,
        locale="en-US",
        timezone_id="America/Chicago",
        ignore_https_errors=True,
        storage_state=storage_state,
    )
    context.add_init_script(ANTI_BOT_SCRIPT)
    context.set_default_timeout(ELEMENT_WAIT_TIMEOUT)
    return context


def _do_login(page: Page) -> bool:
    """执行登录操作，返回是否成功。"""
    from tests.utils.helpers import goto_spa

    for attempt in range(LOGIN_RETRY_MAX):
        # 先到 landing page（模拟真实用户行为）
        try:
            page.goto(BASE_URL, wait_until="load", timeout=NAVIGATION_TIMEOUT)
        except Exception:
            try:
                page.goto(BASE_URL, wait_until="commit", timeout=NAVIGATION_TIMEOUT)
            except Exception:
                pass

        # 到登录页
        goto_spa(page, f"{BASE_URL}/auth/sign-in", wait="load", timeout=NAVIGATION_TIMEOUT)

        email_input = page.locator("input[name='email']").first
        try:
            email_input.wait_for(state="visible", timeout=ELEMENT_WAIT_TIMEOUT)
        except Exception:
            # SPA 未渲染（反爬拦截），重试
            continue

        email_input.fill(QUOTR_EMAIL)
        page.locator("input[type='password']").first.fill(QUOTR_PASSWORD)
        page.locator("button[type='submit']").first.click()
        # 等待登录完成：URL 跳转 或 token 写入
        try:
            page.wait_for_url("**/dashboard/**", timeout=WAIT.AFTER_LOGIN_SUBMIT)
        except Exception:
            pass
        page.wait_for_timeout(WAIT.SESSION_CHECK)

        has_token = page.evaluate(
            "() => !!(localStorage.getItem('auth_v2_session') || localStorage.getItem('token'))"
        )
        if has_token:
            wait_for_spa(page, max_wait=SPA_MOUNT_TIMEOUT)
            return True

    return False


# ==================== Fixtures ====================


@pytest.fixture(scope="session")
def browser():
    """Session 级 browser 实例，整个测试会话复用。"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture(scope="function")
def context(browser):
    """每个测试函数的独立 browser context。"""
    ctx = _create_context(browser)
    yield ctx
    ctx.close()


@pytest.fixture(scope="function")
def page(context):
    """空白页面，无认证。"""
    p = context.new_page()
    yield p
    p.close()


@pytest.fixture(scope="session")
def logged_in_context(browser):
    """
    Session 级已登录 context。
    只在第一次创建时执行登录，后续复用 storageState。
    """
    # 尝试从缓存恢复
    if AUTH_STATE_PATH.exists():
        ctx = _create_context(browser, storage_state=str(AUTH_STATE_PATH))
        page = ctx.new_page()
        page.goto(f"{BASE_URL}/dashboard/project", wait_until="commit", timeout=NAVIGATION_TIMEOUT)
        wait_for_spa(page, max_wait=10)
        # 验证登录状态是否仍有效：有 token 且未被重定向到登录页
        has_token = page.evaluate(
            "() => !!(localStorage.getItem('auth_v2_session') || localStorage.getItem('token'))"
        )
        on_signin = "sign in" in page.locator("body").inner_text().lower()[:200]
        page.close()
        if has_token and not on_signin:
            return ctx
        # token 过期或无效，删除缓存重新登录
        ctx.close()
        AUTH_STATE_PATH.unlink(missing_ok=True)

    # 新建登录
    ctx = _create_context(browser)
    page = ctx.new_page()
    ok = _do_login(page)
    page.close()
    if not ok:
        ctx.close()
        raise RuntimeError("Fixtures: 登录失败，无法创建 logged_in_context")
    # 保存 auth state
    ctx.storage_state(path=str(AUTH_STATE_PATH))
    return ctx


@pytest.fixture(scope="function")
def logged_in_page(logged_in_context):
    """已登录页面。每次创建时验证 session 有效性，过期则自动重新登录。"""
    # 先检查 cached context 的 session 是否还活着
    check = logged_in_context.new_page()
    check.goto(f"{BASE_URL}/dashboard/project", wait_until="commit", timeout=NAVIGATION_TIMEOUT)
    wait_for_spa(check, max_wait=10)
    body = check.locator("body").inner_text()[:200].lower()
    check.close()

    if "sign in" in body:
        # Session 过期：清除缓存，重新登录
        AUTH_STATE_PATH.unlink(missing_ok=True)
        lp = logged_in_context.new_page()
        ok = _do_login(lp)
        lp.close()
        if ok:
            logged_in_context.storage_state(path=str(AUTH_STATE_PATH))

    p = logged_in_context.new_page()
    p.goto(f"{BASE_URL}/dashboard/project", wait_until="commit", timeout=NAVIGATION_TIMEOUT)
    wait_for_spa(p, max_wait=10)
    yield p
    p.close()


@pytest.fixture(scope="function")
def app(page):
    """PageFactory with unauthenticated page. Use logged_in_app for auth-required tests."""
    return PageFactory(page)


@pytest.fixture(scope="function")
def logged_in_app(logged_in_page):
    """PageFactory with authenticated page — main fixture for most tests."""
    return PageFactory(logged_in_page)


@pytest.fixture(scope="session")
def api_base_url():
    return BASE_URL


@pytest.fixture(scope="session")
def auth_token(logged_in_context):
    """从已登录 context 中提取 JWT token，供 API 测试使用。"""
    page = logged_in_context.new_page()
    page.goto(f"{BASE_URL}/dashboard/project", wait_until="commit", timeout=NAVIGATION_TIMEOUT)
    wait_for_spa(page, max_wait=10)
    token = page.evaluate("() => localStorage.getItem('token') || localStorage.getItem('auth_v2_session')")
    page.close()
    if not token:
        raise RuntimeError("Fixtures: 无法提取 auth token")
    return token


# ==================== HTML 报告 Hooks ====================


def _ci_layer() -> str:
    """读取当前 CI 层级（由 run_ci.py 设置）。"""
    import os
    return os.environ.get("QUOTR_CI_LAYER", "")


def _layer_for_nodeid(nodeid: str) -> str:
    """从测试路径推断 CI 层级（全量模式无 env var 时使用）。"""
    if "/smoke/" in nodeid:
        return "L0-Smoke"
    if "/security/" in nodeid or "/api/" in nodeid:
        return "L1-Critical"
    if "/regression/" in nodeid or "/performance/" in nodeid or "/ai/" in nodeid:
        return "L2-Regression"
    if any(x in nodeid for x in ["/payment/", "/a11y/", "/migration/", "/concurrency/"]):
        return "BLOCKED"
    return "—"


def _get_layer(nodeid: str = "") -> str:
    """获取层级标签：CI env 优先，否则从路径推断。"""
    ci = _ci_layer()
    return ci if ci else _layer_for_nodeid(nodeid)


def pytest_configure(config):
    """每个 session 创建全新 HtmlReport + 清理旧中间文件（保留 .html 报告）。"""
    from tests.utils.html_reporter import HtmlReport, REPORT_DIR
    # 清理上次 CI 分层残留 JSON + 旧日志
    for stale in REPORT_DIR.glob("ci_layer_*.json"):
        stale.unlink(missing_ok=True)
    for old_log in REPORT_DIR.glob("*.log"):
        old_log.unlink(missing_ok=True)
    (REPORT_DIR / ".ci_accumulator.json").unlink(missing_ok=True)

    reporter = HtmlReport()
    ci = _ci_layer()
    if ci:
        reporter.set_layer(ci)
    config._html_reporter = reporter


def pytest_runtest_makereport(item, call):
    """捕获 passed/failed/error。xdist 下在 worker 进程运行，config._html_reporter 可能为 None。"""
    reporter = getattr(item.config, "_html_reporter", None)
    if not reporter:
        return
    nid, layer = item.nodeid, _get_layer(item.nodeid)
    if call.when == "call":
        reporter.add_result(nodeid=nid, outcome="passed" if call.excinfo is None else "failed",
                           duration=call.duration, phase="call", layer=layer)
    elif call.when == "setup" and call.excinfo is not None:
        reporter.add_result(nodeid=nid, outcome="error", duration=call.duration, phase="setup", layer=layer)


def pytest_sessionfinish(session):
    """CI 模式：保存 per-layer JSON（供 run_ci.py 最终合并）。直接模式：不操作。"""
    reporter = getattr(session.config, "_html_reporter", None)
    if not reporter or reporter.total == 0:
        return
    if _ci_layer():
        reporter.save_layer_json()


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """xdist 安全：主进程在所有 worker 完成后执行。
    从 terminalreporter.stats 读取聚合结果，生成最终 HTML 报告。"""
    reporter = getattr(config, "_html_reporter", None)
    if not reporter:
        return
    # 从终端统计读取所有结果（兼容 xdist——worker 的结果已聚合到主进程）
    outcome_map = {"passed": "passed", "failed": "failed", "skipped": "skipped",
                   "error": "error", "deselected": "skipped"}
    for category, outcome in outcome_map.items():
        for rep in terminalreporter.stats.get(category, []):
            nid = getattr(rep, "nodeid", "")
            if nid:
                reporter.add_result(nodeid=nid, outcome=outcome,
                                   duration=getattr(rep, "duration", 0), phase="call",
                                   layer=_get_layer(nid))
    if reporter.total == 0:
        return
    if _ci_layer():
        reporter.save_layer_json()
    else:
        path = reporter.generate()
        terminalreporter.write_sep("=", f"HTML report: {path}")

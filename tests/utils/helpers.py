"""通用工具函数。"""
import time
import random
from pathlib import Path
from tests.config.settings import WAIT, NAVIGATION_TIMEOUT, SPA_MOUNT_TIMEOUT

SCREENSHOT_DIR = Path("tests/screenshots")
SCREENSHOT_DIR.mkdir(exist_ok=True)


def human_pause():
    """模拟人类操作的随机短暂停顿（用于反爬规避）。"""
    time.sleep(random.uniform(WAIT.HUMAN_DELAY_MIN, WAIT.HUMAN_DELAY_MAX) / 1000)


def snap(page, name: str):
    path = SCREENSHOT_DIR / f"{name}.png"
    page.screenshot(path=str(path), full_page=True)
    return path


def dump_text(page, max_lines=40):
    lines = [l.strip() for l in page.locator("body").inner_text().split("\n") if l.strip()]
    result = []
    for line in lines[:max_lines]:
        result.append(line[:140])
    return "\n".join(result)


def wait_for_spa(page, max_wait: int = None):
    """轮询直到 React 挂载到 #root。
    使用 Playwright 的 expect 断言机制等待，而非死循环 sleep。
    """
    seconds = max_wait if max_wait is not None else SPA_MOUNT_TIMEOUT
    for _ in range(seconds):
        time.sleep(WAIT.SPA_POLL_INTERVAL / 1000)
        try:
            mounted = page.evaluate(
                "() => { const r = document.getElementById('root'); return r && r.children.length > 0; }"
            )
            if mounted:
                return True
        except Exception:
            pass
    return False


def goto_spa(page, url: str, wait="load", timeout=None):
    """导航到 SPA 页面并等待 React 挂载。先试 load，失败回退 commit + 轮询。"""
    t = timeout or NAVIGATION_TIMEOUT
    try:
        page.goto(url, wait_until=wait, timeout=t)
    except Exception:
        try:
            page.goto(url, wait_until="commit", timeout=t)
        except Exception:
            pass
    wait_for_spa(page)
    human_pause()

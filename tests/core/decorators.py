"""Decorators — retry, screenshot on failure, step logging."""
import functools
import time
from pathlib import Path
from datetime import datetime

SCREENSHOT_DIR = Path("tests/screenshots")


def retry(times: int = 3, delay: float = 2.0, backoff: float = 1.5):
    """Retry on assertion error or timeout — handles flaky anti-bot/network."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last = None
            wait = delay
            for i in range(1, times + 1):
                try:
                    return func(*args, **kwargs)
                except (AssertionError, TimeoutError, Exception) as e:
                    last = e
                    if i < times:
                        time.sleep(wait)
                        wait *= backoff
            raise last

        return wrapper

    return decorator


def screenshot_on_failure(func):
    """Auto-screenshot when test fails. First arg or kwarg 'page' must have .screenshot()."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            page = None
            for a in args:
                if hasattr(a, "screenshot"):
                    page = a
                    break
            if not page:
                page = kwargs.get("page")
            if page:
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                p = SCREENSHOT_DIR / f"FAIL_{func.__name__}_{ts}.png"
                SCREENSHOT_DIR.mkdir(exist_ok=True)
                try:
                    page.screenshot(path=str(p), full_page=True)
                except Exception:
                    pass
            raise

    return wrapper

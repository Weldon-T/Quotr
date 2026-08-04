"""
读取测试配置。所有敏感值从 .env 读取，零硬编码。
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

BASE_URL = "https://test.quotr.ai"

# 凭据
QUOTR_EMAIL = os.environ["QUOTR_EMAIL"]
QUOTR_PASSWORD = os.environ["QUOTR_PASSWORD"]

# 超时配置（毫秒，除标注外）
NAVIGATION_TIMEOUT = 60000
SPA_MOUNT_TIMEOUT = 20  # 秒，轮询 #root 的最大等待
ELEMENT_WAIT_TIMEOUT = 15000
LOGIN_RETRY_MAX = 3

# 等待时间常量（毫秒）—— 避免硬编码 wait_for_timeout()
# 仅用于确实无法用 wait_for_selector/wait_for_url 等条件等待的场景
WAIT = type("Wait", (), {
    "AFTER_LOGIN_SUBMIT": 8000,    # 登录提交后等 redirect
    "AFTER_CLICK": 2000,           # 点击后等 UI 反应（Modal/Tab 切换）
    "AFTER_GOTO": 1000,            # 页面跳转后的缓冲
    "SPA_POLL_INTERVAL": 1000,     # wait_for_spa 轮询间隔（ms）
    "HUMAN_DELAY_MIN": 300,        # 模拟人类操作的最小延迟
    "HUMAN_DELAY_MAX": 1500,       # 模拟人类操作的最大延迟
    "SESSION_CHECK": 3000,         # 检查 localStorage/session 前的等待
    "RATE_LIMIT_THROTTLE": 300,    # Rate limit 测试的请求间隔（ms）
})()

# 浏览器
VIEWPORT = {"width": 1440, "height": 900}
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

# 已知测试环境数据（ID 用于 API 测试）
KNOWN_PROJECT_ID = 703
KNOWN_ORG_ID = "384"
KNOWN_SUPPLIER_ID = "CS0126"

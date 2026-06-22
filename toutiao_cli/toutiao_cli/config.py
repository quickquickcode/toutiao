"""
配置文件
"""

import os
from pathlib import Path

# Cookie 文件路径
COOKIES_FILE = os.getenv("TOUTIAO_COOKIES_FILE", "toutiao_cookies.json")
STORAGE_STATE_FILE = os.getenv("TOUTIAO_STORAGE_STATE_FILE", "")
BROWSER_STORAGE_FILE = os.getenv("TOUTIAO_BROWSER_STORAGE_FILE", "")
USER_DATA_DIR = os.getenv("TOUTIAO_USER_DATA_DIR", "")
CHROME_PATH = os.getenv(
    "TOUTIAO_CHROME_PATH",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
)

# 用户代理
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# 请求头
DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

# 今日头条 URL
TOUTIAO_URLS = {
    "login": "https://mp.toutiao.com/auth/page/login/",
    "homepage": "https://mp.toutiao.com/profile_v4/index",
    "article_publish": "https://mp.toutiao.com/profile_v4/graphic/publish",
    "micro_publish": "https://mp.toutiao.com/profile_v4/weitoutiao/publish",
}


def get_project_root() -> Path:
    """获取项目根目录"""
    return Path(__file__).parent.parent


def _resolve_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return get_project_root() / path


def get_cookies_path() -> str:
    """获取 Cookie 文件路径"""
    return str(_resolve_path(COOKIES_FILE))


def get_storage_state_path() -> str:
    """获取 Playwright storage_state 文件路径。"""
    if STORAGE_STATE_FILE:
        return str(_resolve_path(STORAGE_STATE_FILE))
    cookies_path = Path(get_cookies_path())
    return str(cookies_path.with_name(f"{cookies_path.stem}_storage_state.json"))


def get_browser_storage_path() -> str:
    """获取 sessionStorage 兼容存档路径。"""
    if BROWSER_STORAGE_FILE:
        return str(_resolve_path(BROWSER_STORAGE_FILE))
    cookies_path = Path(get_cookies_path())
    return str(cookies_path.with_name(f"{cookies_path.stem}_browser_storage.json"))


def get_user_data_dir() -> str:
    """获取 Playwright 持久化浏览器 Profile 目录。"""
    if USER_DATA_DIR:
        return str(_resolve_path(USER_DATA_DIR))
    cookies_path = Path(get_cookies_path())
    return str(cookies_path.with_name(f"{cookies_path.stem}_browser_profile"))

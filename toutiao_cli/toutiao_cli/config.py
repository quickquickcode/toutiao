"""
配置文件
"""

import os
from pathlib import Path

# Cookie 文件路径
COOKIES_FILE = os.getenv("TOUTIAO_COOKIES_FILE", "toutiao_cookies.json")

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


def get_cookies_path() -> str:
    """获取 Cookie 文件路径"""
    path = Path(COOKIES_FILE)
    if path.is_absolute():
        return str(path)
    return str(get_project_root() / path)

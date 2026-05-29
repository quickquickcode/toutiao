"""
今日头条 MCP 服务器配置模块

包含所有配置常量、URL 地址、请求头信息等。
"""

import os
from pathlib import Path
from typing import Dict, Any

# 基础配置
DEFAULT_COOKIES_FILE = os.getenv("TOUTIAO_COOKIES_FILE", "toutiao_cookies.json")
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# 今日头条相关 URL
TOUTIAO_URLS = {
    "login": "https://mp.toutiao.com/auth/page/login/",
    "homepage": "https://mp.toutiao.com/profile_v4/index",
    "publish_article": "https://mp.toutiao.com/mp/agw/article/publish/",
    "publish_micro": "https://mp.toutiao.com/mp/agw/article/publish_weitoutiao/",
    "article_list": "https://mp.toutiao.com/mp/agw/article/list/",
    "delete_article": "https://mp.toutiao.com/mp/agw/article/delete/",
    "upload": "https://mp.toutiao.com/mp/agw/media/upload_image/",
    "user_info": "https://mp.toutiao.com/mp/agw/media/user_login_status_api/",
    "content_stats": "https://mp.toutiao.com/mp/agw/article/article_read_detail/",
    "article_page": "https://mp.toutiao.com/profile_v4/graphic/publish",
    "micro_page": "https://mp.toutiao.com/profile_v4/ugc/weitt-new"
}

# 默认请求头
DEFAULT_HEADERS = {
    "User-Agent": DEFAULT_USER_AGENT,
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin"
}

# Selenium 配置
SELENIUM_CONFIG = {
    "headless": False,  # 改为False，方便用户看到登录过程
    "window_size": (1920, 1080),
    "timeout": 30,
    "implicit_wait": 10,
    "explicit_wait": 30,
    "chrome_options": [
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-blink-features=AutomationControlled",
        "--disable-extensions",
        "--no-first-run",
        "--disable-default-apps",
        "--disable-web-security",
        "--allow-running-insecure-content",
        "--disable-features=VizDisplayCompositor"
    ]
}# 内容发布配置
CONTENT_CONFIG = {
    "max_title_length": 100,
    "max_content_length": 50000,
    "max_weitoutiao_length": 2000,
    "supported_image_types": [".jpg", ".jpeg", ".png", ".gif", ".webp"],
    "max_image_size": 10 * 1024 * 1024,  # 10MB
    "max_images_per_post": 9
}

def get_project_root() -> Path:
    """获取项目根目录路径"""
    return Path(__file__).parent.parent

def get_cookies_file_path() -> str:
    """获取 Cookie 文件完整路径"""
    if os.path.isabs(DEFAULT_COOKIES_FILE):
        return DEFAULT_COOKIES_FILE
    return str(get_project_root() / DEFAULT_COOKIES_FILE)
"""
认证模块 - 使用 Playwright 扫码登录
"""

import json
import time
import logging
from typing import Optional

import requests
from playwright.sync_api import sync_playwright

from .config import TOUTIAO_URLS, DEFAULT_HEADERS, get_cookies_path

logger = logging.getLogger(__name__)


class TouTiaoAuth:
    """今日头条认证管理"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        self._load_cookies()

    def _get_cookies_path(self) -> str:
        return get_cookies_path()

    def _load_cookies(self) -> None:
        """从文件加载 Cookie"""
        try:
            path = self._get_cookies_path()
            if Path(path).exists():
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for cookie in data.get('cookies', []):
                    self.session.cookies.set(
                        cookie['name'],
                        cookie['value'],
                        domain=cookie.get('domain', '.toutiao.com')
                    )
                logger.info(f"已加载 {len(data.get('cookies', []))} 个 Cookie")
        except Exception as e:
            logger.warning(f"加载 Cookie 失败: {e}")

    def _save_cookies(self, cookies: list) -> None:
        """保存 Cookie 到文件"""
        try:
            path = Path(self._get_cookies_path())
            path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                'cookies': cookies,
                'timestamp': int(time.time())
            }
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"已保存 {len(cookies)} 个 Cookie")
        except Exception as e:
            logger.error(f"保存 Cookie 失败: {e}")

    def login(self) -> bool:
        """
        扫码登录（使用 Playwright）
        打开浏览器，等待用户扫码，完成后保存 Cookie
        """
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=False)
                context = browser.new_context()
                page = context.new_page()

                logger.info("正在打开登录页面...")
                page.goto(TOUTIAO_URLS['login'], timeout=60000)
                page.wait_for_load_state("domcontentloaded")

                logger.info("请在浏览器中扫码登录...")
                logger.info("登录成功后程序将自动检测")

                # 等待登录成功跳转
                try:
                    page.wait_for_url(
                        lambda url: (
                            'mp.toutiao.com/profile' in url or
                            'creator.toutiao.com' in url
                        ),
                        timeout=600000  # 10 分钟超时
                    )
                except Exception:
                    logger.error("登录超时")
                    browser.close()
                    return False

                # 保存 Cookie
                cookies = context.cookies()
                self._save_cookies(cookies)

                # 更新 session
                for cookie in cookies:
                    self.session.cookies.set(
                        cookie['name'],
                        cookie['value'],
                        domain=cookie.get('domain', '.toutiao.com')
                    )

                logger.info("登录成功！")
                browser.close()
                return True

        except Exception as e:
            logger.error(f"登录失败: {e}")
            return False

    def check_status(self) -> bool:
        """检查登录状态"""
        try:
            response = self.session.get(TOUTIAO_URLS['homepage'], timeout=10)
            if response.status_code == 200:
                text = response.text.lower()
                indicators = ['profile', 'creator', 'dashboard', 'publish', '创作者', '发布']
                for indicator in indicators:
                    if indicator in text:
                        logger.info(f"登录状态: 已登录 (检测到: {indicator})")
                        return True
                if 'login' not in text and 'auth' not in text:
                    return True
            return False
        except Exception as e:
            logger.error(f"检查登录状态失败: {e}")
            return False

    def get_session(self) -> requests.Session:
        """获取 requests Session"""
        return self.session


from pathlib import Path

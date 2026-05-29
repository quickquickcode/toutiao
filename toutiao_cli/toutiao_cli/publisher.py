"""
发布器 - 使用 Playwright 发布内容
"""

import logging
import os
from typing import Optional, List

from playwright.sync_api import sync_playwright

from .auth import TouTiaoAuth
from .config import TOUTIAO_URLS

logger = logging.getLogger(__name__)

# 系统 Chrome 路径
CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


class TouTiaoPublisher:
    """今日头条内容发布器"""

    def __init__(self, auth: TouTiaoAuth, use_chrome: bool = True):
        """
        初始化发布器

        Args:
            auth: 认证实例
            use_chrome: 是否使用系统 Chrome（默认 True，使用 Google Chrome.app）
                       False 则使用 Playwright 内置 Chromium
        """
        self.auth = auth
        self.use_chrome = use_chrome

    def _get_browser_context(self):
        """获取 Playwright 浏览器上下文"""
        pw = sync_playwright().start()

        if self.use_chrome and os.path.exists(CHROME_PATH):
            # 使用系统安装的 Google Chrome
            logger.info(f"使用系统 Chrome: {CHROME_PATH}")
            # 注意：如果要复用 Chrome 已登录状态，可以添加 user_data_dir 参数
            # 但这需要关闭正在运行的 Chrome
            browser = pw.chromium.launch(
                headless=False,
                executable_path=CHROME_PATH,
                args=[
                    "--disable-blink-features=AutomationControlled",
                ]
            )
        else:
            # 使用 Playwright 内置 Chromium
            logger.info("使用 Playwright 内置 Chromium")
            browser = pw.chromium.launch(headless=False)

        context = browser.new_context(
            viewport={"width": 1920, "height": 1080}
        )
        return pw, browser, context

    def _close_browser(self, pw, browser):
        """关闭浏览器"""
        try:
            browser.close()
        finally:
            pw.stop()

    def _transfer_cookies(self, context):
        """转移 Cookie 到浏览器上下文"""
        cookies = []
        for c in self.auth.get_session().cookies:
            if 'toutiao.com' in (c.domain or ''):
                cookies.append({
                    'name': c.name,
                    'value': c.value,
                    'domain': c.domain or '.toutiao.com',
                    'path': c.path or '/',
                })
        if cookies:
            context.add_cookies(cookies)
            logger.info(f"已转移 {len(cookies)} 个 Cookie")

    def publish_article(
        self,
        title: str,
        html_content: str,
        images: Optional[List[str]] = None,
        cover_image: Optional[str] = None,
    ):
        """
        发布图文文章

        打开浏览器，填充内容，等待用户手动点击发布按钮

        Args:
            title: 文章标题
            html_content: HTML 格式的文章内容
            images: 本地图片路径列表（暂不支持）
            cover_image: 封面图片路径（暂不支持）
        """
        pw, browser, context = self._get_browser_context()

        try:
            # 转移 Cookie
            self._transfer_cookies(context)
            page = context.new_page()

            # 打开发布页面
            logger.info("正在打开发布页面...")
            page.goto(TOUTIAO_URLS['article_publish'], timeout=60000)
            page.wait_for_load_state("domcontentloaded")

            # 检查是否需要登录
            if 'login' in page.url or 'auth' in page.url:
                logger.error("未登录或登录已过期，请先运行: python3 cli.py login")
                return {'success': False, 'message': '请先登录'}

            # 填入标题
            logger.info("正在填入标题...")
            title_selector = "textarea[placeholder*='标题']"
            page.wait_for_selector(title_selector, timeout=10000)
            page.fill(title_selector, title)

            # 填入内容
            logger.info("正在填入内容...")
            editor = page.locator(".ProseMirror").first
            editor.click()

            # 使用 JavaScript 设置 HTML 内容
            page.evaluate(
                """(el, html) => {
                    el.innerHTML = html;
                    el.dispatchEvent(new Event('input', {bubbles: true}));
                    el.dispatchEvent(new Event('change', {bubbles: true}));
                }""",
                html_content
            )

            logger.info("内容已填充，请在浏览器中手动检查并点击发布按钮")
            logger.info("按 Ctrl+C 终止程序")

            # 等待 5 分钟（用户手动发布）
            page.wait_for_timeout(300000)

            return {'success': True, 'message': '请在浏览器中手动发布'}

        except Exception as e:
            logger.error(f"发布异常: {e}")
            return {'success': False, 'message': str(e)}
        finally:
            self._close_browser(pw, browser)

    def publish_micro(
        self,
        content: str,
        html_content: Optional[str] = None,
        images: Optional[List[str]] = None,
        topic: Optional[str] = None,
    ):
        """
        发布微头条

        打开浏览器，填充内容，等待用户手动点击发布按钮

        Args:
            content: 微头条文本内容（纯文本或 Markdown）
            html_content: HTML 格式内容（如果提供，则忽略 content 的 Markdown 解析）
            images: 本地图片路径列表（最多9张）
            topic: 话题标签（会自动添加 #）
        """
        pw, browser, context = self._get_browser_context()

        try:
            # 转移 Cookie
            self._transfer_cookies(context)
            page = context.new_page()

            # 打开微头条页面
            logger.info("正在打开微头条发布页面...")
            page.goto(TOUTIAO_URLS['micro_publish'], timeout=60000)
            page.wait_for_load_state("domcontentloaded")

            # 检查是否需要登录
            if 'login' in page.url or 'auth' in page.url:
                logger.error("未登录或登录已过期，请先运行: python3 cli.py login")
                return {'success': False, 'message': '请先登录'}

            # 处理话题
            if topic:
                if not topic.startswith('#'):
                    topic = f'#{topic}#'
                content = f"{topic}\n\n{content}"

            # 填入内容
            logger.info("正在填入内容...")
            # 尝试多种选择器
            editor = page.locator(".ProseMirror, textarea.byte-textarea-content, [contenteditable='true']").first
            editor.wait_for(state="visible", timeout=10000)

            # 如果提供了 HTML 内容，直接使用；否则解析 Markdown
            final_content = html_content if html_content else content

            if editor.evaluate("el => el.tagName.toLowerCase()") == "textarea":
                editor.fill(final_content)
            else:
                editor.click()
                editor.evaluate(
                    """(el, html) => {
                        el.innerHTML = html;
                        el.dispatchEvent(new Event('input', {bubbles: true}));
                    }""",
                    final_content
                )

            # 上传图片（如果有）
            if images:
                for i, img_path in enumerate(images[:9]):
                    if not os.path.exists(img_path):
                        logger.warning(f"图片不存在，跳过: {img_path}")
                        continue
                    logger.info(f"正在上传第 {i+1} 张图片...")
                    selectors = [
                        "input[type='file'][accept*='image']",
                        "input[type='file']",
                    ]
                    for selector in selectors:
                        locator = page.locator(selector)
                        if locator.count() > 0:
                            locator.first.set_input_files(img_path)
                            page.wait_for_timeout(1000)
                            break

            logger.info("内容已填充，请在浏览器中手动检查并点击发布按钮")
            logger.info("按 Ctrl+C 终止程序")

            # 等待 5 分钟（用户手动发布）
            page.wait_for_timeout(300000)

            return {'success': True, 'message': '请在浏览器中手动发布'}

        except Exception as e:
            logger.error(f"发布异常: {e}")
            return {'success': False, 'message': str(e)}
        finally:
            self._close_browser(pw, browser)

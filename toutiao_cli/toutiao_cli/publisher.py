"""
发布器 - 使用 Playwright 发布内容
"""

import logging
import os
from pathlib import Path
import json
from typing import Optional, List

from playwright.sync_api import sync_playwright

from .auth import TouTiaoAuth
from .config import (
    CHROME_PATH,
    TOUTIAO_URLS,
    get_browser_storage_path,
    get_storage_state_path,
    get_user_data_dir,
)

logger = logging.getLogger(__name__)

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
            logger.info(f"使用系统 Chrome: {CHROME_PATH}")
            browser = pw.chromium.launch(
                headless=False,
                executable_path=CHROME_PATH,
                args=[
                    "--disable-blink-features=AutomationControlled",
                ],
            )
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                locale="zh-CN",
                timezone_id="Asia/Shanghai",
            )
            self._hydrate_context_storage(context)
            self._install_storage_init_script(context)
            return pw, browser, context

        logger.info("使用 Playwright Chromium 持久化 Profile")
        user_data_dir = get_user_data_dir()
        Path(user_data_dir).mkdir(parents=True, exist_ok=True)
        context = pw.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            viewport={"width": 1920, "height": 1080},
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
            ),
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-features=IsolateOrigins,site-per-process",
                "--disable-site-isolation-trials",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-accelerated-2d-canvas",
                "--disable-gpu",
            ],
        )
        self._hydrate_context_storage(context)
        self._install_storage_init_script(context)
        return pw, context, context

    def _close_browser(self, pw, browser):
        """关闭浏览器"""
        try:
            browser.close()
        finally:
            pw.stop()

    def _hydrate_context_storage(self, context) -> None:
        """补齐旧 Cookie 文件和 storage_state 的登录态。"""
        storage_state_path = Path(get_storage_state_path())
        if storage_state_path.exists():
            try:
                data = json.loads(storage_state_path.read_text(encoding="utf-8"))
                cookies = data.get("cookies", [])
                if cookies:
                    context.add_cookies(cookies)
                    logger.info(f"已从 storage_state 转移 {len(cookies)} 个 Cookie")
            except Exception as exc:
                logger.warning(f"加载 storage_state 失败: {exc}")
        self._transfer_cookies(context)

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

    def _restore_page_storage(self, page) -> None:
        """把登录时保存的 localStorage/sessionStorage 写回页面。"""
        storage_path = Path(get_browser_storage_path())
        if not storage_path.exists():
            return
        try:
            data = json.loads(storage_path.read_text(encoding="utf-8"))
            page.evaluate(
                """(data) => {
                    for (const [key, value] of Object.entries(data.localStorage || {})) {
                        window.localStorage.setItem(key, String(value));
                    }
                    for (const [key, value] of Object.entries(data.sessionStorage || {})) {
                        window.sessionStorage.setItem(key, String(value));
                    }
                }""",
                data,
            )
            logger.info("已恢复 localStorage/sessionStorage")
        except Exception as exc:
            logger.warning(f"恢复浏览器 Storage 失败: {exc}")

    def _saved_storage_payload(self) -> dict:
        """读取保存的浏览器 Storage，兼容旧文件与 Playwright storage_state。"""
        storage_path = Path(get_browser_storage_path())
        if storage_path.exists():
            try:
                return json.loads(storage_path.read_text(encoding="utf-8"))
            except Exception as exc:
                logger.warning(f"读取浏览器 Storage 失败: {exc}")

        state_path = Path(get_storage_state_path())
        if not state_path.exists():
            return {}
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
            local_storage = {}
            for origin in state.get("origins", []):
                if "toutiao.com" not in origin.get("origin", ""):
                    continue
                for item in origin.get("localStorage", []):
                    if item.get("name"):
                        local_storage[item["name"]] = item.get("value", "")
            return {"localStorage": local_storage, "sessionStorage": {}}
        except Exception as exc:
            logger.warning(f"读取 storage_state 失败: {exc}")
            return {}

    def _install_storage_init_script(self, context) -> None:
        """在头条页面脚本运行前恢复 Storage，避免页面渲染成降级状态。"""
        data = self._saved_storage_payload()
        if not data:
            return
        payload = json.dumps(data, ensure_ascii=False)
        script = """(() => {
                const data = __PAYLOAD__;
                if (!location.hostname.includes('toutiao.com')) return;
                for (const [key, value] of Object.entries(data.localStorage || {})) {
                    window.localStorage.setItem(key, String(value));
                }
                for (const [key, value] of Object.entries(data.sessionStorage || {})) {
                    window.sessionStorage.setItem(key, String(value));
                }
            })()""".replace("__PAYLOAD__", payload)
        context.add_init_script(script)
        logger.info("已安装头条 Storage 预注入脚本")

    def _prepare_publish_page(self, page) -> dict:
        """滚动到底部并确认底部发布栏状态。"""
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(2500)
        self._restore_page_storage(page)

        # 尝试关闭可能遮挡发布按钮的弹窗/抽屉
        page.evaluate(
            """() => {
                const selectors = [
                    '.byte-drawer-mask',
                    '.byte-modal-mask',
                    '.tt-login-guide__mask',
                    '.guide-popup-mask',
                    '[class*="mask"]',
                ];
                selectors.forEach((sel) => {
                    document.querySelectorAll(sel).forEach((el) => {
                        try { el.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true })); } catch {}
                    });
                });
                window.scrollTo(0, document.documentElement.scrollHeight || document.body.scrollHeight);
            }"""
        )
        page.wait_for_timeout(1000)

        # 如果发布按钮固定在底部但不在视口，尝试滚动让它可见
        page.evaluate(
            """() => {
                const all = Array.from(document.querySelectorAll('button, span, div, a'));
                const publish = all.find((el) => (el.textContent || '').trim() === '发布');
                if (publish) {
                    const rect = publish.getBoundingClientRect();
                    if (rect.top > window.innerHeight || rect.bottom < 0) {
                        publish.scrollIntoView({ block: 'center', behavior: 'instant' });
                    }
                }
            }"""
        )
        page.wait_for_timeout(500)

        return page.evaluate(
            """() => {
                const all = Array.from(document.querySelectorAll('button, span, div, a'));
                const items = all
                    .map((el) => {
                        const rect = el.getBoundingClientRect();
                        const style = getComputedStyle(el);
                        return {
                            tag: el.tagName,
                            text: (el.textContent || '').trim(),
                            className: String(el.className || ''),
                            visible: rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden',
                            fixed: style.position === 'fixed',
                            disabled: el.disabled,
                            rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height },
                        };
                    })
                    .filter((item) => item.visible && item.text && item.text.length <= 20);
                const publishLike = items.filter((item) => item.text === '发布' || item.text === '存草稿');
                const publishBtn = all.find((el) => (el.textContent || '').trim() === '发布');
                return {
                    url: location.href,
                    innerWidth,
                    innerHeight,
                    scrollY,
                    scrollHeight: document.documentElement.scrollHeight,
                    publishLike,
                    hasPublishText: document.body.innerText.includes('发布'),
                    hasDraftText: document.body.innerText.includes('存草稿'),
                    publishBtnExists: !!publishBtn,
                    publishBtnRect: publishBtn ? publishBtn.getBoundingClientRect() : null,
                };
            }"""
        )

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
            page = context.pages[0] if context.pages else context.new_page()

            # 打开发布页面
            logger.info("正在打开发布页面...")
            page.goto(TOUTIAO_URLS['article_publish'], timeout=60000)
            self._prepare_publish_page(page)

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
            page = context.pages[0] if context.pages else context.new_page()

            # 打开微头条页面
            logger.info("正在打开微头条发布页面...")
            page.goto(TOUTIAO_URLS['micro_publish'], timeout=60000)
            page_state = self._prepare_publish_page(page)
            logger.info(f"微头条页面状态: {page_state}")

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
            page_state = self._prepare_publish_page(page)
            if not page_state.get("hasPublishText"):
                logger.warning(f"页面未检测到发布入口，请检查账号状态或页面版本: {page_state}")
            logger.info("按 Ctrl+C 终止程序")

            # 等待 5 分钟（用户手动发布）
            page.wait_for_timeout(300000)

            return {'success': True, 'message': '请在浏览器中手动发布'}

        except Exception as e:
            logger.error(f"发布异常: {e}")
            return {'success': False, 'message': str(e)}
        finally:
            self._close_browser(pw, browser)

    def debug_micro_page(self) -> dict:
        """打开微头条页并返回页面/按钮诊断信息。"""
        pw, browser, context = self._get_browser_context()
        try:
            page = context.pages[0] if context.pages else context.new_page()
            page.goto(TOUTIAO_URLS["micro_publish"], timeout=60000)
            if "login" in page.url or "auth" in page.url:
                return {"ok": False, "message": "需要登录", "url": page.url}
            page_state = self._prepare_publish_page(page)
            screenshot_path = Path(get_browser_storage_path()).with_name("toutiao_micro_debug.png")
            try:
                page.screenshot(path=str(screenshot_path), full_page=False)
                page_state["screenshot_path"] = str(screenshot_path)
            except Exception as exc:
                page_state["screenshot_error"] = str(exc)
            page.wait_for_timeout(5000)
            return {"ok": True, **page_state}
        finally:
            self._close_browser(pw, browser)

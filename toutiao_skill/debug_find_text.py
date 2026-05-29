#!/usr/bin/env python3
"""Debug - find text article and click it"""

import asyncio
from playwright.async_api import async_playwright

async def debug_click():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
        )
        page = await context.new_page()

        await page.goto("https://open.toutiao.com/", wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(3)

        # Click tech tab
        tabs = await page.query_selector_all('.fx-tab-cell')
        for tab in tabs:
            text = await tab.inner_text()
            if '科技' in text:
                await tab.click()
                print(f"Clicked: {text}")
                break
        await asyncio.sleep(3)

        # Find first NON-VIDEO article
        articles_info = await page.evaluate('''
            () => {
                const cards = document.querySelectorAll('.fx-feed-card-wrapper');
                for (const card of cards) {
                    const isVideo = card.querySelector('.is_video_class') !== null;
                    const groupId = card.getAttribute('data-group-id');
                    const titleEl = card.querySelector('.title');
                    const title = titleEl ? titleEl.innerText : '';
                    if (!isVideo && groupId) {
                        return { groupId, title, isVideo };
                    }
                }
                return null;
            }
        ''')

        if not articles_info:
            print("No text articles found!")
            await browser.close()
            return

        print(f"Found text article: group_id={articles_info['groupId']}")
        print(f"Title: {articles_info['title'][:50]}...")

        # Scroll to make it visible
        selector = f'.fx-feed-card-wrapper[data-group-id="{articles_info["groupId"]}"]'
        await page.evaluate(f'''
            () => {{
                const card = document.querySelector('{selector}');
                if (card) {{
                    const container = card.closest('.fx-pull-refresh');
                    if (container) {{
                        container.scrollTop = card.offsetTop - 100;
                    }}
                    card.click();
                }}
            }}
        ''')

        await asyncio.sleep(4)
        print(f"URL after click: {page.url}")

        if '/a' in page.url:
            print("SUCCESS!")
            html = await page.content()
            if 'window._SSR_DATA' in html:
                print("Found _SSR_DATA")
        else:
            print("Click didn't navigate")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_click())
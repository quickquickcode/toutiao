#!/usr/bin/env python3
"""Debug - try different click methods"""

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
                break
        await asyncio.sleep(3)

        # Find first non-video article
        articles_info = await page.evaluate('''
            () => {
                const cards = document.querySelectorAll('.fx-feed-card-wrapper');
                for (const card of cards) {
                    const isVideo = card.querySelector('.is_video_class') !== null;
                    const groupId = card.getAttribute('data-group-id');
                    const titleEl = card.querySelector('.title');
                    const title = titleEl ? titleEl.innerText : '';
                    if (!isVideo && groupId) {
                        return { groupId, title };
                    }
                }
                return null;
            }
        ''')

        if not articles_info:
            print("No text articles found!")
            await browser.close()
            return

        print(f"Article: {articles_info['groupId']}")
        selector = f'.fx-feed-card-wrapper[data-group-id="{articles_info["groupId"]}"]'

        # Try dispatchEvent
        print("\nTrying dispatchEvent...")
        await page.evaluate(f'''
            () => {{
                const card = document.querySelector('{selector}');
                if (card) {{
                    const event = new MouseEvent('click', {{
                        view: window,
                        bubbles: true,
                        cancelable: true
                    }});
                    card.dispatchEvent(event);
                    console.log('dispatchEvent sent');
                }}
            }}
        ''')

        await asyncio.sleep(4)
        print(f"URL: {page.url}")

        if '/a' in page.url:
            print("SUCCESS!")
        else:
            # Maybe need to interact with a child element
            print("\nTrying to find clickable child...")
            child_info = await page.evaluate(f'''
                (gid) => {{
                    const card = document.querySelector('.fx-feed-card-wrapper[data-group-id="' + gid + '"]');
                    if (!card) return 'card not found';

                    // Try clicking on title
                    const title = card.querySelector('.title');
                    if (title) {{
                        title.click();
                        return 'clicked title';
                    }}

                    // Try clicking on info-box
                    const infoBox = card.querySelector('.info-box');
                    if (infoBox) {{
                        infoBox.click();
                        return 'clicked info-box';
                    }}

                    return 'no clickable children found';
                }}
            ''', articles_info["groupId"])
            print(f"Child click result: {child_info}")
            await asyncio.sleep(4)
            print(f"URL after child click: {page.url}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_click())
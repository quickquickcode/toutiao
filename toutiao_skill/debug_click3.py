#!/usr/bin/env python3
"""Debug - try force click"""

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

        # Get first article
        cards = await page.query_selector_all('.fx-feed-card-wrapper')
        first_card = cards[0]
        group_id = await first_card.get_attribute('data-group-id')
        print(f"group_id: {group_id}")

        selector = f'.fx-feed-card-wrapper[data-group-id="{group_id}"]'

        # Try scrolling into view via JS first
        print("\nScrolling into view via JS...")
        await page.evaluate(f'''
            () => {{
                const card = document.querySelector('{selector}');
                if (card) {{
                    card.scrollIntoView({{block: 'center'}});
                    console.log('Scrolled into view');
                }} else {{
                    console.log('Card not found');
                }}
            }}
        ''')
        await asyncio.sleep(2)

        # Now try page.click with force
        print("Trying page.click with force=true...")
        try:
            await page.click(selector, force=True, timeout=5000)
            print("Force click succeeded!")
        except Exception as e:
            print(f"Force click failed: {e}")

        await asyncio.sleep(3)
        print(f"URL: {page.url}")

        if '/a' in page.url:
            print("SUCCESS!")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_click())
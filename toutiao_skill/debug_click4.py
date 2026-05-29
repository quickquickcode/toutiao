#!/usr/bin/env python3
"""Debug - try JS click after scrolling"""

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

        # Scroll via the container
        container = await page.query_selector('.fx-pull-refresh.feedback-feed-list-wrapper')
        print(f"\nContainer found: {container is not None}")

        if container:
            # Scroll to make element visible
            await container.evaluate('''(el) => {
                const card = el.querySelector('.fx-feed-card-wrapper');
                if (card) {
                    el.scrollTop = card.offsetTop - 200;
                    console.log("Scrolled to:", card.offsetTop);
                }
            }''')
            await asyncio.sleep(1)

        # Now try JS click
        print("\nTrying JS click via evaluate...")
        click_result = await page.evaluate(f'''
            () => {{
                const card = document.querySelector('{selector}');
                if (card) {{
                    card.click();
                    return 'clicked';
                }}
                return 'not_found';
            }}
        ''')
        print(f"JS click result: {click_result}")

        await asyncio.sleep(3)
        print(f"URL: {page.url}")

        if '/a' in page.url:
            print("SUCCESS - on article page!")

            # Try to extract content
            html = await page.content()
            if 'window._SSR_DATA' in html:
                print("Found _SSR_DATA")
            else:
                print("No _SSR_DATA")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_click())
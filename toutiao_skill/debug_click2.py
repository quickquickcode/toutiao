#!/usr/bin/env python3
"""Debug article click with page.click"""

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

        # Get first article info
        cards = await page.query_selector_all('.fx-feed-card-wrapper')
        print(f"Found {len(cards)} cards")

        first_card = cards[0]
        group_id = await first_card.get_attribute('data-group-id')
        print(f"First article group_id: {group_id}")

        # Try using page.click on the selector
        selector = f'.fx-feed-card-wrapper[data-group-id="{group_id}"]'

        print(f"\nTrying page.click('{selector[:50]}...')")

        # Scroll to make sure visible
        container = await page.query_selector('.fx-pull-refresh.feedback-feed-list-wrapper')
        if container:
            await container.evaluate('el => el.scrollTo(0, 0)')
        await asyncio.sleep(1)

        url_before = page.url
        print(f"URL before: {url_before}")

        try:
            await page.click(selector, timeout=5000)
            print("Click succeeded")
        except Exception as e:
            print(f"Click failed: {e}")

        await asyncio.sleep(3)
        print(f"URL after: {page.url}")

        if '/a' in page.url:
            print("SUCCESS!")
        else:
            print("Not on article page")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_click())
#!/usr/bin/env python3
"""Debug page.goto approach"""

import asyncio
from playwright.async_api import async_playwright

async def debug_goto():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
        )
        page = await context.new_page()

        # First load
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

        # Check cards
        cards = await page.query_selector_all('.fx-feed-card-wrapper')
        print(f"After first load: {len(cards)} cards")

        # Find a group_id
        if cards:
            group_id = await cards[0].get_attribute('data-group-id')
            print(f"First card group_id: {group_id}")

        # Now goto again
        await page.goto("https://open.toutiao.com/", wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(3)

        # Click tech tab again
        tabs = await page.query_selector_all('.fx-tab-cell')
        for tab in tabs:
            text = await tab.inner_text()
            if '科技' in text:
                await tab.click()
                print(f"Clicked again: {text}")
                break
        await asyncio.sleep(3)

        # Check cards again
        cards = await page.query_selector_all('.fx-feed-card-wrapper')
        print(f"After second load: {len(cards)} cards")

        # Try to find the same group_id
        if group_id:
            selector = f'.fx-feed-card-wrapper[data-group-id="{group_id}"]'
            card = await page.query_selector(selector)
            if card:
                print(f"Found same card!")
            else:
                print(f"Same card NOT found!")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_goto())
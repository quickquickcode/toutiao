#!/usr/bin/env python3
"""Debug scrolling to see what's on the page"""

import asyncio
from playwright.async_api import async_playwright

async def debug_scroll():
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

        # Check initial state
        cards = await page.query_selector_all('.news_tech .fx-feed-card-wrapper')
        print(f"Initial cards: {len(cards)}")

        # Scroll multiple times
        for i in range(5):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2)

            cards = await page.query_selector_all('.news_tech .fx-feed-card-wrapper')
            print(f"After scroll {i+1}: {len(cards)} cards")

            # Check body height
            height = await page.evaluate("document.body.scrollHeight")
            print(f"  Page height: {height}")

        # Get some card info
        cards = await page.query_selector_all('.news_tech .fx-feed-card-wrapper')
        for j, card in enumerate(cards[:3]):
            group_id = await card.get_attribute('data-group-id')
            title_elem = await card.query_selector('.title')
            title = await title_elem.inner_text() if title_elem else 'N/A'
            print(f"Card {j}: group_id={group_id}, title={title[:30]}...")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_scroll())
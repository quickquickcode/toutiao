#!/usr/bin/env python3
"""Debug container scroll"""

import asyncio
from playwright.async_api import async_playwright

async def debug_container_scroll():
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

        # Find container
        container = await page.query_selector('.fx-pull-refresh.feedback-feed-list-wrapper')
        if container:
            info = await container.evaluate('''el => ({
                scrollHeight: el.scrollHeight,
                scrollTop: el.scrollTop,
                clientHeight: el.clientHeight
            })''')
            print(f"Container initial: scrollH={info['scrollHeight']}, scrollTop={info['scrollTop']}, clientH={info['clientHeight']}")

        # Check cards
        cards = await page.query_selector_all('.fx-feed-card-wrapper')
        print(f"Initial cards: {len(cards)}")

        # Scroll container
        for i in range(5):
            if container:
                await container.evaluate('el => el.scrollBy(0, 800)')
            await asyncio.sleep(1.5)

            if container:
                info = await container.evaluate('''el => ({
                    scrollHeight: el.scrollHeight,
                    scrollTop: el.scrollTop,
                    clientHeight: el.clientHeight
                })''')
                print(f"After scroll {i+1}: scrollH={info['scrollHeight']}, scrollTop={info['scrollTop']}")

            cards = await page.query_selector_all('.fx-feed-card-wrapper')
            print(f"  Cards: {len(cards)}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_container_scroll())
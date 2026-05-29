#!/usr/bin/env python3
"""Debug - check all containers and their content"""

import asyncio
from playwright.async_api import async_playwright

async def debug_containers():
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

        # Find ALL containers
        containers = await page.query_selector_all('.fx-pull-refresh.feedback-feed-list-wrapper')
        print(f"Total containers: {len(containers)}")

        for i, c in enumerate(containers):
            info = await c.evaluate('''el => ({
                scrollHeight: el.scrollHeight,
                scrollTop: el.scrollTop,
                clientHeight: el.clientHeight,
                children: el.children.length,
                visible: el.offsetParent !== null || el.style.display !== 'none'
            })''')
            cards_in_container = await c.query_selector_all('.fx-feed-card-wrapper')
            print(f"\nContainer {i}:")
            print(f"  scrollH={info['scrollHeight']}, scrollTop={info['scrollTop']}, clientH={info['clientHeight']}")
            print(f"  children={info['children']}, visible={info['visible']}")
            print(f"  fx-feed-card-wrapper count: {len(cards_in_container)}")

        # Check which container has the most cards
        all_cards = await page.query_selector_all('.fx-feed-card-wrapper')
        print(f"\nTotal .fx-feed-card-wrapper on page: {len(all_cards)}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_containers())
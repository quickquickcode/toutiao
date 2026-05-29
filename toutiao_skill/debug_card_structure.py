#!/usr/bin/env python3
"""Debug card structure"""

import asyncio
from playwright.async_api import async_playwright

async def debug_card():
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

        # Get first card HTML
        card = await page.query_selector('.fx-feed-card-wrapper')
        if card:
            html = await card.evaluate('el => el.outerHTML')
            print(f"Card HTML:\n{html[:2000]}")

            # Check for clickable elements
            print("\n\nLooking for links...")
            links = await card.query_selector_all('a')
            print(f"Found {len(links)} <a> tags")
            for i, link in enumerate(links[:3]):
                href = await link.get_attribute('href')
                text = await link.inner_text()
                print(f"  Link {i}: href={href}, text={text[:30]}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_card())
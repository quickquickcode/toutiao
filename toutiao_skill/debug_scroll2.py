#!/usr/bin/env python3
"""Debug scrolling - check scrollHeight vs innerHeight"""

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

        # Check scroll info
        info = await page.evaluate("""
            () => ({
                scrollHeight: document.body.scrollHeight,
                clientHeight: document.body.clientHeight,
                scrollTop: document.documentElement.scrollTop,
                windowHeight: window.innerHeight
            })
        """)
        print(f"Initial: scrollHeight={info['scrollHeight']}, clientHeight={info['clientHeight']}, scrollTop={info['scrollTop']}, windowHeight={info['windowHeight']}")

        # Try scrolling down incrementally
        for i in range(5):
            await page.evaluate("window.scrollBy(0, 800)")
            await asyncio.sleep(1.5)

            info = await page.evaluate("""
                () => ({
                    scrollHeight: document.body.scrollHeight,
                    scrollTop: document.documentElement.scrollTop,
                    windowHeight: window.innerHeight,
                    cards: document.querySelectorAll('.news_tech .fx-feed-card-wrapper').length
                })
            """)
            print(f"After scroll {i+1}: scrollHeight={info['scrollHeight']}, scrollTop={info['scrollTop']}, cards={info['cards']}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_scroll())
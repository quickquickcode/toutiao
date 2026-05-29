#!/usr/bin/env python3
"""Debug scrolling - find the actual scroll container"""

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
                break
        await asyncio.sleep(3)

        # Find scrollable containers
        scroll_info = await page.evaluate("""
            () => {
                const containers = [];
                const allElements = document.querySelectorAll('*');
                for (const el of allElements) {
                    const style = window.getComputedStyle(el);
                    if (style.overflowY === 'auto' || style.overflowY === 'scroll' ||
                        style.overflow === 'auto' || style.overflow === 'scroll') {
                        containers.push({
                            tag: el.tagName,
                            class: el.className.substring(0, 100),
                            id: el.id,
                            scrollHeight: el.scrollHeight,
                            clientHeight: el.clientHeight,
                            overflow: style.overflow
                        });
                    }
                }
                return containers;
            }
        """)
        print("Scrollable containers:")
        for c in scroll_info[:10]:
            print(f"  {c}")

        # Check for specific toutiao scroll elements
        toutiao_scroll = await page.query_selector_all('[class*="scroll"]')
        print(f"\nElements with 'scroll' in class: {len(toutiao_scroll)}")

        # Check the main content area
        main_area = await page.query_selector('.fx-feed-card-list')
        if main_area:
            info = await page.evaluate("""(el) => ({
                scrollHeight: el.scrollHeight,
                clientHeight: el.clientHeight,
                scrollTop: el.scrollTop,
                class: el.className
            })""", main_area)
            print(f"\n.feed-card-list: {info}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_scroll())
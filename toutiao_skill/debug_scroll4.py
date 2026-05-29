#!/usr/bin/env python3
"""Debug - check structure after clicking tech tab"""

import asyncio
from playwright.async_api import async_playwright

async def debug_structure():
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

        # Check cards before scrolling
        cards_before = await page.query_selector_all('.news_tech .fx-feed-card-wrapper')
        print(f"Cards after click (no scroll): {len(cards_before)}")

        # Check all fx-pull-refresh containers
        containers = await page.query_selector_all('.fx-pull-refresh')
        print(f"fx-pull-refresh containers: {len(containers)}")
        for i, c in enumerate(containers):
            cls = await c.get_attribute('class')
            scroll_info = await c.evaluate("""el => ({
                scrollHeight: el.scrollHeight,
                clientHeight: el.clientHeight,
                scrollTop: el.scrollTop,
                children: el.children.length
            })""")
            print(f"  Container {i}: class={cls[:80]}, scrollH={scroll_info['scrollHeight']}, clientH={scroll_info['clientHeight']}, children={scroll_info['children']}")

        # Check news_tech section
        tech_section = await page.query_selector('.news_tech')
        if tech_section:
            print(f"\n.news_tech found")
            # Check its children
            children = await tech_section.evaluate("""el => ({
                children: el.children.length,
                innerHTML: el.innerHTML.substring(0, 200)
            })""")
            print(f"  children: {children['children']}")
        else:
            print(f"\n.news_tech NOT found!")

        # Get page HTML snippet around the feed
        body_html = await page.evaluate("""document.body.innerHTML.substring(0, 3000)""")
        print(f"\nBody HTML (first 3000 chars):\n{body_html}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_structure())
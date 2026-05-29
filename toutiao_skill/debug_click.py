#!/usr/bin/env python3
"""Debug article click"""

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

        # Get first article group_id
        first_card = await page.query_selector('.fx-feed-card-wrapper')
        group_id = await first_card.get_attribute('data-group-id')
        title = await first_card.query_selector('.title')
        title_text = await title.inner_text() if title else 'N/A'
        print(f"First article: group_id={group_id}, title={title_text[:30]}")

        # Scroll to top first
        container = await page.query_selector('.fx-pull-refresh.feedback-feed-list-wrapper')
        if container:
            await container.evaluate('el => el.scrollTo(0, 0)')
        await asyncio.sleep(1)

        # Click the article
        print(f"\nClicking article...")
        url_before = page.url
        print(f"URL before click: {url_before}")

        await page.evaluate(f'''
            () => {{
                const cards = document.querySelectorAll('.fx-feed-card-wrapper');
                for (const card of cards) {{
                    if (card.getAttribute('data-group-id') === '{group_id}') {{
                        card.scrollIntoView();
                        card.click();
                        break;
                    }}
                }}
            }}
        ''')

        # Wait for navigation
        print("Waiting for navigation...")
        try:
            await page.wait_for_url('**/a**', timeout=5000)
            print(f"Navigated to: {page.url}")
        except:
            print(f"Navigation timeout! URL is still: {page.url}")

        await asyncio.sleep(3)
        print(f"Final URL: {page.url}")

        # Check if we're on article page
        if '/a' in page.url:
            print("SUCCESS - on article page!")
            html = await page.content()
            print(f"HTML length: {len(html)}")
            if 'window._SSR_DATA' in html:
                print("Found _SSR_DATA in HTML")
            else:
                print("No _SSR_DATA found!")
        else:
            print("NOT on article page")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_click())
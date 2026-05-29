#!/usr/bin/env python3
"""Debug - check all cards and their types"""

import asyncio
from playwright.async_api import async_playwright

async def debug_collect():
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

        # Check all cards
        articles_info = await page.evaluate('''
            () => {
                const cards = document.querySelectorAll('.fx-feed-card-wrapper');
                const results = [];
                for (let i = 0; i < Math.min(cards.length, 10); i++) {
                    const card = cards[i];
                    const isVideo = card.querySelector('.is_video_class') !== null;
                    const groupId = card.getAttribute('data-group-id');
                    const titleEl = card.querySelector('.title');
                    const title = titleEl ? titleEl.innerText : 'N/A';
                    results.push({
                        index: i,
                        isVideo,
                        groupId,
                        title: title.substring(0, 30)
                    });
                }
                return results;
            }
        ''')

        print(f"Found {len(articles_info)} cards:")
        for a in articles_info:
            print(f"  {a['index']}: video={a['isVideo']}, id={a['groupId']}, title={a['title']}...")

        # Try finding non-video
        non_video = await page.evaluate('''
            () => {
                const cards = document.querySelectorAll('.fx-feed-card-wrapper');
                for (const card of cards) {
                    const isVideo = card.querySelector('.is_video_class') !== null;
                    if (!isVideo) {
                        return card.getAttribute('data-group-id');
                    }
                }
                return null;
            }
        ''')

        print(f"\nFirst non-video card group_id: {non_video}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_collect())
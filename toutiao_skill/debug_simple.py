#!/usr/bin/env python3
"""简单测试点击和导航"""

import asyncio
from playwright.async_api import async_playwright

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        await page.goto("https://open.toutiao.com/", wait_until="domcontentloaded")
        await asyncio.sleep(3)

        # 点击科技
        tabs = await page.query_selector_all('.fx-tab-cell')
        for tab in tabs:
            if '科技' in await tab.inner_text():
                await tab.click()
                break
        await asyncio.sleep(3)

        # 找第一个非视频文章的标题
        result = await page.evaluate('''
            () => {
                const cards = document.querySelectorAll('.fx-feed-card-wrapper');
                for (const card of cards) {
                    const isVideo = card.querySelector('.is_video_class');
                    if (!isVideo) {
                        const title = card.querySelector('.title');
                        const gid = card.getAttribute('data-group-id');
                        return {
                            groupId: gid,
                            title: title ? title.innerText : null
                        };
                    }
                }
                return null;
            }
        ''')

        if not result:
            print("No non-video articles found!")
            await browser.close()
            return

        print(f"Found article: {result['title'][:30]}...")
        print(f"Group ID: {result['groupId']}")

        # 尝试点击
        print("\nClicking title via JS...")
        await page.evaluate(f'''
            () => {{
                const title = document.querySelector('.fx-feed-card-wrapper[data-group-id="{result['groupId']}"] .title');
                if (title) {{
                    console.log('Found title, clicking...');
                    title.click();
                }} else {{
                    console.log('Title not found!');
                }}
            }}
        ''')

        print(f"URL after click: {page.url}")
        await asyncio.sleep(5)
        print(f"URL after wait: {page.url}")

        if '/a' in page.url:
            print("SUCCESS - on article page!")
        else:
            print("Still on main page")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(test())
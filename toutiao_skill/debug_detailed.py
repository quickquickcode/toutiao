#!/usr/bin/env python3
"""详细调试脚本"""

import asyncio
import json
from playwright.async_api import async_playwright

async def test():
    async with async_playwright() as p:
        print("启动浏览器...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
        )
        page = await context.new_page()

        print("访问今日头条...")
        await page.goto("https://open.toutiao.com/", wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(3)

        print("点击科技Tab...")
        tabs = await page.query_selector_all('.fx-tab-cell')
        for tab in tabs:
            text = await tab.inner_text()
            if '科技' in text:
                await tab.click()
                print(f"  已点击: {text}")
                break
        await asyncio.sleep(3)

        print("\n获取文章列表...")
        articles_data = await page.evaluate('''
            () => {
                const cards = document.querySelectorAll('.fx-feed-card-wrapper');
                const results = [];
                let videoCount = 0;
                let textCount = 0;
                for (const card of cards) {
                    const isVideo = card.querySelector('.is_video_class') !== null;
                    const groupId = card.getAttribute('data-group-id');
                    const titleEl = card.querySelector('.title');
                    const title = titleEl ? titleEl.innerText : '';
                    if (isVideo) {
                        videoCount++;
                    } else {
                        textCount++;
                        if (results.length < 3) {
                            results.push({ groupId, title: title.substring(0, 30), isVideo });
                        }
                    }
                }
                return { total: cards.length, videoCount, textCount, samples: results };
            }
        ''')

        print(f"  总卡片: {articles_data['total']}")
        print(f"  视频: {articles_data['videoCount']}")
        print(f"  图文: {articles_data['textCount']}")
        print(f"  样本: {articles_data['samples']}")

        if articles_data['textCount'] == 0:
            print("没有找到图文文章!")
            await browser.close()
            return

        # 获取第一个图文文章的 gid
        first_gid = await page.evaluate('''
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

        print(f"\n第一个图文文章 gid: {first_gid}")

        # 点击标题
        print("点击标题...")
        click_result = await page.evaluate(f'''
            () => {{
                const title = document.querySelector('.fx-feed-card-wrapper[data-group-id="{first_gid}"] .title');
                if (title) {{
                    title.click();
                    return 'clicked';
                }}
                return 'not_found';
            }}
        ''')
        print(f"  点击结果: {click_result}")

        await asyncio.sleep(4)

        url = page.url
        print(f"  当前URL: {url[:60]}...")

        if '/a' in url:
            print("  成功进入文章页!")

            # 提取内容
            html = await page.content()
            print(f"  HTML长度: {len(html)}")

            if 'window._SSR_DATA' in html:
                print("  找到 _SSR_DATA!")
            else:
                print("  没有 _SSR_DATA")

        await browser.close()
        print("\n完成")

if __name__ == "__main__":
    asyncio.run(test())
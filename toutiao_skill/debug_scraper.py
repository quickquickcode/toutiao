#!/usr/bin/env python3
"""调试 open.toutiao.com - 滚动触发懒加载"""

import asyncio
from playwright.async_api import async_playwright

async def debug():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        print("访问 open.toutiao.com...")
        await page.goto("https://open.toutiao.com/", wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(3)

        # 点击科技tab
        print("\n点击科技tab...")
        tabs = await page.query_selector_all(".fx-tab-cell")
        for tab in tabs:
            text = await tab.inner_text()
            if "科技" in text:
                await tab.click()
                print("已点击科技")
                break

        await asyncio.sleep(3)

        # 滚动页面
        print("\n滚动页面触发懒加载...")
        for i in range(10):
            await page.evaluate("window.scrollBy(0, 1000)")
            await asyncio.sleep(0.5)

        await asyncio.sleep(2)

        # 检查 news_tech
        print("\n检查 news_tech...")
        tech = await page.query_selector(".news_tech")
        if tech:
            print("找到 news_tech!")
            cards = await tech.query_selector_all(".fx-feed-card-wrapper")
            print(f"找到 {len(cards)} 个卡片")
        else:
            print("未找到 news_tech，尝试其他选择器...")

        # 尝试其他选择器
        for selector in [".news_tech", "[class*='tech']", ".feed-list"]:
            elems = await page.query_selector_all(selector)
            if elems:
                print(f"  {selector}: {len(elems)} 个")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug())

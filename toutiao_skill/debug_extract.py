#!/usr/bin/env python3
"""Debug - click title and extract content"""

import asyncio
import re
import json
from playwright.async_api import async_playwright

def extract_article(html):
    """From HTML extract article content"""
    if not html:
        return None

    ssr_data = None
    patterns = [
        r'window\._SSR_DATA\s*=\s*({.*?})\s*</script>',
        r'"_SSR_DATA"\s*:\s*({.*?})\s*</script>',
        r'<script[^>]*id="__MODERN_SERVER_DATA__"[^>]*>({.*?})</script>',
    ]

    for pattern in patterns:
        match = re.search(pattern, html, re.DOTALL)
        if match:
            try:
                ssr_data = json.loads(match.group(1))
                break
            except json.JSONDecodeError:
                continue

    if ssr_data:
        loaders = ssr_data.get('data', {}).get('loadersData', {})
        for key, loader in loaders.items():
            article_data = loader.get('data', {}).get('articleData', {})
            if article_data and article_data.get('title'):
                title = article_data.get('title', '')
                content_html = article_data.get('content', '')
                return {
                    'title': title,
                    'content': content_html[:200],  # First 200 chars
                }

    return None

async def debug_extract():
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

        # Find first non-video article
        articles_info = await page.evaluate('''
            () => {
                const cards = document.querySelectorAll('.fx-feed-card-wrapper');
                for (const card of cards) {
                    const isVideo = card.querySelector('.is_video_class') !== null;
                    const groupId = card.getAttribute('data-group-id');
                    const titleEl = card.querySelector('.title');
                    const title = titleEl ? titleEl.innerText : '';
                    if (!isVideo && groupId) {
                        return { groupId, title };
                    }
                }
                return null;
            }
        ''')

        if not articles_info:
            print("No text articles found!")
            await browser.close()
            return

        print(f"Article: {articles_info['title'][:40]}...")

        # Click on title
        selector = f'.fx-feed-card-wrapper[data-group-id="{articles_info["groupId"]}"] .title'
        await page.click(selector)
        await asyncio.sleep(4)

        print(f"URL: {page.url}")

        if '/a' in page.url:
            print("SUCCESS - on article page!")

            html = await page.content()
            result = extract_article(html)

            if result:
                print(f"\nExtracted:")
                print(f"  Title: {result['title'][:50]}...")
                print(f"  Content: {result['content'][:100]}...")
            else:
                print("Extraction failed - no _SSR_DATA found")
                # Check what we have
                if 'article' in html.lower():
                    print("  'article' found in HTML")
                if '_SSR' in html:
                    print("  '_SSR' found in HTML")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_extract())
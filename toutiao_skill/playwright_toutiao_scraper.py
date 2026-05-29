#!/usr/bin/env python3
"""
今日头条科技文章爬虫 - Playwright版
直接点击文章，等待加载，提取内容，然后重新加载页面
"""

import asyncio
import re
import sys
import json
from typing import List, Dict, Optional
from playwright.async_api import async_playwright

TARGET_COUNT = 3000
OUTPUT_FILE = "toutiao_tech_articles.json"

# 解析参数
arg_idx = 1
while arg_idx < len(sys.argv):
    if sys.argv[arg_idx].isdigit():
        TARGET_COUNT = int(sys.argv[arg_idx])
        print(f"[设置] 目标: {TARGET_COUNT} 篇")
    arg_idx += 1


def extract_article(html: str) -> Optional[Dict]:
    """从HTML提取文章内容"""
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
                content = clean_html_content(content_html)
                return {
                    'title': title,
                    'content': content,
                    'source': article_data.get('source', ''),
                    'publish_time': article_data.get('publishTime', ''),
                }

    return None


def clean_html_content(html: str) -> str:
    """清理HTML内容"""
    if not html:
        return ''

    html = re.sub(r'<img[^>]*src="[^"]*"[^>]*>', '', html)
    html = re.sub(r'<img[^>]*>', '', html)
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
    html = html.replace('&nbsp;', ' ').replace('&lt;', '<').replace('&gt;', '>')
    html = html.replace('&amp;', '&').replace('&quot;', '"').replace('&#39;', "'")
    html = html.replace('\\n', '\n').replace('\\"', '"').replace('\\/', '/')
    html = re.sub(r'<[^>]+>', '\n', html)
    html = re.sub(r'\n\s*\n', '\n', html)
    html = re.sub(r'[ \t]+', ' ', html)
    html = re.sub(r'\n+', '\n', html)

    return html.strip()


async def main():
    print("=" * 60)
    print("  今日头条科技文章爬虫 - Playwright版")
    print("=" * 60)

    async with async_playwright() as p:
        print("\n[0/3] 启动浏览器...")
        browser = await p.chromium.launch(headless=True)

        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )

        page = await context.new_page()

        print("\n[0/3] 访问今日头条...")
        await page.goto("https://open.toutiao.com/", wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(3)

        print("[0/3] 点击科技Tab...")
        tabs = await page.query_selector_all('.fx-tab-cell')
        for tab in tabs:
            text = await tab.inner_text()
            if '科技' in text:
                await tab.click()
                print(f"  已点击: {text}")
                break
        await asyncio.sleep(3)

        # 滚动到顶部
        container = await page.query_selector('.fx-pull-refresh.feedback-feed-list-wrapper')
        if container:
            await container.evaluate('el => el.scrollTo(0, 0)')
        await asyncio.sleep(1)

        # 爬取文章内容
        print(f"\n[1/3] 爬取文章内容...")
        results = []
        seen_ids = set()
        failed = 0
        scroll_count = 0
        max_scrolls = 100

        while scroll_count < max_scrolls and len(results) < TARGET_COUNT:
            scroll_count += 1

            # 获取当前可见的非视频文章
            articles_data = await page.evaluate('''
                () => {
                    const cards = document.querySelectorAll('.fx-feed-card-wrapper');
                    const results = [];
                    for (const card of cards) {
                        const isVideo = card.querySelector('.is_video_class') !== null;
                        if (isVideo) continue;

                        const groupId = card.getAttribute('data-group-id');
                        if (!groupId) continue;

                        const titleEl = card.querySelector('.title');
                        const title = titleEl ? titleEl.innerText : '';
                        const spans = card.querySelectorAll('.info-panel span');
                        let source = '', readCount = '';
                        for (const span of spans) {
                            const text = span.innerText;
                            if (text.includes('阅读') || text.includes('播放')) readCount = text;
                            else if (text && !source) source = text;
                        }
                        const timeEl = card.querySelector('.info-panel__publish-time');
                        const publishTime = timeEl ? timeEl.innerText : '';

                        results.push({ groupId, title, source, readCount, publishTime });
                    }
                    return results;
                }
            ''')

            # 处理当前可见的文章
            for article in articles_data:
                gid = article['groupId']
                if gid in seen_ids:
                    continue
                seen_ids.add(gid)

                print(f"\r  滚动{scroll_count} | 进度: {len(results)}/{TARGET_COUNT} (失败{failed})", end='')

                # 点击标题 (用JS避免viewport问题)
                click_js = f'''
                    () => {{
                        const title = document.querySelector('.fx-feed-card-wrapper[data-group-id="{gid}"] .title');
                        if (title) {{
                            title.click();
                            return true;
                        }}
                        return false;
                    }}
                '''
                try:
                    await page.evaluate(click_js)
                except:
                    failed += 1
                    continue

                # 等待文章页加载
                await asyncio.sleep(4)

                url = page.url
                if '/a' in url:
                    html = await page.content()
                    result = extract_article(html)

                    if result:
                        result['url'] = url
                        result['read_count'] = article['readCount']
                        result['publish_time'] = article['publishTime']
                        result['category'] = '科技'
                        results.append(result)
                        print(f"\r  ✓ {article['title'][:30]}...")
                    else:
                        failed += 1
                else:
                    failed += 1

                # 重新加载页面恢复状态
                await page.goto("https://open.toutiao.com/", wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(2)

                # 点击科技Tab
                tabs = await page.query_selector_all('.fx-tab-cell')
                for tab in tabs:
                    text = await tab.inner_text()
                    if '科技' in text:
                        await tab.click()
                        await asyncio.sleep(2)
                        break

                # 保存进度
                if len(results) % 10 == 0:
                    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                        json.dump(results, f, ensure_ascii=False, indent=2)

            # 滚动加载更多
            if len(results) < TARGET_COUNT:
                container = await page.query_selector('.fx-pull-refresh.feedback-feed-list-wrapper')
                if container:
                    await container.evaluate('el => el.scrollBy(0, 800)')
                else:
                    await page.evaluate('window.scrollBy(0, 800)')
            await asyncio.sleep(1.5)

        # 保存最终结果
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"\n\n完成! 共获取 {len(results)} 篇文章")
        print(f"保存至: {OUTPUT_FILE}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())

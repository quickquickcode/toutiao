#!/usr/bin/env python3
"""
今日头条科技文章爬虫
保留完整的正则匹配逻辑
"""

import asyncio
import re
import sys
import time
import httpx
import json
from typing import List, Dict, Optional

TARGET_COUNT = 3000
OUTPUT_FILE = "toutiao_tech_articles.json"

# 解析参数
arg_idx = 1
while arg_idx < len(sys.argv):
    if sys.argv[arg_idx].isdigit():
        TARGET_COUNT = int(sys.argv[arg_idx])
        print(f"[设置] 目标: {TARGET_COUNT} 篇")
    arg_idx += 1


async def fetch_article_list() -> List[Dict]:
    """从API获取文章列表"""
    article_list = []
    seen_urls = set()

    print("[1/2] 获取文章列表...")

    for i in range(50):
        timestamp = str(int(time.time()))
        url = f"https://open.toutiao.com/content/stream?category=news_tech&partner=toutiao&allow_stick=0&first_refresh=0&allow_force_insert=0&access_token=wap&timestamp={timestamp}&from=h5"

        try:
            resp = httpx.get(url, timeout=30)
            data = resp.json()
            articles = data.get('data', []) or []

            for article in articles:
                has_video = article.get('has_video', False)
                read_count = article.get('article_read_count') or article.get('video_watch_count') or 0
                article_url = article.get('article_url', '')
                group_id = article.get('group_id', '')

                # 筛选: 非视频类 + 阅读>5万
                if not has_video and read_count > 50000:
                    if group_id and group_id not in seen_urls:
                        seen_urls.add(group_id)
                        article_list.append({
                            'url': article_url,
                            'title': article.get('title', ''),
                            'read_count': read_count,
                            'comment_count': article.get('comment_count', 0),
                        })

            print(f"\r  第{i+1}次请求: 符合条件 {len(article_list)} 篇", end='')

            if len(article_list) >= TARGET_COUNT:
                break

            await asyncio.sleep(0.3)

        except Exception as e:
            print(f"\n  请求失败: {e}")

    print(f"\n  共获取 {len(article_list)} 篇文章")
    return article_list[:TARGET_COUNT]


def extract_article(html: str) -> Optional[Dict]:
    """从HTML提取文章内容 - 完整正则匹配"""
    if not html:
        return None

    # 方法1: 提取 window._SSR_DATA
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
        # 遍历loadersData提取articleData
        loaders = ssr_data.get('data', {}).get('loadersData', {})
        for key, loader in loaders.items():
            article_data = loader.get('data', {}).get('articleData', {})
            if article_data.get('title'):
                return parse_article_data(article_data)

    # 方法2: 直接从HTML提取
    return extract_from_html(html)


def parse_article_data(data: Dict) -> Dict:
    """解析articleData"""
    title = data.get('title', '')
    content_html = data.get('content', '')

    # 清理HTML内容
    content = clean_html_content(content_html)

    return {
        'title': title,
        'content': content,
        'source': data.get('source', ''),
        'publish_time': data.get('publishTime', ''),
        'content_cnt': data.get('contentCnt', 0),
    }


def extract_from_html(html: str) -> Optional[Dict]:
    """直接从HTML提取文章"""
    result = {}

    # 提取标题
    title_patterns = [
        r'<h1[^>]*class="[^"]*article_title[^"]*"[^>]*>([^<]+)</h1>',
        r'<h1[^>]*class="[^"]*pgc-h-forward-slash[^"]*"[^>]*>([^<]+)</h1>',
        r'<title[^>]*>([^<]+)</title>',
        r'"title"\s*:\s*"([^"]+)"',
    ]
    for pattern in title_patterns:
        match = re.search(pattern, html)
        if match:
            result['title'] = match.group(1).strip()
            break

    # 提取作者/来源
    source_patterns = [
        r'<span[^>]*class="[^"]*author_bar[^"]*"[^>]*>.*?<span[^>]*>([^<]+)</span>',
        r'"source"\s*:\s*"([^"]+)"',
        r'"screenName"\s*:\s*"([^"]+)"',
    ]
    for pattern in source_patterns:
        match = re.search(pattern, html, re.DOTALL)
        if match:
            result['source'] = match.group(1).strip()
            break

    # 提取发布时间
    time_patterns = [
        r'"publishTime"\s*:\s*(\d+)',
        r'<span[^>]*class="[^"]*publish_time[^"]*"[^>]*>([^<]+)</span>',
        r'(\d{4}[-/]\d{2}[-/]\d{2})',
    ]
    for pattern in time_patterns:
        match = re.search(pattern, html)
        if match:
            result['publish_time'] = match.group(1).strip()
            break

    # 提取文章内容
    content_patterns = [
        r'<article[^>]*class="[^"]*syl-article[^"]*"[^>]*>(.*?)</article>',
        r'<div[^>]*class="[^"]*article-content[^"]*"[^>]*>(.*?)</div>',
        r'<div[^>]*class="[^"]*fx-detail-content[^"]*"[^>]*>(.*?)</div>',
        r'"content"\s*:\s*"((?:[^"\\]|\\.)*)"',
    ]
    for pattern in content_patterns:
        match = re.search(pattern, html, re.DOTALL)
        if match:
            content_html = match.group(1)
            result['content'] = clean_html_content(content_html)
            if result['content'] and len(result['content']) > 100:
                break

    if not result.get('title'):
        return None

    return result


def clean_html_content(html: str) -> str:
    """清理HTML内容 - 完整正则"""
    if not html:
        return ''

    # 移除img标签和src
    html = re.sub(r'<img[^>]*src="[^"]*"[^>]*>', '', html)
    html = re.sub(r'<img[^>]*>', '', html)

    # 移除script标签
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)

    # 移除style标签
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)

    # 移除注释
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)

    # 处理特殊HTML实体
    html = html.replace('&nbsp;', ' ')
    html = html.replace('&lt;', '<')
    html = html.replace('&gt;', '>')
    html = html.replace('&amp;', '&')
    html = html.replace('&quot;', '"')
    html = html.replace('&#39;', "'")
    html = html.replace('\\n', '\n')
    html = html.replace('\\"', '"')
    html = html.replace('\\/', '/')

    # 移除所有HTML标签
    html = re.sub(r'<[^>]+>', '\n', html)

    # 规范化换行
    html = re.sub(r'\n\s*\n', '\n', html)
    html = re.sub(r'[ \t]+', ' ', html)
    html = re.sub(r'\n+', '\n', html)

    # 移除首尾空白
    html = html.strip()

    return html


async def fetch_article_html(url: str) -> str:
    """获取单个页面HTML"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
    }
    resp = httpx.get(url, headers=headers, timeout=30)
    return resp.text


async def crawl_articles(article_list: List[Dict]) -> List[Dict]:
    """爬取所有文章"""
    print(f"\n[2/2] 爬取文章内容...")

    results = []

    for i, item in enumerate(article_list):
        print(f"\r  进度: {i+1}/{len(article_list)}", end='')

        try:
            html = await fetch_article_html(item['url'])
            article = extract_article(html)

            if article:
                article['url'] = item['url']
                article['read_count'] = item['read_count']
                article['comment_count'] = item['comment_count']
                article['category'] = '科技'
                results.append(article)
                print(f" ✓ {article.get('title', '')[:30]}...")
            else:
                print(f" ✗ 解析失败")

        except Exception as e:
            print(f" ✗ {e}")

        if len(results) % 20 == 0:
            save_json(results)

        await asyncio.sleep(0.3)

    return results


def save_json(data: List[Dict]):
    """保存为JSON"""
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


async def main():
    print("=" * 50)
    print("  今日头条科技文章爬虫")
    print("=" * 50)

    # 获取文章列表
    article_list = await fetch_article_list()
    if not article_list:
        print("  获取失败，退出")
        return

    # 爬取文章
    results = await crawl_articles(article_list)

    # 保存
    save_json(results)

    print(f"\n\n完成! 共获取 {len(results)} 篇文章")
    print(f"保存至: {OUTPUT_FILE}")


if __name__ == "__main__":
    asyncio.run(main())

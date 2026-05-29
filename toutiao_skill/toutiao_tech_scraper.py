#!/usr/bin/env python3
"""
今日头条科技文章爬虫 - 简洁版
用法:
  python toutiao_tech_scraper.py 100
"""

import asyncio
import re
import sys
import time
import httpx
import json
from typing import List, Dict

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
    max_behot_time = None

    print("[1/2] 获取文章列表...")

    for i in range(50):
        if max_behot_time:
            url = f"https://open.toutiao.com/content/stream?category=news_tech&partner=toutiao&allow_stick=0&first_refresh=0&allow_force_insert=0&access_token=wap&timestamp={int(time.time())}&from=h5&max_behot_time={max_behot_time}"
        else:
            url = f"https://open.toutiao.com/content/stream?category=news_tech&partner=toutiao&allow_stick=0&first_refresh=0&allow_force_insert=0&access_token=wap&timestamp={int(time.time())}&from=h5"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Referer': 'https://open.toutiao.com/',
        }

        try:
            print(f"  URL: {url}")
            resp = httpx.get(url, headers=headers, timeout=30)
            data = resp.json()
            articles = data.get('data', []) or []

            print(f"  第{i+1}次请求: 返回 {len(articles)} 篇")
            for article in articles:
                has_video = article.get('has_video', False)
                read_count = article.get('article_read_count') or article.get('video_watch_count') or 0
                article_url = article.get('article_url', '')
                group_id = article.get('group_id', '')
                title = article.get('title', '')[:30]
                is_video_str = "视频" if has_video else "图文"

                print(f"    [{is_video_str}] {title}... 阅读:{read_count}")

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

            print(f"  -> 累计符合条件 {len(article_list)} 篇")

            # 获取下一页的behot_time
            if articles:
                max_behot_time = articles[-1].get('behot_time')

            if len(article_list) >= TARGET_COUNT:
                break

            await asyncio.sleep(0.3)

        except Exception as e:
            print(f"\n  请求失败: {e}")

    print(f"\n  共获取 {len(article_list)} 篇文章")
    return article_list[:TARGET_COUNT]


def extract_article(html: str) -> Dict:
    """从HTML提取文章内容"""
    # 提取 window._SSR_DATA
    match = re.search(r'window\._SSR_DATA\s*=\s*({.*?})\s*</script>', html, re.DOTALL)
    if not match:
        return {}

    try:
        ssr_data = json.loads(match.group(1))
    except:
        return {}

    # 提取文章数据
    loaders = ssr_data.get('data', {}).get('loadersData', {})
    for loader in loaders.values():
        article = loader.get('data', {}).get('articleData', {})
        if article.get('title'):
            return {
                'title': article.get('title', ''),
                'content': clean_content(article.get('content', '')),
                'source': article.get('source', ''),
                'publish_time': article.get('publishTime', ''),
            }
    return {}


def clean_content(html: str) -> str:
    """清理HTML标签"""
    if not html:
        return ''
    # 移除img
    html = re.sub(r'<img[^>]*>', '', html)
    # 移除script/style
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
    # 转标签为换行
    html = re.sub(r'<[^>]+>', '\n', html)
    # 清理空白
    html = re.sub(r'\n\s*\n', '\n', html)
    html = re.sub(r' +', ' ', html)
    return html.strip()


async def fetch_article(client: httpx.AsyncClient, url: str) -> str:
    """获取单个页面HTML"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml',
    }
    resp = await client.get(url, headers=headers, timeout=30)
    return resp.text


async def crawl_articles(article_list: List[Dict]) -> List[Dict]:
    """爬取所有文章"""
    print(f"\n[2/2] 爬取文章内容...")

    results = []
    client = httpx.AsyncClient(timeout=30.0)

    for i, item in enumerate(article_list):
        print(f"\r  进度: {i+1}/{len(article_list)}", end='')

        try:
            html = await fetch_article(client, item['url'])
            article = extract_article(html)

            if article:
                article['url'] = item['url']
                article['read_count'] = item['read_count']
                article['comment_count'] = item['comment_count']
                article['category'] = '科技'
                results.append(article)
                print(f" ✓ {article['title'][:30]}...")
            else:
                print(f" ✗ 解析失败")

        except Exception as e:
            print(f" ✗ {e}")

        if len(results) % 20 == 0:
            save_json(results)

        await asyncio.sleep(0.3)

    await client.aclose()
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

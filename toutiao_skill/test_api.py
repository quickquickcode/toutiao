#!/usr/bin/env python3
"""测试今日头条API分页"""

import requests
import json

def test_api():
    base_url = "https://open.toutiao.com/content/stream"

    params = {
        "category": "news_tech",
        "partner": "toutiao",
        "allow_stick": "0",
        "first_refresh": "0",
        "allow_force_insert": "0",
        "access_token": "wap",
        "timestamp": "1776256919",
        "from": "h5"
    }

    # 第一次请求
    print("=== 第一次请求 ===")
    resp = requests.get(base_url, params=params, timeout=30)
    data = resp.json()
    print(f"返回数量: {len(data.get('data', []))}")
    print(f"返回字段: {list(data.keys())}")

    if 'max_behot_time' in data:
        print(f"max_behot_time: {data['max_behot_time']}")
    if 'next' in data:
        print(f"next: {data['next']}")
    if 'total_count' in data:
        print(f"total_count: {data['total_count']}")

    # 用第一次的timestamp继续请求
    print("\n=== 第二次请求(用更早timestamp) ===")
    params["timestamp"] = "1776250000"
    resp = requests.get(base_url, params=params, timeout=30)
    data = resp.json()
    print(f"返回数量: {len(data.get('data', []))}")

    # 打印第一篇文章的关键信息
    articles = data.get('data', [])
    if articles:
        a = articles[0]
        print(f"\n示例文章:")
        print(f"  title: {a.get('title', '')[:50]}")
        print(f"  article_url: {a.get('article_url', '')}")
        print(f"  comment_count: {a.get('comment_count', 0)}")
        print(f"  article_read_count: {a.get('article_read_count', 0)}")

if __name__ == "__main__":
    test_api()

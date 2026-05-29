#!/usr/bin/env python3
"""
今日头条MCP服务器使用示例
"""

import asyncio
import json
from pathlib import Path

from toutiao_mcp_server.server import (
    login_with_credentials,
    check_login_status,
    publish_article,
    publish_micro_post,
    get_article_list,
    get_account_overview,
    generate_report
)

async def demo_authentication():
    """演示认证功能"""
    print("\n=== 认证功能演示 ===")
    
    # 检查当前登录状态
    status = check_login_status()
    print(f"当前登录状态: {status}")
    
    # 如果未登录，提示用户登录
    if not status.get('is_logged_in', False):
        print("请手动登录后再试，或使用 login_with_credentials 函数")
        return False
    
    return True

async def demo_content_publishing():
    """演示内容发布功能"""
    print("\n=== 内容发布功能演示 ===")
    
    # 发布微头条示例
    micro_result = publish_micro_post(
        content="这是一条测试微头条 #科技#",
        topic="科技",
        # images=["path/to/image1.jpg", "path/to/image2.jpg"]  # 可选图片
    )
    print(f"微头条发布结果: {micro_result}")
    
    # 发布图文文章示例
    article_result = publish_article(
        title="今日头条MCP服务器使用指南",
        content="""
        # 今日头条MCP服务器使用指南
        
        这是一个功能强大的今日头条内容管理工具，支持：
        
        ## 主要功能
        1. 自动登录认证
        2. 图文文章发布
        3. 微头条发布
        4. 数据统计分析
        5. 内容管理
        
        ## 使用方法
        通过MCP协议调用各种工具函数即可实现自动化内容管理。
        
        更多详情请参考项目文档。
        """,
        tags=["科技", "工具", "自动化"],
        category="科技",
        original=True
        # cover_image="path/to/cover.jpg",  # 可选封面图
        # publish_time="2024-01-15 10:00:00"  # 可选定时发布
    )
    print(f"文章发布结果: {article_result}")

async def demo_content_management():
    """演示内容管理功能"""
    print("\n=== 内容管理功能演示 ===")
    
    # 获取文章列表
    articles = get_article_list(page=1, page_size=10, status='all')
    print(f"文章列表: {json.dumps(articles, indent=2, ensure_ascii=False)}")
    
    # 如果有文章，显示详细信息
    if articles.get('success') and articles.get('articles'):
        article_count = len(articles['articles'])
        total_count = articles.get('total', 0)
        print(f"共获取到 {article_count} 篇文章，总计 {total_count} 篇")

async def demo_analytics():
    """演示数据分析功能"""
    print("\n=== 数据分析功能演示 ===")
    
    # 获取账户概览
    overview = get_account_overview()
    print(f"账户概览: {json.dumps(overview, indent=2, ensure_ascii=False)}")
    
    # 生成周报
    weekly_report = generate_report(report_type='weekly')
    print(f"周报数据: {json.dumps(weekly_report, indent=2, ensure_ascii=False)}")

async def main():
    """主函数"""
    print("今日头条MCP服务器功能演示")
    print("=" * 50)
    
    # 1. 检查认证状态
    if not await demo_authentication():
        print("请先登录后再运行演示")
        return
    
    # 2. 演示内容发布（可选，避免频繁发布测试内容）
    choice = input("\n是否演示内容发布功能？(y/N): ").lower()
    if choice == 'y':
        await demo_content_publishing()
    
    # 3. 演示内容管理
    await demo_content_management()
    
    # 4. 演示数据分析
    await demo_analytics()
    
    print("\n演示完成！")

if __name__ == "__main__":
    # 运行演示
    asyncio.run(main()) 
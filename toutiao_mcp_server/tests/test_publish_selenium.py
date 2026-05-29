"""
测试今日头条内容发布功能（使用Selenium方式）
"""

import os
import sys
import logging
import time
from pathlib import Path

# 添加项目根目录到系统路径
sys.path.append(str(Path(__file__).parent.parent))

from toutiao_mcp_server.auth import TouTiaoAuth
from toutiao_mcp_server.publisher import TouTiaoPublisher

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_article_publish():
    """测试文章发布功能"""
    
    # 初始化认证
    auth = TouTiaoAuth()
    
    # 检查是否已登录
    if not auth.is_logged_in():
        print("❌ 未登录，请先运行登录脚本")
        return
    
    # 初始化发布器
    publisher = TouTiaoPublisher(auth)
    
    # 准备测试文章数据
    title = "【测试】通过Selenium发布的测试文章"
    content = """
    <h2>这是一篇使用Selenium自动发布的测试文章</h2>
    
    <p>这篇文章用于测试今日头条MCP服务器的发布功能。</p>
    
    <p>发布时间：{timestamp}</p>
    
    <p>如果您看到这篇文章，说明自动发布功能已经正常工作！</p>
    """.format(timestamp=time.strftime("%Y-%m-%d %H:%M:%S"))
    
    tags = ["技术测试", "自动化", "Selenium"]
    
    # 发布文章
    print(f"📝 开始发布测试文章：{title}")
    
    result = publisher.publish_article(
        title=title,
        content=content,
        tags=tags,
        original=True
    )
    
    # 输出结果
    if result['success']:
        print(f"✅ 文章发布成功！")
    else:
        print(f"❌ 文章发布失败")
        print(f"❗ 错误信息: {result['message']}")

def test_micro_post_publish():
    """测试微头条发布功能"""
    
    # 初始化认证
    auth = TouTiaoAuth()
    
    # 检查是否已登录
    if not auth.is_logged_in():
        print("❌ 未登录，请先运行登录脚本")
        return
    
    # 初始化发布器
    publisher = TouTiaoPublisher(auth)
    
    # 准备测试微头条数据
    content = f"""🔄 使用Selenium发布的测试微头条！

今日头条MCP服务器Selenium发布功能测试，发布时间：{time.strftime("%Y-%m-%d %H:%M:%S")}

#技术测试 #自动化 #Selenium"""
    
    # 发布微头条
    print(f"📝 开始发布测试微头条")
    
    result = publisher.publish_micro_post(
        content=content,
        topic="技术测试"
    )
    
    # 输出结果
    if result['success']:
        print(f"✅ 微头条发布成功！")
    else:
        print(f"❌ 微头条发布失败")
        print(f"❗ 错误信息: {result['message']}")

if __name__ == "__main__":
    print("==== 今日头条内容发布测试（Selenium方式）====")
    
    choice = input("请选择测试类型：\n1. 测试文章发布\n2. 测试微头条发布\n选择[1/2]: ")
    
    if choice == "1":
        test_article_publish()
    elif choice == "2":
        test_micro_post_publish()
    else:
        print("无效的选择")
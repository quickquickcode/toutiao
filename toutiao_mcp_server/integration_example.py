#!/usr/bin/env python3
"""
小红书与今日头条多平台发布集成示例
完全兼容现有的小红书自动发布工具数据格式
"""

import asyncio
import json
import os
import httpx
import lark_oapi as lark
from lark_oapi.api.bitable.v1 import ListAppTableRecordRequest
import sys
import re
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

# --- 配置部分（与小红书工具保持一致） ---
# 飞书多维表格配置
LARK_APP_ID = "cli_a8977ba659bb500d"
LARK_APP_SECRET = "JQiOACg1B6U3mXLqSEPrHgljt8Ho8rfW"
APP_TOKEN = "VnfWbazvga8JRtsLvHPc5GwyngP"
TABLE_ID = "tblgaGUqrCiL3y6n"

# 图片下载配置
BASE_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_DOWNLOAD_DIR = os.path.join(BASE_PROJECT_DIR, "downloaded_images")

# MCP 服务器配置
XIAOHONGSHU_MCP_URL = "http://localhost:8002/xhs-mcp-server"  # 小红书MCP服务器
TOUTIAO_MCP_URL = "http://localhost:8003"  # 今日头条MCP服务器

def sanitize_text(text: str) -> str:
    """
    清理文本，移除问题字符（与小红书工具完全兼容）
    """
    import re
    
    if not text:
        return text
    
    # 只移除真正有问题的字符，保留常用emoji
    problematic_chars = re.compile(
        "["
        "\uFE0F"                 # variation selector-16
        "\u200D"                 # zero width joiner
        "\u200C"                 # zero width non-joiner
        "\u200B"                 # zero width space
        "\uFEFF"                 # byte order mark
        "]+", 
        flags=re.UNICODE
    )
    
    # 移除有问题的字符
    cleaned_text = problematic_chars.sub('', text)
    
    # 清理多余的空白字符，但保留换行
    cleaned_text = re.sub(r'[ \t]+', ' ', cleaned_text)
    cleaned_text = re.sub(r'\n\s*\n', '\n\n', cleaned_text)
    cleaned_text = cleaned_text.strip()
    
    return cleaned_text

def get_bitable_records():
    """
    从飞书多维表格获取记录（与小红书工具代码一致）
    """
    client = lark.Client.builder() \
        .app_id(LARK_APP_ID) \
        .app_secret(LARK_APP_SECRET) \
        .build()
    
    req = ListAppTableRecordRequest.builder() \
        .app_token(APP_TOKEN) \
        .table_id(TABLE_ID) \
        .build()
    
    try:
        resp = client.bitable.v1.app_table_record.list(req)
        if resp.code != 0:
            print(f"获取多维表格记录失败: {resp.msg}")
            return None
        
        records_file_path = os.path.join(BASE_PROJECT_DIR, "飞书多维表格记录.json")
        
        items_to_save = []
        if resp.data and resp.data.items:
            print("\n--- 原始飞书记录 (record.fields) ---")
            for i, record in enumerate(resp.data.items):
                print(f"记录 {i+1}: {record.fields}")
            print("--- 结束原始飞书记录 ---\n")

            # 保持与小红书工具一致的字段名
            items_to_save = [
                {
                    "title": record.fields.get("小红书标题", "无标题"),
                    "content": record.fields.get("仿写小红书文案", ""),
                    "image_url": record.fields.get("配图", None)
                }
                for record in resp.data.items
            ]
        
        with open(records_file_path, "w", encoding="utf-8") as f:
            json.dump(items_to_save, f, ensure_ascii=False, indent=4)
        print(f"文件 {records_file_path} 已成功保存。")
        
        return items_to_save
    except Exception as e:
        print(f"获取多维表格记录时发生错误: {e}")
        return None

async def publish_to_xiaohongshu(title: str, content: str, image_paths: list):
    """
    发布到小红书（保持原有逻辑不变）
    """
    print(f"准备发布到小红书：")
    print(f"  标题: {title}")
    print(f"  内容: {content[:100]}...")
    print(f"  图片路径: {image_paths}")
    
    # 清理标题和内容
    sanitized_title = sanitize_text(title)
    sanitized_content = sanitize_text(content)
    
    try:
        absolute_image_paths = [os.path.abspath(p) for p in image_paths]
        
        if not sanitized_title:
            print("错误：标题不能为空，跳过此条发布。")
            return False
        if not sanitized_content:
            print("错误：内容不能为空，跳过此条发布。")
            return False
        if not absolute_image_paths:
            print("错误：至少需要一张图片，跳过此条发布。")
            return False

        async with httpx.AsyncClient(timeout=120.0) as client:
            api_url = f"{XIAOHONGSHU_MCP_URL}/create_note"
            
            request_data = {
                "title": sanitized_title,
                "content": sanitized_content,
                "images": absolute_image_paths
            }
            
            response = await client.post(
                api_url,
                json=request_data,
                headers={
                    "Content-Type": "application/json; charset=utf-8",
                    "Accept": "application/json; charset=utf-8"
                }
            )
            
            response.raise_for_status()
            
            try:
                response_data = response.json()
                if isinstance(response_data, dict) and response_data.get("success"):
                    print("✓ 小红书发布成功！")
                    return True
                else:
                    print(f"✗ 小红书发布失败: {response_data}")
                    return False
            except json.JSONDecodeError:
                response_text = response.text
                if "发布成功" in response_text or "success" in response_text.lower():
                    print(f"✓ 小红书发布成功！")
                    return True
                else:
                    print(f"✗ 小红书发布失败: {response_text}")
                    return False
                
    except Exception as e:
        print(f"✗ 小红书发布异常: {e}")
        return False

async def publish_to_toutiao(title: str, content: str, image_url: str = None):
    """
    发布到今日头条（使用新的兼容接口）
    """
    print(f"准备发布到今日头条：")
    print(f"  标题: {title}")
    print(f"  内容: {content[:100]}...")
    print(f"  图片URL: {image_url}")
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            # 使用今日头条MCP服务器的兼容接口
            api_url = f"{TOUTIAO_MCP_URL}/publish_single_xiaohongshu_record"
            
            request_data = {
                "title": title,
                "content": content,
                "image_url": image_url,
                "download_folder": IMAGE_DOWNLOAD_DIR
            }
            
            response = await client.post(
                api_url,
                json=request_data,
                headers={
                    "Content-Type": "application/json; charset=utf-8",
                    "Accept": "application/json; charset=utf-8"
                }
            )
            
            response.raise_for_status()
            
            response_data = response.json()
            if response_data.get("success"):
                print("✓ 今日头条发布成功！")
                return True
            else:
                print(f"✗ 今日头条发布失败: {response_data.get('message')}")
                return False
                
    except Exception as e:
        print(f"✗ 今日头条发布异常: {e}")
        return False

async def batch_publish_to_toutiao(records: list):
    """
    批量发布到今日头条
    """
    print(f"准备批量发布到今日头条，共 {len(records)} 条记录")
    
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            # 使用今日头条MCP服务器的批量发布接口
            api_url = f"{TOUTIAO_MCP_URL}/publish_xiaohongshu_data"
            
            request_data = {
                "records": records,
                "download_folder": IMAGE_DOWNLOAD_DIR
            }
            
            response = await client.post(
                api_url,
                json=request_data,
                headers={
                    "Content-Type": "application/json; charset=utf-8",
                    "Accept": "application/json; charset=utf-8"
                }
            )
            
            response.raise_for_status()
            
            response_data = response.json()
            if response_data.get("success"):
                summary = response_data.get("summary", {})
                print(f"✓ 今日头条批量发布完成！")
                print(f"  总计: {summary.get('total_records', 0)} 条")
                print(f"  成功: {summary.get('success_count', 0)} 条")
                print(f"  失败: {summary.get('failed_count', 0)} 条")
                print(f"  成功率: {summary.get('success_rate', 0)}%")
                return True
            else:
                print(f"✗ 今日头条批量发布失败: {response_data.get('message')}")
                return False
                
    except Exception as e:
        print(f"✗ 今日头条批量发布异常: {e}")
        return False

async def multi_platform_publish(records: list, platforms: list = ["xiaohongshu", "toutiao"]):
    """
    多平台发布函数
    
    Args:
        records: 数据记录列表
        platforms: 要发布的平台列表 ["xiaohongshu", "toutiao"]
    """
    print(f"\n开始多平台发布，目标平台: {platforms}")
    print(f"共 {len(records)} 条记录需要发布")
    
    results = {
        "xiaohongshu": {"success": 0, "failed": 0},
        "toutiao": {"success": 0, "failed": 0}
    }
    
    # 为小红书处理图片下载
    from toutiao_mcp_server.multi_platform_publisher import MultiPlatformPublisher
    from toutiao_mcp_server.auth import TouTiaoAuth
    
    # 创建临时的多平台发布器实例用于图片下载
    temp_auth = TouTiaoAuth()
    multi_publisher = MultiPlatformPublisher(temp_auth)
    
    for i, record in enumerate(records):
        print(f"\n--- 处理记录 {i+1}/{len(records)} ---")
        
        title = record.get("title", "")
        content = record.get("content", "")
        image_url = record.get("image_url", None)
        
        # 下载图片（用于小红书发布）
        local_image_paths = []
        if image_url:
            local_image_paths = multi_publisher.process_images(image_url, IMAGE_DOWNLOAD_DIR)
        
        # 小红书发布
        if "xiaohongshu" in platforms:
            if local_image_paths:  # 小红书需要本地图片
                xiaohongshu_success = await publish_to_xiaohongshu(title, content, local_image_paths)
                if xiaohongshu_success:
                    results["xiaohongshu"]["success"] += 1
                else:
                    results["xiaohongshu"]["failed"] += 1
            else:
                print("⚠ 小红书发布跳过：缺少图片")
                results["xiaohongshu"]["failed"] += 1
        
        # 今日头条发布
        if "toutiao" in platforms:
            toutiao_success = await publish_to_toutiao(title, content, image_url)
            if toutiao_success:
                results["toutiao"]["success"] += 1
            else:
                results["toutiao"]["failed"] += 1
        
        # 间隔发布，避免频率过高
        await asyncio.sleep(3)
    
    # 打印最终结果
    print(f"\n{'='*50}")
    print("多平台发布完成！")
    print(f"{'='*50}")
    
    for platform in platforms:
        if platform in results:
            success = results[platform]["success"]
            failed = results[platform]["failed"]
            total = success + failed
            rate = (success / total * 100) if total > 0 else 0
            
            print(f"{platform.upper()}:")
            print(f"  成功: {success}/{total} ({rate:.1f}%)")
            print(f"  失败: {failed}/{total}")

async def main():
    """
    主函数 - 演示多平台发布功能
    """
    print("多平台内容发布工具")
    print("支持平台：小红书 + 今日头条")
    print("=" * 50)
    
    # 1. 获取飞书数据
    print("1. 从飞书多维表格获取数据...")
    records = get_bitable_records()
    
    if not records:
        print("未能获取到有效数据，程序退出")
        return
    
    print(f"成功获取 {len(records)} 条记录")
    
    # 2. 确保下载目录存在
    os.makedirs(IMAGE_DOWNLOAD_DIR, exist_ok=True)
    
    # 3. 用户选择发布方式
    print("\n2. 选择发布方式：")
    print("1) 仅发布到小红书")
    print("2) 仅发布到今日头条")
    print("3) 发布到两个平台")
    print("4) 今日头条批量发布")
    
    choice = input("请输入选择 (1-4): ").strip()
    
    if choice == "1":
        # 仅小红书发布（原有逻辑）
        await multi_platform_publish(records, ["xiaohongshu"])
    elif choice == "2":
        # 仅今日头条发布
        await multi_platform_publish(records, ["toutiao"])
    elif choice == "3":
        # 多平台发布
        await multi_platform_publish(records, ["xiaohongshu", "toutiao"])
    elif choice == "4":
        # 今日头条批量发布
        await batch_publish_to_toutiao(records)
    else:
        print("无效选择，程序退出")
        return
    
    print("\n程序执行完毕！")

if __name__ == "__main__":
    # 确保事件循环策略在Windows上正确设置
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(main()) 
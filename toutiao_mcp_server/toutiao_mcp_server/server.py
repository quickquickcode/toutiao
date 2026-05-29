"""
今日头条MCP服务器主模块
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Sequence

from fastmcp import FastMCP, Context

from .auth import TouTiaoAuth
from .publisher import TouTiaoPublisher
from .analytics import TouTiaoAnalytics
from .multi_platform_publisher import MultiPlatformPublisher
from .config import get_cookies_file_path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建MCP应用
mcp = FastMCP("TouTiao MCP Server")

# 全局变量存储服务实例
auth_manager: Optional[TouTiaoAuth] = None
publisher: Optional[TouTiaoPublisher] = None
analytics: Optional[TouTiaoAnalytics] = None
multi_platform_publisher: Optional[MultiPlatformPublisher] = None

def initialize_services() -> bool:
    """
    初始化所有服务实例
    
    Returns:
        bool: 初始化是否成功
    """
    global auth_manager, publisher, analytics, multi_platform_publisher
    
    try:
        # 初始化认证管理器
        auth_manager = TouTiaoAuth()
        
        # 初始化发布器和分析器
        publisher = TouTiaoPublisher(auth_manager)
        analytics = TouTiaoAnalytics(auth_manager)
        
        # 初始化多平台发布器
        multi_platform_publisher = MultiPlatformPublisher(auth_manager)
        
        logger.info("服务实例初始化成功")
        return True
    except Exception as e:
        logger.error(f"服务实例初始化失败: {e}")
        return False

@mcp.tool()
def login_with_credentials(username: str, password: str) -> Dict[str, Any]:
    """
    使用用户名密码登录今日头条
    
    Args:
        username: 用户名（手机号/邮箱）
        password: 密码
        
    Returns:
        Dict: 登录结果
    """
    try:
        if not auth_manager:
            return {"success": False, "message": "服务未初始化"}
        
        success = auth_manager.login_with_selenium(username, password)
        
        if success:
            return {
                "success": True,
                "message": "登录成功",
                "login_status": auth_manager.check_login_status()
            }
        else:
            return {
                "success": False,
                "message": "登录失败，请检查用户名密码或网络连接"
            }
    except Exception as e:
        logger.error(f"登录异常: {e}")
        return {"success": False, "message": f"登录异常: {str(e)}"}

@mcp.tool()
def check_login_status() -> Dict[str, Any]:
    """
    检查当前登录状态
    
    Returns:
        Dict: 登录状态信息
    """
    try:
        if not auth_manager:
            return {"success": False, "message": "服务未初始化"}
        
        is_logged_in = auth_manager.check_login_status()
        user_info = auth_manager.get_user_info() if is_logged_in else None
        
        return {
            "success": True,
            "is_logged_in": is_logged_in,
            "user_info": user_info
        }
    except Exception as e:
        logger.error(f"检查登录状态异常: {e}")
        return {"success": False, "message": f"检查异常: {str(e)}"}

@mcp.tool()
def logout() -> Dict[str, Any]:
    """
    登出当前账户
    
    Returns:
        Dict: 登出结果
    """
    try:
        if not auth_manager:
            return {"success": False, "message": "服务未初始化"}
        
        success = auth_manager.logout()
        return {
            "success": success,
            "message": "登出成功" if success else "登出失败"
        }
    except Exception as e:
        logger.error(f"登出异常: {e}")
        return {"success": False, "message": f"登出异常: {str(e)}"}

@mcp.tool()
def publish_article(
    title: str,
    content: str,
    images: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
    category: Optional[str] = None,
    cover_image: Optional[str] = None,
    publish_time: Optional[str] = None,
    original: bool = True
) -> Dict[str, Any]:
    """
    发布图文文章到今日头条
    
    Args:
        title: 文章标题
        content: 文章内容
        images: 文章图片路径列表
        tags: 文章标签列表
        category: 文章分类
        cover_image: 封面图片路径
        publish_time: 定时发布时间（格式：YYYY-MM-DD HH:MM:SS）
        original: 是否为原创内容
        
    Returns:
        Dict: 发布结果
    """
    try:
        if not publisher:
            return {"success": False, "message": "发布服务未初始化"}
        
        if not auth_manager or not auth_manager.check_login_status():
            return {"success": False, "message": "请先登录"}
        
        result = publisher.publish_article(
            title=title,
            content=content,
            images=images,
            tags=tags,
            category=category,
            cover_image=cover_image,
            publish_time=publish_time,
            original=original
        )
        
        return result
    except Exception as e:
        logger.error(f"发布文章异常: {e}")
        return {"success": False, "message": f"发布异常: {str(e)}"}

@mcp.tool()
def publish_micro_post(
    content: str,
    images: Optional[List[str]] = None,
    topic: Optional[str] = None,
    location: Optional[str] = None,
    publish_time: Optional[str] = None
) -> Dict[str, Any]:
    """
    发布微头条
    
    Args:
        content: 微头条内容
        images: 配图路径列表（最多9张）
        topic: 话题标签
        location: 位置信息
        publish_time: 定时发布时间
        
    Returns:
        Dict: 发布结果
    """
    try:
        if not publisher:
            return {"success": False, "message": "发布服务未初始化"}
        
        if not auth_manager or not auth_manager.check_login_status():
            return {"success": False, "message": "请先登录"}
        
        result = publisher.publish_micro_post(
            content=content,
            images=images,
            topic=topic,
            location=location,
            publish_time=publish_time
        )
        
        return result
    except Exception as e:
        logger.error(f"发布微头条异常: {e}")
        return {"success": False, "message": f"发布异常: {str(e)}"}

@mcp.tool()
def get_article_list(
    page: int = 1,
    page_size: int = 20,
    status: str = 'all'
) -> Dict[str, Any]:
    """
    获取已发布文章列表
    
    Args:
        page: 页码
        page_size: 每页数量
        status: 文章状态 (all/published/draft/review)
        
    Returns:
        Dict: 文章列表数据
    """
    try:
        if not publisher:
            return {"success": False, "message": "发布服务未初始化"}
        
        if not auth_manager or not auth_manager.check_login_status():
            return {"success": False, "message": "请先登录"}
        
        result = publisher.get_article_list(
            page=page,
            page_size=page_size,
            status=status
        )
        
        return result
    except Exception as e:
        logger.error(f"获取文章列表异常: {e}")
        return {"success": False, "message": f"获取异常: {str(e)}"}

@mcp.tool()
def delete_article(article_id: str) -> Dict[str, Any]:
    """
    删除指定文章
    
    Args:
        article_id: 文章ID
        
    Returns:
        Dict: 删除结果
    """
    try:
        if not publisher:
            return {"success": False, "message": "发布服务未初始化"}
        
        if not auth_manager or not auth_manager.check_login_status():
            return {"success": False, "message": "请先登录"}
        
        result = publisher.delete_article(article_id)
        return result
    except Exception as e:
        logger.error(f"删除文章异常: {e}")
        return {"success": False, "message": f"删除异常: {str(e)}"}

@mcp.tool()
def get_account_overview() -> Dict[str, Any]:
    """
    获取账户数据概览
    
    Returns:
        Dict: 账户概览数据
    """
    try:
        if not analytics:
            return {"success": False, "message": "分析服务未初始化"}
        
        if not auth_manager or not auth_manager.check_login_status():
            return {"success": False, "message": "请先登录"}
        
        result = analytics.get_account_overview()
        return result
    except Exception as e:
        logger.error(f"获取账户概览异常: {e}")
        return {"success": False, "message": f"获取异常: {str(e)}"}

@mcp.tool()
def get_article_stats(article_id: str) -> Dict[str, Any]:
    """
    获取指定文章的统计数据
    
    Args:
        article_id: 文章ID
        
    Returns:
        Dict: 文章统计数据
    """
    try:
        if not analytics:
            return {"success": False, "message": "分析服务未初始化"}
        
        if not auth_manager or not auth_manager.check_login_status():
            return {"success": False, "message": "请先登录"}
        
        result = analytics.get_article_stats(article_id)
        return result
    except Exception as e:
        logger.error(f"获取文章统计异常: {e}")
        return {"success": False, "message": f"获取异常: {str(e)}"}

@mcp.tool()
def get_trending_analysis(days: int = 7) -> Dict[str, Any]:
    """
    获取趋势分析数据
    
    Args:
        days: 分析天数
        
    Returns:
        Dict: 趋势分析数据
    """
    try:
        if not analytics:
            return {"success": False, "message": "分析服务未初始化"}
        
        if not auth_manager or not auth_manager.check_login_status():
            return {"success": False, "message": "请先登录"}
        
        result = analytics.get_trending_analysis(days)
        return result
    except Exception as e:
        logger.error(f"获取趋势分析异常: {e}")
        return {"success": False, "message": f"获取异常: {str(e)}"}

@mcp.tool()
def get_content_performance(
    limit: int = 10,
    sort_by: str = 'read_count'
) -> Dict[str, Any]:
    """
    获取内容表现排行
    
    Args:
        limit: 获取数量
        sort_by: 排序字段 (read_count/comment_count/like_count/share_count)
        
    Returns:
        Dict: 内容表现数据
    """
    try:
        if not analytics:
            return {"success": False, "message": "分析服务未初始化"}
        
        if not auth_manager or not auth_manager.check_login_status():
            return {"success": False, "message": "请先登录"}
        
        result = analytics.get_content_performance(limit, sort_by)
        return result
    except Exception as e:
        logger.error(f"获取内容表现异常: {e}")
        return {"success": False, "message": f"获取异常: {str(e)}"}

@mcp.tool()
def generate_report(report_type: str = 'weekly') -> Dict[str, Any]:
    """
    生成数据分析报告
    
    Args:
        report_type: 报告类型 (daily/weekly/monthly)
        
    Returns:
        Dict: 生成的报告数据
    """
    try:
        if not analytics:
            return {"success": False, "message": "分析服务未初始化"}
        
        if not auth_manager or not auth_manager.check_login_status():
            return {"success": False, "message": "请先登录"}
        
        result = analytics.generate_report(report_type)
        return result
    except Exception as e:
        logger.error(f"生成报告异常: {e}")
        return {"success": False, "message": f"生成异常: {str(e)}"}

@mcp.tool()
def publish_xiaohongshu_data(
    records: List[Dict[str, Any]],
    download_folder: str = "downloaded_images"
) -> Dict[str, Any]:
    """
    发布小红书格式数据到今日头条（兼容小红书自动发布工具）
    
    Args:
        records: 小红书格式的数据记录列表
        download_folder: 图片下载目录
        
    Returns:
        Dict: 批量发布结果
    """
    try:
        if not multi_platform_publisher:
            return {"success": False, "message": "多平台发布服务未初始化"}
        
        if not auth_manager or not auth_manager.check_login_status():
            return {"success": False, "message": "请先登录今日头条"}
        
        # 异步处理记录
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            results = loop.run_until_complete(
                multi_platform_publisher.process_xiaohongshu_records(
                    records, download_folder
                )
            )
            
            # 生成摘要报告
            summary = multi_platform_publisher.generate_publish_summary(results)
            
            return {
                "success": True,
                "message": f"批量发布完成，成功 {summary['success_count']}/{summary['total_records']} 条",
                "summary": summary
            }
        finally:
            loop.close()
        
    except Exception as e:
        logger.error(f"批量发布异常: {e}")
        return {"success": False, "message": f"批量发布异常: {str(e)}"}

@mcp.tool()
def publish_single_xiaohongshu_record(
    title: str,
    content: str,
    image_url: Optional[str] = None,
    download_folder: str = "downloaded_images"
) -> Dict[str, Any]:
    """
    发布单条小红书格式数据到今日头条
    
    Args:
        title: 标题（支持小红书标题格式）
        content: 内容（支持小红书文案格式）
        image_url: 图片URL（可选）
        download_folder: 图片下载目录
        
    Returns:
        Dict: 发布结果
    """
    try:
        if not multi_platform_publisher:
            return {"success": False, "message": "多平台发布服务未初始化"}
        
        if not auth_manager or not auth_manager.check_login_status():
            return {"success": False, "message": "请先登录今日头条"}
        
        # 构造记录格式
        record = {
            "title": title,
            "content": content,
            "image_url": image_url
        }
        
        # 异步发布单条记录
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            results = loop.run_until_complete(
                multi_platform_publisher.process_xiaohongshu_records(
                    [record], download_folder
                )
            )
            
            if results and len(results) > 0:
                return results[0]["publish_result"]
            else:
                return {"success": False, "message": "发布处理失败"}
        finally:
            loop.close()
        
    except Exception as e:
        logger.error(f"发布单条记录异常: {e}")
        return {"success": False, "message": f"发布异常: {str(e)}"}

@mcp.tool()
def convert_xiaohongshu_format(
    xiaohongshu_title: str,
    xiaohongshu_content: str,
    image_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    转换小红书格式数据为今日头条格式（用于预览转换效果）
    
    Args:
        xiaohongshu_title: 小红书标题
        xiaohongshu_content: 小红书内容
        image_url: 图片URL
        
    Returns:
        Dict: 转换后的数据格式
    """
    try:
        if not multi_platform_publisher:
            return {"success": False, "message": "多平台发布服务未初始化"}
        
        # 构造小红书格式记录
        record = {
            "title": xiaohongshu_title,
            "content": xiaohongshu_content, 
            "image_url": image_url
        }
        
        # 转换格式
        converted_data = multi_platform_publisher.process_xiaohongshu_format(record)
        
        return {
            "success": True,
            "original_data": record,
            "converted_data": converted_data,
            "message": "格式转换成功"
        }
        
    except Exception as e:
        logger.error(f"格式转换异常: {e}")
        return {"success": False, "message": f"转换异常: {str(e)}"}

@mcp.tool()
def process_feishu_records(
    feishu_records: List[Dict[str, Any]], 
    download_folder: str = "downloaded_images"
) -> Dict[str, Any]:
    """
    处理飞书多维表格记录并发布到今日头条（完全兼容小红书工具的飞书数据格式）
    
    Args:
        feishu_records: 飞书多维表格记录列表（包含"小红书标题"、"仿写小红书文案"、"配图"字段）
        download_folder: 图片下载目录
        
    Returns:
        Dict: 批量处理结果
    """
    try:
        if not multi_platform_publisher:
            return {"success": False, "message": "多平台发布服务未初始化"}
        
        if not auth_manager or not auth_manager.check_login_status():
            return {"success": False, "message": "请先登录今日头条"}
        
        # 转换飞书记录格式为标准格式
        converted_records = []
        for record in feishu_records:
            converted_record = {
                "title": record.get("小红书标题", record.get("title", "无标题")),
                "content": record.get("仿写小红书文案", record.get("content", "")),
                "image_url": record.get("配图", record.get("image_url", None))
            }
            converted_records.append(converted_record)
        
        logger.info(f"转换了 {len(converted_records)} 条飞书记录")
        
        # 使用多平台发布器处理记录
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            results = loop.run_until_complete(
                multi_platform_publisher.process_xiaohongshu_records(
                    converted_records, download_folder
                )
            )
            
            # 生成摘要报告
            summary = multi_platform_publisher.generate_publish_summary(results)
            
            return {
                "success": True,
                "message": f"飞书记录批量发布完成，成功 {summary['success_count']}/{summary['total_records']} 条",
                "summary": summary,
                "converted_records_count": len(converted_records)
            }
        finally:
            loop.close()
        
    except Exception as e:
        logger.error(f"处理飞书记录异常: {e}")
        return {"success": False, "message": f"处理异常: {str(e)}"}

# 模块初始化
logger.info("正在初始化今日头条MCP服务器...")
logger.info("可用功能:")
logger.info("- 用户认证: login_with_credentials, check_login_status, logout")
logger.info("- 内容发布: publish_article, publish_micro_post")
logger.info("- 内容管理: get_article_list, delete_article")
logger.info("- 数据分析: get_account_overview, get_article_stats, get_trending_analysis")
logger.info("- 报告生成: get_content_performance, generate_report")
logger.info("- 多平台兼容: publish_xiaohongshu_data, publish_single_xiaohongshu_record")
logger.info("- 格式转换: convert_xiaohongshu_format, process_feishu_records")

# 初始化服务
initialize_services()
"""
多平台内容发布模块 - 兼容小红书自动发布工具
"""

import asyncio
import json
import logging
import os
import httpx
from typing import Dict, List, Optional, Any
from pathlib import Path

from .auth import TouTiaoAuth
from .publisher import TouTiaoPublisher
from .config import TOUTIAO_URLS

logger = logging.getLogger(__name__)

class MultiPlatformPublisher:
    """多平台内容发布管理类 - 兼容小红书数据格式"""
    
    def __init__(self, auth: TouTiaoAuth):
        """
        初始化多平台发布管理器
        
        Args:
            auth: 认证管理器实例
        """
        self.auth = auth
        self.publisher = TouTiaoPublisher(auth)
        
    def sanitize_text(self, text: str) -> str:
        """
        清理文本，移除问题字符（与小红书工具完全兼容）
        
        Args:
            text: 原始文本
            
        Returns:
            str: 清理后的文本
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
    
    def process_xiaohongshu_format(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理小红书格式的数据记录，转换为今日头条格式
        
        Args:
            record: 小红书格式的数据记录
            
        Returns:
            Dict: 转换后的今日头条格式数据
        """
        # 兼容小红书工具的字段名
        title = record.get("title", record.get("小红书标题", "无标题"))
        content = record.get("content", record.get("仿写小红书文案", ""))
        image_url = record.get("image_url", record.get("配图", None))
        
        # 清理文本内容
        sanitized_title = self.sanitize_text(title)
        sanitized_content = self.sanitize_text(content)
        
        # 转换为今日头条需要的格式
        toutiao_data = {
            "title": sanitized_title,
            "content": sanitized_content,
            "image_url": image_url,
            "original_title": title,
            "original_content": content
        }
        
        return toutiao_data
    
    def download_image_sync(self, image_url: str, download_folder: str, index: int = 0) -> Optional[str]:
        """
        同步下载图片（与小红书工具保持一致）
        
        Args:
            image_url: 图片URL
            download_folder: 下载目录
            index: 图片索引
            
        Returns:
            Optional[str]: 下载成功的本地路径，失败返回None
        """
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(image_url)
                response.raise_for_status()
                
                # 生成文件名
                try:
                    original_filename = os.path.basename(image_url.split('?')[0])
                    _, ext = os.path.splitext(original_filename)
                    if not ext:
                        ext = '.jpg'
                except Exception:
                    original_filename = f"image_{index}"
                    ext = '.jpg'
                
                # 构建安全的文件名
                safe_filename_base = "".join(c if c.isalnum() or c in ('_', '-') else '_' 
                                           for c in original_filename.replace(ext, ''))
                if not safe_filename_base:
                    safe_filename_base = f"toutiao_image_{index}"
                
                file_name = f"{safe_filename_base}{ext}"
                local_file_path = os.path.join(download_folder, file_name)
                
                # 确保下载目录存在
                os.makedirs(download_folder, exist_ok=True)
                
                with open(local_file_path, "wb") as f:
                    f.write(response.content)
                
                logger.info(f"图片已下载: {local_file_path}")
                return os.path.abspath(local_file_path)
                
        except Exception as e:
            logger.error(f"下载图片失败 {image_url}: {e}")
            return None
    
    def process_images(self, image_data_input, download_folder: str) -> List[str]:
        """
        处理图片数据（与小红书工具兼容）
        
        Args:
            image_data_input: 图片数据（可能是URL字符串或None）
            download_folder: 下载目录
            
        Returns:
            List[str]: 本地图片路径列表
        """
        if not image_data_input:
            return []
        
        # 统一处理为URL列表
        image_url_list = []
        if isinstance(image_data_input, str) and image_data_input.startswith(("http://", "https://")):
            image_url_list.append(image_data_input)
        elif isinstance(image_data_input, list):
            for item in image_data_input:
                if isinstance(item, str) and item.startswith(("http://", "https://")):
                    image_url_list.append(item)
                elif isinstance(item, dict) and 'url' in item:
                    if item['url'].startswith(("http://", "https://")):
                        image_url_list.append(item['url'])
        
        if not image_url_list:
            return []
        
        # 下载图片
        local_image_paths = []
        for i, image_url in enumerate(image_url_list):
            local_path = self.download_image_sync(image_url, download_folder, i)
            if local_path:
                local_image_paths.append(local_path)
        
        return local_image_paths
    
    async def publish_to_toutiao_compatible(self, title: str, content: str, image_paths: List[str]) -> Dict[str, Any]:
        """
        以兼容小红书工具的方式发布到今日头条
        
        Args:
            title: 标题
            content: 内容
            image_paths: 本地图片路径列表
            
        Returns:
            Dict: 发布结果
        """
        logger.info(f"准备发布到今日头条：")
        logger.info(f"  标题: {title}")
        logger.info(f"  内容: {content[:100]}...")
        logger.info(f"  图片路径: {image_paths}")
        
        try:
            # 检查登录状态
            if not self.auth.check_login_status():
                return {
                    "success": False,
                    "message": "请先登录今日头条账户"
                }
            
            # 验证必要字段
            if not title:
                return {
                    "success": False,
                    "message": "标题不能为空"
                }
            
            if not content:
                return {
                    "success": False,
                    "message": "内容不能为空"
                }
            
            # 检查内容长度，今日头条支持长文本，但微头条有限制
            is_micro_post = len(content) <= 2000 and len(image_paths) <= 9
            
            if is_micro_post:
                # 发布为微头条
                result = self.publisher.publish_micro_post(
                    content=f"{title}\n\n{content}",
                    images=image_paths
                )
            else:
                # 发布为图文文章
                result = self.publisher.publish_article(
                    title=title,
                    content=content,
                    images=image_paths,
                    original=True
                )
            
            return result
            
        except Exception as e:
            logger.error(f"发布到今日头条异常: {e}")
            return {
                "success": False,
                "message": f"发布异常: {str(e)}"
            }
    
    async def process_xiaohongshu_records(self, records: List[Dict[str, Any]], 
                                        download_folder: str) -> List[Dict[str, Any]]:
        """
        批量处理小红书格式的记录并发布到今日头条
        
        Args:
            records: 小红书格式的记录列表
            download_folder: 图片下载目录
            
        Returns:
            List[Dict]: 发布结果列表
        """
        results = []
        
        # 确保下载目录存在
        os.makedirs(download_folder, exist_ok=True)
        logger.info(f"图片下载目录: {download_folder}")
        
        for i, record in enumerate(records):
            logger.info(f"\n--- 正在处理记录 {i+1}/{len(records)} ---")
            
            try:
                # 转换数据格式
                toutiao_data = self.process_xiaohongshu_format(record)
                
                logger.info(f"原始标题: {toutiao_data['original_title']}")
                logger.info(f"清理后标题: {toutiao_data['title']}")
                logger.info(f"内容长度: {len(toutiao_data['content'])}")
                
                # 处理图片
                local_image_paths = []
                if toutiao_data['image_url']:
                    local_image_paths = self.process_images(
                        toutiao_data['image_url'], 
                        download_folder
                    )
                    
                    if local_image_paths:
                        logger.info(f"成功下载图片: {local_image_paths}")
                    else:
                        logger.warning(f"未能下载图片: {toutiao_data['image_url']}")
                
                # 发布到今日头条
                publish_result = await self.publish_to_toutiao_compatible(
                    toutiao_data['title'],
                    toutiao_data['content'], 
                    local_image_paths
                )
                
                # 记录结果
                result_item = {
                    "index": i + 1,
                    "title": toutiao_data['title'],
                    "publish_result": publish_result,
                    "image_count": len(local_image_paths)
                }
                
                results.append(result_item)
                
                if publish_result.get('success'):
                    logger.info(f"✓ 记录 {i+1} 发布成功")
                else:
                    logger.error(f"✗ 记录 {i+1} 发布失败: {publish_result.get('message')}")
                
                # 避免过于频繁的请求
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"处理记录 {i+1} 时发生异常: {e}")
                results.append({
                    "index": i + 1,
                    "title": record.get("title", "unknown"),
                    "publish_result": {
                        "success": False,
                        "message": f"处理异常: {str(e)}"
                    },
                    "image_count": 0
                })
        
        return results
    
    def generate_publish_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        生成发布摘要报告
        
        Args:
            results: 发布结果列表
            
        Returns:
            Dict: 摘要报告
        """
        total = len(results)
        success_count = sum(1 for r in results if r['publish_result'].get('success'))
        failed_count = total - success_count
        
        summary = {
            "total_records": total,
            "success_count": success_count,
            "failed_count": failed_count,
            "success_rate": round((success_count / total * 100) if total > 0 else 0, 2),
            "details": results
        }
        
        return summary 
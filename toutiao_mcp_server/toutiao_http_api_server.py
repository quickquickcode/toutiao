# -*- coding: utf-8 -*-
"""
今日头条发布HTTP API服务器
采用和小红书相同的简单实现方式
"""
import sys
import os

# 强制设置UTF-8编码
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

os.environ['PYTHONIOENCODING'] = 'utf-8'

from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
from typing import List, Optional

# 导入头条发布功能
from toutiao_mcp_server.auth import TouTiaoAuth
from toutiao_mcp_server.publisher import TouTiaoPublisher

app = FastAPI(title="今日头条发布API", version="1.0.0")

# 全局变量存储服务实例
auth_manager = None
publisher = None

def initialize_services():
    """初始化服务实例"""
    global auth_manager, publisher
    try:
        auth_manager = TouTiaoAuth()
        publisher = TouTiaoPublisher(auth_manager)
        print("头条服务实例初始化成功")
        return True
    except Exception as e:
        print(f"头条服务实例初始化失败: {e}")
        return False

class CreateArticleRequest(BaseModel):
    """创建文章请求模型"""
    title: str
    content: str
    images: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None
    cover_image: Optional[str] = None
    publish_time: Optional[str] = None
    original: bool = True

class CreateMicroPostRequest(BaseModel):
    """创建微头条请求模型"""
    content: str
    images: Optional[List[str]] = None
    topic: Optional[str] = None
    location: Optional[str] = None
    publish_time: Optional[str] = None

@app.post("/toutiao-mcp-server/create_article")
async def create_article(request: CreateArticleRequest):
    """创建今日头条文章"""
    try:
        print(f"收到文章发布请求:")
        print(f"  标题: {request.title}")
        print(f"  内容长度: {len(request.content)}")
        print(f"  图片数量: {len(request.images) if request.images else 0}")
        
        # 检查服务是否初始化
        if not publisher or not auth_manager:
            return {"status": "error", "message": "服务未初始化"}
        
        # 检查登录状态
        if not auth_manager.check_login_status():
            return {"status": "error", "message": "请先登录"}
        
        # 执行发布
        print("开始执行文章发布...")
        result = publisher.publish_article(
            title=request.title,
            content=request.content,
            images=request.images,
            tags=request.tags,
            category=request.category,
            cover_image=request.cover_image,
            publish_time=request.publish_time,
            original=request.original
        )
        
        print(f"文章发布结果: {result}")
        
        if result.get("success"):
            return {"status": "success", "message": result.get("message", "发布成功"), "data": result}
        else:
            return {"status": "error", "message": result.get("message", "发布失败"), "data": result}
        
    except Exception as e:
        import traceback
        error_msg = str(e)
        error_trace = traceback.format_exc()
        print(f"文章发布失败: {error_msg}")
        print(f"错误堆栈: {error_trace}")
        
        return {"status": "error", "message": error_msg, "trace": error_trace}

@app.post("/toutiao-mcp-server/create_micro_post")
async def create_micro_post(request: CreateMicroPostRequest):
    """创建今日头条微头条"""
    try:
        print(f"收到微头条发布请求:")
        print(f"  内容长度: {len(request.content)}")
        print(f"  图片数量: {len(request.images) if request.images else 0}")
        
        # 检查服务是否初始化
        if not publisher or not auth_manager:
            return {"status": "error", "message": "服务未初始化"}
        
        # 检查登录状态
        if not auth_manager.check_login_status():
            return {"status": "error", "message": "请先登录"}
        
        # 执行发布
        print("开始执行微头条发布...")
        result = publisher.publish_micro_post(
            content=request.content,
            images=request.images,
            topic=request.topic,
            location=request.location,
            publish_time=request.publish_time
        )
        
        print(f"微头条发布结果: {result}")
        
        if result.get("success"):
            return {"status": "success", "message": result.get("message", "发布成功"), "data": result}
        else:
            return {"status": "error", "message": result.get("message", "发布失败"), "data": result}
        
    except Exception as e:
        import traceback
        error_msg = str(e)
        error_trace = traceback.format_exc()
        print(f"微头条发布失败: {error_msg}")
        print(f"错误堆栈: {error_trace}")
        
        return {"status": "error", "message": error_msg, "trace": error_trace}

@app.get("/toutiao-mcp-server/health")
async def health_check():
    """健康检查接口"""
    try:
        # 检查服务状态
        service_status = "initialized" if (publisher and auth_manager) else "not_initialized"
        login_status = auth_manager.check_login_status() if auth_manager else False
        
        return {
            "status": "ok",
            "service_status": service_status,
            "login_status": login_status,
            "message": "头条发布服务运行正常"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"健康检查失败: {str(e)}"
        }

if __name__ == "__main__":
    print("启动今日头条发布HTTP API服务器...")
    
    # 初始化服务
    if initialize_services():
        print("服务初始化成功，启动HTTP API服务器...")
        uvicorn.run(app, host="0.0.0.0", port=8003)
    else:
        print("服务初始化失败，无法启动服务器") 
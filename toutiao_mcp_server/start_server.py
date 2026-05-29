"""
启动今日头条MCP服务器
"""

import os
import logging
import argparse
import asyncio
from pathlib import Path

from fastmcp import FastMCP
from toutiao_mcp_server.server import mcp, initialize_services

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="启动今日头条MCP服务器")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="服务器监听地址")
    parser.add_argument("--port", type=int, default=8003, help="服务器监听端口")
    parser.add_argument("--debug", action="store_true", help="启用调试模式")
    parser.add_argument("--transport", type=str, default="streamable-http", 
                       choices=["streamable-http", "http", "sse", "stdio"], 
                       help="传输协议")
    
    args = parser.parse_args()
    
    logger.info(f"正在启动今日头条MCP服务器，地址: {args.host}:{args.port}，传输方式: {args.transport}")
    
    # 初始化服务
    if not initialize_services():
        logger.error("服务初始化失败，无法启动服务器")
        return
    
    # 使用改进的启动方式，确保正确的生命周期管理
    try:
        if args.transport == "streamable-http":
            # 使用更稳定的streamable-http启动方式
            logger.info("使用streamable-http传输方式启动服务器...")
            
            # 创建HTTP应用并确保正确的生命周期配置
            http_app = mcp.http_app()
            
            # 使用uvicorn直接运行，确保正确的ASGI生命周期
            import uvicorn
            
            # 启动服务器
            uvicorn.run(
                http_app,
                host=args.host, 
                port=args.port,
                log_level="info" if not args.debug else "debug",
                access_log=True,
                lifespan="on"  # 确保生命周期管理正确
            )
            
        elif args.transport == "http":
            mcp.run(
                transport="http", 
                host=args.host, 
                port=args.port
            )
        elif args.transport == "sse":
            mcp.run(
                transport="sse", 
                host=args.host, 
                port=args.port
            )
        else:  # stdio
            mcp.run()
            
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在关闭服务器...")
    except Exception as e:
        logger.error(f"服务器启动失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
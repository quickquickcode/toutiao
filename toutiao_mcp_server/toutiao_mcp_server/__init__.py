"""
今日头条 MCP 服务器

这是一个专为今日头条内容发布和管理而设计的 MCP (Model Context Protocol) 服务器。
支持文章发布、微头条发布、内容管理等功能。

主要功能：
- 用户认证管理
- 内容发布功能  
- 内容管理
- 数据分析

作者: TouTiao MCP Developer
版本: 1.0.0
许可证: MIT
"""

from .server import mcp
from .auth import TouTiaoAuth
from .publisher import TouTiaoPublisher
from .analytics import TouTiaoAnalytics

__version__ = "1.0.0"
__author__ = "TouTiao MCP Developer"

__all__ = [
    "mcp",
    "TouTiaoAuth", 
    "TouTiaoPublisher",
    "TouTiaoAnalytics"
]
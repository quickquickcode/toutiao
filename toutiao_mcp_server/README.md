# 今日头条 MCP 服务器

一个功能完整的今日头条内容管理MCP服务器，支持自动登录、内容发布、数据分析等功能。**完全兼容小红书自动发布工具的数据格式，支持一键多平台发布。**

## ✨ 主要特性

- 🔐 **用户认证管理** - 自动登录、Cookie持久化、登录状态检查
- 📝 **内容发布功能** - 图文文章发布、微头条发布、图片上传与压缩
- 📊 **数据分析统计** - 阅读量统计、粉丝增长分析、内容表现评估
- 🗂️ **内容管理** - 获取文章列表、编辑删除内容、状态管理
- 📈 **报告生成** - 自动生成日报、周报、月报
- 🌐 **多平台兼容** - **完全兼容小红书自动发布工具，支持一键发布多个平台**
- ⚡ **现代化架构** - 基于FastMCP框架，支持HTTP Streamable模式

## 🔗 多平台兼容特性

### 与小红书自动发布工具完全兼容

本项目完全兼容您现有的小红书自动发布工具数据格式，可以实现：

1. **相同的数据源** - 支持相同的飞书多维表格格式
2. **相同的字段名** - 兼容"小红书标题"、"仿写小红书文案"、"配图"字段
3. **相同的图片处理** - 支持图片URL下载和本地存储
4. **一键多平台发布** - 可以同时发布到小红书和今日头条

### 支持的兼容接口

- `publish_xiaohongshu_data` - 批量发布小红书格式数据到今日头条
- `publish_single_xiaohongshu_record` - 发布单条小红书记录到今日头条
- `process_feishu_records` - 处理飞书多维表格记录（兼容小红书工具格式）
- `convert_xiaohongshu_format` - 预览小红书格式转换为今日头条格式

## 📦 安装指南

### 环境要求

- Python 3.8+
- Chrome 浏览器（用于Selenium自动登录）
- Windows/macOS/Linux

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd toutiao_mcp_server
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **安装Chrome WebDriver**
```bash
# WebDriver会通过webdriver-manager自动下载
# 确保系统已安装Chrome浏览器
```

4. **配置设置（可选）**
```bash
# 复制配置示例文件
cp config.example.py config_local.py
# 根据需要修改配置
```

## 🚀 快速开始

### 1. 启动服务器

```bash
# 使用默认端口8003启动
python start_server.py

# 或指定端口和日志级别
python start_server.py --port 8080 --log-level DEBUG
```

### 2. 多平台发布示例

**使用集成示例文件（推荐）：**

```bash
# 运行多平台发布示例
python integration_example.py
```

这个示例文件完全兼容您现有的小红书工具，支持：
- 从相同的飞书多维表格获取数据
- 同时发布到小红书和今日头条
- 支持批量发布和单个发布
- 提供详细的发布结果统计

**或通过MCP工具调用：**

```python
import asyncio
import httpx

async def multi_platform_publish():
    # 飞书数据格式（与小红书工具完全一致）
    records = [
        {
            "title": "科技前沿：AI发展趋势",
            "content": "人工智能正在改变我们的生活...",
            "image_url": "https://example.com/image.jpg"
        }
    ]
    
    # 发布到今日头条
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8003/publish_xiaohongshu_data",
            json={
                "records": records,
                "download_folder": "downloaded_images"
            }
        )
        result = response.json()
        print(f"发布结果: {result}")

# 运行示例
asyncio.run(multi_platform_publish())
```

### 3. 基本功能使用

**登录今日头条：**
```python
# 通过MCP工具调用
result = login_with_credentials("your_username", "your_password")
```

**发布内容：**
```python
# 发布图文文章
result = publish_article(
    title="今日头条MCP服务器使用指南",
    content="这是一个功能强大的今日头条内容管理工具...",
    images=["path/to/image1.jpg", "path/to/image2.jpg"],
    tags=["科技", "工具"]
)

# 发布微头条
result = publish_micro_post(
    content="这是一条测试微头条 #科技#",
    images=["path/to/image.jpg"]
)
```

## 🛠️ 主要功能模块

### 1. 认证管理 (`auth.py`)
- 自动登录（支持用户名密码登录）
- Cookie持久化存储
- 登录状态检查和维护
- 用户信息获取

### 2. 内容发布 (`publisher.py`)
- 图文文章发布（支持富文本、图片、标签）
- 微头条发布（支持图片、话题、位置）
- 图片自动上传和压缩
- 定时发布功能

### 3. 数据分析 (`analytics.py`)
- 账户概览数据（粉丝数、文章数、阅读量）
- 文章详细统计（阅读、评论、分享、点赞）
- 趋势分析（指定时间段的数据变化）
- 内容表现排行（按各项指标排序）

### 4. 多平台兼容 (`multi_platform_publisher.py`)
- 兼容小红书数据格式
- 智能格式转换
- 批量处理和发布
- 发布结果统计

### 5. MCP服务器 (`server.py`)
- 基于FastMCP框架
- 提供HTTP API接口
- 支持Streamable模式
- 完整的错误处理

## 🔧 配置选项

### 基本配置
```python
# 今日头条相关URL（可自定义）
TOUTIAO_URLS = {
    'login': 'https://sso.toutiao.com/login',
    'publish_article': 'https://mp.toutiao.com/core/article/add/',
    # ... 更多URL配置
}

# Selenium配置
SELENIUM_CONFIG = {
    'implicit_wait': 10,
    'explicit_wait': 30,
    'headless': False,  # 是否无头模式
    'chrome_options': [...]
}

# 内容发布配置
CONTENT_CONFIG = {
    'default_category': '科技',
    'max_images_per_article': 20,
    'auto_compress_images': True,
    # ... 更多配置
}
```

### 多平台配置
```python
# 在 integration_example.py 中配置
XIAOHONGSHU_MCP_URL = "http://localhost:8002/xhs-mcp-server"
TOUTIAO_MCP_URL = "http://localhost:8003"

# 飞书多维表格配置（与小红书工具保持一致）
LARK_APP_ID = "your_app_id"
LARK_APP_SECRET = "your_app_secret"
APP_TOKEN = "your_app_token"
TABLE_ID = "your_table_id"
```

## 📡 API 接口文档

### 用户认证接口

#### `login_with_credentials(username, password)`
使用用户名密码登录

**参数：**
- `username` (str): 用户名（手机号/邮箱）
- `password` (str): 密码

**返回：**
```json
{
    "success": true,
    "message": "登录成功",
    "login_status": true
}
```

#### `check_login_status()`
检查当前登录状态

**返回：**
```json
{
    "success": true,
    "is_logged_in": true,
    "user_info": {
        "user_id": "12345",
        "username": "example_user"
    }
}
```

### 内容发布接口

#### `publish_article(title, content, images, tags, category, ...)`
发布图文文章

**参数：**
- `title` (str): 文章标题
- `content` (str): 文章内容
- `images` (List[str], 可选): 图片路径列表
- `tags` (List[str], 可选): 标签列表
- `category` (str, 可选): 文章分类
- `cover_image` (str, 可选): 封面图片路径
- `publish_time` (str, 可选): 定时发布时间
- `original` (bool): 是否原创

#### `publish_micro_post(content, images, topic, location, ...)`
发布微头条

**参数：**
- `content` (str): 微头条内容
- `images` (List[str], 可选): 配图路径列表（最多9张）
- `topic` (str, 可选): 话题标签
- `location` (str, 可选): 位置信息
- `publish_time` (str, 可选): 定时发布时间

### 多平台兼容接口

#### `publish_xiaohongshu_data(records, download_folder)`
批量发布小红书格式数据到今日头条

**参数：**
- `records` (List[Dict]): 小红书格式的数据记录列表
- `download_folder` (str): 图片下载目录

**数据格式：**
```json
[
    {
        "title": "文章标题",
        "content": "文章内容",
        "image_url": "图片URL"
    }
]
```

**返回：**
```json
{
    "success": true,
    "message": "批量发布完成，成功 8/10 条",
    "summary": {
        "total_records": 10,
        "success_count": 8,
        "failed_count": 2,
        "success_rate": 80.0
    }
}
```

#### `publish_single_xiaohongshu_record(title, content, image_url, download_folder)`
发布单条小红书格式数据

#### `process_feishu_records(feishu_records, download_folder)`
处理飞书多维表格记录（完全兼容小红书工具格式）

**支持字段：**
- `小红书标题` → 转换为今日头条标题
- `仿写小红书文案` → 转换为今日头条内容
- `配图` → 图片URL，自动下载后用于发布

#### `convert_xiaohongshu_format(xiaohongshu_title, xiaohongshu_content, image_url)`
预览小红书格式转换效果

### 内容管理接口

#### `get_article_list(page, page_size, status)`
获取文章列表

#### `delete_article(article_id)`
删除指定文章

### 数据分析接口

#### `get_account_overview()`
获取账户概览数据

#### `get_article_stats(article_id)`
获取文章统计数据

#### `generate_report(report_type)`
生成数据报告

## 🎯 使用场景

### 1. 单平台使用
- 纯今日头条内容管理
- 自动化发布和数据分析
- 内容策略优化

### 2. 多平台使用（推荐）
- 同时管理小红书和今日头条
- 一键发布到两个平台
- 统一的数据管理和分析

### 3. 企业级应用
- 团队协作内容管理
- 批量内容发布
- 数据驱动的内容优化

## 🔄 与小红书工具的对比

| 功能 | 小红书工具 | 今日头条MCP | 多平台集成 |
|------|-----------|-------------|-----------|
| 数据源 | 飞书多维表格 | ✅ 完全兼容 | ✅ 统一数据源 |
| 字段格式 | 小红书标题/文案/配图 | ✅ 完全兼容 | ✅ 无需修改 |
| 图片处理 | URL下载 | ✅ 相同逻辑 | ✅ 共享下载 |
| 发布方式 | 单平台 | 单平台 | ✅ 多平台 |
| 错误处理 | 详细日志 | ✅ 详细日志 | ✅ 统一处理 |

## 🚨 注意事项

1. **登录要求**：首次使用需要手动登录一次，后续会自动保持登录状态
2. **图片格式**：支持 JPG、PNG、GIF、WebP 格式，自动压缩优化
3. **内容长度**：
   - 微头条：建议2000字符以内
   - 图文文章：支持长文本
4. **发布频率**：建议控制发布频率，避免被平台限制
5. **多平台兼容**：确保小红书MCP服务器和今日头条MCP服务器都已启动

## 🐛 故障排除

### 常见问题

1. **登录失败**
   - 检查用户名密码是否正确
   - 确认Chrome浏览器已安装
   - 检查网络连接

2. **图片上传失败**
   - 检查图片文件是否存在
   - 确认图片格式支持
   - 检查网络连接

3. **发布失败**
   - 确认已登录
   - 检查内容是否符合平台规范
   - 查看详细错误日志

4. **多平台发布问题**
   - 确认两个MCP服务器都已启动
   - 检查端口配置是否正确
   - 验证数据格式是否正确

### 日志查看

```bash
# 查看运行日志
tail -f toutiao_mcp.log

# 调试模式启动
python start_server.py --log-level DEBUG
```

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进项目！

### 开发环境设置

1. Fork 项目
2. 创建功能分支
3. 安装开发依赖：`pip install -r requirements.txt`
4. 运行测试：`python -m pytest tests/`
5. 提交更改并创建Pull Request

## 📄 许可证

本项目采用 MIT 许可证。详情请查看 [LICENSE](LICENSE) 文件。

## 🔗 相关链接

- [FastMCP 框架文档](https://fastmcp.readthedocs.io/)
- [今日头条创作者平台](https://mp.toutiao.com/)
- [Selenium 文档](https://selenium-python.readthedocs.io/)

## 📞 支持与反馈

如有问题或建议，请通过以下方式联系：

- 提交 GitHub Issue
- 发送邮件至项目维护者
- 查看项目Wiki获取更多帮助

---

**立即开始多平台内容发布之旅！** 🚀
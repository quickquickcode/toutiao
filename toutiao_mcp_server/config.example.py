"""
今日头条MCP服务器配置示例文件

复制此文件为 config_local.py 并根据需要修改配置
"""

# 自定义今日头条URLs（如果官方URL发生变化）
CUSTOM_TOUTIAO_URLS = {
    'login': 'https://sso.toutiao.com/login',
    'logout': 'https://sso.toutiao.com/logout',
    'profile': 'https://mp.toutiao.com/profile/v4/graphic/articles',
    'publish_article': 'https://mp.toutiao.com/core/article/add/',
    'publish_micro': 'https://mp.toutiao.com/core/toutiao/add/',
    'upload': 'https://mp.toutiao.com/upload_photo/',
    'article_list': 'https://mp.toutiao.com/core/article/list/',
    'delete_article': 'https://mp.toutiao.com/core/article/delete/',
    
    # 数据分析相关URL
    'analytics_overview': 'https://mp.toutiao.com/core/statistic/overview/',
    'article_stats': 'https://mp.toutiao.com/core/statistic/article_detail/',
    'trending_analysis': 'https://mp.toutiao.com/core/statistic/trending/',
    'content_performance': 'https://mp.toutiao.com/core/statistic/performance/',
    'audience_analysis': 'https://mp.toutiao.com/core/statistic/audience/',
}

# 自定义请求头
CUSTOM_DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Origin': 'https://mp.toutiao.com',
    'Referer': 'https://mp.toutiao.com/',
    'X-Requested-With': 'XMLHttpRequest',
}

# 自定义Selenium配置
CUSTOM_SELENIUM_CONFIG = {
    'implicit_wait': 10,  # 隐式等待时间（秒）
    'explicit_wait': 30,  # 显式等待时间（秒）
    'page_load_timeout': 60,  # 页面加载超时（秒）
    'headless': False,  # 是否无头模式
    'chrome_options': [
        '--no-sandbox',
        '--disable-dev-shm-usage',
        '--disable-blink-features=AutomationControlled',
        '--exclude-switches=enable-automation',
        '--disable-extensions',
        '--start-maximized',
        '--disable-web-security',
        '--allow-running-insecure-content',
    ]
}

# 自定义内容发布配置
CUSTOM_CONTENT_CONFIG = {
    'default_category': '科技',  # 默认文章分类
    'max_title_length': 100,    # 最大标题长度
    'max_content_length': 50000,  # 最大内容长度
    'max_images_per_article': 20,  # 每篇文章最大图片数
    'max_images_per_micro': 9,     # 每条微头条最大图片数
    'image_quality': 85,           # 图片压缩质量
    'max_image_size': 1024 * 1024,  # 最大图片大小（字节）
    'supported_image_formats': ['.jpg', '.jpeg', '.png', '.gif', '.webp'],
    'auto_compress_images': True,   # 是否自动压缩图片
}

# 自定义Cookie文件路径
def get_custom_cookies_file_path():
    """获取自定义Cookie文件路径"""
    from pathlib import Path
    return str(Path.home() / '.toutiao_mcp' / 'custom_cookies.json')

# 日志配置
CUSTOM_LOGGING_CONFIG = {
    'level': 'INFO',  # 日志级别
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file_path': 'toutiao_mcp_custom.log',  # 日志文件路径
    'max_bytes': 10 * 1024 * 1024,  # 最大日志文件大小（10MB）
    'backup_count': 5,  # 备份文件数量
}

# MCP服务器配置
CUSTOM_MCP_CONFIG = {
    'default_port': 8003,
    'host': '0.0.0.0',
    'debug': False,
    'auto_reload': False,
}

# 使用示例：
# 1. 复制此文件为 config_local.py
# 2. 修改上述配置项
# 3. 在主程序中导入：
#    try:
#        from .config_local import CUSTOM_TOUTIAO_URLS
#        TOUTIAO_URLS.update(CUSTOM_TOUTIAO_URLS)
#    except ImportError:
#        pass  # 使用默认配置 
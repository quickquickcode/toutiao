#!/usr/bin/env python3
"""
今日头条MCP服务器基本功能测试
"""

import unittest
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from toutiao_mcp_server.auth import TouTiaoAuth
from toutiao_mcp_server.publisher import TouTiaoPublisher
from toutiao_mcp_server.analytics import TouTiaoAnalytics
from toutiao_mcp_server.config import TOUTIAO_URLS, DEFAULT_HEADERS

class TestTouTiaoAuth(unittest.TestCase):
    """测试认证模块"""
    
    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.cookies_file = Path(self.temp_dir) / "test_cookies.json"
        self.auth = TouTiaoAuth(str(self.cookies_file))
    
    def test_init(self):
        """测试初始化"""
        self.assertIsNotNone(self.auth.session)
        self.assertEqual(self.auth.cookies_file, str(self.cookies_file))
    
    def test_check_login_status_no_cookies(self):
        """测试无Cookie时的登录状态检查"""
        # 模拟请求失败
        with patch.object(self.auth.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 401
            mock_get.return_value = mock_response
            
            result = self.auth.check_login_status()
            self.assertFalse(result)
    
    def test_logout(self):
        """测试登出功能"""
        result = self.auth.logout()
        self.assertTrue(result)
        self.assertEqual(len(self.auth.session.cookies), 0)

class TestTouTiaoPublisher(unittest.TestCase):
    """测试发布模块"""
    
    def setUp(self):
        """设置测试环境"""
        self.auth_mock = Mock(spec=TouTiaoAuth)
        self.auth_mock.session = Mock()
        self.publisher = TouTiaoPublisher(self.auth_mock)
    
    def test_init(self):
        """测试初始化"""
        self.assertEqual(self.publisher.auth, self.auth_mock)
        self.assertEqual(self.publisher.session, self.auth_mock.session)
    
    @patch('toutiao_mcp_server.publisher.Path')
    def test_upload_image_file_not_exists(self, mock_path):
        """测试上传不存在的图片文件"""
        mock_path.return_value.exists.return_value = False
        
        result = self.publisher._upload_image("nonexistent.jpg")
        self.assertIsNone(result)
    
    def test_publish_article_basic(self):
        """测试基本的文章发布功能"""
        # 模拟成功响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'message': 'success',
            'data': {
                'id': '12345',
                'article_url': 'https://example.com/article/12345'
            }
        }
        self.auth_mock.session.post.return_value = mock_response
        
        result = self.publisher.publish_article(
            title="测试文章",
            content="这是一篇测试文章"
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['article_id'], '12345')

class TestTouTiaoAnalytics(unittest.TestCase):
    """测试分析模块"""
    
    def setUp(self):
        """设置测试环境"""
        self.auth_mock = Mock(spec=TouTiaoAuth)
        self.auth_mock.session = Mock()
        self.analytics = TouTiaoAnalytics(self.auth_mock)
    
    def test_init(self):
        """测试初始化"""
        self.assertEqual(self.analytics.auth, self.auth_mock)
        self.assertEqual(self.analytics.session, self.auth_mock.session)
    
    def test_get_account_overview_success(self):
        """测试获取账户概览成功"""
        # 模拟成功响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'message': 'success',
            'data': {
                'followers_count': 1000,
                'total_articles': 50,
                'total_read_count': 10000
            }
        }
        self.auth_mock.session.get.return_value = mock_response
        
        result = self.analytics.get_account_overview()
        
        self.assertTrue(result['success'])
        self.assertEqual(result['data']['followers_count'], 1000)
        self.assertEqual(result['data']['total_articles'], 50)

class TestConfiguration(unittest.TestCase):
    """测试配置模块"""
    
    def test_urls_configuration(self):
        """测试URL配置"""
        self.assertIn('login', TOUTIAO_URLS)
        self.assertIn('publish_article', TOUTIAO_URLS)
        self.assertIn('upload', TOUTIAO_URLS)
        
        # 检查URL格式
        for url in TOUTIAO_URLS.values():
            self.assertTrue(url.startswith('https://'))
    
    def test_headers_configuration(self):
        """测试请求头配置"""
        self.assertIn('User-Agent', DEFAULT_HEADERS)
        self.assertIn('Accept', DEFAULT_HEADERS)
        self.assertIn('Content-Type', DEFAULT_HEADERS)

class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def test_service_creation_flow(self):
        """测试服务创建流程"""
        # 创建认证管理器
        auth = TouTiaoAuth()
        self.assertIsNotNone(auth)
        
        # 创建发布器
        publisher = TouTiaoPublisher(auth)
        self.assertIsNotNone(publisher)
        self.assertEqual(publisher.auth, auth)
        
        # 创建分析器
        analytics = TouTiaoAnalytics(auth)
        self.assertIsNotNone(analytics)
        self.assertEqual(analytics.auth, auth)
    
    def test_error_handling(self):
        """测试错误处理"""
        auth = TouTiaoAuth()
        publisher = TouTiaoPublisher(auth)
        
        # 测试发布空内容
        result = publisher.publish_article("", "")
        # 应该处理空内容的情况
        self.assertIn('success', result)

if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2) 
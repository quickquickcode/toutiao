"""
今日头条数据分析模块
"""

import json
import time
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta

import requests

from .config import TOUTIAO_URLS
from .auth import TouTiaoAuth

logger = logging.getLogger(__name__)

class TouTiaoAnalytics:
    """今日头条数据分析管理类"""
    
    def __init__(self, auth: TouTiaoAuth):
        """
        初始化数据分析管理器
        
        Args:
            auth: 认证管理器实例
        """
        self.auth = auth
        self.session = auth.session
    
    def get_account_overview(self) -> Dict[str, Any]:
        """
        获取账户概览数据
        
        Returns:
            Dict: 账户概览信息
        """
        try:
            response = self.session.get(
                TOUTIAO_URLS['analytics_overview'],
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('message') == 'success':
                    data = result.get('data', {})
                    
                    overview = {
                        'followers_count': data.get('followers_count', 0),
                        'total_articles': data.get('total_articles', 0),
                        'total_read_count': data.get('total_read_count', 0),
                        'total_comment_count': data.get('total_comment_count', 0),
                        'total_share_count': data.get('total_share_count', 0),
                        'total_like_count': data.get('total_like_count', 0),
                        'month_read_count': data.get('month_read_count', 0),
                        'week_read_count': data.get('week_read_count', 0),
                        'yesterday_read_count': data.get('yesterday_read_count', 0)
                    }
                    
                    logger.info("获取账户概览成功")
                    return {
                        'success': True,
                        'data': overview
                    }
                else:
                    logger.error(f"获取账户概览失败: {result.get('message')}")
                    return {
                        'success': False,
                        'message': result.get('message', '获取失败')
                    }
            else:
                logger.error(f"获取账户概览请求失败，状态码: {response.status_code}")
                return {
                    'success': False,
                    'message': f'请求失败，状态码: {response.status_code}'
                }
                
        except Exception as e:
            logger.error(f"获取账户概览异常: {e}")
            return {
                'success': False,
                'message': f'获取异常: {str(e)}'
            }
    
    def get_article_stats(self, article_id: str) -> Dict[str, Any]:
        """
        获取指定文章的详细统计数据
        
        Args:
            article_id: 文章ID
            
        Returns:
            Dict: 文章统计数据
        """
        try:
            params = {
                'article_id': article_id,
                'from': 'pc'
            }
            
            response = self.session.get(
                TOUTIAO_URLS['article_stats'],
                params=params,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('message') == 'success':
                    data = result.get('data', {})
                    
                    stats = {
                        'article_id': article_id,
                        'read_count': data.get('read_count', 0),
                        'comment_count': data.get('comment_count', 0),
                        'share_count': data.get('share_count', 0),
                        'like_count': data.get('like_count', 0),
                        'collect_count': data.get('collect_count', 0),
                        'play_duration': data.get('play_duration', 0),
                        'completion_rate': data.get('completion_rate', 0.0),
                        'publish_time': data.get('publish_time'),
                        'last_update_time': data.get('last_update_time'),
                        'status': data.get('status', 'unknown')
                    }
                    
                    logger.info(f"获取文章统计成功: {article_id}")
                    return {
                        'success': True,
                        'data': stats
                    }
                else:
                    logger.error(f"获取文章统计失败: {result.get('message')}")
                    return {
                        'success': False,
                        'message': result.get('message', '获取失败')
                    }
            else:
                logger.error(f"获取文章统计请求失败，状态码: {response.status_code}")
                return {
                    'success': False,
                    'message': f'请求失败，状态码: {response.status_code}'
                }
                
        except Exception as e:
            logger.error(f"获取文章统计异常: {e}")
            return {
                'success': False,
                'message': f'获取异常: {str(e)}'
            }
    
    def get_trending_analysis(self, days: int = 7) -> Dict[str, Any]:
        """
        获取趋势分析数据
        
        Args:
            days: 分析天数
            
        Returns:
            Dict: 趋势分析数据
        """
        try:
            params = {
                'days': days,
                'from': 'pc'
            }
            
            response = self.session.get(
                TOUTIAO_URLS['trending_analysis'],
                params=params,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('message') == 'success':
                    data = result.get('data', {})
                    
                    # 处理趋势数据
                    trend_data = []
                    for item in data.get('trend_list', []):
                        trend_data.append({
                            'date': item.get('date'),
                            'read_count': item.get('read_count', 0),
                            'comment_count': item.get('comment_count', 0),
                            'share_count': item.get('share_count', 0),
                            'like_count': item.get('like_count', 0),
                            'followers_increase': item.get('followers_increase', 0)
                        })
                    
                    analysis = {
                        'period_days': days,
                        'trend_data': trend_data,
                        'total_read_increase': data.get('total_read_increase', 0),
                        'total_followers_increase': data.get('total_followers_increase', 0),
                        'avg_daily_read': data.get('avg_daily_read', 0),
                        'peak_day': data.get('peak_day'),
                        'growth_rate': data.get('growth_rate', 0.0)
                    }
                    
                    logger.info(f"获取趋势分析成功，周期: {days}天")
                    return {
                        'success': True,
                        'data': analysis
                    }
                else:
                    logger.error(f"获取趋势分析失败: {result.get('message')}")
                    return {
                        'success': False,
                        'message': result.get('message', '获取失败')
                    }
            else:
                logger.error(f"获取趋势分析请求失败，状态码: {response.status_code}")
                return {
                    'success': False,
                    'message': f'请求失败，状态码: {response.status_code}'
                }
                
        except Exception as e:
            logger.error(f"获取趋势分析异常: {e}")
            return {
                'success': False,
                'message': f'获取异常: {str(e)}'
            }
    
    def get_content_performance(self, limit: int = 10, sort_by: str = 'read_count') -> Dict[str, Any]:
        """
        获取内容表现排行
        
        Args:
            limit: 获取数量
            sort_by: 排序字段 (read_count/comment_count/like_count/share_count)
            
        Returns:
            Dict: 内容表现数据
        """
        try:
            params = {
                'limit': limit,
                'sort_by': sort_by,
                'from': 'pc'
            }
            
            response = self.session.get(
                TOUTIAO_URLS['content_performance'],
                params=params,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('message') == 'success':
                    articles = result.get('data', {}).get('articles', [])
                    
                    # 处理文章表现数据
                    performance_list = []
                    for article in articles:
                        performance_list.append({
                            'article_id': article.get('id'),
                            'title': article.get('title'),
                            'read_count': article.get('read_count', 0),
                            'comment_count': article.get('comment_count', 0),
                            'like_count': article.get('like_count', 0),
                            'share_count': article.get('share_count', 0),
                            'publish_time': article.get('publish_time'),
                            'completion_rate': article.get('completion_rate', 0.0),
                            'category': article.get('category'),
                            'tags': article.get('tags', [])
                        })
                    
                    logger.info(f"获取内容表现成功，排序: {sort_by}，数量: {len(performance_list)}")
                    return {
                        'success': True,
                        'data': {
                            'articles': performance_list,
                            'sort_by': sort_by,
                            'total_count': len(performance_list)
                        }
                    }
                else:
                    logger.error(f"获取内容表现失败: {result.get('message')}")
                    return {
                        'success': False,
                        'message': result.get('message', '获取失败')
                    }
            else:
                logger.error(f"获取内容表现请求失败，状态码: {response.status_code}")
                return {
                    'success': False,
                    'message': f'请求失败，状态码: {response.status_code}'
                }
                
        except Exception as e:
            logger.error(f"获取内容表现异常: {e}")
            return {
                'success': False,
                'message': f'获取异常: {str(e)}'
            }
    
    def get_audience_analysis(self) -> Dict[str, Any]:
        """
        获取受众分析数据
        
        Returns:
            Dict: 受众分析数据
        """
        try:
            response = self.session.get(
                TOUTIAO_URLS['audience_analysis'],
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('message') == 'success':
                    data = result.get('data', {})
                    
                    audience = {
                        'gender_distribution': data.get('gender_distribution', {}),
                        'age_distribution': data.get('age_distribution', {}),
                        'region_distribution': data.get('region_distribution', {}),
                        'device_distribution': data.get('device_distribution', {}),
                        'interest_tags': data.get('interest_tags', []),
                        'active_time': data.get('active_time', {}),
                        'follower_growth': data.get('follower_growth', [])
                    }
                    
                    logger.info("获取受众分析成功")
                    return {
                        'success': True,
                        'data': audience
                    }
                else:
                    logger.error(f"获取受众分析失败: {result.get('message')}")
                    return {
                        'success': False,
                        'message': result.get('message', '获取失败')
                    }
            else:
                logger.error(f"获取受众分析请求失败，状态码: {response.status_code}")
                return {
                    'success': False,
                    'message': f'请求失败，状态码: {response.status_code}'
                }
                
        except Exception as e:
            logger.error(f"获取受众分析异常: {e}")
            return {
                'success': False,
                'message': f'获取异常: {str(e)}'
            }
    
    def generate_report(self, report_type: str = 'weekly') -> Dict[str, Any]:
        """
        生成数据报告
        
        Args:
            report_type: 报告类型 (daily/weekly/monthly)
            
        Returns:
            Dict: 生成的报告数据
        """
        try:
            # 获取各项数据
            overview = self.get_account_overview()
            trending = self.get_trending_analysis(
                days=1 if report_type == 'daily' else 
                7 if report_type == 'weekly' else 30
            )
            performance = self.get_content_performance(limit=20)
            audience = self.get_audience_analysis()
            
            # 组合报告数据
            report = {
                'report_type': report_type,
                'generate_time': datetime.now().isoformat(),
                'overview': overview.get('data') if overview.get('success') else None,
                'trending': trending.get('data') if trending.get('success') else None,
                'top_content': performance.get('data') if performance.get('success') else None,
                'audience': audience.get('data') if audience.get('success') else None,
                'summary': {
                    'status': 'generated',
                    'data_completeness': sum([
                        1 for x in [overview.get('success'), trending.get('success'), 
                                  performance.get('success'), audience.get('success')] 
                        if x
                    ]) / 4 * 100
                }
            }
            
            logger.info(f"生成{report_type}报告成功")
            return {
                'success': True,
                'data': report
            }
            
        except Exception as e:
            logger.error(f"生成报告异常: {e}")
            return {
                'success': False,
                'message': f'生成报告异常: {str(e)}'
            } 
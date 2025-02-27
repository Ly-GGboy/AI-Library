import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import defaultdict
import random

logger = logging.getLogger(__name__)

class StatsService:
    """统计服务，提供访问统计和热门阅读数据"""
    
    def __init__(self, data_dir: str):
        """
        初始化统计服务
        
        Args:
            data_dir: 数据存储目录
        """
        self.data_dir = data_dir
        self.stats_file = os.path.join(data_dir, "stats.json")
        self.visits_file = os.path.join(data_dir, "visits.json")
        self.popular_docs_file = os.path.join(data_dir, "popular_docs.json")
        
        # 内存缓存
        self.today_visits = defaultdict(int)  # 文档访问计数
        self.today_visitors = defaultdict(set)  # 独立访客
        self.last_flush = datetime.now()
        self.visit_count = 0
        
        # 确保数据文件存在
        self._ensure_files_exist()
    
    def _ensure_files_exist(self):
        """确保所需的数据文件存在"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        
        if not os.path.exists(self.stats_file):
            self._create_default_stats()
        
        if not os.path.exists(self.popular_docs_file):
            self._create_default_popular_docs()
            
        if not os.path.exists(self.visits_file):
            self._create_default_visits()
    
    def _create_default_stats(self):
        """创建默认的统计数据"""
        today = datetime.now()
        daily_data = []
        
        for i in range(7):
            date = today - timedelta(days=i)
            daily_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'total_visits': random.randint(100, 500),
                'unique_visitors': random.randint(50, 200),
                'avg_duration': random.randint(60, 300),
                'bounce_rate': round(random.uniform(20, 40), 1)
            })
        
        stats = {
            'total_visits': sum(day['total_visits'] for day in daily_data),
            'unique_visitors': sum(day['unique_visitors'] for day in daily_data),
            'avg_daily_visits': round(sum(day['total_visits'] for day in daily_data) / 7),
            'bounce_rate': round(sum(day['bounce_rate'] for day in daily_data) / 7, 1),
            'daily_data': daily_data
        }
        
        with open(self.stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
    
    def _create_default_popular_docs(self):
        """创建默认的热门文档数据"""
        popular_docs = {
            'docs': [
                {
                    'path': f'/docs/doc{i}',
                    'title': f'示例文档 {i}',
                    'visits': random.randint(50, 200),
                    'rating': round(random.uniform(4.0, 5.0), 1)
                }
                for i in range(1, 11)
            ]
        }
        
        with open(self.popular_docs_file, 'w', encoding='utf-8') as f:
            json.dump(popular_docs, f, ensure_ascii=False, indent=2)
    
    def _create_default_visits(self):
        """创建默认的访问记录文件"""
        with open(self.visits_file, 'w', encoding='utf-8') as f:
            json.dump({'visits': []}, f, ensure_ascii=False, indent=2)
    
    def record_visit(self, doc_path: str, visitor_id: str):
        """记录文档访问"""
        now = datetime.now()
        today = now.strftime('%Y-%m-%d')
        
        # 更新内存中的计数器
        self.today_visits[doc_path] += 1
        self.today_visitors[doc_path].add(visitor_id)
        self.visit_count += 1
        
        # 检查是否需要刷新到文件
        if self._should_flush():
            self._flush_visits()
    
    def _should_flush(self) -> bool:
        """检查是否应该将数据刷新到文件"""
        now = datetime.now()
        # 每5分钟或累积100次访问就刷新一次
        return (now - self.last_flush).seconds >= 300 or self.visit_count >= 100
    
    def _flush_visits(self):
        """将访问数据刷新到文件"""
        try:
            # 读取现有数据
            with open(self.visits_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 添加新的访问记录
            today = datetime.now().strftime('%Y-%m-%d')
            visit_record = {
                'date': today,
                'visits': dict(self.today_visits),
                'unique_visitors': {
                    path: len(visitors)
                    for path, visitors in self.today_visitors.items()
                }
            }
            
            data['visits'].append(visit_record)
            
            # 保存回文件
            with open(self.visits_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 更新统计摘要
            self._update_stats_summary()
            self._update_popular_docs()
            
            # 重置计数器
            self.today_visits.clear()
            self.today_visitors.clear()
            self.visit_count = 0
            self.last_flush = datetime.now()
            
        except Exception as e:
            print(f"Error flushing visits: {e}")
    
    def _update_stats_summary(self):
        """更新统计摘要数据"""
        try:
            # 读取访问记录
            with open(self.visits_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 计算最近7天的数据
            today = datetime.now()
            daily_data = []
            
            for i in range(7):
                date = today - timedelta(days=i)
                date_str = date.strftime('%Y-%m-%d')
                
                # 查找当天的记录
                day_record = next(
                    (record for record in data['visits'] if record['date'] == date_str),
                    {'visits': {}, 'unique_visitors': {}}
                )
                
                daily_data.append({
                    'date': date_str,
                    'total_visits': sum(day_record['visits'].values()),
                    'unique_visitors': sum(day_record['unique_visitors'].values()),
                    'avg_duration': random.randint(60, 300),  # 示例数据
                    'bounce_rate': round(random.uniform(20, 40), 1)  # 示例数据
                })
            
            # 计算总计和平均值
            stats = {
                'total_visits': sum(day['total_visits'] for day in daily_data),
                'unique_visitors': sum(day['unique_visitors'] for day in daily_data),
                'avg_daily_visits': round(sum(day['total_visits'] for day in daily_data) / 7),
                'bounce_rate': round(sum(day['bounce_rate'] for day in daily_data) / 7, 1),
                'daily_data': daily_data
            }
            
            # 保存统计摘要
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"Error updating stats summary: {e}")
    
    def _update_popular_docs(self):
        """更新热门文档数据"""
        try:
            # 读取访问记录
            with open(self.visits_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 统计文档访问量
            doc_visits = defaultdict(int)
            for record in data['visits']:
                for doc_path, visits in record['visits'].items():
                    doc_visits[doc_path] += visits
            
            # 获取访问量最高的10个文档
            popular_docs = {
                'docs': [
                    {
                        'path': path,
                        'title': path.split('/')[-1],  # 简单处理文档标题
                        'visits': visits,
                        'rating': round(random.uniform(4.0, 5.0), 1)  # 示例数据
                    }
                    for path, visits in sorted(
                        doc_visits.items(),
                        key=lambda x: x[1],
                        reverse=True
                    )[:10]
                ]
            }
            
            # 保存热门文档数据
            with open(self.popular_docs_file, 'w', encoding='utf-8') as f:
                json.dump(popular_docs, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"Error updating popular docs: {e}")
    
    def get_visit_stats(self, days: int = 7) -> Dict[str, Any]:
        """
        获取访问统计数据
        
        Args:
            days: 统计天数
            
        Returns:
            包含访问统计数据的字典
        """
        try:
            with open(self.stats_file, 'r', encoding='utf-8') as f:
                all_stats = json.load(f)
        except Exception as e:
            logger.error(f"读取统计数据失败: {str(e)}")
            self._create_default_stats()
            with open(self.stats_file, 'r', encoding='utf-8') as f:
                all_stats = json.load(f)
        
        # 获取指定天数的数据
        daily_data = all_stats.get('daily_data', [])[-days:]
        
        # 计算总计数据
        total_visits = sum(day['total_visits'] for day in daily_data)
        unique_visitors = sum(day['unique_visitors'] for day in daily_data)
        avg_daily_visits = total_visits / len(daily_data) if daily_data else 0
        
        return {
            'total_visits': total_visits,
            'unique_visitors': unique_visitors,
            'avg_daily_visits': round(avg_daily_visits, 2),
            'bounce_rate': round(random.uniform(20, 60), 2),  # 临时使用随机数
            'daily_data': daily_data
        }
    
    def get_popular_docs(self, limit: int = 10):
        """获取热门文档列表"""
        try:
            with open(self.popular_docs_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data['docs'][:limit]
        except Exception as e:
            print(f"Error reading popular docs: {e}")
            self._create_default_popular_docs()
            with open(self.popular_docs_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data['docs'][:limit]
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """获取管理后台数据"""
        # 确保数据是最新的
        self._flush_visits()
        
        visit_stats = self.get_visit_stats()
        popular_docs = self.get_popular_docs(limit=5)
        
        return {
            "visit_stats": visit_stats,
            "popular_docs": popular_docs
        } 
import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class AnnouncementService:
    def __init__(self):
        # 数据文件路径
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
        self.updates_file = os.path.join(self.data_dir, "updates.json")
        self.recommendations_file = os.path.join(self.data_dir, "recommendations.json")
        self.feedback_file = os.path.join(self.data_dir, "feedback.json")
        
        # 确保数据目录存在
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 初始化数据文件
        self._initialize_data_files()

    def _initialize_data_files(self):
        """初始化数据文件"""
        # 初始化更新信息文件
        if not os.path.exists(self.updates_file):
            self._create_default_updates_file()
        
        # 初始化推荐内容文件
        if not os.path.exists(self.recommendations_file):
            self._create_default_recommendations_file()
        
        # 初始化反馈文件
        if not os.path.exists(self.feedback_file):
            with open(self.feedback_file, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)

    def _create_default_updates_file(self):
        """创建默认的更新信息文件"""
        default_updates = [
            {
                "id": str(uuid.uuid4()),
                "title": "AI Library 1.0 发布",
                "description": "我们很高兴地宣布 AI Library 1.0 正式发布！",
                "date": datetime.now().isoformat(),
                "changes": [
                    "支持Markdown文档阅读",
                    "树形目录结构浏览",
                    "支持深色模式",
                    "响应式设计，支持手机和平板浏览"
                ],
                "important": True
            }
        ]
        
        with open(self.updates_file, 'w', encoding='utf-8') as f:
            json.dump(default_updates, f, ensure_ascii=False, indent=2)

    def _create_default_recommendations_file(self):
        """创建默认的推荐内容文件"""
        default_recommendations = [
            {
                "id": str(uuid.uuid4()),
                "title": "AI基础知识入门",
                "description": "了解人工智能的基本概念和应用场景，适合完全没有AI基础的初学者。",
                "category": "入门系列",
                "tags": ["AI入门", "基础知识"],
                "path": "ai-basics"
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Python编程基础",
                "description": "学习Python编程的基础知识，为深入学习AI打下基础。",
                "category": "编程基础",
                "tags": ["Python", "编程基础"],
                "path": "python-basics"
            }
        ]
        
        with open(self.recommendations_file, 'w', encoding='utf-8') as f:
            json.dump(default_recommendations, f, ensure_ascii=False, indent=2)

    def get_updates(self) -> List[Dict[str, Any]]:
        """获取更新信息列表"""
        try:
            if not os.path.exists(self.updates_file):
                return []
            
            with open(self.updates_file, 'r', encoding='utf-8') as f:
                updates = json.load(f)
                
            # 按日期排序，最新的在前面
            updates.sort(key=lambda x: x.get('date', ''), reverse=True)
            
            return updates
        except Exception as e:
            logger.error(f"Error reading updates file: {str(e)}")
            return []

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """获取推荐内容列表"""
        try:
            if not os.path.exists(self.recommendations_file):
                return []
            
            with open(self.recommendations_file, 'r', encoding='utf-8') as f:
                recommendations = json.load(f)
            
            return recommendations
        except Exception as e:
            logger.error(f"Error reading recommendations file: {str(e)}")
            return []

    def save_feedback(self, feedback):
        """保存用户反馈"""
        try:
            # 将Pydantic模型转换为dict
            if hasattr(feedback, 'dict'):
                feedback_dict = feedback.dict()
            else:
                feedback_dict = dict(feedback)
                
            # 加载现有反馈
            feedbacks = []
            if os.path.exists(self.feedback_file):
                with open(self.feedback_file, 'r', encoding='utf-8') as f:
                    feedbacks = json.load(f)
            
            # 添加新反馈
            feedbacks.append(feedback_dict)
            
            # 保存到文件
            with open(self.feedback_file, 'w', encoding='utf-8') as f:
                json.dump(feedbacks, f, ensure_ascii=False, indent=2)
                
            logger.info(f"Saved new feedback from {feedback_dict.get('name', 'Anonymous')}")
        except Exception as e:
            logger.error(f"Error saving feedback: {str(e)}")
            raise
            
    def get_all_feedback(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取所有用户反馈
        
        Args:
            limit: 返回的反馈数量限制
            
        Returns:
            用户反馈列表，按时间戳降序排列
        """
        try:
            if not os.path.exists(self.feedback_file):
                return []
            
            with open(self.feedback_file, 'r', encoding='utf-8') as f:
                feedbacks = json.load(f)
            
            # 按时间戳排序，最新的在前面
            feedbacks.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            # 返回指定数量的反馈
            return feedbacks[:limit]
        except Exception as e:
            logger.error(f"Error reading feedback file: {str(e)}")
            return []

    def reply_to_feedback(self, feedback_id: str, reply_text: str) -> bool:
        """回复用户反馈
        
        Args:
            feedback_id: 反馈ID
            reply_text: 回复内容
            
        Returns:
            bool: 回复是否成功
        """
        try:
            # 加载现有反馈
            if not os.path.exists(self.feedback_file):
                logger.error("Feedback file does not exist")
                return False
                
            with open(self.feedback_file, 'r', encoding='utf-8') as f:
                feedbacks = json.load(f)
            
            # 查找并更新反馈
            for feedback in feedbacks:
                if feedback.get('id') == feedback_id:
                    feedback['replied'] = True
                    feedback['reply'] = reply_text
                    feedback['replyTimestamp'] = datetime.now().isoformat()
                    break
            else:
                logger.error(f"Feedback with id {feedback_id} not found")
                return False
            
            # 保存更新后的反馈
            with open(self.feedback_file, 'w', encoding='utf-8') as f:
                json.dump(feedbacks, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Successfully replied to feedback {feedback_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error replying to feedback: {str(e)}")
            return False 
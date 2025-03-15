from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import os

from ..services.announcement_service import AnnouncementService
from ..services.doc_service import DocService
from ..services.stats_service import StatsService

router = APIRouter(prefix="/api/admin", tags=["admin"])
logger = logging.getLogger(__name__)

# 初始化服务
data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
os.makedirs(data_dir, exist_ok=True)  # 确保数据目录存在

announcement_service = AnnouncementService()
stats_service = StatsService(data_dir=data_dir)

# 获取服务实例
def get_announcement_service():
    return announcement_service

def get_doc_service():
    return DocService()

def get_stats_service():
    return stats_service

# 热门阅读API
@router.get("/popular", response_model=List[Dict[str, Any]])
async def get_popular_docs(
    limit: int = 10,
    stats_service: StatsService = Depends(get_stats_service)
):
    """获取热门阅读文档列表"""
    try:
        popular_docs = stats_service.get_popular_docs(limit)
        return popular_docs
    except Exception as e:
        logger.error(f"获取热门阅读文档失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取热门阅读文档失败: {str(e)}"
        )

# 访问统计API
@router.get("/stats", response_model=Dict[str, Any])
async def get_visit_stats(
    range: str = "7d",
    stats_service: StatsService = Depends(get_stats_service)
):
    """获取访问统计数据"""
    try:
        # 解析时间范围
        days = {
            "7d": 7,
            "30d": 30,
            "90d": 90
        }.get(range, 7)
        
        stats = stats_service.get_visit_stats(days)
        return {"stats": stats}
    except Exception as e:
        logger.error(f"获取访问统计数据失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取访问统计数据失败: {str(e)}"
        )

# 反馈信息API
@router.get("/feedback", response_model=List[Dict[str, Any]])
async def get_feedback_list(
    limit: int = 50,
    announcement_service: AnnouncementService = Depends(get_announcement_service)
):
    """获取用户反馈列表"""
    try:
        feedback_list = announcement_service.get_all_feedback(limit)
        return feedback_list
    except Exception as e:
        logger.error(f"获取用户反馈列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户反馈列表失败: {str(e)}"
        )

# 仪表盘概览API
@router.get("/dashboard", response_model=Dict[str, Any])
async def get_dashboard_data():
    """
    获取管理后台仪表盘数据，包括：
    - 热门阅读文档
    - 访问统计数据
    - 最新反馈信息
    """
    try:
        # 获取基本统计数据
        dashboard_data = stats_service.get_dashboard_data()
        
        # 获取最新反馈
        recent_feedback = announcement_service.get_all_feedback(limit=10)
        dashboard_data["recent_feedback"] = recent_feedback
        
        return dashboard_data
    except Exception as e:
        logger.error(f"获取仪表盘数据失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取仪表盘数据失败: {str(e)}"
        )

@router.get("/stats", response_model=Dict[str, Any])
async def get_stats():
    """
    获取详细的访问统计数据
    """
    try:
        return stats_service.get_visit_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计数据失败: {str(e)}")

@router.get("/popular-docs", response_model=List[Dict[str, Any]])
async def get_popular_docs(limit: int = 10):
    """
    获取热门阅读文档列表
    
    Args:
        limit: 返回的文档数量
    """
    try:
        return stats_service.get_popular_docs(limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取热门文档失败: {str(e)}")

@router.get("/feedback", response_model=List[Dict[str, Any]])
async def get_all_feedback(limit: int = 50):
    """
    获取所有用户反馈
    
    Args:
        limit: 返回的反馈数量
    """
    try:
        return announcement_service.get_all_feedback(limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户反馈失败: {str(e)}")

@router.post("/feedback/{feedback_id}/reply", response_model=Dict[str, Any])
async def reply_to_feedback(
    feedback_id: str,
    reply_text: str = Body(..., embed=True),
    announcement_service: AnnouncementService = Depends(get_announcement_service)
):
    """回复用户反馈"""
    try:
        success = announcement_service.reply_to_feedback(feedback_id, reply_text)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Feedback not found or reply failed"
            )
        return {"message": "Reply sent successfully"}
    except Exception as e:
        logger.error(f"Error replying to feedback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error replying to feedback: {str(e)}"
        ) 
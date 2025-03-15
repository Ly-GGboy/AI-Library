from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import List, Optional
import os
import json
from datetime import datetime
from pydantic import BaseModel
import logging

from ..services.announcement_service import AnnouncementService

router = APIRouter(prefix="", tags=["announcements"])
logger = logging.getLogger(__name__)

# 数据模型
class UpdateItem(BaseModel):
    id: str
    title: str
    description: str
    date: str
    changes: Optional[List[str]] = None
    important: Optional[bool] = None

class RecommendationItem(BaseModel):
    id: str
    title: str
    description: str
    category: str
    tags: List[str]
    path: Optional[str] = None
    url: Optional[str] = None

class FeedbackItem(BaseModel):
    name: Optional[str] = ""
    type: str
    content: str
    contact: Optional[str] = ""
    timestamp: str

# 获取服务实例
def get_announcement_service():
    return AnnouncementService()

# 路由
@router.get("/updates", response_model=List[UpdateItem])
async def get_updates(
    announcement_service: AnnouncementService = Depends(get_announcement_service)
):
    """获取更新信息列表"""
    try:
        updates = announcement_service.get_updates()
        return updates
    except Exception as e:
        logger.error(f"Error getting updates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting updates: {str(e)}"
        )

@router.get("/recommendations", response_model=List[RecommendationItem])
async def get_recommendations(
    announcement_service: AnnouncementService = Depends(get_announcement_service)
):
    """获取推荐内容列表"""
    try:
        recommendations = announcement_service.get_recommendations()
        return recommendations
    except Exception as e:
        logger.error(f"Error getting recommendations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting recommendations: {str(e)}"
        )

@router.post("/feedback", status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    feedback: FeedbackItem,
    announcement_service: AnnouncementService = Depends(get_announcement_service)
):
    """提交用户反馈"""
    try:
        announcement_service.save_feedback(feedback)
        return {"message": "Feedback submitted successfully"}
    except Exception as e:
        logger.error(f"Error submitting feedback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error submitting feedback: {str(e)}"
        ) 
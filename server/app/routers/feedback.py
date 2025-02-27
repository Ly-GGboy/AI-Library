from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import List, Optional
import logging
from pydantic import BaseModel

from ..services.announcement_service import AnnouncementService

router = APIRouter(prefix="", tags=["feedback"])
logger = logging.getLogger(__name__)

class FeedbackItem(BaseModel):
    name: Optional[str] = ""
    type: str
    content: str
    contact: Optional[str] = ""
    timestamp: str

# 获取服务实例
def get_announcement_service():
    return AnnouncementService()

@router.post("", status_code=status.HTTP_201_CREATED)
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
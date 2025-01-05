from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Optional
from app.services.search_service import SearchService

router = APIRouter()
search_service = SearchService()

@router.get("/")
async def search_docs(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    limit: int = Query(10, ge=1, le=100, description="返回结果数量限制")
) -> List[Dict]:
    """搜索文档"""
    try:
        return await search_service.search(q, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/suggest")
async def get_suggestions(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    limit: int = Query(5, ge=1, le=20, description="返回建议数量限制")
) -> List[str]:
    """获取搜索建议"""
    try:
        return await search_service.get_suggestions(q, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 
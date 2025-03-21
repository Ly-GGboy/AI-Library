from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Optional
from datetime import datetime
import os
from app.services.search_service import SearchService

router = APIRouter()
# 初始化搜索服务
search_service = SearchService()

@router.get("/")
async def search_docs(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    per_page: int = Query(10, ge=1, le=50, description="每页结果数"),
    sort_by: str = Query("relevance", regex="^(relevance|date|name)$", description="排序方式"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="排序顺序"),
    doc_type: Optional[str] = Query(None, description="文档类型"),
    date_from: Optional[str] = Query(None, description="开始日期 (ISO格式)"),
    date_to: Optional[str] = Query(None, description="结束日期 (ISO格式)")
) -> Dict:
    """搜索文档，支持分页和高级搜索"""
    try:
        # 检查索引是否为空，如果为空则自动构建
        if len(search_service.file_index) == 0:
            print("[INFO] 索引为空，自动构建索引...")
            await search_service.build_index()
            
        # 验证日期格式
        if date_from:
            try:
                datetime.fromisoformat(date_from)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date_from format")
        if date_to:
            try:
                datetime.fromisoformat(date_to)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date_to format")

        return await search_service.search(
            q,
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order,
            doc_type=doc_type,
            date_from=date_from,
            date_to=date_to
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/suggest")
async def get_suggestions(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    limit: int = Query(5, ge=1, le=20, description="返回建议数量限制"),
    doc_type: Optional[str] = Query(None, description="文档类型")
) -> List[str]:
    """获取搜索建议，支持文档类型过滤"""
    try:
        return await search_service.get_suggestions(q, limit, doc_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rebuild-index")
async def rebuild_index():
    """重新构建搜索索引"""
    try:
        await search_service.build_index()
        return {"status": "success", "message": "Search index rebuilt successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 
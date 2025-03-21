from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Optional
from datetime import datetime
import os
import asyncio
from app.services.meilisearch_service import MeiliSearchService

router = APIRouter()
# 只初始化MeiliSearch服务
meili_search_service = MeiliSearchService()

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
        # 验证日期格式
        if date_from:
            try:
                datetime.fromisoformat(date_from)
            except ValueError:
                return {
                    "status": "error",
                    "message": "Invalid date_from format",
                    "results": [],
                    "total": 0,
                    "page": page,
                    "per_page": per_page,
                    "total_pages": 0
                }
        if date_to:
            try:
                datetime.fromisoformat(date_to)
            except ValueError:
                return {
                    "status": "error",
                    "message": "Invalid date_to format",
                    "results": [],
                    "total": 0,
                    "page": page,
                    "per_page": per_page,
                    "total_pages": 0
                }
        
        # 直接使用MeiliSearch，不再回退到本地索引
        try:
            # 检查MeiliSearch状态
            status = await meili_search_service.check_status()
            print(f"[DEBUG] MeiliSearch状态: {status}")
            
            if status.get("status") == "available":
                return await meili_search_service.search(
                    q,
                    page=page,
                    per_page=per_page,
                    sort_by=sort_by,
                    sort_order=sort_order,
                    doc_type=doc_type,
                    date_from=date_from,
                    date_to=date_to
                )
            else:
                # MeiliSearch不可用时返回错误信息
                print(f"[WARNING] MeiliSearch服务不可用: {status}")
                return {
                    "status": "error",
                    "message": f"搜索服务暂时不可用: {status.get('status', 'unknown')}",
                    "results": [],
                    "total": 0,
                    "page": page,
                    "per_page": per_page,
                    "total_pages": 0
                }
        except Exception as e:
            print(f"[ERROR] 使用MeiliSearch搜索失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "message": f"搜索服务错误: {str(e)}",
                "results": [],
                "total": 0,
                "page": page,
                "per_page": per_page,
                "total_pages": 0
            }
    except Exception as e:
        print(f"[ERROR] 搜索请求处理失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": f"服务器错误: {str(e)}",
            "results": [],
            "total": 0,
            "page": page,
            "per_page": per_page,
            "total_pages": 0
        }

@router.get("/suggest")
async def get_suggestions(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    limit: int = Query(5, ge=1, le=20, description="返回建议数量限制"),
    doc_type: Optional[str] = Query(None, description="文档类型")
) -> List[str]:
    """获取搜索建议，支持文档类型过滤"""
    try:
        # 直接使用MeiliSearch获取建议
        try:
            # 检查MeiliSearch状态
            status = await meili_search_service.check_status()
            if status.get("status") == "available":
                return await meili_search_service.get_suggestions(q, limit, doc_type)
            else:
                # MeiliSearch不可用时返回空列表
                print(f"[WARNING] MeiliSearch服务不可用: {status}")
                return []
        except Exception as e:
            print(f"[ERROR] 使用MeiliSearch获取建议失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    except Exception as e:
        print(f"[ERROR] 获取建议请求处理失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

@router.post("/rebuild-index")
async def rebuild_index():
    """重新构建搜索索引"""
    try:
        # 只构建MeiliSearch索引
        try:
            meili_result = await meili_search_service.build_index()
            return {
                "status": "success", 
                "message": "MeiliSearch index rebuilt successfully",
                "details": {"meilisearch": meili_result}
            }
        except Exception as e:
            print(f"[ERROR] 构建MeiliSearch索引失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "message": f"构建MeiliSearch索引失败: {str(e)}",
                "details": {"error": str(e)}
            }
    except Exception as e:
        print(f"[ERROR] rebuild_index端点处理失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": f"服务器错误: {str(e)}"}

@router.get("/status")
async def get_search_status():
    """获取搜索状态信息"""
    try:
        # 只返回MeiliSearch状态
        try:
            meili_status = await meili_search_service.check_status()
            return {"meilisearch": meili_status}
        except Exception as e:
            print(f"[ERROR] 获取MeiliSearch状态失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "meilisearch": {
                    "status": "error",
                    "error": str(e)
                }
            }
    except Exception as e:
        print(f"[ERROR] 获取搜索状态失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": f"服务器错误: {str(e)}"} 
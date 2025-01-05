from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from typing import List, Dict, Optional
import os
import json
from app.services.doc_service import DocService

router = APIRouter()
doc_service = DocService()

@router.get("/tree")
async def get_doc_tree() -> Dict:
    """获取文档目录树"""
    try:
        return await doc_service.get_doc_tree()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/content/{path:path}")
async def get_doc_content(path: str):
    """获取文档内容或图片"""
    try:
        # 检查是否是图片或其他二进制文件
        if not path.endswith('.md'):
            file_path, mime_type = await doc_service.get_file_response(path)
            return FileResponse(
                file_path,
                media_type=mime_type,
                filename=os.path.basename(file_path)
            )
        
        # 如果是 Markdown 文件，返回内容
        return await doc_service.get_doc_content(path)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recent")
async def get_recent_docs(limit: int = 10) -> List[Dict]:
    """获取最近更新的文档"""
    try:
        return await doc_service.get_recent_docs(limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/breadcrumb/{path:path}")
async def get_breadcrumb(path: str) -> List[Dict]:
    """获取文档的面包屑导航"""
    try:
        return await doc_service.get_breadcrumb(path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 
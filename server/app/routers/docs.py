from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse
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
    """获取文档内容或文件"""
    try:
        # 获取文件路径和MIME类型
        file_path, mime_type = await doc_service.get_file_response(path)
        
        # 如果是Markdown文件，返回内容
        if path.endswith('.md'):
            return await doc_service.get_doc_content(path)
            
        # 如果是PDF文件，返回文件和正确的Content-Type
        if mime_type == 'application/pdf':
            return FileResponse(
                file_path,
                media_type=mime_type,
                filename=os.path.basename(file_path),
                headers={
                    "Content-Disposition": "inline",  # 在浏览器中直接显示
                    "Accept-Ranges": "bytes"  # 支持范围请求，用于大文件加载
                }
            )
            
        # 其他类型文件
        return FileResponse(
            file_path,
            media_type=mime_type,
            filename=os.path.basename(file_path)
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metadata/{path:path}")
async def get_doc_metadata(path: str):
    """获取文档元数据，包括PDF的页数等信息"""
    try:
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
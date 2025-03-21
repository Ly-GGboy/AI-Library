from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import FileResponse, JSONResponse
from typing import List, Dict, Optional
import os
import json
import logging
from app.services.doc_service import DocService
from app.services.stats_service import StatsService

router = APIRouter(prefix="", tags=["docs"])
logger = logging.getLogger(__name__)

def get_doc_service():
    return DocService()

def get_stats_service():
    # 获取项目根目录
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    # 创建数据目录路径
    data_dir = os.path.join(project_root, 'server', 'static', 'stats')
    # 确保目录存在
    os.makedirs(data_dir, exist_ok=True)
    return StatsService(data_dir)

@router.get("/tree")
async def get_doc_tree() -> Dict:
    """获取文档目录树"""
    try:
        return await get_doc_service().get_doc_tree()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/subtree/{path:path}")
async def get_doc_subtree(path: str) -> Dict:
    """获取指定路径的子树"""
    try:
        logger.info(f"正在获取子树: {path}")
        result = await get_doc_service().get_doc_subtree(path)
        if "error" in result:
            logger.error(f"获取子树失败: {path}, 错误: {result['error']}")
            raise HTTPException(status_code=400, detail=result["error"])
        logger.info(f"子树获取成功: {path}, 子节点数量: {len(result.get('children', []))}")
        return result
    except Exception as e:
        logger.error(f"获取子树失败: {path}, 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/content/{path:path}")
async def get_doc_content(path: str, request: Request):
    """获取文档内容或文件"""
    try:
        # 获取真实IP地址（考虑代理情况）
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # X-Forwarded-For格式为: client, proxy1, proxy2, ...
            ip_address = forwarded_for.split(",")[0].strip()
            logger.debug(f"文档访问 - 从X-Forwarded-For获取IP: {ip_address}")
        else:
            ip_address = request.client.host
            logger.debug(f"文档访问 - 从client.host获取IP: {ip_address}")
        
        # 更新在线状态
        await get_doc_service().update_reader(ip_address, path)
        logger.debug(f"已更新用户状态: {ip_address} 访问文档 {path}")
        
        # 获取文件路径和MIME类型
        file_path, mime_type = await get_doc_service().get_file_response(path)
        
        # 如果是Markdown文件，返回内容
        if path.endswith('.md'):
            return await get_doc_service().get_doc_content(path)
            
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
        logger.error(f"获取文档内容失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metadata/{path:path}")
async def get_doc_metadata(path: str):
    """获取文档元数据，包括PDF的页数等信息"""
    try:
        return await get_doc_service().get_doc_content(path)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recent")
async def get_recent_docs(limit: int = 10) -> List[Dict]:
    """获取最近更新的文档"""
    try:
        return await get_doc_service().get_recent_docs(limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/breadcrumb/{path:path}")
async def get_breadcrumb(path: str) -> List[Dict]:
    """获取文档的面包屑导航"""
    try:
        return await get_doc_service().get_breadcrumb(path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/online-readers")
async def get_online_readers(request: Request):
    """获取当前在线阅读人数"""
    try:
        # 获取真实IP地址（考虑代理情况）
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # X-Forwarded-For格式为: client, proxy1, proxy2, ...
            ip_address = forwarded_for.split(",")[0].strip()
            logger.debug(f"从X-Forwarded-For获取IP: {ip_address}")
        else:
            ip_address = request.client.host
            logger.debug(f"从client.host获取IP: {ip_address}")
        
        # 更新在线状态
        await get_doc_service().update_reader(ip_address, "homepage")
        logger.debug(f"已更新用户状态: {ip_address} 在首页")
        
        # 获取总数
        count = await get_doc_service().get_online_readers_count()
        logger.debug(f"当前在线用户数: {count}")
        
        return {"count": count}
    except Exception as e:
        logger.error(f"获取在线读者数量出错: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{doc_path:path}")
async def get_doc(
    doc_path: str,
    request: Request,
    doc_service: DocService = Depends(get_doc_service),
    stats_service: StatsService = Depends(get_stats_service)
):
    """获取文档内容"""
    try:
        # 获取用户ID或会话ID
        user_id = request.cookies.get("user_id") or request.client.host
        
        # 记录访问
        stats_service.record_visit(doc_path, user_id)
        
        # 获取文档内容
        doc = await doc_service.get_doc_content(doc_path)
        if not doc:
            raise HTTPException(status_code=404, detail="文档不存在")
        return doc
    except Exception as e:
        logger.error(f"获取文档失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取文档失败: {str(e)}"
        )
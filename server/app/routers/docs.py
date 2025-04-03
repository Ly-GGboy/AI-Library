from fastapi import APIRouter, HTTPException, Request, Depends, Response
from fastapi.responses import FileResponse, JSONResponse
from typing import List, Dict, Optional, Any
import os
import json
import logging
import time
from datetime import datetime, timedelta
from app.services.doc_service import DocService
from app.services.stats_service import StatsService

router = APIRouter(prefix="", tags=["docs"])
logger = logging.getLogger(__name__)

class CompressedJSONResponse(JSONResponse):
    """增强的JSON响应，确保内容被压缩且有适当的缓存控制"""
    def __init__(
        self, 
        content: Any, 
        max_age: int = 3600,  # 默认缓存1小时
        status_code: int = 200, 
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ):
        if headers is None:
            headers = {}
        
        # 添加缓存控制头
        headers.update({
            "Cache-Control": f"public, max-age={max_age}",
            "Vary": "Accept-Encoding",  # 确保缓存考虑不同的编码
            "ETag": f"\"{hash(str(content)) & 0xffffffff:08x}\"",  # 简单的ETag实现
        })
        
        super().__init__(content, status_code, headers, **kwargs)

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
async def get_doc_tree():
    """获取文档目录树"""
    try:
        tree_data = await get_doc_service().get_doc_tree()
        # 树数据可以缓存较长时间，因为它不经常变化
        return CompressedJSONResponse(tree_data, max_age=7200)  # 缓存2小时
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/subtree/{path:path}")
async def get_doc_subtree(path: str):
    """获取指定路径的子树"""
    try:
        logger.info(f"正在获取子树: {path}")
        result = await get_doc_service().get_doc_subtree(path)
        if "error" in result:
            logger.error(f"获取子树失败: {path}, 错误: {result['error']}")
            raise HTTPException(status_code=400, detail=result["error"])
        logger.info(f"子树获取成功: {path}, 子节点数量: {len(result.get('children', []))}")
        return CompressedJSONResponse(result, max_age=3600)  # 缓存1小时
    except Exception as e:
        logger.error(f"获取子树失败: {path}, 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/debug/tree-has-children/{path:path}")
async def debug_tree_has_children(path: str) -> Dict:
    """调试端点：检查路径是否设置了has_children标记"""
    try:
        logger.info(f"调试：检查路径是否有子内容: {path}")
        # 构建一个简单的树，只加载顶层内容
        tree = await get_doc_service().get_doc_tree()
        
        # 递归查找节点
        def find_node(node, target_path):
            if node.get("path") == target_path:
                return node
            if node.get("children"):
                for child in node["children"]:
                    result = find_node(child, target_path)
                    if result:
                        return result
            return None
        
        node = find_node(tree, path)
        if not node:
            return {"found": False, "message": "节点未找到"}
        
        has_children = node.get("has_children", False)
        children_count = len(node.get("children", []))
        
        return {
            "found": True,
            "path": path,
            "has_children": has_children,
            "children_count": children_count,
            "is_dir": node.get("is_dir", False),
            "is_file": node.get("is_file", False),
            "name": node.get("name", ""),
        }
    except Exception as e:
        logger.error(f"调试has_children检查失败: {str(e)}")
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
            content = await get_doc_service().get_doc_content(path)
            return CompressedJSONResponse(content, max_age=3600)  # 缓存1小时
            
        # 如果是PDF文件，返回文件和正确的Content-Type
        if mime_type == 'application/pdf':
            response = FileResponse(
                file_path,
                media_type=mime_type,
                filename=os.path.basename(file_path),
                headers={
                    "Content-Disposition": "inline",  # 在浏览器中直接显示
                    "Accept-Ranges": "bytes"  # 支持范围请求，用于大文件加载
                }
            )
            # 添加缓存控制
            return add_cache_headers(response, max_age=7200)  # 缓存2小时
            
        # 其他类型文件
        response = FileResponse(
            file_path,
            media_type=mime_type,
            filename=os.path.basename(file_path)
        )
        # 为图片等静态资源添加较长的缓存时间
        if mime_type and (mime_type.startswith('image/') or mime_type.startswith('font/')):
            return add_cache_headers(response, max_age=604800)  # 缓存7天
        return add_cache_headers(response)  # 默认缓存1小时
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取文档内容失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metadata/{path:path}")
async def get_doc_metadata(path: str):
    """获取文档元数据，包括PDF的页数等信息"""
    try:
        content = await get_doc_service().get_doc_content(path)
        # 元数据不经常变化，可以缓存较长时间
        return CompressedJSONResponse(content, max_age=7200)  # 缓存2小时
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recent")
async def get_recent_docs(limit: int = 10):
    """获取最近更新的文档"""
    try:
        data = await get_doc_service().get_recent_docs(limit)
        # 最近文档变化较频繁，使用较短的缓存时间
        return CompressedJSONResponse(data, max_age=900)  # 缓存15分钟
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/breadcrumb/{path:path}")
async def get_breadcrumb(path: str):
    """获取文档的面包屑导航"""
    try:
        data = await get_doc_service().get_breadcrumb(path)
        # 面包屑导航不经常变化
        return CompressedJSONResponse(data, max_age=7200)  # 缓存2小时
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
        
        # 在线读者数据频繁变化，使用短缓存
        return CompressedJSONResponse({"count": count}, max_age=60)  # 缓存1分钟
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
            
        # 根据文档类型确定缓存时间
        max_age = 3600  # 默认1小时
        if doc_path.endswith('.pdf'):
            max_age = 7200  # PDF缓存2小时
            
        return CompressedJSONResponse(doc, max_age=max_age)
    except Exception as e:
        logger.error(f"获取文档失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取文档失败: {str(e)}"
        )

@router.get("/debug/compression-test")
async def compression_test(request: Request):
    """测试压缩是否生效的调试端点"""
    # 检查请求头是否支持压缩
    accepts_encoding = request.headers.get("Accept-Encoding", "")
    supports_gzip = "gzip" in accepts_encoding.lower()
    
    # 创建一些重复的数据以便演示压缩效果
    # 真实场景中，压缩比可能在60-90%之间
    original_data = {
        "test": "compression_test" * 100,
        "repeated_data": ["item" * 20] * 50,
        "numbers": list(range(1000)),
        "explanation": "这个响应包含重复数据，以便演示压缩效果。在真实场景中，文本和JSON数据通常有50-90%的压缩率。",
        "original_size": 0,  # 将在下面计算
        "supports_compression": supports_gzip,
        "client_headers": {
            "accept_encoding": accepts_encoding,
            "user_agent": request.headers.get("User-Agent", "Unknown")
        },
        "timestamp": datetime.now().isoformat()
    }
    
    # 估算原始大小
    original_size = len(json.dumps(original_data))
    original_data["original_size"] = original_size
    
    # 使用压缩响应
    return CompressedJSONResponse(
        original_data,
        max_age=60,  # 短缓存，以便于测试
        headers={
            "X-Original-Size": str(original_size),
            "X-Compression-Enabled": "true"
        }
    )

# 添加缓存控制headers
def add_cache_headers(response: Response, max_age: int = 3600):
    """添加缓存控制头到响应"""
    try:
        response.headers["Cache-Control"] = f"public, max-age={max_age}"
        response.headers["Vary"] = "Accept-Encoding"
        
        # FileResponse 需要特殊处理
        if isinstance(response, FileResponse):
            # 某些文件类型应添加额外的压缩提示
            content_type = response.headers.get("Content-Type", "")
            if any(ct in content_type.lower() for ct in ["text/", "application/json", "image/svg", "application/javascript"]):
                response.headers["Content-Encoding"] = "gzip"  # 提示客户端内容已被压缩
        
        # 如果没有ETag，尝试添加简单的ETag
        if not response.headers.get("ETag"):
            try:
                # 对于FileResponse，基于文件路径和修改日期创建ETag
                if isinstance(response, FileResponse) and hasattr(response, "path"):
                    file_path = str(response.path)
                    m_time = os.path.getmtime(file_path)
                    file_size = os.path.getsize(file_path)
                    etag_data = f"{file_path}:{m_time}:{file_size}"
                    response.headers["ETag"] = f"\"{hash(etag_data) & 0xffffffff:08x}\""
                # 对于其他响应，基于响应体创建ETag
                elif hasattr(response, "body"):
                    response.headers["ETag"] = f"\"{hash(str(response.body)) & 0xffffffff:08x}\""
            except Exception as e:
                logger.warning(f"无法为响应生成ETag: {str(e)}")
        
        return response
    except Exception as e:
        logger.error(f"添加缓存头时出错: {str(e)}")
        return response
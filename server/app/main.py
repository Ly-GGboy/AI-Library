from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import time
import os
import asyncio
import logging
import gc
import psutil
from app.services.doc_service import DocService
from app.services.search_service import SearchService

app = FastAPI(
    title="AI Library API",
    description="AI Library Backend API with HTTP/2 Support",
    version="2.0.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://ailibrary.space", 
        "https://localhost:5173",
        "https://localhost:5175",
        "http://localhost:5173",
        "http://localhost:5175",
        "https://frp6.mmszxc.xin:18925",
        "http://localhost:5175",  # 添加admin后台域名
        "https://localhost:5175",  # 添加admin后台域名(HTTPS)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 启用压缩
app.add_middleware(GZipMiddleware, minimum_size=500)

# 性能监控中间件
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    # 检测实际的 HTTP 版本
    if request.scope.get("http_version") == "2":
        http_version = "2.0"
    else:
        http_version = "1.1"
    response.headers["X-HTTP-Version"] = http_version
    return response

# 健康检查
@app.get("/api/health")
async def health_check(request: Request):
    http_version = "2.0" if request.scope.get("http_version") == "2" else "1.1"
    return {"status": "healthy", "http_version": http_version}

# 详细健康检查
@app.get("/api/health/detailed")
async def detailed_health_check():
    """详细的健康检查，包括服务状态"""
    doc_service = DocService()
    search_service = SearchService()
    
    # 检查文件监视器状态
    watcher_status = "unknown"
    try:
        if await doc_service.check_file_watcher():
            watcher_status = "restarted"
        else:
            watcher_status = "healthy"
    except Exception as e:
        watcher_status = f"error: {str(e)}"
    
    # 检查缓存状态
    cache_status = {
        "content_cache_size": len(doc_service._content_cache),
        "pdf_metadata_cache_size": len(doc_service._pdf_metadata_cache),
        "locks_count": len(doc_service._cache_locks)
    }
    
    # 检查搜索索引状态
    search_status = {
        "index_size": len(search_service.file_index)
    }
    
    # 获取内存使用情况
    process = psutil.Process()
    memory_info = process.memory_info()
    
    return {
        "status": "healthy",
        "watcher_status": watcher_status,
        "cache_status": cache_status,
        "search_status": search_status,
        "memory_usage": {
            "rss_mb": memory_info.rss / (1024 * 1024),  # RSS内存（MB）
            "vms_mb": memory_info.vms / (1024 * 1024),  # 虚拟内存（MB）
            "percent": process.memory_percent()  # 内存使用百分比
        },
        "uptime_seconds": time.time() - process.create_time()  # 运行时间（秒）
    }

# 导入路由
from app.routers import docs, search, announcements, feedback, admin

# 初始化服务
data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
os.makedirs(data_dir, exist_ok=True)  # 确保数据目录存在

# 注册路由
app.include_router(docs.router, prefix="/api/docs", tags=["docs"])
app.include_router(search.router, prefix="/api/search", tags=["search"])
app.include_router(announcements.router, prefix="/api/announcements", tags=["announcements"])
app.include_router(feedback.router, prefix="/api/feedback", tags=["feedback"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])

# 定期维护任务
async def perform_maintenance():
    """定期执行维护任务"""
    doc_service = DocService()
    
    while True:
        try:
            logging.info("执行定期维护任务...")
            
            # 执行DocService维护
            await doc_service.perform_maintenance()
            
            # 检查内存使用情况
            process = psutil.Process()
            memory_percent = process.memory_percent()
            
            # 如果内存使用超过70%，执行额外的清理
            if memory_percent > 70:
                logging.warning(f"内存使用率过高: {memory_percent:.1f}%，执行额外清理")
                # 强制执行垃圾回收
                gc.collect()
                
            logging.info("维护任务完成")
            
        except Exception as e:
            logging.error(f"维护任务出错: {str(e)}")
        
        # 每天执行一次
        await asyncio.sleep(86400)

@app.on_event("startup")
async def startup_event():
    """应用启动时执行的事件"""
    # 启动定期维护任务
    asyncio.create_task(perform_maintenance())
    
    print("Application started with maintenance tasks. If search index is empty, please use the /api/search/rebuild-index endpoint to build it.")
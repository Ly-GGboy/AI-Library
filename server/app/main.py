from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import time
import os

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

@app.on_event("startup")
async def startup_event():
    """应用启动时执行的事件"""
    print("Application started. If search index is empty, please use the /api/search/rebuild-index endpoint to build it.")
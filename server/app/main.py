from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import time

app = FastAPI(
    title="AI Library API",
    description="AI Library Backend API with HTTP/2 Support",
    version="2.0.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://ailibrary.space", "https://localhost:5173"],
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
from app.routers import docs, search

# 注册路由
app.include_router(docs.router, prefix="/api/docs", tags=["docs"])
app.include_router(search.router, prefix="/api/search", tags=["search"]) 
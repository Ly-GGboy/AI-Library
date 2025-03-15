import os
import asyncio
from hypercorn.config import Config
from hypercorn.asyncio import serve
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('hypercorn.error')

config = Config()
config.bind = ["0.0.0.0:8000"]
config.worker_class = "uvloop"  # 使用 uvloop
config.use_reloader = True  # 启用热重载
config.accesslog = "-"  # 输出访问日志到 stdout
config.errorlog = logger  # 使用自定义的错误日志处理器

# 错误处理装饰器
def handle_errors(func):
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            if isinstance(e, KeyError) and str(e) == '1':
                # 忽略 stream 1 的错误（通常是客户端断开连接）
                logger.debug("Client disconnected, stream 1 not found")
            else:
                logger.exception("Unexpected error occurred")
            return None
    return wrapper

# 启动服务器
if __name__ == "__main__":
    from app.main import app
    # 包装应用以处理错误
    @handle_errors
    async def wrapped_app(*args, **kwargs):
        return await app(*args, **kwargs)
    
    asyncio.run(serve(wrapped_app, config)) 
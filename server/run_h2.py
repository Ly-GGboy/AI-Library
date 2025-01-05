import os
import asyncio
from hypercorn.config import Config
from hypercorn.asyncio import serve
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('hypercorn.error')

# 获取证书文件的路径
cert_dir = os.path.dirname(os.path.abspath(__file__))
ssl_keyfile = os.path.join(cert_dir, "key.pem")
ssl_certfile = os.path.join(cert_dir, "cert.pem")

config = Config()
config.bind = ["0.0.0.0:8000"]
config.certfile = ssl_certfile
config.keyfile = ssl_keyfile
config.verify_mode = None  # 不验证客户端证书
config.alpn_protocols = ["h2", "http/1.1"]  # 优先使用 HTTP/2
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
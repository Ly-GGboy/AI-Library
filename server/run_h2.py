import os
import asyncio
from hypercorn.config import Config
from hypercorn.asyncio import serve
import logging

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('hypercorn.error')

config = Config()
config.bind = ["0.0.0.0:8000"]
config.worker_class = "uvloop"  # 使用 uvloop
config.use_reloader = True  # 启用热重载
config.accesslog = "-"  # 输出访问日志到 stdout
config.errorlog = logger  # 使用自定义的错误日志处理器

# 配置SSL/HTTPS
cert_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "certs")
config.certfile = os.path.join(cert_dir, "cert.pem")
config.keyfile = os.path.join(cert_dir, "key.pem")

# 如果证书文件不存在，则输出警告
if not os.path.exists(config.certfile) or not os.path.exists(config.keyfile):
    logger.warning(f"SSL证书文件不存在: {config.certfile} 或 {config.keyfile}")
    logger.warning("使用以下命令生成自签名证书:")
    logger.warning("mkdir -p certs && openssl req -x509 -newkey rsa:4096 "
                  f"-keyout {config.keyfile} -out {config.certfile} -days 365 -nodes")
    raise FileNotFoundError("SSL证书文件不存在")

# 启用HTTPS
config.scheme = "https"
logger.info(f"服务器将使用HTTPS启动，监听端口 {config.bind[0]}")

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
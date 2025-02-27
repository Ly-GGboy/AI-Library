import uvicorn
import os
import ssl
import logging
from app.main import app
from fastapi.routing import APIRoute

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def print_routes():
    """打印所有可用的路由"""
    route_info = []
    for route in app.routes:
        if isinstance(route, APIRoute):
            methods = [method for method in route.methods]
            route_info.append({
                "path": route.path,
                "name": route.name,
                "methods": methods
            })
    
    # 按路径排序
    route_info.sort(key=lambda x: x["path"])
    
    # 打印路由信息
    print("\n=== Available API Routes ===")
    print(f"{'Method':<10} {'Path':<50} {'Name':<30}")
    print("-" * 90)
    for route in route_info:
        methods_str = ", ".join(route["methods"])
        print(f"{methods_str:<10} {route['path']:<50} {route['name']:<30}")
    print("=" * 90 + "\n")

if __name__ == "__main__":
    # 打印路由信息
    print_routes()
    
    # 获取证书文件的路径
    cert_dir = os.path.dirname(os.path.abspath(__file__))
    ssl_keyfile = os.path.join(cert_dir, "key.pem")
    ssl_certfile = os.path.join(cert_dir, "cert.pem")

    # 创建 SSL 上下文
    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain(ssl_certfile, ssl_keyfile)
    # 设置支持的协议
    ssl_context.set_alpn_protocols(['h2', 'http/1.1'])

    # 配置 uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        ssl_keyfile=ssl_keyfile,
        ssl_certfile=ssl_certfile,
        ssl_version=ssl.PROTOCOL_TLS_SERVER,  # 使用 TLS
        reload=True,
        log_level="info",
        http="httptools",  # 使用更高性能的 HTTP 服务器
        ws="websockets",
        loop="uvloop",  # 使用更高性能的事件循环
        proxy_headers=True,  # 支持代理头
    ) 
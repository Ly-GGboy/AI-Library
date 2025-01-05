import uvicorn
import os
import ssl

if __name__ == "__main__":
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
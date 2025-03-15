#!/bin/bash

# 更新系统包
sudo yum update -y

# 安装 EPEL 源
sudo yum install epel-release -y

# 安装 Nginx
sudo yum install nginx -y

# 创建网站目录
sudo mkdir -p /var/www/ailibrary

# 确保目录权限正确
sudo chown -R nginx:nginx /var/www/ailibrary
sudo chmod -R 755 /var/www/ailibrary

# 配置 Nginx
sudo mkdir -p /etc/nginx/conf.d
sudo tee /etc/nginx/conf.d/ailibrary.conf << EOF
server {
    listen 80;
    server_name _;  # 暂时匹配所有域名

    root /var/www/ailibrary;
    index index.html;

    # 启用 gzip 压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 10240;
    gzip_proxied expired no-cache no-store private auth;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml;
    gzip_disable "MSIE [1-6]\.";

    location / {
        try_files \$uri \$uri/ /index.html;  # 支持 Vue Router 的 history 模式
    }

    # 缓存静态资源
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }
}
EOF

# 创建日志目录（如果不存在）
sudo mkdir -p /var/log/nginx
sudo chown -R nginx:nginx /var/log/nginx

# 配置 SELinux（如果启用）
if command -v sestatus >/dev/null 2>&1; then
    if sestatus | grep "SELinux status" | grep -q "enabled"; then
        sudo setsebool -P httpd_can_network_connect 1
        sudo chcon -Rt httpd_sys_content_t /var/www/ailibrary
    fi
fi

# 启动 Nginx 并设置开机自启
sudo systemctl enable nginx
sudo systemctl start nginx

# 配置防火墙
if command -v firewall-cmd >/dev/null 2>&1; then
    sudo firewall-cmd --permanent --zone=public --add-service=http
    sudo firewall-cmd --permanent --zone=public --add-service=https
    sudo firewall-cmd --reload
fi

echo "部署脚本执行完成！"
echo "现在你可以将构建好的 dist 目录内容上传到 /var/www/ailibrary/ 目录" 
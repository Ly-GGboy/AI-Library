#!/bin/bash
# AI Library 管理后台启动脚本

echo "===== 启动 AI Library 管理后台 ====="
echo "确保已安装Node.js和npm..."

# 检查是否已安装依赖
if [ ! -d "node_modules" ]; then
  echo "正在安装依赖..."
  npm install
fi

# 启动开发服务器
echo "启动管理后台开发服务器..."
npm run dev

# 如果需要构建生产版本
# echo "构建管理后台生产版本..."
# npm run build 
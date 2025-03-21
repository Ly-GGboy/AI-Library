#!/bin/bash

# 输出带颜色的文字
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}启动 MeiliSearch 服务...${NC}"
docker-compose up -d meilisearch

# 等待 MeiliSearch 启动
echo -e "${YELLOW}等待 MeiliSearch 启动 (10秒)...${NC}"
sleep 10

# 设置环境变量
export MEILISEARCH_HOST="http://localhost:7700"
export MEILISEARCH_API_KEY="masterKey"

# 进入服务器目录
cd server

# 启动后端服务器
echo -e "${GREEN}启动后端服务器...${NC}"
python run_h2.py 
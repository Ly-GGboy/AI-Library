# AI Library

AI Library 是一个由ai开发的现代化的文档管理系统，专注于提供优雅的阅读体验和高效的知识管理。

## ✨ 功能展示

### 📱 响应式布局
![响应式布局](responsive.png)
完美适配桌面端和移动端，提供一致的阅读体验。

### 🌓 深色模式
![深色模式](dark-mode.png)
自动跟随系统切换，保护你的眼睛。

### 🔍 实时搜索
![实时搜索](search.png)
快速定位文档，支持标题和内容搜索。



## 功能特点

### 文档管理
- 支持 Markdown 格式文档
- 树形目录结构
- 文档实时搜索
- 最近访问记录
- 移动端适配

### 用户体验
- 响应式设计
- 深色模式支持
- 优雅的动画过渡
- 手势操作支持

### 特性
- HTTP/2 支持
- 高性能后端 API
- 实时搜索引擎
- 缓存优化

## 技术栈

### 前端
- Vue 3 (Composition API)
- TypeScript
- Tailwind CSS
- Vite
- Pinia 状态管理
- Vue Router

### 后端
- FastAPI
- Uvicorn (HTTP/2 支持)
- Python 3.10+
- SQLite 数据库

### 部署
- HTTPS/HTTP2
- Docker 支持

## 环境要求

### 开发环境
- Node.js 16+
- Python 3.10+
- pip
- yarn/npm
- Git

### 生产环境
- Linux/macOS/Windows
- Docker (可选)


## 安装指南

### 1. 克隆项目
```bash
git clone https://github.com/yourusername/ai-library.git
cd ai-library
```

### 2. 后端设置
```bash
# 创建 Python 虚拟环境
python -m venv py310
source py310/bin/activate  # Linux/macOS
# 或
.\py310\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 生成 SSL 证书（用于开发环境）
openssl req -x509 -newkey rsa:4096 -keyout server/key.pem -out server/cert.pem -days 365 -nodes
```

### 3. 前端设置
```bash
cd client
yarn install  # 或 npm install

# 开发环境配置
cp .env.example .env.local
```

## 开发指南

### 启动开发服务器

1. 后端服务器
```bash
cd server
PYTHONPATH=/path/to/project/server python run.py
```

2. 前端服务器
```bash
cd client
yarn dev  # 或 npm run dev
```

### 开发模式
- 后端服务器运行在 https://localhost:8000
- 前端服务器运行在 https://localhost:5173
- API 文档访问地址：https://localhost:8000/docs

## 部署指南


### 1. 生产环境部署

1. 构建前端
```bash
cd client
yarn build  # 或 npm run build
```

2. 启动服务
```bash
# 后端服务
cd server
PYTHONPATH=/path/to/project/server python run.py

```

## 项目结构
```
.
├── client/                 # 前端代码
│   ├── src/
│   │   ├── components/    # Vue 组件
│   │   ├── stores/        # Pinia 状态管理
│   │   ├── services/      # API 服务
│   │   └── styles/        # 全局样式
│   └── public/            # 静态资源
├── server/                # 后端代码
│   ├── app/              # FastAPI 应用
│   │   ├── api/          # API 路由
│   │   ├── models/       # 数据模型
│   │   └── services/     # 业务逻辑
│   └── tests/            # 测试用例
└── docs/                 # 文档目录
```

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

## 许可证

[MIT License](LICENSE)

## 联系方式

- 项目维护者：[LY-GGBOY](li1980303503@gmail.com)
- 项目主页：[GitHub](https://github.com/Ly-GGboy/ai-library)
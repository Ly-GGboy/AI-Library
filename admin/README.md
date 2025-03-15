# AI Library 管理后台

AI Library 管理后台是一个独立的管理界面，用于管理AI Library的内容、监控用户访问和查看用户反馈。

## 功能特性

- **仪表盘**: 总览网站访问数据、热门文档和用户反馈
- **访问统计**: 查看详细的访问统计和趋势分析
- **用户反馈**: 管理用户提交的反馈和建议

## 技术栈

- **前端框架**: Vue.js 3 + TypeScript
- **UI组件**: 纯CSS自定义组件
- **状态管理**: Vue Composition API
- **HTTP客户端**: Axios
- **构建工具**: Vite

## 开发指南

### 环境准备

确保已安装以下工具:

- Node.js (v14+)
- npm 或 yarn

### 安装依赖

```bash
npm install
# 或
yarn
```

### 启动开发服务器

```bash
npm run dev
# 或
yarn dev
```

或者使用提供的启动脚本:

```bash
chmod +x start.sh
./start.sh
```

### 构建生产版本

```bash
npm run build
# 或
yarn build
```

## API接口

管理后台通过以下API与后端通信:

- `GET /api/admin/dashboard` - 获取仪表盘数据
- `GET /api/admin/stats` - 获取访问统计数据
- `GET /api/admin/popular-documents` - 获取热门文档
- `GET /api/admin/feedback` - 获取用户反馈

## 项目结构

```
admin/
├── public/              # 静态资源
├── src/
│   ├── assets/          # 项目资源文件
│   ├── components/      # 共享组件
│   ├── router/          # 路由配置
│   ├── services/        # API服务
│   ├── views/           # 页面组件
│   ├── App.vue          # 根组件
│   └── main.ts          # 入口文件
├── .env                 # 环境变量
├── index.html           # HTML模板
├── package.json         # 项目依赖
├── tsconfig.json        # TypeScript配置
├── vite.config.ts       # Vite配置
└── README.md            # 项目文档
```

## 部署指南

1. 构建生产版本:
   ```bash
   npm run build
   ```

2. 将 `dist` 目录部署到Web服务器的适当位置

3. 确保API服务器正在运行并配置了正确的API基础URL

## 许可证

[MIT License](LICENSE)

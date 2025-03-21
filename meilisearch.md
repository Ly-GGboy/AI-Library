# MeiliSearch 搜索集成

AI Library 现在支持使用 MeiliSearch 进行全文搜索，这极大提高了搜索性能和用户体验。

## 什么是 MeiliSearch？

MeiliSearch 是一个开源、快速、强大的全文搜索引擎。与文件系统搜索相比，它提供：

- 毫秒级搜索响应时间
- 拼写容错（模糊搜索）
- 智能排名与相关性评分
- 过滤器和分面搜索
- 支持中文和其他多语言搜索

## 安装与设置

### 使用 Docker（推荐）

最简单的方法是使用 Docker 和 Docker Compose：

1. 确保已安装 Docker 和 Docker Compose
2. 运行 `docker-compose up -d meilisearch` 启动 MeiliSearch 服务
3. MeiliSearch 将在端口 7700 上运行

或者直接使用提供的脚本：

```bash
# 给脚本执行权限
chmod +x start_with_meilisearch.sh

# 启动 MeiliSearch 和应用服务器
./start_with_meilisearch.sh
```

### 手动安装

如果您不想使用 Docker，可以按照 [MeiliSearch 官方文档](https://docs.meilisearch.com/learn/getting_started/installation.html) 进行安装。

## 配置

默认配置应该能够正常工作，但您可以通过环境变量自定义：

- `MEILISEARCH_HOST`: MeiliSearch 服务器地址，默认为 `http://localhost:7700`
- `MEILISEARCH_API_KEY`: MeiliSearch 主密钥，默认为 `masterKey`

示例：

```bash
# 设置环境变量
export MEILISEARCH_HOST="http://meilisearch.example.com"
export MEILISEARCH_API_KEY="your-secret-key"

# 然后启动应用
python server/run_h2.py
```

## 构建索引

首次使用需要构建搜索索引：

1. 启动应用服务器
2. 访问 `/api/search/rebuild-index` API 端点 (POST 请求)
3. 等待索引构建完成

例如：

```bash
curl -X POST http://localhost:8000/api/search/rebuild-index
```

## 故障排除

如果 MeiliSearch 无法正常工作，系统会自动回退到文件系统搜索。您可以通过访问 `/api/search/status` 端点检查搜索服务状态。

常见问题：

1. MeiliSearch 服务未运行 - 确保 Docker 容器正在运行
2. 连接失败 - 检查 `MEILISEARCH_HOST` 环境变量
3. 索引为空 - 重新构建索引

## 性能比较

与文件系统搜索相比，MeiliSearch 提供了显著的性能改进：

- 搜索速度提高约 20-50 倍
- 更好的搜索相关性和排序
- 支持更复杂的查询和过滤

## 局限性

当前实现有一些限制：

1. PDF 文件仅索引标题，不索引内容
2. 未使用 MeiliSearch 的高级分面功能
3. 首次索引构建可能较慢

这些问题将在未来版本中改进。 
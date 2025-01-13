# Instructions

During you interaction with the user, if you find anything reusable in this project (e.g. version of a library, model name), especially about a fix to a mistake you made or a correction you received, you should take note in the `Lessons` section in the `.cursorrules` file so you will not make the same mistake again. 

You should also use the `.cursorrules` file as a scratchpad to organize your thoughts. Especially when you receive a new task, you should first review the content of the scratchpad, clear old different task if necessary, first explain the task, and plan the steps you need to take to complete the task. You can use todo markers to indicate the progress, e.g.
[X] Task 1
[ ] Task 2
Also update the progress of the task in the Scratchpad when you finish a subtask.
Especially when you finished a milestone, it will help to improve your depth of task accomplishment to use the scratchpad to reflect and plan.
The goal is to help you maintain a big picture as well as the progress of the task. Always refer to the Scratchpad when you plan the next step.

# Tools

Note all the tools are in python. So in the case you need to do batch processing, you can always consult the python files and write your own script.

## LLM

You always have an LLM at your side to help you with the task. For simple tasks, you could invoke the LLM by running the following command:
```
py310/bin/python ./tools/llm_api.py --prompt "What is the capital of France?"
```

But usually it's a better idea to check the content of the file and use the APIs in the `tools/llm_api.py` file to invoke the LLM if needed.

## Web browser

You could use the `tools/web_scraper.py` file to scrape the web.
```
py310/bin/python ./tools/web_scraper.py --max-concurrent 3 URL1 URL2 URL3
```
This will output the content of the web pages.

## Search engine

You could use the `tools/search_engine.py` file to search the web.
```
py310/bin/python ./tools/search_engine.py "your search keywords"
```
This will output the search results in the following format:
```
URL: https://example.com
Title: This is the title of the search result
Snippet: This is a snippet of the search result
```
If needed, you can further use the `web_scraper.py` file to scrape the web page content.

# Lessons

## User Specified Lessons

- You have a python venv in ./py310.
- Include info useful for debugging in the program output.
- Read the file before you try to edit it.
- Use LLM to perform flexible text understanding tasks. First test on a few files. After success, make it parallel.
- Keep article and image processing together in the same thread for better efficiency

## Cursor learned

- For website image paths, always use the correct relative path (e.g., 'images/filename.png') and ensure the images directory exists
- For search results, ensure proper handling of different character encodings (UTF-8) for international queries
- Add debug information to stderr while keeping the main output clean in stdout for better pipeline integration
- When using seaborn styles in matplotlib, use 'seaborn-v0_8' instead of 'seaborn' as the style name due to recent seaborn version changes

## Web Scraping Improvements

### Directory Structure
- Create flat directory structure for articles instead of nested ones
- Each article should have its own directory with the article name
- Store article content in a markdown file with the same name as the directory
- Keep images in an 'images' subdirectory within each article directory

### Content Processing
- Skip favicon.png when downloading images
- Remove Google notification content from articles
- Convert HTML to Markdown while preserving formatting
- Use relative paths for all internal links
- Handle Chinese characters and special symbols in filenames properly

### Performance & Reliability
- Implement rate limiting with random delays between requests
- Add retry mechanism for failed requests
- Handle HTTP 429 (Too Many Requests) with exponential backoff
- Process one section at a time for testing and validation

### Code Organization
- Use separate methods for different responsibilities (downloading, processing, saving)
- Maintain a set of processed URLs to avoid duplicates
- Implement proper error handling and logging
- Keep track of progress with informative log messages

# Version History

## Version 1.0 - Basic Scraping Functionality
- [X] Basic website structure scraping
- [X] Content organization in a clean directory structure
- [X] HTML to Markdown conversion with formatting preserved
- [X] Image downloading and proper path handling
- [X] Rate limiting and retry mechanism
- [X] Error handling and logging
- [X] Clean file naming and sanitization
- [X] Proper handling of nested content
- [X] Progress tracking and duplicate URL prevention

## Version 2.0 - Performance Improvements (Planning)
[ ] Multi-threading implementation
  - Use ThreadPoolExecutor to process articles in parallel
  - Each thread handles one complete article (including its images)
  - Thread-safe logging and URL tracking
  - Configurable number of worker threads

[ ] Resource management
  - Rate limiting across all threads
  - Graceful shutdown handling
  - Basic progress tracking per article

# Scratchpad

## Current Task: Restructuring Web Scraper

### Analysis of Current Issues
1. Thread granularity incorrect (article-based instead of series-based) ✓
2. Scattered image storage ✓
3. Complex directory structure ✓

### Required Changes
1. Directory Structure:
   - [X] Create all directories first
   - [X] Flatten article structure
   - [X] Centralize images in series assets folder

2. Threading Model:
   - [X] Series-based threading (each series is a thread)
   - [X] Single thread for menu listing
   - [X] Serial article processing within series
   - [X] Serial image processing within article

3. Processing Flow:
   - [X] First pass: create series directories
   - [X] Second pass: process series in parallel
   - [X] Process articles serially within each series
   - [X] Download images to series assets folder

### Implementation Plan
1. Directory Structure: ✓
   ```
   output_dir/
   ├── series_name/
   │   ├── assets/
   │   └── articles/
   ```

2. Processing Flow: ✓
   a. Create all series directories
   b. Process each series in parallel
   c. Process articles serially within each series
   d. Download images to series assets folder

3. Progress Tracking: ✓
   - Track series separately from articles
   - Show clear progress for each phase

### Code Changes Completed
1. Class Structure:
   - [X] Update initialization with series tracking
   - [X] Add series-specific directory creation
   - [X] Add series processing methods

2. Processing Logic:
   - [X] Implement series-level threading
   - [X] Implement serial article processing
   - [X] Update image storage to use series assets
   - [X] Update progress tracking for series

3. Main Flow:
   - [X] Update main scraping logic
   - [X] Update thread pool management
   - [X] Update error handling

### Next Steps
1. Testing:
   - [ ] Test with a small series first
   - [ ] Monitor memory usage
   - [ ] Verify directory structure
   - [ ] Check image paths in articles

# Current Task: Code Structure Analysis

[X] Task: Explain the code structure and logic of the web scraper

## Main Components
1. LiangLiangScraper class - Main scraper implementation
2. Threading and concurrency management
3. Content processing and markdown conversion
4. Resource management and rate limiting
5. Error handling and logging

## Progress
[X] Identify main components
[ ] Explain class structure
[ ] Explain threading model
[ ] Explain content processing
[ ] Explain error handling

# Current Task: Cloudflare Tunnel Deployment Plan

## Prerequisites
- [X] 已有阿里云域名
- [X] Cloudflare 账号设置
- [ ] Cloudflare Tunnel 配置
- [X] DNS 设置

## Deployment Steps

### 1. Cloudflare 账号设置
- [X] 注册 Cloudflare 账号
- [X] 添加域名到 Cloudflare
- [ ] 获取 Cloudflare API tokens

### 2. DNS 迁移方案
1. 获取 Cloudflare NS 地址：
   - [X] 登录 Cloudflare Dashboard
   - [X] 获取 NS 服务器地址（sarah.ns.cloudflare.com 和 jerry.ns.cloudflare.com）

2. 阿里云 DNS 设置：
   - [X] 更新 DNS 服务器
   - [X] DNS 迁移完成并验证成功

3. Cloudflare DNS 设置：
   - [X] 添加域名到 Cloudflare
   - [X] 验证域名所有权
   - [ ] 配置必要的 DNS 记录

### 3. Cloudflare Tunnel 配置

1. Docker 安装方案：
   - [ ] 安装 Docker Desktop for Mac：
     ```bash
     # 方法1：直接下载安装（推荐）
     # 访问 https://www.docker.com/products/docker-desktop/
     # 下载 Mac with Apple chip 版本
     # 双击下载的 .dmg 文件安装

     # 方法2：使用 Homebrew 安装（如果方法1不行）
     brew update
     brew cleanup
     brew install --cask docker

     # 如果下载太慢，可以先设置镜像源：
     git -C "$(brew --repo)" remote set-url origin https://mirrors.tuna.tsinghua.edu.cn/git/homebrew/brew.git
     ```
   - [ ] 启动 Docker Desktop：
     - 从应用程序文件夹打开 Docker Desktop
     - 等待 Docker Desktop 启动完成（状态栏图标变为运行状态）
   - [ ] 验证 Docker 安装：
     ```bash
     docker --version
     ```
   - [ ] 创建配置目录：
     ```bash
     mkdir -p ~/.cloudflared
     ```
   - [ ] 拉取官方镜像：
     ```bash
     docker pull cloudflare/cloudflared:latest
     ```
   - [ ] 验证安装：
     ```bash
     docker run cloudflare/cloudflared:latest version
     ```

2. 认证配置：
   - [ ] 运行认证命令：
     ```bash
     docker run -v ~/.cloudflared:/home/nonroot/.cloudflared cloudflare/cloudflared:latest tunnel login
     ```
   - [ ] 在浏览器中完成授权
   - [ ] 验证证书已保存在 ~/.cloudflared/cert.pem

3. 创建和配置隧道：
   - [ ] 创建隧道：
     ```bash
     docker run -v ~/.cloudflared:/home/nonroot/.cloudflared cloudflare/cloudflared:latest tunnel create ailibrary-tunnel
     ```
   - [ ] 创建配置文件 ~/.cloudflared/config.yml：
     ```yaml
     tunnel: <Tunnel-ID>
     credentials-file: /home/nonroot/.cloudflared/<Tunnel-ID>.json
     ingress:
       - hostname: ailibrary.space
         service: http://host.docker.internal:3000  # 假设本地服务运行在3000端口
       - service: http_status:404
     ```

4. 运行隧道：
   - [ ] 使用 Docker Compose 运行（创建 docker-compose.yml）：
     ```yaml
     version: '3'
     services:
       cloudflared:
         image: cloudflare/cloudflared:latest
         container_name: cloudflared
         restart: unless-stopped
         command: tunnel run
         volumes:
           - ~/.cloudflared:/home/nonroot/.cloudflared
         environment:
           - TUNNEL_TOKEN=your-tunnel-token
     ```

5. DNS 配置：
   - [ ] 添加 CNAME 记录指向隧道
   - [ ] 验证连接是否成功

注意事项：
- host.docker.internal 是 Docker 提供的特殊DNS名称，用于从容器内访问宿主机
- 配置文件中的端口号需要与本地服务的实际端口匹配
- 所有证书和配置文件都会保存在 ~/.cloudflared 目录中
- Docker 容器应该设置为自动重启，以确保服务的可靠性

### 4. 安全设置
- [ ] 启用 Cloudflare SSL/TLS
- [ ] 配置访问策略
- [ ] 设置 Web 应用防火墙规则
- [ ] 启用 DDoS 防护

### 5. 监控和维护
- [ ] 设置监控告警
- [ ] 配置日志收集
- [ ] 制定备份策略

## Implementation Details

我们将按以下步骤详细实施：

# Current Task: PDF Support Development Plan

## Analysis of Current System

### Current Document Handling
1. File Types:
   - [X] Markdown (.md) support
   - [ ] PDF support needed
   - [X] Image support
   - [X] Binary file handling infrastructure exists

### Components to Modify
1. Backend:
   - DocService: Handles file operations and caching
   - API Routes: Handles file serving
   - MIME type detection already implemented

2. Frontend:
   - MarkdownViewer component for MD files
   - Need new PDFViewer component
   - DocView handles document display logic

## Development Plan

### Phase 1: Backend PDF Support
- [ ] Add PDF file detection in DocService
- [ ] Update file response handling for PDFs
- [ ] Add PDF metadata extraction (title, pages, etc.)
- [ ] Implement PDF caching strategy

### Phase 2: Frontend PDF Viewer
- [ ] Create PDFViewer Vue component
- [ ] Integrate PDF.js for rendering
- [ ] Implement viewer controls (zoom, page navigation)
- [ ] Add PDF loading states and error handling

### Phase 3: Integration
- [ ] Update DocView to handle PDF files
- [ ] Modify document tree to show PDF icons
- [ ] Add PDF-specific navigation controls
- [ ] Implement PDF search functionality

### Phase 4: Testing & Optimization
- [ ] Test PDF loading performance
- [ ] Implement lazy loading for large PDFs
- [ ] Add PDF caching in browser
- [ ] Test mobile responsiveness

## Implementation Steps

1. Backend Changes:
   ```python
   # Required changes in doc_service.py
   - Update get_file_response() for PDF handling
   - Add PDF metadata extraction
   - Implement PDF-specific caching
   ```

2. Frontend Changes:
   ```typescript
   # New components needed
   - PDFViewer.vue
   - PDFControls.vue
   - PDFThumbnails.vue (optional)
   ```

3. Dependencies to Add:
   - PDF.js for PDF rendering
   - PDF metadata extraction library for backend

## Progress Tracking
[ ] Phase 1: Backend PDF Support
[ ] Phase 2: Frontend PDF Viewer
[ ] Phase 3: Integration
[ ] Phase 4: Testing & Optimization

## PDF Viewer Improvements
- When implementing PDF viewer functionality, ensure bookmark selection is handled properly with proper state management
- Implement proper navigation controls with clear visual feedback
- Handle PDF loading states and errors gracefully
- Test PDF viewer functionality across different document sizes and types

## Markdown Processing
- When splitting markdown files, maintain proper header hierarchy
- Preserve metadata and front matter when processing markdown files
- Handle special characters and formatting during file operations
- Implement proper error handling for file operations
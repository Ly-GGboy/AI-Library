import os
import re
import json
import time
import math
import aiofiles
import asyncio
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from meilisearch_python_sdk import AsyncClient

class MeiliSearchService:
    """MeiliSearch 搜索服务实现"""
    
    def __init__(self):
        """初始化 MeiliSearch 搜索服务"""
        # MeiliSearch 连接配置
        self.host = os.environ.get("MEILISEARCH_HOST", "http://localhost:7700")
        self.api_key = os.environ.get("MEILISEARCH_API_KEY", "masterKey")
        self.index_name = "documents"
        
        # 文档和缓存目录
        self.docs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static", "docs")
        self.cache_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static", "cache")
        
        # 确保缓存目录存在
        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(self.docs_dir, exist_ok=True)
        
        # 客户端实例在初始化时不创建，而是在需要时异步创建
        self.client = None
        self.is_initialized = False
        
        print(f"[INFO] MeiliSearch 服务初始化完成，主机: {self.host}")
    
    async def get_client(self):
        """获取或创建 MeiliSearch 客户端"""
        if self.client is None:
            try:
                self.client = AsyncClient(self.host, self.api_key)
                print(f"[INFO] MeiliSearch 客户端创建成功，连接到 {self.host}")
            except Exception as e:
                print(f"[ERROR] 连接 MeiliSearch 失败: {str(e)}")
                raise
        return self.client
    
    async def init_search_engine(self):
        """初始化搜索引擎，创建索引和设置设置"""
        if self.is_initialized:
            return
            
        try:
            client = await self.get_client()
            
            # 检查索引是否存在
            indexes = await client.get_indexes()
            index_exists = False
            if indexes:
                index_exists = any(index.uid == self.index_name for index in indexes)
            
            if not index_exists:
                print(f"[INFO] 创建新索引: {self.index_name}")
                await client.create_index(self.index_name)
            
            # 获取索引
            index = await client.get_index(self.index_name)
            print(f"获取到索引: {self.index_name}")
            
            # 按照测试类的顺序设置属性
            print("\n设置可过滤属性...")
            await index.update_filterable_attributes(['type'])
            
            print("\n设置可排序属性...")
            await index.update_sortable_attributes(['name'])
            
            self.is_initialized = True
            print(f"[INFO] MeiliSearch 索引设置完成")
            
        except Exception as e:
            print(f"[ERROR] 初始化 MeiliSearch 失败: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _generate_safe_id(self, file_path: str) -> str:
        """生成安全的文档ID"""
        # 使用文件路径的MD5作为ID
        return hashlib.md5(file_path.encode()).hexdigest()

    async def build_index(self):
        """构建搜索索引"""
        await self.init_search_engine()
        
        print(f"[DEBUG] 开始构建 MeiliSearch 索引，文档目录: {self.docs_dir}")
        
        # 使用异步方式收集文件
        async def collect_files():
            all_files = []
            for root, _, files in os.walk(self.docs_dir):
                for file in files:
                    if file.startswith('.'):  # 跳过隐藏文件
                        continue
                    file_path = os.path.join(root, file)
                    all_files.append(file_path)
            return all_files
        
        # 异步处理单个文件
        async def process_file(file_path: str):
            try:
                rel_path = os.path.relpath(file_path, self.docs_dir).replace('\\', '/')
                file_ext = os.path.splitext(file_path)[1][1:].lower()
                file_name = os.path.basename(file_path)
                
                # 使用安全的ID
                doc_id = self._generate_safe_id(rel_path)
                
                # 简化文档结构
                document = {
                    'id': doc_id,
                    'path': rel_path,
                    'name': file_name,
                    'type': file_ext
                }
                
                # 处理 Markdown 文件
                if file_ext == 'md':
                    try:
                        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                            content = await f.read()
                    except UnicodeDecodeError:
                        async with aiofiles.open(file_path, 'r', encoding='gbk') as f:
                            content = await f.read()
                    document['content'] = content
                    return document, 'md'
                
                # 处理 PDF 文件
                elif file_ext == 'pdf':
                    document['content'] = file_name  # 只索引文件名
                    return document, 'pdf'
                
                return None, None
            except Exception as e:
                print(f"[ERROR] 处理文件 {file_path} 时出错: {e}")
                return None, None
        
        # 异步处理文件批次
        async def process_batch(batch_files, batch_index, total_batches):
            batch_start_time = time.time()
            batch_documents = []
            md_count = pdf_count = error_count = 0
            
            # 并行处理批次中的文件
            tasks = [process_file(file_path) for file_path in batch_files]
            results = await asyncio.gather(*tasks)
            
            for doc, doc_type in results:
                if doc is not None:
                    batch_documents.append(doc)
                    if doc_type == 'md':
                        md_count += 1
                    elif doc_type == 'pdf':
                        pdf_count += 1
                else:
                    error_count += 1
            
            if batch_documents:
                try:
                    print(f"\n处理批次 {batch_index + 1}/{total_batches}...")
                    client = await self.get_client()
                    index = await client.get_index(self.index_name)
                    
                    task = await index.add_documents(batch_documents)
                    print(f"[DEBUG] 添加文档任务ID: {task.task_uid}")
                    
                    # 等待任务完成
                    while True:
                        task_info = await client.get_task(task.task_uid)
                        if task_info.status != 'enqueued' and task_info.status != 'processing':
                            break
                        await asyncio.sleep(0.5)
                    
                    if task_info.status != 'succeeded':
                        print(f"[ERROR] 添加文档任务失败: {task_info.error}")
                        error_count += len(batch_documents)
                    else:
                        print(f"[INFO] 已添加 {len(batch_documents)} 个文档")
                    
                except Exception as e:
                    print(f"[ERROR] 处理批次失败: {str(e)}")
                    error_count += len(batch_documents)
            
            batch_time = time.time() - batch_start_time
            return {
                'documents': len(batch_documents),
                'md_count': md_count,
                'pdf_count': pdf_count,
                'errors': error_count,
                'time': batch_time
            }
        
        # 主处理流程
        try:
            # 收集文件
            all_files = await collect_files()
            total_files = len(all_files)
            print(f"[INFO] 发现 {total_files} 个文件需要索引")
            
            # 分批处理，每批20个文件
            batch_size = 20
            batches = [all_files[i:i + batch_size] for i in range(0, len(all_files), batch_size)]
            
            # 并行处理批次，但限制并发数
            max_concurrent_batches = 3  # 最多同时处理3个批次
            semaphore = asyncio.Semaphore(max_concurrent_batches)
            
            async def process_batch_with_semaphore(batch, index, total):
                async with semaphore:
                    return await process_batch(batch, index, total)
            
            # 启动所有批次的处理
            batch_tasks = [
                process_batch_with_semaphore(batch, i, len(batches))
                for i, batch in enumerate(batches)
            ]
            
            # 等待所有批次完成
            batch_results = await asyncio.gather(*batch_tasks)
            
            # 汇总结果
            total_docs = sum(r['documents'] for r in batch_results)
            total_md = sum(r['md_count'] for r in batch_results)
            total_pdf = sum(r['pdf_count'] for r in batch_results)
            total_errors = sum(r['errors'] for r in batch_results)
            total_time = sum(r['time'] for r in batch_results)
            
            print(f"\n[INFO] 索引构建完成:")
            print(f"总文件数: {total_docs}")
            print(f"Markdown文件: {total_md}")
            print(f"PDF文件: {total_pdf}")
            print(f"错误数: {total_errors}")
            print(f"总耗时: {total_time:.2f}秒")
            
            # 执行测试查询
            print("\n[DEBUG] 执行测试查询...")
            client = await self.get_client()
            index = await client.get_index(self.index_name)
            
            # 获取索引统计
            stats = await index.get_stats()
            print(f"[DEBUG] 索引统计: {stats.model_dump()}")
            
            # 测试搜索
            search_results = await index.search(
                "",
                limit=10,
                offset=0,
                attributes_to_retrieve=["id", "name", "type", "path"]
            )
            
            print("\n[DEBUG] 索引中的前10条文档:")
            for i, doc in enumerate(search_results.hits, 1):
                print(f"{i}. {doc.get('name')} (类型: {doc.get('type')}, ID: {doc.get('id')}, 路径: {doc.get('path')})")
            print(f"\n[DEBUG] 索引中总文档数: {search_results.estimated_total_hits}")
            
            return {
                "indexed_files": total_docs,
                "markdown_files": total_md,
                "pdf_files": total_pdf,
                "errors": total_errors,
                "time_taken": total_time
            }
            
        except Exception as e:
            print(f"[ERROR] 构建索引时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "indexed_files": 0,
                "errors": 1,
                "error_message": str(e)
            }
    
    async def search(
        self, 
        q: str,
        page: int = 1,
        per_page: int = 10,
        sort_by: str = "relevance",
        sort_order: str = "desc",
        doc_type: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> Dict:
        """搜索文档"""
        await self.init_search_engine()
        
        client = await self.get_client()
        index = await client.get_index(self.index_name)
        
        # 构建搜索选项
        search_options = {
            'limit': per_page,
            'offset': (page - 1) * per_page,
            'attributes_to_retrieve': ["id", "name", "content", "type", "path"]  # 移除 last_modified
        }
        
        # 构建排序规则
        if sort_by and sort_by != 'relevance':
            search_options['sort'] = [f'{sort_by}:{sort_order}']
        
        # 构建过滤条件
        filter_conditions = []
        
        if doc_type and doc_type != 'all':
            filter_conditions.append(f'type = "{doc_type}"')
        
        if filter_conditions:
            search_options['filter'] = ' AND '.join(filter_conditions)
        
        # 执行搜索
        print(f"[DEBUG] MeiliSearch 搜索参数: q='{q}', 选项={search_options}")
        try:
            search_results = await index.search(q, **search_options)
        except Exception as e:
            print(f"[ERROR] 使用MeiliSearch搜索失败: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
        
        # 处理搜索结果
        results = []
        for hit in search_results.hits:
            matches = []
            
            # 添加文件名匹配
            matches.append({
                "type": "title",
                "text": hit.get('name', ''),
                "line": 0
            })
            
            # 添加内容匹配 (如果是 markdown)
            if hit.get('type') == 'md' and hit.get('content'):
                content = hit.get('content', '')
                lines = content.split('\n')
                
                # 简单匹配前3个包含查询词的行
                matched_lines = 0
                for i, line in enumerate(lines, 1):
                    if q.lower() in line.lower() and matched_lines < 2:
                        context_start = max(0, i - 2)
                        context_end = min(len(lines), i + 2)
                        context = '\n'.join(lines[context_start:context_end])
                        
                        matches.append({
                            "type": "content",
                            "text": context,
                            "line": i
                        })
                        matched_lines += 1
            
            # 不要添加空匹配结果
            if matches:
                results.append({
                    "path": hit.get('path', ''),
                    "name": hit.get('name', ''),
                    "matches": matches,
                    "relevance_score": 1.0  # MeiliSearch 不直接提供分数，使用默认值
                })
        
        # 构造分页信息
        total = search_results.estimated_total_hits
        total_pages = math.ceil(total / per_page) if total > 0 else 0
        
        return {
            "results": results,
            "total": total,
            "total_matches": total,  # MeiliSearch 不区分文档数和匹配数
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages
        }
    
    async def get_suggestions(
        self, 
        q: str, 
        limit: int = 5,
        doc_type: Optional[str] = None
    ) -> List[str]:
        """获取搜索建议"""
        await self.init_search_engine()
        
        client = await self.get_client()
        index = await client.get_index(self.index_name)
        
        # 构建搜索选项
        search_options = {
            'limit': limit,
            'attributes_to_retrieve': ["name", "headers"]
        }
        
        # 文档类型过滤
        if doc_type and doc_type != 'all':
            search_options['filter'] = f'type = "{doc_type}"'
        
        # 执行搜索
        try:
            print(f"[DEBUG] MeiliSearch 搜索建议参数: q='{q}', 选项={search_options}")
            search_results = await index.search(q, **search_options)
        except Exception as e:
            print(f"[ERROR] 获取搜索建议失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
        
        # 从结果中提取建议
        suggestions = []
        for hit in search_results.hits:
            # 添加文件名作为建议
            file_name = os.path.splitext(hit.get('name', ''))[0]
            if file_name and len(suggestions) < limit:
                suggestions.append(file_name)
            
            # 添加标题作为建议
            for header in hit.get('headers', []):
                if q.lower() in header.lower() and len(suggestions) < limit:
                    suggestions.append(header)
        
        return suggestions[:limit]
    
    async def check_status(self):
        """检查 MeiliSearch 服务状态"""
        try:
            client = await self.get_client()
            
            # 首先检查服务是否可用
            try:
                health = await client.health()
                status = health.status
            except Exception as e:
                print(f"[ERROR] 检查MeiliSearch健康状态失败: {str(e)}")
                return {"status": "error", "error": f"健康检查失败: {str(e)}"}
            
            # 检查索引状态
            index_exists = False
            document_count = 0
            try:
                # 先检查索引是否存在
                indexes = await client.get_indexes()
                if indexes:
                    index_exists = any(index.uid == self.index_name for index in indexes)
                
                if index_exists:
                    # 索引存在，获取统计信息
                    index = await client.get_index(self.index_name)
                    stats = await index.get_stats()
                    document_count = stats.number_of_documents
            except Exception as e:
                print(f"[WARNING] 获取索引状态失败: {str(e)}")
                import traceback
                traceback.print_exc()
            
            return {
                "status": status,
                "index_exists": index_exists,
                "document_count": document_count
            }
        except Exception as e:
            print(f"[ERROR] 检查MeiliSearch状态时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e)}
    
    async def test_index_stats(self):
        """测试获取索引统计信息结构"""
        try:
            client = await self.get_client()
            index = await client.get_index(self.index_name)
            stats = await index.get_stats()
            
            print(f"[DEBUG] Stats对象类型: {type(stats)}")
            print(f"[DEBUG] Stats对象属性: {dir(stats)}")
            print(f"[DEBUG] Stats对象字符串表示: {str(stats)}")
            print(f"[DEBUG] Stats对象字典表示: {stats.model_dump()}")
            
            return stats
        except Exception as e:
            print(f"[ERROR] 测试获取索引统计信息失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return None 
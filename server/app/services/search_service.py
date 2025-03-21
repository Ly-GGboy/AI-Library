import os
from typing import List, Dict, Optional
import re
from datetime import datetime
import aiofiles
from math import ceil
import json
from pathlib import Path

class SearchService:
    def __init__(self):
        """初始化搜索服务"""
        self.docs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static", "docs")
        self.cache_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static", "cache")
        self.index_path = os.path.join(self.cache_dir, "search_index.json")
        self.file_index = {}
        self.content_cache = {}
        self.max_cache_size = 10  # 最大缓存文件数
        
        # 确保缓存目录存在
        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(self.docs_dir, exist_ok=True)
        
        # 加载索引
        self._load_index()
        
        # 检查是否为空索引
        self.is_empty = len(self.file_index) == 0
        print(f"[INFO] 搜索服务初始化完成，索引文件数: {len(self.file_index)}, 是否为空: {self.is_empty}")

    def _load_index(self):
        """加载搜索索引"""
        try:
            if os.path.exists(self.index_path):
                print(f"[DEBUG] 加载搜索索引: {self.index_path}")
                with open(self.index_path, 'r', encoding='utf-8') as f:
                    self.file_index = json.load(f)
                print(f"[DEBUG] 索引加载成功，包含 {len(self.file_index)} 个文件")
                
                # 打印索引中的文件类型统计
                file_types = {}
                for rel_path, file_data in self.file_index.items():
                    file_type = file_data.get('type', 'unknown')
                    file_types[file_type] = file_types.get(file_type, 0) + 1
                
                print(f"[DEBUG] 索引文件类型统计: {file_types}")
            else:
                print(f"[DEBUG] 索引文件不存在: {self.index_path}")
                self.file_index = {}
        except Exception as e:
            print(f"[ERROR] 加载索引时出错: {e}")
            self.file_index = {}

    async def _save_index(self):
        """保存搜索索引"""
        try:
            print(f"[DEBUG] 保存搜索索引到: {self.index_path}, 包含 {len(self.file_index)} 个文件")
            with open(self.index_path, 'w', encoding='utf-8') as f:
                json.dump(self.file_index, f, ensure_ascii=False, indent=2)
            print(f"[DEBUG] 索引保存成功")
        except Exception as e:
            print(f"[ERROR] 保存索引时出错: {e}")

    async def _update_index(self, file_path: str, content: str):
        """更新文件索引"""
        rel_path = os.path.relpath(file_path, self.docs_dir).replace('\\', '/')
        
        # 提取关键信息
        words = set(re.findall(r'\w+', content.lower()))
        headers = re.findall(r'^#+\s+(.+)$', content, re.MULTILINE)
        
        self.file_index[rel_path] = {
            'words': list(words),
            'headers': headers,
            'last_modified': os.path.getmtime(file_path),
            'type': os.path.splitext(file_path)[1][1:],
            'size': os.path.getsize(file_path)
        }
        
        await self._save_index()

    async def _get_file_content(self, file_path: str) -> str:
        """获取文件内容，使用缓存"""
        try:
            stat = os.stat(file_path)
            cache_key = f"{file_path}:{stat.st_mtime}"
            
            # 检查缓存
            if cache_key in self.content_cache:
                return self.content_cache[cache_key]
            
            # 读取文件
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            
            # 更新缓存和索引
            self.content_cache[cache_key] = content
            await self._update_index(file_path, content)
            
            # 限制缓存大小
            if len(self.content_cache) > self.max_cache_size:  # 最多缓存max_cache_size个文件
                self.content_cache.pop(next(iter(self.content_cache)))
            
            return content
            
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return ""

    def _calculate_relevance(self, query_words: set, file_data: dict) -> float:
        """计算文档相关度"""
        score = 0
        file_words = set(file_data['words'])
        
        # 词匹配得分
        word_matches = query_words & file_words
        score += len(word_matches) * 1.0
        
        # 标题匹配加权
        for header in file_data['headers']:
            header_lower = header.lower()
            # 检查每个查询词是否在标题中
            for word in query_words:
                if word in header_lower:
                    score += 2.0
                    break
        
        return score

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
        print(f"[DEBUG] 开始搜索，参数: q='{q}', doc_type='{doc_type}', 索引文件数量: {len(self.file_index)}")
        
        results = []
        q = q.lower()
        # 改进中文处理，使用更宽松的正则表达式
        query_words = set(re.findall(r'[\w\u4e00-\u9fff]+', q))
        total_matches = 0
        
        print(f"[DEBUG] 提取的搜索关键词: {query_words}")
        
        # 过滤和搜索文件
        for rel_path, file_data in self.file_index.items():
            try:
                # 类型过滤
                if doc_type and doc_type != 'all' and file_data['type'] != doc_type:
                    continue
                
                # 日期过滤
                file_time = datetime.fromtimestamp(file_data['last_modified'])
                if date_from:
                    from_date = datetime.fromisoformat(date_from)
                    if file_time < from_date:
                        continue
                if date_to:
                    to_date = datetime.fromisoformat(date_to)
                    if file_time > to_date:
                        continue
                
                # 获取文件名和类型
                file_name = os.path.basename(rel_path)
                file_type = file_data['type']
                
                print(f"[DEBUG] 检查文件: {rel_path}, 类型: {file_type}")
                
                # PDF 文件只搜索文件名
                if file_type == 'pdf':
                    # 检查文件名是否匹配搜索词
                    name_matches = [word for word in query_words if word in file_name.lower()]
                    if name_matches:
                        print(f"[DEBUG] PDF文件名匹配: {file_name}, 匹配词: {name_matches}")
                        results.append({
                            "path": rel_path,
                            "name": file_name,
                            "matches": [{
                                "type": "title",
                                "text": file_name,
                                "line": 0
                            }],
                            "last_modified": datetime.fromtimestamp(file_data['last_modified']).isoformat(),
                            "relevance_score": len(name_matches)
                        })
                        total_matches += 1
                    continue
                
                # 非 PDF 文件进行全文搜索
                relevance_score = self._calculate_relevance(query_words, file_data)
                print(f"[DEBUG] 文件相关度: {rel_path}, 得分: {relevance_score}")
                
                if relevance_score > 0:
                    abs_path = os.path.join(self.docs_dir, rel_path)
                    content = await self._get_file_content(abs_path)
                    
                    # 提取匹配上下文
                    matches = []
                    
                    # 先检查文件名是否匹配
                    name_matches = [word for word in query_words if word in file_name.lower()]
                    if name_matches:
                        matches.append({
                            "type": "title",
                            "text": file_name,
                            "line": 0
                        })
                    
                    # 然后检查内容匹配（仅对Markdown文件）
                    if file_type == 'md':
                        lines = content.split('\n')
                        for i, line in enumerate(lines, 1):
                            if any(word in line.lower() for word in query_words):
                                context_start = max(0, i - 2)
                                context_end = min(len(lines), i + 2)
                                context = '\n'.join(lines[context_start:context_end])
                                
                                matches.append({
                                    "type": "content",
                                    "text": context,
                                    "line": i
                                })
                                
                                if len(matches) >= 3:  # 限制每个文件的匹配数
                                    break
                    
                    if matches:
                        print(f"[DEBUG] 找到内容匹配: {rel_path}, 匹配数: {len(matches)}")
                        results.append({
                            "path": rel_path,
                            "name": file_name,
                            "matches": matches,
                            "last_modified": datetime.fromtimestamp(file_data['last_modified']).isoformat(),
                            "relevance_score": relevance_score
                        })
                        total_matches += len(matches)
                        
            except Exception as e:
                print(f"[ERROR] 处理文件 {rel_path} 时出错: {e}")
                continue

        # 排序结果
        if sort_by == "date":
            results.sort(key=lambda x: x["last_modified"], reverse=(sort_order == "desc"))
        elif sort_by == "name":
            results.sort(key=lambda x: x["name"], reverse=(sort_order == "desc"))
        else:  # relevance
            results.sort(key=lambda x: x["relevance_score"], reverse=True)

        # 分页
        total = len(results)
        total_pages = ceil(total / per_page)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_results = results[start_idx:end_idx]
        
        print(f"[DEBUG] 搜索完成，总匹配文件: {total}, 总匹配数: {total_matches}, 页数: {total_pages}")

        return {
            "results": paginated_results,
            "total": total,
            "total_matches": total_matches,
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
        suggestions = set()
        q = q.lower()
        
        for rel_path, file_data in self.file_index.items():
            # 类型过滤
            if doc_type and doc_type != 'all' and file_data['type'] != doc_type:
                continue
            
            # 获取文件名和类型
            file_name = os.path.splitext(os.path.basename(rel_path))[0]
            file_type = file_data['type']
            
            # 从文件名中提取建议
            if q in file_name.lower():
                suggestions.add(file_name)
                
            # 对非 PDF 文件，从标题中提取建议
            if file_type != 'pdf':
                # 从标题中提取建议
                for header in file_data['headers']:
                    if q in header.lower():
                        suggestions.add(header)
            
            if len(suggestions) >= limit:
                break
        
        return list(suggestions)[:limit]

    async def build_index(self):
        """构建搜索索引"""
        print(f"[DEBUG] 开始构建搜索索引，文档目录: {self.docs_dir}")
        
        # 清空当前索引
        self.file_index = {}
        file_count = 0
        md_count = 0
        pdf_count = 0
        
        # 遍历文档目录
        for root, _, files in os.walk(self.docs_dir):
            for file in files:
                if file.startswith('.'):  # 跳过隐藏文件
                    continue
                    
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, self.docs_dir).replace('\\', '/')
                
                # 获取文件类型
                file_ext = os.path.splitext(file)[1][1:].lower()
                
                try:
                    # 处理 Markdown 文件
                    if file_ext == 'md':
                        try:
                            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                                content = await f.read()
                        except UnicodeDecodeError:
                            # 尝试其他编码
                            async with aiofiles.open(file_path, 'r', encoding='gbk') as f:
                                content = await f.read()
                            
                        # 提取关键信息 - 改进中文处理
                        # 使用更宽松的正则表达式，包括中文字符
                        words = set(re.findall(r'[\w\u4e00-\u9fff]+', content.lower()))
                        headers = re.findall(r'^#+\s+(.+)$', content, re.MULTILINE)
                        
                        self.file_index[rel_path] = {
                            'words': list(words),
                            'headers': headers,
                            'last_modified': os.path.getmtime(file_path),
                            'type': file_ext,
                            'size': os.path.getsize(file_path)
                        }
                        md_count += 1
                        print(f"[DEBUG] 已索引 Markdown 文件: {rel_path}, 词数: {len(words)}, 标题数: {len(headers)}")
                    
                    # 处理 PDF 文件
                    elif file_ext == 'pdf':
                        # 对 PDF 文件，只索引文件名
                        file_name = os.path.basename(file_path)
                        # 改进中文处理
                        words = set(re.findall(r'[\w\u4e00-\u9fff]+', file_name.lower()))
                        
                        self.file_index[rel_path] = {
                            'words': list(words),
                            'headers': [],
                            'last_modified': os.path.getmtime(file_path),
                            'type': file_ext,
                            'size': os.path.getsize(file_path)
                        }
                        pdf_count += 1
                        print(f"[DEBUG] 已索引 PDF 文件: {rel_path}, 文件名词数: {len(words)}")
                    else:
                        print(f"[DEBUG] 跳过不支持的文件类型: {rel_path}, 类型: {file_ext}")
                        continue
                    
                    file_count += 1
                except Exception as e:
                    print(f"[ERROR] 索引文件 {file_path} 时出错: {e}")
                    import traceback
                    traceback.print_exc()
        
        # 保存索引
        await self._save_index()
        print(f"[DEBUG] 搜索索引构建完成，总文件数: {file_count}, Markdown: {md_count}, PDF: {pdf_count}")
        print(f"[DEBUG] 索引文件保存至: {self.index_path}") 
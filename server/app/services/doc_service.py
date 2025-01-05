import os
import json
import time
from typing import Dict, List, Optional, Tuple, Set
import aiofiles
from datetime import datetime
import mimetypes
from asyncio import Lock
from contextlib import asynccontextmanager
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class DocChangeHandler(FileSystemEventHandler):
    def __init__(self, doc_service):
        self.doc_service = doc_service
        self.debounce_time = 1.0  # 防抖时间窗口
        self.last_event_time = 0
        self.modified_files: Set[str] = set()

    def on_any_event(self, event):
        current_time = time.time()
        if current_time - self.last_event_time > self.debounce_time:
            self.last_event_time = current_time
            # 清除相关缓存
            if event.is_directory:
                self.doc_service.invalidate_tree_cache()
                self.doc_service.invalidate_recent_docs_cache()
            else:
                rel_path = os.path.relpath(event.src_path, self.doc_service.docs_dir)
                self.doc_service.invalidate_doc_cache(rel_path)

class DocService:
    def __init__(self):
        self.docs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static", "docs")
        os.makedirs(self.docs_dir, exist_ok=True)
        mimetypes.init()

        # 缓存相关
        self._doc_tree_cache = None
        self._doc_tree_last_modified = 0
        self._doc_tree_version = 0
        
        self._content_cache = {}
        self._content_cache_size = 100    # 最多缓存100个文档
        self._content_cache_ttl = 3600    # 缓存1小时
        
        self._recent_docs_cache = None
        self._recent_docs_last_check = 0
        self._recent_docs_ttl = 1800      # 缓存30分钟
        
        self._breadcrumb_cache = {}
        
        # 缓存控制
        self._global_cache_lock = Lock()
        self._cache_locks = {}
        self._cache_version = 0
        self._cache_metadata = {}
        
        # 文件监控
        self._setup_file_watcher()

    def _setup_file_watcher(self):
        """设置文件系统监控"""
        self.event_handler = DocChangeHandler(self)
        self.observer = Observer()
        self.observer.schedule(self.event_handler, self.docs_dir, recursive=True)
        self.observer.start()

    @asynccontextmanager
    async def _cache_lock(self, cache_key: str):
        """获取特定缓存项的锁"""
        if cache_key not in self._cache_locks:
            self._cache_locks[cache_key] = Lock()
        async with self._cache_locks[cache_key]:
            yield

    def _update_cache_metadata(self, cache_key: str, data: Dict):
        """更新缓存元数据"""
        self._cache_metadata[cache_key] = {
            "last_access": time.time(),
            "access_count": self._cache_metadata.get(cache_key, {}).get("access_count", 0) + 1,
            "size": len(str(data))  # 简单的大小估算
        }

    def invalidate_tree_cache(self):
        """使文档树缓存失效"""
        self._doc_tree_cache = None
        self._cache_version += 1

    def invalidate_doc_cache(self, path: str):
        """使特定文档的缓存失效"""
        if path in self._content_cache:
            del self._content_cache[path]
        if path in self._breadcrumb_cache:
            del self._breadcrumb_cache[path]
        self._cache_version += 1

    def invalidate_recent_docs_cache(self):
        """使最近文档缓存失效"""
        self._recent_docs_cache = None
        self._cache_version += 1

    async def _cleanup_expired_cache(self):
        """清理过期缓存"""
        async with self._global_cache_lock:
            current_time = time.time()
            # 清理过期的文档内容缓存
            expired_keys = [
                k for k, v in self._content_cache.items()
                if current_time - v["cache_time"] > self._content_cache_ttl
            ]
            for key in expired_keys:
                del self._content_cache[key]
                if key in self._cache_metadata:
                    del self._cache_metadata[key]

    def _extract_number(self, name: str) -> Tuple:
        """从文件名或目录名中提取序号，用于排序"""
        # 移除 .md 后缀
        name = name.replace('.md', '')
        
        # 尝试提取序号
        parts = name.split('_', 1)
        if len(parts) != 2:
            return (float('inf'), name)  # 无序号的排在最后
        
        number = parts[0]
        # 处理多级序号，如 "1.1"、"1.2"
        try:
            if '.' in number:
                return tuple(map(int, number.split('.')))
            return (int(number), 0)
        except ValueError:
            return (float('inf'), name)

    def _sort_items(self, items: List[Dict]) -> List[Dict]:
        """排序文件或目录列表"""
        return sorted(items, key=lambda x: self._extract_number(x["name"]))

    async def get_file_response(self, path: str) -> tuple[str, str]:
        """获取文件路径和MIME类型"""
        file_path = os.path.join(self.docs_dir, path)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {path}")
            
        # 获取文件的MIME类型
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = 'application/octet-stream'
            
        return file_path, mime_type

    async def get_doc_tree(self) -> Dict:
        """获取文档目录树，带缓存和并发控制"""
        async with self._cache_lock("tree"):
            current_mtime = os.path.getmtime(self.docs_dir)
            
            if (self._doc_tree_cache and 
                current_mtime <= self._doc_tree_last_modified and
                self._doc_tree_version == self._cache_version):
                return self._doc_tree_cache

            tree = {"name": "root", "children": []}
            for root, dirs, files in os.walk(self.docs_dir):
                # 跳过隐藏文件夹
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                files = [f for f in files if not f.startswith('.') and f.endswith('.md')]
                
                # 计算相对路径
                rel_path = os.path.relpath(root, self.docs_dir)
                if rel_path == '.':
                    current_node = tree
                else:
                    # 找到或创建父节点
                    parts = rel_path.split(os.sep)
                    current_node = tree
                    for part in parts:
                        found = False
                        for child in current_node["children"]:
                            if child["name"] == part:
                                current_node = child
                                found = True
                                break
                        if not found:
                            new_node = {"name": part, "children": []}
                            current_node["children"].append(new_node)
                            current_node = new_node
                
                # 添加文件
                file_nodes = []
                for file in files:
                    file_path = os.path.join(rel_path, file)
                    if rel_path == '.':
                        file_path = file
                    file_nodes.append({
                        "name": file,
                        "path": file_path.replace('\\', '/'),
                        "type": "file"
                    })
                
                # 对文件节点排序并添加到当前节点
                current_node["children"].extend(self._sort_items(file_nodes))
                
                # 对当前节点的所有子节点排序
                current_node["children"] = self._sort_items(current_node["children"])

            self._doc_tree_cache = tree
            self._doc_tree_last_modified = current_mtime
            self._doc_tree_version = self._cache_version
            return tree

    async def get_doc_content(self, path: str) -> Dict:
        """获取文档内容，带缓存一致性控制"""
        async with self._cache_lock(f"content:{path}"):
            file_path = os.path.join(self.docs_dir, path)
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Document not found: {path}")

            current_mtime = os.path.getmtime(file_path)
            cache_key = path
            
            # 检查缓存和版本
            if cache_key in self._content_cache:
                cached_data = self._content_cache[cache_key]
                if (current_mtime <= cached_data["mtime"] and 
                    time.time() - cached_data["cache_time"] < self._content_cache_ttl and
                    cached_data["version"] == self._cache_version):
                    self._update_cache_metadata(cache_key, cached_data["content"])
                    return cached_data["content"]

            # 读取文件内容
            async with aiofiles.open(file_path, mode='r', encoding='utf-8') as f:
                content = await f.read()

            result = {
                "path": path,
                "content": content,
                "last_modified": datetime.fromtimestamp(current_mtime).isoformat()
            }

            # 更新缓存
            if len(self._content_cache) >= self._content_cache_size:
                oldest_key = min(
                    self._content_cache.items(),
                    key=lambda x: x[1]["cache_time"]
                )[0]
                del self._content_cache[oldest_key]

            self._content_cache[cache_key] = {
                "content": result,
                "mtime": current_mtime,
                "cache_time": time.time(),
                "version": self._cache_version
            }
            
            self._update_cache_metadata(cache_key, result)
            return result

    async def get_recent_docs(self, limit: int = 10) -> List[Dict]:
        """获取最近更新的文档，带缓存"""
        async with self._cache_lock("recent_docs"):
            current_time = time.time()
            
            # 检查缓存
            if (self._recent_docs_cache and 
                current_time - self._recent_docs_last_check < self._recent_docs_ttl):
                return self._recent_docs_cache[:limit]

            docs = []
            # 使用同步文件系统操作，因为 os.walk 是同步的
            for root, _, files in os.walk(self.docs_dir):
                md_files = [f for f in files if f.endswith('.md')]
                for file in md_files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, self.docs_dir)
                    # 使用同步的 os.stat 而不是异步版本
                    stat = os.stat(file_path)
                    docs.append({
                        "path": rel_path.replace('\\', '/'),
                        "name": file,
                        "last_modified": stat.st_mtime
                    })

            # 按最后修改时间排序
            docs.sort(key=lambda x: x["last_modified"], reverse=True)
            
            # 转换时间格式
            for doc in docs:
                doc["last_modified"] = datetime.fromtimestamp(doc["last_modified"]).isoformat()

            # 更新缓存
            self._recent_docs_cache = docs
            self._recent_docs_last_check = current_time
            
            return docs[:limit]

    async def get_breadcrumb(self, path: str) -> List[Dict]:
        """获取文档的面包屑导航，带缓存"""
        cache_key = f"breadcrumb:{path}"
        async with self._cache_lock(cache_key):
            if path in self._breadcrumb_cache:
                return self._breadcrumb_cache[path]

            parts = path.split('/')
            breadcrumb = []
            current_path = ""
            
            for part in parts:
                current_path = os.path.join(current_path, part).replace('\\', '/')
                breadcrumb.append({
                    "name": part,
                    "path": current_path
                })

            # 缓存结果
            self._breadcrumb_cache[path] = breadcrumb
            return breadcrumb 
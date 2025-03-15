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
import logging
import magic
from PyPDF2 import PdfReader
import asyncio
from functools import lru_cache

# 设置日志级别为 DEBUG
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

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
    _instance = None
    _observer = None
    _last_watcher_check = 0
    _watcher_check_interval = 300  # 5分钟检查一次文件监视器状态

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DocService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # 如果已经初始化过，直接返回
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        
        # 获取项目根目录
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        self.docs_dir = os.path.join(project_root, 'server', 'static', 'docs')
        logging.debug(f"初始化 DocService, 文档目录路径: {self.docs_dir}")
        
        # 检查是否是符号链接
        if os.path.islink(self.docs_dir):
            target = os.readlink(self.docs_dir)
            logging.debug(f"软链接指向: {target}")
        else:
            logging.warning(f"docs_dir 不是软链接: {self.docs_dir}")
            
        # 确保目录存在并可访问
        try:
            if os.path.exists(self.docs_dir):
                logging.debug(f"目录存在: {self.docs_dir}")
            else:
                logging.error(f"目录不存在: {self.docs_dir}")
                # 创建目录
                os.makedirs(self.docs_dir, exist_ok=True)
                logging.info(f"已创建目录: {self.docs_dir}")
        except Exception as e:
            logging.error(f"访问目录失败: {str(e)}")
        
        mimetypes.init()

        # 缓存相关 - 减少缓存大小
        self._doc_tree_cache = None
        
        self._content_cache = {}
        self._content_cache_size = 50    # 减少缓存大小
        self._content_cache_ttl = 3600   # 缓存1小时
        
        self._recent_docs_cache = None
        self._recent_docs_last_check = 0
        self._recent_docs_ttl = 1800     # 缓存30分钟
        
        self._breadcrumb_cache = {}
        
        # 缓存控制
        self._global_cache_lock = Lock()
        self._cache_locks = {}
        
        # 服务就绪状态
        self._service_ready = False
        self._ready_event = asyncio.Event()
        
        # 初始化服务（异步）
        asyncio.create_task(self._initialize_service())

    def __del__(self):
        """析构函数，确保在对象被销毁时停止文件监视器"""
        self._stop_file_watcher()
        
    def _stop_file_watcher(self):
        """停止文件监视器"""
        try:
            if DocService._observer is not None and DocService._observer.is_alive():
                DocService._observer.unschedule_all()  # 取消所有监视
                DocService._observer.stop()
                DocService._observer.join(timeout=3)  # 等待最多3秒
                DocService._observer = None
                logging.debug("文件监视器已停止")
        except Exception as e:
            logging.error(f"停止文件监视器时出错: {str(e)}")
            DocService._observer = None

    def _setup_file_watcher(self):
        """设置文件系统监控"""
        try:
            # 如果已经有观察者在运行，先停止它
            self._stop_file_watcher()
            
            # 确保目录存在
            if not os.path.exists(self.docs_dir):
                os.makedirs(self.docs_dir, exist_ok=True)
                
            # 创建新的观察者
            self.event_handler = DocChangeHandler(self)
            DocService._observer = Observer()
            DocService._observer.schedule(self.event_handler, self.docs_dir, recursive=True)
            DocService._observer.start()
            DocService._last_watcher_check = time.time()
            logging.debug(f"文件监视器已启动，监视目录: {self.docs_dir}")
        except Exception as e:
            logging.error(f"设置文件监视器失败: {str(e)}")
            DocService._observer = None
            
    async def check_file_watcher(self):
        """检查文件监视器状态，必要时重启"""
        current_time = time.time()
        
        # 如果距离上次检查不到指定间隔，则跳过
        if current_time - DocService._last_watcher_check < DocService._watcher_check_interval:
            return
            
        DocService._last_watcher_check = current_time
        
        try:
            # 检查文件监视器是否存在且活跃
            if DocService._observer is None or not DocService._observer.is_alive():
                logging.warning("文件监视器不活跃，尝试重启")
                self._setup_file_watcher()
                return True  # 表示已重启
            return False  # 表示无需重启
        except Exception as e:
            logging.error(f"检查文件监视器状态时出错: {str(e)}")
            try:
                # 尝试重新设置
                self._setup_file_watcher()
                return True
            except Exception as e2:
                logging.error(f"重启文件监视器失败: {str(e2)}")
                return False

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

    async def _cleanup_unused_locks(self):
        """清理不再使用的锁"""
        try:
            # 找出所有活跃的缓存键
            active_keys = set()
            
            # 内容缓存相关的锁
            for k in self._content_cache.keys():
                active_keys.add(f"content:{k}")
                
            # 树缓存锁
            active_keys.add("tree")
            
            # 清理不再使用的锁
            unused_locks = [k for k in self._cache_locks.keys() if k not in active_keys]
            for k in unused_locks:
                del self._cache_locks[k]
                
            if unused_locks:
                logging.debug(f"已清理 {len(unused_locks)} 个未使用的锁")
        except Exception as e:
            logging.error(f"清理未使用锁时出错: {str(e)}")

    async def _cleanup_expired_cache(self):
        """清理过期缓存"""
        try:
            async with self._global_cache_lock:
                current_time = time.time()
                
                # 清理过期的文档内容缓存
                expired_content_keys = [
                    k for k, v in self._content_cache.items()
                    if current_time - v["cache_time"] > self._content_cache_ttl
                ]
                for key in expired_content_keys:
                    del self._content_cache[key]
                    if key in self._cache_metadata:
                        del self._cache_metadata[key]
                
                # 清理过期的PDF元数据缓存
                expired_pdf_keys = [
                    k for k, v in self._pdf_metadata_cache.items()
                    if current_time - v["cache_time"] > self._pdf_metadata_ttl
                ]
                for key in expired_pdf_keys:
                    del self._pdf_metadata_cache[key]
                
                # 限制PDF元数据缓存大小
                if len(self._pdf_metadata_cache) > 100:  # 最多缓存100个PDF元数据
                    # 按最后访问时间排序，删除最旧的
                    sorted_keys = sorted(
                        self._pdf_metadata_cache.keys(),
                        key=lambda k: self._pdf_metadata_cache[k]["cache_time"]
                    )
                    for key in sorted_keys[:-100]:  # 保留最新的100个
                        del self._pdf_metadata_cache[key]
                
                # 清理元数据缓存中不存在于内容缓存的项
                orphaned_metadata = [
                    k for k in self._cache_metadata.keys()
                    if k not in self._content_cache
                ]
                for key in orphaned_metadata:
                    del self._cache_metadata[key]
                
                # 清理不再使用的锁
                await self._cleanup_unused_locks()
                
                if expired_content_keys or expired_pdf_keys or orphaned_metadata:
                    logging.debug(
                        f"缓存清理完成: 删除了 {len(expired_content_keys)} 个内容缓存, "
                        f"{len(expired_pdf_keys)} 个PDF元数据缓存, "
                        f"{len(orphaned_metadata)} 个孤立元数据"
                    )
        except Exception as e:
            logging.error(f"清理缓存时出错: {str(e)}")

    async def perform_maintenance(self):
        """执行维护任务，包括检查文件监视器和清理缓存"""
        try:
            # 检查文件监视器
            await self.check_file_watcher()
            
            # 清理缓存
            await self._cleanup_expired_cache()
            
            logging.debug("维护任务完成")
            return True
        except Exception as e:
            logging.error(f"执行维护任务时出错: {str(e)}")
            return False

    def _extract_number(self, name: str) -> tuple:
        """从文件名或目录名中提取序号，用于排序"""
        # 移除 .md 或 .pdf 后缀
        base_name = name
        if base_name.endswith(('.md', '.pdf')):
            base_name = os.path.splitext(base_name)[0]
        
        # 尝试提取序号
        parts = base_name.split('_', 1)
        if len(parts) != 2:
            return (float('inf'), name)  # 无序号的排在最后
        
        number = parts[0]
        # 处理多级序号，如 "1.1"、"1.2"
        try:
            if '.' in number:
                # 将 "1.2.3" 转换为 (1, 2, 3) 元组
                return tuple(map(int, number.split('.'))) + (0,) * 5  # 补充足够的0确保比较一致
            return (int(number), 0, 0, 0, 0, 0)  # 单级序号，补充0
        except ValueError:
            return (float('inf'), name)

    def _sort_items(self, items: List[Dict]) -> List[Dict]:
        """排序文件或目录列表，使用缓存提高性能"""
        # 使用缓存避免重复计算排序键
        sort_keys = {}
        
        def get_sort_key(item):
            name = item["name"]
            if name not in sort_keys:
                sort_keys[name] = self._extract_number(name)
            return sort_keys[name]
        
        # 使用缓存的排序键进行排序
        return sorted(items, key=get_sort_key)

    async def get_file_response(self, path: str) -> tuple[str, str]:
        """获取文件路径和MIME类型，简化版本，不预加载PDF元数据"""
        file_path = os.path.join(self.docs_dir, path)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {path}")
            
        try:
            # 使用简单的扩展名检测，避免使用 python-magic
            mime_type, _ = mimetypes.guess_type(file_path)
            return file_path, mime_type or 'application/octet-stream'
        except Exception as e:
            logging.error(f"获取文件MIME类型出错: {str(e)}")
            return file_path, 'application/octet-stream'

    @lru_cache(maxsize=100)
    def _get_pdf_page_count(self, file_path: str) -> int:
        """获取PDF页数（使用缓存）"""
        try:
            with open(file_path, 'rb') as file:
                pdf = PdfReader(file)
                return len(pdf.pages)
        except Exception as e:
            logging.error(f"Error reading PDF page count: {str(e)}")
            return 0
            
    async def _get_pdf_page_count_with_timeout(self, file_path: str, timeout: float = 10.0) -> int:
        """带超时的PDF页数获取"""
        try:
            loop = asyncio.get_event_loop()
            return await asyncio.wait_for(
                loop.run_in_executor(None, self._get_pdf_page_count, file_path),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            logging.error(f"获取PDF页数超时: {file_path}")
            return 0
        except Exception as e:
            logging.error(f"获取PDF页数出错: {str(e)}")
            return 0

    async def _cache_pdf_metadata(self, path: str, file_path: str):
        """按需获取PDF元数据，不缓存"""
        try:
            # 只获取基本信息，不读取页数
            file_size = os.path.getsize(file_path)
            last_modified = os.path.getmtime(file_path)
            
            return {
                'file_size': file_size,
                'last_modified': datetime.fromtimestamp(last_modified).isoformat(),
                # 不读取页数，避免内存占用
                'page_count': 0
            }
        except Exception as e:
            logging.error(f"获取PDF元数据出错: {str(e)}")
            return {
                'file_size': 0,
                'last_modified': datetime.now().isoformat(),
                'page_count': 0,
                'error': str(e)
            }

    async def _initialize_service(self):
        """异步初始化服务，优化版本，不预加载PDF元数据"""
        try:
            logging.info("开始初始化服务...")
            start_time = time.time()
            
            # 设置文件监控（同步操作）
            self._setup_file_watcher()
            
            # 预加载文档树
            await self._preload_doc_tree()
            
            # 标记服务为就绪状态
            self._service_ready = True
            self._ready_event.set()
            
            end_time = time.time()
            logging.info(f"服务初始化完成，耗时: {end_time - start_time:.2f}秒")
        except Exception as e:
            logging.error(f"服务初始化失败: {str(e)}")
            # 即使初始化失败，也标记为就绪，以便服务可以响应请求
            self._service_ready = True
            self._ready_event.set()
            
    async def wait_until_ready(self, timeout=None):
        """等待服务就绪"""
        try:
            await asyncio.wait_for(self._ready_event.wait(), timeout=timeout)
            return self._service_ready
        except asyncio.TimeoutError:
            logging.warning(f"等待服务就绪超时（{timeout}秒）")
            return False

    async def get_doc_tree(self) -> Dict:
        """获取文档目录树，简化高效版本，支持服务就绪检查"""
        # 如果服务尚未就绪，返回一个简单的树结构
        if not self._service_ready:
            logging.warning("服务尚未就绪，返回空文档树")
            return {"name": "root", "children": [], "status": "loading"}
            
        # 使用简单的缓存策略
        if self._doc_tree_cache:
            return self._doc_tree_cache
            
        logging.info("构建文档树...")
        start_time = time.time()
        
        # 构建树结构
        tree = {"name": "root", "children": []}
        
        try:
            # 使用同步方法在线程池中执行，避免阻塞事件循环
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._build_tree_sync, self.docs_dir, tree)
            
            # 更新缓存
            self._doc_tree_cache = tree
            
            end_time = time.time()
            logging.info(f"文档树构建完成，耗时: {end_time - start_time:.2f}秒")
            
            return tree
        except Exception as e:
            logging.error(f"构建文档树出错: {str(e)}")
            return {"name": "root", "children": [], "error": str(e)}
    
    def _build_tree_sync(self, dir_path, parent_node):
        """同步构建文档树，内存优化版本"""
        try:
            # 一次性获取所有文件和目录
            all_items = os.listdir(dir_path)
            
            # 预先分类，避免重复调用 os.path.isdir
            dirs = []
            files = []
            
            for item in all_items:
                if item.startswith('.'):
                    continue
                    
                item_path = os.path.join(dir_path, item)
                try:
                    if os.path.isdir(item_path):
                        dirs.append(item)
                    elif item.endswith(('.md', '.pdf')):
                        files.append(item)
                except Exception:
                    continue
            
            # 处理文件 - 批量处理以减少内存分配
            if files:
                file_nodes = []
                rel_dir_path = os.path.relpath(dir_path, self.docs_dir)
                rel_dir_path = '.' if rel_dir_path == '.' else rel_dir_path.replace('\\', '/')
                
                for file in files:
                    file_path = os.path.join(rel_dir_path, file)
                    if rel_dir_path == '.':
                        file_path = file
                    
                    file_type = "markdown" if file.endswith('.md') else "pdf"
                    
                    file_nodes.append({
                        "name": file,
                        "path": file_path.replace('\\', '/'),
                        "type": file_type
                    })
                
                # 排序并添加文件节点
                parent_node["children"].extend(self._sort_items(file_nodes))
                # 释放内存
                del file_nodes
            
            # 处理目录 - 递归处理子目录
            for dir_name in dirs:
                dir_node = {"name": dir_name, "children": []}
                sub_dir_path = os.path.join(dir_path, dir_name)
                
                # 递归处理子目录
                self._build_tree_sync(sub_dir_path, dir_node)
                
                # 只有当目录非空时才添加
                if dir_node["children"]:
                    parent_node["children"].append(dir_node)
            
            # 对目录节点排序
            if parent_node["children"]:
                parent_node["children"] = self._sort_items(parent_node["children"])
            
        except Exception as e:
            logging.error(f"处理目录 {dir_path} 时出错: {str(e)}")
    
    async def get_doc_content(self, path: str) -> Dict:
        """获取文档内容，简化版本，减少内存使用"""
        file_path = os.path.join(self.docs_dir, path)
        
        # 简化文件存在检查
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Document not found: {path}")
        
        # 使用简单的扩展名检测
        if path.endswith('.pdf'):
            # 对于PDF文件，只返回基本信息
            try:
                file_size = os.path.getsize(file_path)
                last_modified = os.path.getmtime(file_path)
                
                return {
                    "path": path,
                    "type": "pdf",
                    "metadata": {
                        'file_size': file_size,
                        'last_modified': datetime.fromtimestamp(last_modified).isoformat(),
                        'page_count': 0  # 不读取页数
                    },
                    "last_modified": datetime.fromtimestamp(last_modified).isoformat()
                }
            except Exception as e:
                logging.error(f"获取PDF信息出错: {str(e)}")
                return {
                    "path": path,
                    "type": "pdf",
                    "error": str(e)
                }

        # 对于Markdown文件
        if path.endswith('.md'):
            # 检查缓存
            cache_key = path
            if cache_key in self._content_cache:
                cached_data = self._content_cache[cache_key]
                if time.time() - cached_data["cache_time"] < self._content_cache_ttl:
                    return cached_data["content"]

            # 读取文件内容
            try:
                async with aiofiles.open(file_path, mode='r', encoding='utf-8') as f:
                    content = await f.read()
            except UnicodeDecodeError:
                # 尝试使用其他编码
                try:
                    async with aiofiles.open(file_path, mode='r', encoding='gbk') as f:
                        content = await f.read()
                except Exception as e:
                    logging.error(f"读取文件内容出错: {str(e)}")
                    raise FileNotFoundError(f"Error reading document content: {path}")
            except Exception as e:
                logging.error(f"读取文件内容出错: {str(e)}")
                raise FileNotFoundError(f"Error reading document content: {path}")

            # 获取修改时间
            try:
                last_modified = os.path.getmtime(file_path)
            except Exception:
                last_modified = time.time()

            result = {
                "path": path,
                "type": "markdown",
                "content": content,
                "last_modified": datetime.fromtimestamp(last_modified).isoformat()
            }

            # 更新缓存，限制缓存大小
            if len(self._content_cache) >= self._content_cache_size:
                # 简单地清除最旧的缓存项
                oldest_key = min(
                    self._content_cache.keys(),
                    key=lambda k: self._content_cache[k]["cache_time"]
                )
                del self._content_cache[oldest_key]

            self._content_cache[cache_key] = {
                "content": result,
                "cache_time": time.time()
            }
            
            return result

        # 其他类型文件
        raise ValueError(f"Unsupported file type: {path}")

    async def get_recent_docs(self, limit: int = 10) -> List[Dict]:
        """获取最近更新的文档，简化版本，不读取PDF页数"""
        # 检查缓存
        current_time = time.time()
        if (self._recent_docs_cache and 
            current_time - self._recent_docs_last_check < self._recent_docs_ttl):
            return self._recent_docs_cache[:limit]

        docs = []
        try:
            # 使用同步文件系统操作
            for root, _, files in os.walk(self.docs_dir):
                # 同时处理 .md 和 .pdf 文件
                doc_files = [f for f in files if f.endswith(('.md', '.pdf'))]
                for file in doc_files:
                    try:
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, self.docs_dir)
                        # 使用同步的 os.stat 获取文件信息
                        stat = os.stat(file_path)
                        
                        doc_info = {
                            "path": rel_path.replace('\\', '/'),
                            "name": file,
                            "last_modified": stat.st_mtime,
                            "size": stat.st_size,
                            "type": "pdf" if file.endswith('.pdf') else "markdown"
                        }
                        
                        docs.append(doc_info)
                    except Exception as e:
                        logging.error(f"处理文件失败 {file}: {str(e)}")
                        continue

            # 按最后修改时间排序
            docs.sort(key=lambda x: x["last_modified"], reverse=True)
            
            # 转换时间格式
            for doc in docs:
                doc["last_modified"] = datetime.fromtimestamp(doc["last_modified"]).isoformat()

            # 更新缓存
            self._recent_docs_cache = docs
            self._recent_docs_last_check = current_time
            
            return docs[:limit]
            
        except Exception as e:
            logging.error(f"获取最近文档失败: {str(e)}")
            return []

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

    async def _preload_doc_tree(self):
        """预加载文档树，避免第一次请求时的延迟"""
        try:
            logging.info("开始预加载文档树...")
            start_time = time.time()
            
            # 构建树结构
            tree = {"name": "root", "children": []}
            
            # 使用同步方法在线程池中执行
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._build_tree_sync, self.docs_dir, tree)
            
            # 更新缓存
            self._doc_tree_cache = tree
            
            end_time = time.time()
            logging.info(f"文档树预加载完成，耗时: {end_time - start_time:.2f}秒")
        except Exception as e:
            logging.error(f"预加载文档树出错: {str(e)}")
            # 预加载失败不影响系统运行，只是第一次请求会慢一些 
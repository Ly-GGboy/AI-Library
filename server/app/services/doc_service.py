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
                logging.debug(f"目录内容: {os.listdir(self.docs_dir)}")
            else:
                logging.error(f"目录不存在: {self.docs_dir}")
                # 创建目录
                os.makedirs(self.docs_dir, exist_ok=True)
                logging.info(f"已创建目录: {self.docs_dir}")
        except Exception as e:
            logging.error(f"访问目录失败: {str(e)}")
        
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

        # PDF相关缓存
        self._pdf_metadata_cache = {}
        self._pdf_metadata_ttl = 3600  # 1小时

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
        """获取文件路径和MIME类型，增强的PDF支持"""
        file_path = os.path.join(self.docs_dir, path)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {path}")
            
        try:
            # 使用python-magic进行更准确的MIME类型检测，添加超时保护
            loop = asyncio.get_event_loop()
            mime_type = await asyncio.wait_for(
                loop.run_in_executor(None, lambda: magic.from_file(file_path, mime=True)),
                timeout=5.0  # 5秒超时
            )
            
            # 如果是PDF文件，获取元数据
            if mime_type == 'application/pdf':
                await self._cache_pdf_metadata(path, file_path)
                
            return file_path, mime_type
        except asyncio.TimeoutError:
            logging.error(f"获取文件MIME类型超时: {file_path}")
            # 回退到基于扩展名的MIME类型检测
            mime_type, _ = mimetypes.guess_type(file_path)
            return file_path, mime_type or 'application/octet-stream'
        except Exception as e:
            logging.error(f"获取文件MIME类型出错: {str(e)}")
            mime_type, _ = mimetypes.guess_type(file_path)
            return file_path, mime_type or 'application/octet-stream'

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
        """异步缓存PDF元数据，带超时保护"""
        cache_key = f"pdf_metadata:{path}"
        current_time = time.time()
        
        # 检查缓存
        if cache_key in self._pdf_metadata_cache:
            metadata = self._pdf_metadata_cache[cache_key]
            if current_time - metadata['cache_time'] < self._pdf_metadata_ttl:
                return metadata['data']
        
        # 在线程池中执行PDF处理，带超时
        try:
            # 使用带超时的方法获取页数
            page_count = await self._get_pdf_page_count_with_timeout(file_path)
            
            # 获取文件大小和修改时间，也添加超时保护
            loop = asyncio.get_event_loop()
            file_size = await asyncio.wait_for(
                loop.run_in_executor(None, os.path.getsize, file_path),
                timeout=2.0
            )
            
            last_modified = await asyncio.wait_for(
                loop.run_in_executor(None, os.path.getmtime, file_path),
                timeout=2.0
            )
            
            metadata = {
                'page_count': page_count,
                'file_size': file_size,
                'last_modified': datetime.fromtimestamp(last_modified).isoformat()
            }
            
            # 更新缓存
            self._pdf_metadata_cache[cache_key] = {
                'data': metadata,
                'cache_time': current_time
            }
            
            return metadata
            
        except asyncio.TimeoutError:
            logging.error(f"缓存PDF元数据超时: {file_path}")
            # 返回基本元数据
            try:
                return {
                    'page_count': 0,
                    'file_size': os.path.getsize(file_path),
                    'last_modified': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
                    'error': 'Timeout while processing PDF'
                }
            except Exception:
                return {
                    'page_count': 0,
                    'file_size': 0,
                    'last_modified': datetime.now().isoformat(),
                    'error': 'Failed to get PDF metadata'
                }
        except Exception as e:
            logging.error(f"Error caching PDF metadata: {str(e)}")
            # 返回基本元数据
            try:
                return {
                    'page_count': 0,
                    'file_size': os.path.getsize(file_path),
                    'last_modified': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
                    'error': str(e)
                }
            except Exception:
                return {
                    'page_count': 0,
                    'file_size': 0,
                    'last_modified': datetime.now().isoformat(),
                    'error': 'Failed to get PDF metadata'
                }

    async def get_doc_tree(self) -> Dict:
        """获取文档目录树，增加PDF文件支持，添加超时保护和分批处理"""
        async with self._cache_lock("tree"):
            try:
                # 检查缓存是否有效
                current_time = time.time()
                
                # 使用超时保护获取目录修改时间
                loop = asyncio.get_event_loop()
                try:
                    current_mtime = await asyncio.wait_for(
                        loop.run_in_executor(None, os.path.getmtime, self.docs_dir),
                        timeout=3.0
                    )
                except (asyncio.TimeoutError, Exception) as e:
                    logging.error(f"获取目录修改时间失败: {str(e)}")
                    # 如果获取修改时间失败但缓存存在，使用缓存
                    if self._doc_tree_cache:
                        return self._doc_tree_cache
                    current_mtime = 0  # 强制重建缓存
                
                # 如果缓存有效，直接返回
                if (self._doc_tree_cache and 
                    current_mtime <= self._doc_tree_last_modified and
                    self._doc_tree_version == self._cache_version):
                    return self._doc_tree_cache

                # 构建新的文档树
                tree = {"name": "root", "children": []}
                
                # 使用超时保护获取目录内容
                try:
                    # 分批处理目录，避免长时间阻塞
                    async def process_directory(dir_path, parent_node):
                        try:
                            # 获取目录内容
                            items = await asyncio.wait_for(
                                loop.run_in_executor(None, lambda: os.listdir(dir_path)),
                                timeout=5.0
                            )
                            
                            # 分离目录和文件
                            dirs = []
                            files = []
                            
                            for item in items:
                                if item.startswith('.'):
                                    continue
                                    
                                item_path = os.path.join(dir_path, item)
                                try:
                                    is_dir = await asyncio.wait_for(
                                        loop.run_in_executor(None, os.path.isdir, item_path),
                                        timeout=1.0
                                    )
                                    
                                    if is_dir:
                                        dirs.append(item)
                                    elif item.endswith('.md') or item.endswith('.pdf'):
                                        files.append(item)
                                except (asyncio.TimeoutError, Exception):
                                    # 跳过处理超时的项
                                    continue
                            
                            # 处理文件
                            file_nodes = []
                            rel_dir_path = os.path.relpath(dir_path, self.docs_dir)
                            rel_dir_path = '.' if rel_dir_path == '.' else rel_dir_path.replace('\\', '/')
                            
                            for file in files:
                                file_path = os.path.join(rel_dir_path, file)
                                if rel_dir_path == '.':
                                    file_path = file
                                
                                # 确定文件类型
                                file_type = "markdown" if file.endswith('.md') else "pdf"
                                
                                file_nodes.append({
                                    "name": file,
                                    "path": file_path.replace('\\', '/'),
                                    "type": file_type
                                })
                            
                            # 对文件节点排序并添加到当前节点
                            parent_node["children"].extend(self._sort_items(file_nodes))
                            
                            # 处理子目录
                            for dir_name in dirs:
                                # 创建目录节点
                                dir_node = {"name": dir_name, "children": []}
                                parent_node["children"].append(dir_node)
                                
                                # 递归处理子目录
                                sub_dir_path = os.path.join(dir_path, dir_name)
                                await process_directory(sub_dir_path, dir_node)
                            
                            # 对当前节点的所有子节点排序
                            parent_node["children"] = self._sort_items(parent_node["children"])
                            
                        except (asyncio.TimeoutError, Exception) as e:
                            logging.error(f"处理目录 {dir_path} 时出错: {str(e)}")
                    
                    # 开始处理根目录
                    await process_directory(self.docs_dir, tree)
                    
                except (asyncio.TimeoutError, Exception) as e:
                    logging.error(f"构建文档树时出错: {str(e)}")
                    # 如果构建失败但缓存存在，使用缓存
                    if self._doc_tree_cache:
                        return self._doc_tree_cache
                
                # 更新缓存
                self._doc_tree_cache = tree
                self._doc_tree_last_modified = current_mtime
                self._doc_tree_version = self._cache_version
                return tree
                
            except Exception as e:
                logging.error(f"获取文档树时出错: {str(e)}")
                # 如果出错但缓存存在，使用缓存
                if self._doc_tree_cache:
                    return self._doc_tree_cache
                # 否则返回空树
                return {"name": "root", "children": []}

    async def get_doc_content(self, path: str) -> Dict:
        """获取文档内容，支持PDF元数据，添加超时保护和错误处理"""
        file_path = os.path.join(self.docs_dir, path)
        logging.info(f"尝试访问文件: {file_path}")
        
        # 使用超时保护检查文件是否存在
        try:
            loop = asyncio.get_event_loop()
            file_exists = await asyncio.wait_for(
                loop.run_in_executor(None, os.path.exists, file_path),
                timeout=3.0
            )
            logging.info(f"文件是否存在: {file_exists}")
            
            if not file_exists:
                logging.error(f"文件不存在: {file_path}")
                raise FileNotFoundError(f"Document not found: {path}")
        except asyncio.TimeoutError:
            logging.error(f"检查文件存在超时: {file_path}")
            raise FileNotFoundError(f"Timeout checking if document exists: {path}")
        except Exception as e:
            logging.error(f"检查文件存在出错: {str(e)}")
            raise FileNotFoundError(f"Error checking if document exists: {path}")
        
        # 使用锁保护缓存访问
        async with self._cache_lock(f"content:{path}"):
            try:
                # 检测文件类型，使用超时保护
                try:
                    mime_type = await asyncio.wait_for(
                        loop.run_in_executor(None, lambda: magic.from_file(file_path, mime=True)),
                        timeout=5.0
                    )
                except (asyncio.TimeoutError, Exception) as e:
                    logging.error(f"获取文件MIME类型出错: {str(e)}")
                    # 回退到基于扩展名的MIME类型检测
                    mime_type, _ = mimetypes.guess_type(file_path)
                    mime_type = mime_type or 'application/octet-stream'
                
                # 如果是PDF文件，返回元数据
                if mime_type == 'application/pdf' or path.endswith('.pdf'):
                    metadata = await self._cache_pdf_metadata(path, file_path)
                    return {
                        "path": path,
                        "type": "pdf",
                        "metadata": metadata,
                        "last_modified": metadata['last_modified'] if metadata else None
                    }

                # 对于Markdown文件，添加超时保护和错误处理
                if path.endswith('.md'):
                    # 获取文件修改时间，使用超时保护
                    try:
                        current_mtime = await asyncio.wait_for(
                            loop.run_in_executor(None, os.path.getmtime, file_path),
                            timeout=3.0
                        )
                    except (asyncio.TimeoutError, Exception) as e:
                        logging.error(f"获取文件修改时间出错: {str(e)}")
                        current_mtime = time.time()  # 使用当前时间作为回退
                    
                    cache_key = path
                    
                    # 检查缓存和版本
                    if cache_key in self._content_cache:
                        cached_data = self._content_cache[cache_key]
                        if (current_mtime <= cached_data["mtime"] and 
                            time.time() - cached_data["cache_time"] < self._content_cache_ttl and
                            cached_data["version"] == self._cache_version):
                            self._update_cache_metadata(cache_key, cached_data["content"])
                            return cached_data["content"]

                    # 读取文件内容，使用超时保护
                    try:
                        async with aiofiles.open(file_path, mode='r', encoding='utf-8') as f:
                            content = await asyncio.wait_for(f.read(), timeout=10.0)
                    except UnicodeDecodeError:
                        # 尝试使用其他编码
                        try:
                            async with aiofiles.open(file_path, mode='r', encoding='gbk') as f:
                                content = await asyncio.wait_for(f.read(), timeout=10.0)
                        except (asyncio.TimeoutError, Exception) as e:
                            logging.error(f"读取文件内容出错: {str(e)}")
                            raise FileNotFoundError(f"Error reading document content: {path}")
                    except (asyncio.TimeoutError, Exception) as e:
                        logging.error(f"读取文件内容出错: {str(e)}")
                        raise FileNotFoundError(f"Error reading document content: {path}")

                    result = {
                        "path": path,
                        "type": "markdown",
                        "content": content,
                        "last_modified": datetime.fromtimestamp(current_mtime).isoformat()
                    }

                    # 更新缓存，限制缓存大小
                    if len(self._content_cache) >= self._content_cache_size:
                        try:
                            # 找出最旧的缓存项
                            oldest_key = min(
                                self._content_cache.items(),
                                key=lambda x: x[1]["cache_time"]
                            )[0]
                            del self._content_cache[oldest_key]
                        except Exception as e:
                            logging.error(f"清理缓存出错: {str(e)}")
                            # 如果清理失败，简单地清空缓存
                            if len(self._content_cache) > self._content_cache_size * 1.5:
                                self._content_cache.clear()

                    self._content_cache[cache_key] = {
                        "content": result,
                        "mtime": current_mtime,
                        "cache_time": time.time(),
                        "version": self._cache_version
                    }
                    
                    self._update_cache_metadata(cache_key, result)
                    return result

                # 其他类型文件
                raise ValueError(f"Unsupported file type: {mime_type}")
                
            except FileNotFoundError:
                raise
            except Exception as e:
                logging.error(f"获取文档内容出错: {str(e)}")
                raise ValueError(f"Error getting document content: {str(e)}")

    async def get_recent_docs(self, limit: int = 10) -> List[Dict]:
        """获取最近更新的文档，带缓存，支持 PDF 文件"""
        async with self._cache_lock("recent_docs"):
            current_time = time.time()
            
            # 检查缓存
            if (self._recent_docs_cache and 
                current_time - self._recent_docs_last_check < self._recent_docs_ttl):
                return self._recent_docs_cache[:limit]

            docs = []
            try:
                # 使用同步文件系统操作，因为 os.walk 是同步的
                for root, _, files in os.walk(self.docs_dir):
                    # 同时处理 .md 和 .pdf 文件
                    doc_files = [f for f in files if f.endswith(('.md', '.pdf'))]
                    for file in doc_files:
                        try:
                            file_path = os.path.join(root, file)
                            rel_path = os.path.relpath(file_path, self.docs_dir)
                            # 使用同步的 os.stat 而不是异步版本
                            stat = os.stat(file_path)
                            
                            doc_info = {
                                "path": rel_path.replace('\\', '/'),
                                "name": file,
                                "last_modified": stat.st_mtime,
                                "size": stat.st_size,
                                "type": "pdf" if file.endswith('.pdf') else "markdown"
                            }
                            
                            # 如果是 PDF，获取页数
                            if file.endswith('.pdf'):
                                try:
                                    page_count = self._get_pdf_page_count(file_path)
                                    doc_info["page_count"] = page_count
                                    # PDF 的阅读时间基于页数估算，假设每页 2 分钟
                                    doc_info["estimated_reading_time"] = page_count * 2
                                except Exception as e:
                                    logging.error(f"获取PDF信息失败 {file_path}: {str(e)}")
                                    continue
                            
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
                
                logging.debug(f"找到 {len(docs)} 个最近文档")
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
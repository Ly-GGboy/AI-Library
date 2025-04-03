import os
import json
import time
from typing import Dict, List, Optional, Tuple, Set, Any
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
from pathlib import Path
import signal
from collections import OrderedDict

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

class LRUCache:
    """基于 OrderedDict 的 LRU 缓存实现，线程安全"""
    
    def __init__(self, capacity: int, ttl: int = 3600):
        """
        初始化 LRU 缓存
        
        Args:
            capacity: 缓存最大容量
            ttl: 缓存条目的生存时间(秒)，默认1小时
        """
        self.capacity = capacity
        self.ttl = ttl
        self.cache = OrderedDict()  # {key: (value, timestamp)}
        self._lock = Lock()
        self._stats = {"hits": 0, "misses": 0, "evictions": 0, "expirations": 0}
    
    async def get(self, key: str) -> Any:
        """
        获取缓存项，如存在则更新访问顺序
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值或 None (如果不存在或已过期)
        """
        async with self._lock:
            if key not in self.cache:
                self._stats["misses"] += 1
                return None
                
            value, timestamp = self.cache[key]
            current_time = time.time()
            
            # 检查是否过期
            if current_time - timestamp > self.ttl:
                self.cache.pop(key)
                self._stats["expirations"] += 1
                self._stats["misses"] += 1
                return None
            
            # 更新访问顺序 (移到末尾，表示最近使用)
            self.cache.move_to_end(key)
            self._stats["hits"] += 1
            return value
    
    async def put(self, key: str, value: Any) -> None:
        """
        添加或更新缓存项
        
        Args:
            key: 缓存键
            value: 缓存值
        """
        async with self._lock:
            if key in self.cache:
                self.cache.pop(key)
            elif len(self.cache) >= self.capacity:
                # 移除最少使用的项 (OrderedDict 第一项)
                self.cache.popitem(last=False)
                self._stats["evictions"] += 1
                
            self.cache[key] = (value, time.time())
    
    async def remove(self, key: str) -> bool:
        """
        移除缓存项
        
        Args:
            key: 缓存键
            
        Returns:
            是否成功移除
        """
        async with self._lock:
            if key in self.cache:
                self.cache.pop(key)
                return True
            return False
    
    async def clear(self) -> None:
        """清空缓存"""
        async with self._lock:
            self.cache.clear()
    
    async def cleanup_expired(self) -> int:
        """
        清理过期项
        
        Returns:
            已清理的项数
        """
        async with self._lock:
            current_time = time.time()
            expired_keys = [
                k for k, (_, timestamp) in self.cache.items()
                if current_time - timestamp > self.ttl
            ]
            
            for key in expired_keys:
                self.cache.pop(key)
                self._stats["expirations"] += 1
                
            return len(expired_keys)
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计数据"""
        async with self._lock:
            stats = self._stats.copy()
            if (stats["hits"] + stats["misses"]) > 0:
                stats["hit_ratio"] = stats["hits"] / (stats["hits"] + stats["misses"])
            else:
                stats["hit_ratio"] = 0
            stats["size"] = len(self.cache)
            stats["capacity"] = self.capacity
            return stats
    
    def __len__(self) -> int:
        """获取当前缓存大小"""
        return len(self.cache)

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

        # 缓存相关 - 改进缓存策略
        self._doc_tree_cache = None
        # 启用分层加载策略，不使用树缓存
        self._using_layered_loading = True
        
        # 缓存版本控制
        self._cache_version = 0
        
        # 使用 LRU 缓存替代原始简单缓存
        self._content_cache_ttl = 3600    # 缓存生存时间 1 小时
        self._content_cache_size = 200    # 增加缓存容量到 200
        self._content_cache = LRUCache(capacity=self._content_cache_size, ttl=self._content_cache_ttl)
        
        # PDF元数据缓存
        self._pdf_metadata_ttl = 7200    # 延长缓存时间到 2 小时
        self._pdf_metadata_size = 150    # 增加缓存容量到 150
        self._pdf_metadata_cache = LRUCache(capacity=self._pdf_metadata_size, ttl=self._pdf_metadata_ttl)
        
        # 面包屑导航缓存，容量可以更大一些因为它们很小
        self._breadcrumb_cache = LRUCache(capacity=300, ttl=86400)  # 1 天过期
        
        # 最近文档缓存
        self._recent_docs_cache = None
        self._recent_docs_last_check = 0
        self._recent_docs_ttl = 1800      # 保持 30 分钟
        
        # 缓存控制
        self._global_cache_lock = Lock()
        self._cache_locks = {}
        
        # 在线读者相关
        self._online_readers = {}          # 在线读者列表
        self._online_expiry = 300          # 在线状态过期时间（秒）
        
        # 服务就绪状态
        self._service_ready = False
        self._ready_event = asyncio.Event()
        
        # 缓存统计
        self._cache_stats = {
            "content": {"hits": 0, "misses": 0},
            "pdf_metadata": {"hits": 0, "misses": 0},
            "breadcrumb": {"hits": 0, "misses": 0}
        }
        
        # 热门文档集合（用于缓存预热）
        self._hot_documents = set()
        self._hot_document_access_count = {}
        
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
        """使文档树缓存失效（现在只更新缓存版本号）"""
        # 不再需要将缓存置为None
        # self._doc_tree_cache = None
        self._cache_version += 1

    def invalidate_doc_cache(self, path: str):
        """使特定文档的缓存失效"""
        asyncio.create_task(self._content_cache.remove(path))
        asyncio.create_task(self._breadcrumb_cache.remove(path))
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
            
            # 树缓存锁
            active_keys.add("tree")
            
            # 清理不再使用的锁
            unused_locks = [k for k in self._cache_locks.keys() if k not in active_keys]
            for k in unused_locks:
                del self._cache_locks[k]
                
            if unused_locks:
                logging.debug(f"已清理 {len(unused_locks)} 个未使用的锁")
                
            return len(unused_locks)
        except Exception as e:
            logging.error(f"清理未使用锁时出错: {str(e)}")
            return 0

    async def _cleanup_expired_cache(self):
        """清理过期缓存"""
        try:
            async with self._global_cache_lock:
                # 调用各缓存的清理方法
                content_expired = await self._content_cache.cleanup_expired()
                pdf_expired = await self._pdf_metadata_cache.cleanup_expired()
                breadcrumb_expired = await self._breadcrumb_cache.cleanup_expired()
                
                # 清理不再使用的锁
                await self._cleanup_unused_locks()
                
                if content_expired or pdf_expired or breadcrumb_expired:
                    logging.debug(
                        f"缓存清理完成: 删除了 {content_expired} 个内容缓存项, "
                        f"{pdf_expired} 个PDF元数据缓存项, "
                        f"{breadcrumb_expired} 个面包屑缓存项"
                    )
                
                # 返回清理的项目总数
                return content_expired + pdf_expired + breadcrumb_expired
        except Exception as e:
            logging.error(f"清理缓存时出错: {str(e)}")
            return 0

    async def perform_maintenance(self):
        """执行维护任务，包括检查文件监视器、清理缓存和缓存预热"""
        try:
            # 检查文件监视器
            await self.check_file_watcher()
            
            # 清理缓存
            cleaned_items = await self._cleanup_expired_cache()
            
            # 清理过期的在线读者
            await self._cleanup_expired_readers()
            
            # 缓存预热 - 确保热门文档在缓存中
            await self._warm_cache()
            
            logging.debug(f"维护任务完成：清理了 {cleaned_items} 个缓存项")
            return True
        except Exception as e:
            logging.error(f"执行维护任务时出错: {str(e)}")
            return False
            
    async def _warm_cache(self):
        """缓存预热 - 预加载热门文档"""
        if not self._hot_documents:
            return
            
        try:
            warmed_count = 0
            for doc_path in list(self._hot_documents)[:20]:  # 最多预热20个文档
                # 检查文档是否存在于缓存中
                if not await self._content_cache.get(doc_path):
                    try:
                        # 预加载文档
                        await self.get_doc_content(doc_path)
                        warmed_count += 1
                    except Exception as e:
                        logging.error(f"预热缓存时无法加载文档 {doc_path}: {str(e)}")
                        # 如果文档无法加载，从热门文档集合中移除
                        self._hot_documents.discard(doc_path)
                        if doc_path in self._hot_document_access_count:
                            del self._hot_document_access_count[doc_path]
            
            if warmed_count > 0:
                logging.debug(f"缓存预热完成，预加载了 {warmed_count} 个热门文档")
        except Exception as e:
            logging.error(f"缓存预热过程中出错: {str(e)}")
            
    async def reset_cache_stats(self):
        """重置缓存统计信息"""
        try:
            await self._content_cache.clear()
            await self._pdf_metadata_cache.clear()
            await self._breadcrumb_cache.clear()
            self._hot_documents.clear()
            self._hot_document_access_count.clear()
            self._cache_version += 1
            logging.info("已重置所有缓存")
            return True
        except Exception as e:
            logging.error(f"重置缓存统计信息时出错: {str(e)}")
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
        """排序文件或目录列表，确保目录排在文件前面"""
        # 使用缓存避免重复计算排序键
        sort_keys = {}
        
        def get_sort_key(item):
            # 首先按类型分类（目录在前，文件在后）
            is_dir = item.get("is_dir", False)
            
            # 获取或计算排序键
            name = item["name"]
            if name not in sort_keys:
                sort_keys[name] = self._extract_number(name)
                
            # 返回复合排序键：(类型优先级, 数字序号, 名称)
            return (0 if is_dir else 1,) + sort_keys[name]
        
        # 使用复合排序键进行排序
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
        """初始化服务, 包括设置文件监视器和预加载缓存"""
        try:
            # 设置文件监视器
            self._setup_file_watcher()
            
            # 预加载文档树（现在跳过）
            # await self._preload_doc_tree()
            
            # 服务就绪
            self._service_ready = True
            self._ready_event.set()
            
            # 启动定期维护任务
            asyncio.create_task(self._schedule_maintenance())
            
            # 启动定期统计报告
            asyncio.create_task(self._schedule_stats_report())
            
            logging.info("DocService 初始化完成，服务就绪")
        except Exception as e:
            logging.error(f"初始化服务失败: {str(e)}")
            # 尽管有错误，仍然标记服务为就绪以允许基本功能
            self._service_ready = True
            self._ready_event.set()
            
    async def _schedule_stats_report(self):
        """定期报告缓存统计"""
        while True:
            try:
                await asyncio.sleep(1800)  # 每30分钟报告一次
                
                # 获取缓存统计
                stats = await self.get_cache_stats()
                
                # 记录统计信息
                logging.info(f"缓存统计报告:")
                logging.info(f"- 内容缓存: 大小={stats['content_cache']['size']}/{stats['content_cache']['capacity']}, 命中率={stats['content_cache']['hit_ratio']:.2f}")
                logging.info(f"- PDF元数据缓存: 大小={stats['pdf_metadata_cache']['size']}/{stats['pdf_metadata_cache']['capacity']}, 命中率={stats['pdf_metadata_cache']['hit_ratio']:.2f}")
                logging.info(f"- 面包屑缓存: 大小={stats['breadcrumb_cache']['size']}/{stats['breadcrumb_cache']['capacity']}, 命中率={stats['breadcrumb_cache']['hit_ratio']:.2f}")
                logging.info(f"- 热门文档数量: {stats['hot_documents']}")
                
            except Exception as e:
                logging.error(f"生成缓存统计报告时出错: {str(e)}")
                await asyncio.sleep(300)  # 出错后等待5分钟再重试

    async def wait_until_ready(self, timeout=None):
        """等待服务就绪"""
        try:
            await asyncio.wait_for(self._ready_event.wait(), timeout=timeout)
            return self._service_ready
        except asyncio.TimeoutError:
            logging.warning(f"等待服务就绪超时（{timeout}秒）")
            return False

    async def get_doc_tree(self) -> Dict:
        """获取文档目录树，优化版本，默认只加载顶层目录"""
        # 如果服务尚未就绪，返回一个简单的树结构
        if not self._service_ready:
            logging.warning("服务尚未就绪，返回空文档树")
            return {"name": "root", "children": [], "status": "loading"}
            
        # 不再使用缓存，始终重新构建树结构
        logging.info("构建文档树 (使用分层加载模式)...")
        start_time = time.time()
        
        # 构建树结构，只加载顶层
        tree = {"name": "root", "children": []}
        
        try:
            # 使用同步方法在线程池中执行，避免阻塞事件循环
            loop = asyncio.get_event_loop()
            # 修改为调用特殊的根目录构建方法，确保顶层目录和文件都包括在内
            await loop.run_in_executor(None, self._build_root_tree_sync, self.docs_dir, tree)
            
            # 不再更新缓存
            # self._doc_tree_cache = tree
            
            end_time = time.time()
            logging.info(f"文档树构建完成，耗时: {end_time - start_time:.2f}秒，顶层节点数: {len(tree.get('children', []))}")
            
            return tree
        except Exception as e:
            logging.error(f"构建文档树出错: {str(e)}")
            return {"name": "root", "children": [], "error": str(e)}

    def _build_root_tree_sync(self, dir_path, parent_node):
        """特殊的根目录树构建方法，确保包含顶层目录和文件，但子目录仍然懒加载"""
        try:
            logging.debug(f"构建根目录树 - 路径: {dir_path}")
            
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
            
            # 处理文件 - 确保顶层目录下的文件被包括进来
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
                        "type": file_type,
                        "is_file": True
                    })
                
                # 排序并添加文件节点
                parent_node["children"].extend(self._sort_items(file_nodes))
                logging.debug(f"添加了 {len(file_nodes)} 个文件节点到根目录")
                # 释放内存
                del file_nodes
            
            # 处理目录 - 对于子目录，设置has_children标记进行懒加载
            dir_count = 0
            for dir_name in dirs:
                dir_node = {"name": dir_name, "children": []}
                sub_dir_path = os.path.join(dir_path, dir_name)
                
                # 计算相对路径
                rel_path = os.path.relpath(sub_dir_path, self.docs_dir).replace('\\', '/')
                dir_node["path"] = rel_path
                dir_node["is_dir"] = True
                
                # 检查该目录是否有子项，如果有则设置has_children标记
                try:
                    sub_items = os.listdir(sub_dir_path)
                    # 过滤掉隐藏文件
                    sub_items = [item for item in sub_items if not item.startswith('.')]
                    if sub_items:
                        # 设置标记表示有子内容但未加载
                        dir_node["has_children"] = True
                except Exception:
                    pass
                
                # 始终添加目录节点，即使它可能为空
                parent_node["children"].append(dir_node)
                dir_count += 1
            
            # 对所有节点排序
            if parent_node["children"]:
                parent_node["children"] = self._sort_items(parent_node["children"])
                
            logging.debug(f"完成构建根目录树 - 添加了 {dir_count} 个目录节点和 {len(files)} 个文件节点")
            
        except Exception as e:
            logging.error(f"处理根目录 {dir_path} 时出错: {str(e)}")

    async def get_doc_subtree(self, path: str) -> Dict:
        """获取指定路径的子树，用于按需加载"""
        try:
            logging.info(f"开始加载子树: {path}...")
            start_time = time.time()
            
            # 获取绝对路径
            dir_path = os.path.join(self.docs_dir, path)
            
            # 检查路径是否存在且是目录
            if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
                logging.error(f"路径不存在或不是目录: {dir_path}")
                return {"error": "路径不存在或不是目录"}
            
            # 构建子树
            subtree = {"name": os.path.basename(path), "path": path, "children": []}
            
            # 使用线程池执行IO密集操作，构建完整子树（深度设置足够大）
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._build_tree_sync, dir_path, subtree)
            
            end_time = time.time()
            logging.info(f"子树加载完成: {path}, 耗时: {end_time - start_time:.2f}秒, 子节点数: {len(subtree.get('children', []))}")
            
            return subtree
        except Exception as e:
            logging.error(f"获取子树失败: {str(e)}")
            return {"error": str(e)}

    def _build_tree_sync_with_depth(self, dir_path, parent_node, max_depth, current_depth=0):
        """同步构建有限深度的文档树"""
        try:
            logging.debug(f"构建树 - 路径: {dir_path}, 深度: {current_depth}/{max_depth}")
            
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
            
            # 处理文件
            if files and current_depth < max_depth:
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
                        "type": file_type,
                        "is_file": True
                    })
                
                # 排序并添加文件节点
                parent_node["children"].extend(self._sort_items(file_nodes))
                logging.debug(f"添加了 {len(file_nodes)} 个文件节点到 {dir_path}")
                # 释放内存
                del file_nodes
            
            # 处理目录
            dir_count = 0
            for dir_name in dirs:
                dir_node = {"name": dir_name, "children": []}
                sub_dir_path = os.path.join(dir_path, dir_name)
                
                # 计算相对路径
                rel_path = os.path.relpath(sub_dir_path, self.docs_dir).replace('\\', '/')
                dir_node["path"] = rel_path
                dir_node["is_dir"] = True
                
                # 只有深度未达到最大值时才递归处理子目录
                if current_depth < max_depth:
                    self._build_tree_sync_with_depth(sub_dir_path, dir_node, max_depth, current_depth + 1)
                else:
                    # 如果达到最大深度，添加标记表示有子内容但未加载
                    dir_node["has_children"] = True
                    logging.debug(f"目录 {rel_path} 达到最大深度，设置has_children=True标记")
                
                # 只有当目录非空或者有待加载子内容时才添加
                if dir_node["children"] or dir_node.get("has_children", False):
                    parent_node["children"].append(dir_node)
                    dir_count += 1
            
            # 对目录节点排序
            if parent_node["children"]:
                parent_node["children"] = self._sort_items(parent_node["children"])
                
            logging.debug(f"完成构建树 - 路径: {dir_path}, 添加了 {dir_count} 个目录节点")
            
        except Exception as e:
            logging.error(f"处理目录 {dir_path} 时出错: {str(e)}")
    
    def _build_tree_sync(self, dir_path, parent_node):
        """同步构建文档树，使用最大深度为无限的方式构建完整树"""
        try:
            # 调用带深度参数的方法，设置足够大的深度以构建完整树
            return self._build_tree_sync_with_depth(dir_path, parent_node, max_depth=999, current_depth=0)
        except Exception as e:
            logging.error(f"构建树失败: {str(e)}")
            # 确保失败时不会完全崩溃
            return None

    async def get_doc_content(self, path: str) -> Dict:
        """获取文档内容，改进版本，使用LRU缓存并跟踪热门文档"""
        file_path = os.path.join(self.docs_dir, path)
        
        # 记录文档访问，更新热门文档集合
        self._hot_document_access_count[path] = self._hot_document_access_count.get(path, 0) + 1
        if self._hot_document_access_count[path] >= 5:  # 访问5次以上视为热门文档
            self._hot_documents.add(path)
        
        # 简化文件存在检查
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Document not found: {path}")
        
        # 使用简单的扩展名检测
        if path.endswith('.pdf'):
            # 对于PDF文件，尝试从缓存获取元数据
            cached_pdf_data = await self._pdf_metadata_cache.get(path)
            if cached_pdf_data:
                return cached_pdf_data
            
            # 如果缓存未命中，获取基本信息
            try:
                file_size = os.path.getsize(file_path)
                last_modified = os.path.getmtime(file_path)
                
                # 尝试获取PDF页数，但设置超时
                try:
                    page_count = await self._get_pdf_page_count_with_timeout(file_path)
                except asyncio.TimeoutError:
                    logging.warning(f"获取PDF页数超时: {path}")
                    page_count = 0
                
                result = {
                    "path": path,
                    "type": "pdf",
                    "metadata": {
                        'file_size': file_size,
                        'last_modified': datetime.fromtimestamp(last_modified).isoformat(),
                        'page_count': page_count
                    },
                    "last_modified": datetime.fromtimestamp(last_modified).isoformat()
                }
                
                # 缓存结果
                await self._pdf_metadata_cache.put(path, result)
                return result
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
            cached_data = await self._content_cache.get(path)
            if cached_data:
                return cached_data

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

            # 更新缓存
            await self._content_cache.put(path, result)
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
        """获取文档的面包屑导航，使用 LRU 缓存"""
        # 尝试从缓存中获取
        cached_breadcrumb = await self._breadcrumb_cache.get(path)
        if cached_breadcrumb:
            return cached_breadcrumb

        # 缓存未命中，创建面包屑
        parts = path.split('/')
        breadcrumb = []
        current_path = ""
        
        for part in parts:
            if not part:  # 跳过空部分
                continue
                
            current_path = os.path.join(current_path, part).replace('\\', '/')
            breadcrumb.append({
                "name": part,
                "path": current_path
            })

        # 缓存结果
        await self._breadcrumb_cache.put(path, breadcrumb)
        return breadcrumb

    async def _preload_doc_tree(self):
        """预加载文档树，避免第一次请求时的延迟（现在跳过预加载）"""
        logging.info("跳过预加载文档树，将使用按需加载机制")
        # 不再预加载文档树

    async def update_reader(self, ip_address: str, path: str = ""):
        """更新读者活跃状态"""
        try:
            current_time = time.time()
            
            # 更新或添加读者记录
            self._online_readers[ip_address] = {
                "last_active": current_time,
                "current_path": path
            }
            
            logging.debug(f"更新读者状态成功: IP={ip_address}, 路径={path}, 当前在线数={len(self._online_readers)}")
            return True
        except Exception as e:
            logging.error(f"更新读者状态失败: {str(e)}")
            return False
            
    async def _cleanup_expired_readers(self):
        """清理过期的读者记录"""
        try:
            current_time = time.time()
            expired_readers = []
            
            for ip, data in self._online_readers.items():
                if current_time - data["last_active"] > self._online_expiry:
                    expired_readers.append(ip)
                    logging.debug(f"发现过期读者: IP={ip}, 最后活跃时间={data['last_active']}, 超时={current_time - data['last_active']}秒")
            
            # 清理前记录总数
            before_count = len(self._online_readers)
            
            for ip in expired_readers:
                del self._online_readers[ip]
                
            # 清理后记录总数
            after_count = len(self._online_readers)
                
            if expired_readers:
                logging.info(f"清理了 {len(expired_readers)} 个过期读者记录, 清理前={before_count}, 清理后={after_count}")
        except Exception as e:
            logging.error(f"清理过期读者记录时出错: {str(e)}")
            
    async def get_online_readers_count(self) -> int:
        """获取当前在线阅读人数"""
        try:
            # 清理前记录总数
            before_count = len(self._online_readers)
            
            # 顺便清理过期记录
            await self._cleanup_expired_readers()
            
            # 清理后的在线数量
            after_count = len(self._online_readers)
            
            if before_count != after_count:
                logging.debug(f"清理前在线人数={before_count}, 清理后在线人数={after_count}")
            
            logging.debug(f"当前在线读者IP列表: {list(self._online_readers.keys())}")
            
            return after_count
        except Exception as e:
            logging.error(f"获取在线读者数量时出错: {str(e)}")
            return 0 

    async def get_cache_stats(self):
        """获取所有缓存的统计信息"""
        content_stats = await self._content_cache.get_stats()
        pdf_stats = await self._pdf_metadata_cache.get_stats()
        breadcrumb_stats = await self._breadcrumb_cache.get_stats()
        
        return {
            "content_cache": content_stats,
            "pdf_metadata_cache": pdf_stats,
            "breadcrumb_cache": breadcrumb_stats,
            "cache_version": self._cache_version,
            "hot_documents": len(self._hot_documents)
        } 

    async def _schedule_maintenance(self):
        """定期执行维护任务"""
        while True:
            try:
                await asyncio.sleep(300)  # 每5分钟执行一次维护
                await self.perform_maintenance()
            except Exception as e:
                logging.error(f"执行维护任务时出错: {str(e)}")
                await asyncio.sleep(60)  # 出错后等待1分钟再尝试 
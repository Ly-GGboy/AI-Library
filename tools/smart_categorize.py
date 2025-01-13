import os
import json
import shutil
import hashlib
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set
from collections import defaultdict

# 添加项目根目录到Python路径
ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))

def check_dependencies():
    """检查必要的依赖是否已安装"""
    try:
        import openai
    except ImportError:
        print("正在安装必要的依赖...")
        os.system(f"{sys.executable} -m pip install openai")

class CategoryCache:
    """分类缓存管理"""
    def __init__(self, cache_file: Path):
        self.cache_file = cache_file
        self.cache = self._load_cache()
    
    def _load_cache(self) -> Dict:
        """加载缓存数据"""
        default_cache = {
            "articles": {},  # 文章分类缓存
            "categories": {},  # 分类结构
            "stats": {  # 统计信息
                "total_courses": 0,
                "total_categories": 0,
                "category_counts": {},  # 每个分类下的课程数量
                "processed_courses": set()  # 已处理的课程集合
            }
        }
        
        if self.cache_file.exists():
            try:
                cache_data = json.loads(self.cache_file.read_text(encoding='utf-8'))
                # 确保 stats 和 processed_courses 存在且为正确类型
                if "stats" not in cache_data:
                    cache_data["stats"] = default_cache["stats"]
                if "processed_courses" not in cache_data["stats"]:
                    cache_data["stats"]["processed_courses"] = set()
                elif isinstance(cache_data["stats"]["processed_courses"], list):
                    cache_data["stats"]["processed_courses"] = set(cache_data["stats"]["processed_courses"])
                return cache_data
            except Exception as e:
                print(f"Warning: Failed to load cache: {e}")
                return default_cache
        return default_cache
    
    def _save_cache(self) -> None:
        """保存缓存数据"""
        try:
            # 将set转换为list以便JSON序列化
            cache_copy = self.cache.copy()
            if "stats" in cache_copy and "processed_courses" in cache_copy["stats"]:
                cache_copy["stats"]["processed_courses"] = list(cache_copy["stats"]["processed_courses"])
            
            self.cache_file.write_text(
                json.dumps(cache_copy, ensure_ascii=False, indent=2),
                encoding='utf-8'
            )
        except Exception as e:
            print(f"Warning: Failed to save cache: {e}")
    
    def check_duplicate_course(self, course_path: Path) -> Optional[str]:
        """检查课程是否已经被分类过"""
        course_id = str(course_path)
        if course_id in self.cache["stats"].get("processed_courses", set()):
            # 查找课程所在的分类
            for category, courses in self.cache["categories"].items():
                if any(course_id in c for c in courses):
                    return category
        return None
    
    def add_processed_course(self, course_path: Path, category: str) -> None:
        """添加已处理的课程记录"""
        if "stats" not in self.cache:
            self.cache["stats"] = {
                "total_courses": 0,
                "total_categories": 0,
                "category_counts": {},
                "processed_courses": set()
            }
        
        stats = self.cache["stats"]
        # 确保 processed_courses 是 set 类型
        if not isinstance(stats["processed_courses"], set):
            stats["processed_courses"] = set(stats["processed_courses"] if isinstance(stats["processed_courses"], list) else [])
        
        course_id = str(course_path)
        if course_id not in stats["processed_courses"]:
            stats["processed_courses"].add(course_id)
            stats["total_courses"] += 1
            stats["category_counts"][category] = stats["category_counts"].get(category, 0) + 1
            stats["total_categories"] = len(stats["category_counts"])
        
        self._save_cache()
    
    def get_statistics(self) -> Dict:
        """获取分类统计信息"""
        stats = self.cache.get("stats", {})
        # 确保返回的 processed_courses 是 set 类型
        if "processed_courses" in stats:
            if not isinstance(stats["processed_courses"], set):
                stats["processed_courses"] = set(stats["processed_courses"] if isinstance(stats["processed_courses"], list) else [])
        else:
            stats["processed_courses"] = set()
        return stats
    
    def get_article_category(self, article_path: Path) -> Optional[Dict]:
        """获取文章的分类信息"""
        article_hash = self._get_article_hash(article_path)
        return self.cache["articles"].get(article_hash)
    
    def set_article_category(self, article_path: Path, category_info: Dict) -> None:
        """设置文章的分类信息"""
        article_hash = self._get_article_hash(article_path)
        self.cache["articles"][article_hash] = category_info
        self._save_cache()
    
    def _get_article_hash(self, article_path: Path) -> str:
        """计算文章的哈希值（基于内容和修改时间）"""
        try:
            content = article_path.read_bytes()
            mtime = str(article_path.stat().st_mtime)
            return hashlib.md5(content + mtime.encode()).hexdigest()
        except Exception:
            return str(article_path)
    
    def get_existing_categories(self) -> Dict[str, List[str]]:
        """获取现有分类信息"""
        return self.cache.get("categories", {})
    
    def update_categories(self, categories: Dict[str, List[str]]) -> None:
        """更新分类信息"""
        self.cache["categories"] = categories
        self._save_cache()

def read_markdown_content(file_path: str, max_chars: int = 1000) -> str:
    """读取markdown文件的内容，返回开头的一部分用于分析"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read(max_chars)
            return content
    except Exception as e:
        print(f"Warning: Failed to read {file_path}: {e}")
        return ""

def get_category_from_llm(title: str, content: str = None) -> Dict:
    """使用LLM对文章进行分类"""
    from tools.llm_api import query_llm
    
    # 构建分析文本
    analysis_text = f"课程/文章名称: {title}\n"
    if content:
        analysis_text += f"\n内容开头:\n{content[:300]}"
    
    prompt = f"""分析以下内容的主题，给出最合适的两级分类。

{analysis_text}

返回格式:
{{
    "category": "一级分类/二级分类",
    "confidence": 0.95,
    "explanation": "一句话解释分类理由"
}}

要求：
1. 使用两级分类结构，格式为"一级分类/二级分类"，例如：
   - 编程语言/Java
   - 编程语言/Go
   - 系统架构/微服务
   - 系统架构/分布式系统
   - 数据库/关系型数据库
   - 数据库/NoSQL
   - 云计算/容器技术
   - 开发工具/版本控制
   - 职业成长/技术管理
   等

2. 一级分类要求：
   - 使用宏观的技术领域作为一级分类
   - 保持在10-15个大类以内
   - 类别之间界限要清晰

3. 二级分类要求：
   - 在一级分类下进行合理的细分
   - 不要过于具体，一个二级分类应该能容纳多个相关主题
   - 避免过度细分，如不要细分到具体的技术版本或特定功能

4. confidence为0-1之间的数字，表示分类的确定程度
5. explanation用一句话说明选择该分类的理由，解释为什么选择这个一级分类和二级分类
"""
    
    try:
        print("\n正在调用LLM进行分类...")
        response = query_llm(prompt)
        print(f"\nLLM原始响应:\n{response}")
        
        if not response:
            raise Exception("LLM返回为空")
            
        # 尝试清理响应文本，只保留JSON部分
        response = response.strip()
        if response.startswith('```json'):
            response = response[7:]
        if response.startswith('```'):
            response = response[3:]
        if response.endswith('```'):
            response = response[:-3]
        response = response.strip()
        
        result = json.loads(response)
        
        # 验证返回的JSON格式是否符合要求
        required_fields = ['category', 'confidence', 'explanation']
        for field in required_fields:
            if field not in result:
                raise Exception(f"返回结果缺少必要字段: {field}")
        
        # 验证confidence值是否在合理范围内
        if not isinstance(result['confidence'], (int, float)) or not 0 <= result['confidence'] <= 1:
            result['confidence'] = 0.5  # 使用默认值
            
        return result
    except Exception as e:
        print(f"Warning: LLM classification failed: {e}")
        return {
            "category": "未分类",
            "confidence": 0.0,
            "explanation": f"分类失败: {str(e)}"
        }

def load_existing_categories(base_dir: str) -> Dict[str, List[str]]:
    """加载已有的分类结构"""
    categories = defaultdict(list)
    base_path = Path(base_dir)
    
    if base_path.exists():
        for category_dir in base_path.iterdir():
            if category_dir.is_dir() and not category_dir.name.startswith('.'):
                categories[category_dir.name] = [
                    f.name for f in category_dir.iterdir() 
                    if f.is_dir() and not f.name.startswith('.')  # 查找文章目录而不是单个文件
                ]
    
    return categories

def suggest_similar_category(new_category: str, existing_categories: List[str]) -> Optional[str]:
    """使用LLM建议是否应该合并到现有类别中"""
    if not existing_categories:
        return None
        
    from tools.llm_api import query_llm
    
    prompt = f"""分析以下分类名称，判断是否需要合并到现有类别。

新分类: {new_category}
现有分类: {', '.join(existing_categories)}

返回格式:
{{
    "should_merge": true或false,
    "target_category": "目标分类名称",
    "explanation": "一句话解释原因"
}}

要求：
1. 分析两级分类的语义关联度
2. 判断标准：
   - 如果一级分类相同，二级分类相近，应该合并
   - 如果一级分类不同但表达相似概念，考虑统一到更合适的一级分类
   - 如果确实是不同的技术领域，保持独立

3. 合并原则：
   - 优先保持一级分类的稳定性
   - 在同一个一级分类下合并相近的二级分类
   - 合并时使用更准确、更通用的分类名称

4. 示例：
   - "编程语言/Java并发" 应该合并到 "编程语言/Java"
   - "数据库/MySQL优化" 应该合并到 "数据库/关系型数据库"
   - "系统架构/微服务设计" 应该合并到 "系统架构/微服务"
"""
    
    try:
        print("\n正在调用LLM判断类别合并...")
        response = query_llm(prompt)
        print(f"\nLLM原始响应:\n{response}")
        
        if not response:
            return None
            
        # 尝试清理响应文本，只保留JSON部分
        response = response.strip()
        if response.startswith('```json'):
            response = response[7:]
        if response.startswith('```'):
            response = response[3:]
        if response.endswith('```'):
            response = response[:-3]
        response = response.strip()
        
        result = json.loads(response)
        if result.get("should_merge"):
            return result["target_category"]
    except Exception as e:
        print(f"Warning: Category suggestion failed: {e}")
    
    return None

def move_article_directory(src_dir: Path, dst_dir: Path) -> None:
    """移动整个文章目录（包括文章文件和图片）"""
    try:
        if src_dir.exists():
            # 如果目标目录已存在，先删除
            if dst_dir.exists():
                shutil.rmtree(dst_dir)
            # 移动整个目录
            shutil.copytree(src_dir, dst_dir)
            print(f"成功移动目录: {src_dir.name} -> {dst_dir}")
    except Exception as e:
        print(f"Warning: Failed to move directory {src_dir}: {e}")

def create_category_structure(docs_dir: str, categorized: Dict[str, List[Dict]], dry_run: bool = False) -> None:
    """创建分类目录结构"""
    # 使用绝对路径
    docs_path = Path(docs_dir).resolve()
    base_dir = docs_path / "智能分类"
    print(f"\n创建分类目录: {base_dir}")
    
    if not dry_run:
        base_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成分类报告
    report = ["# 文章智能分类报告\n"]
    
    # 添加统计信息
    total_articles = sum(len(articles) for articles in categorized.values())
    total_categories = len(categorized)
    report.append(f"\n## 统计信息")
    report.append(f"- 总课程数：{total_articles}")
    report.append(f"- 总分类数：{total_categories}\n")
    report.append("\n## 分类详情")
    
    # 按分类下的文章数量排序
    sorted_categories = sorted(categorized.items(), 
                             key=lambda x: len(x[1]), 
                             reverse=True)
    
    for category, articles in sorted_categories:
        report.append(f"\n### {category} ({len(articles)}篇)")
        # 处理可能包含斜杠的分类名称
        category_parts = category.split('/')
        current_dir = base_dir
        
        # 逐级创建目录
        for part in category_parts:
            current_dir = current_dir / part
            if not dry_run:
                current_dir.mkdir(parents=True, exist_ok=True)
                print(f"创建目录: {current_dir}")
        
        for article in articles:
            report.append(f"\n#### {article['title']}")
            report.append(f"- 置信度: {article['confidence']:.2%}")
            report.append(f"- 分类理由: {article['explanation']}")
            
            if not dry_run:
                # 移动整个文章目录
                src_dir = docs_path / article['dirname']
                dst_dir = current_dir / article['dirname'].split('/')[-1]
                
                if not src_dir.exists():
                    print(f"警告: 源目录不存在: {src_dir}")
                    continue
                    
                try:
                    if dst_dir.exists():
                        shutil.rmtree(dst_dir)
                    shutil.copytree(src_dir, dst_dir)
                    print(f"成功移动目录: {src_dir.name} -> {dst_dir}")
                except Exception as e:
                    print(f"移动目录失败 {src_dir.name}: {e}")
    
    # 保存分类报告
    report_path = base_dir / "分类报告.md"
    if not dry_run:
        report_path.write_text("\n".join(report), encoding='utf-8')
        print(f"\n分类报告已保存到: {report_path}")
    else:
        print("\n".join(report))

def get_article_directories(articles_dir: Path) -> List[Path]:
    """获取所有文章目录"""
    return [d for d in articles_dir.iterdir() 
            if d.is_dir() and not d.name.startswith('.') and d.name != 'images']

def process_article_directory(
    article_dir: Path,
    existing_categories: Dict[str, List[str]],
    cache: CategoryCache,
    force_update: bool = False
) -> Optional[Dict]:
    """处理单个文章目录"""
    # 检查目录是否存在
    if not article_dir.exists():
        print(f"警告: 目录不存在: {article_dir}")
        return None
        
    # 检查是否已经处理过
    if not force_update:
        existing_category = cache.check_duplicate_course(article_dir)
        if existing_category:
            print(f"使用缓存的分类结果: {existing_category}")
            return {
                "category": existing_category,
                "confidence": 0.95,
                "explanation": "使用缓存的分类结果"
            }
    
    # 查找目录中的主markdown文件
    md_files = list(article_dir.glob("*.md"))
    if not md_files:
        print(f"警告: 目录中没有找到markdown文件: {article_dir}")
        return None
    
    main_file = md_files[0]
    
    # 检查缓存
    if not force_update:
        cached_result = cache.get_article_category(main_file)
        if cached_result:
            print(f"使用缓存的分类结果: {cached_result['category']}")
            return cached_result
    
    # 读取文章内容
    content = read_markdown_content(str(main_file))
    
    # 使用LLM进行分类
    result = get_category_from_llm(article_dir.name, content)
    
    # 更新缓存和统计信息
    if result["category"] != "未分类":
        cache.set_article_category(main_file, result)
        cache.add_processed_course(article_dir, result["category"])
    
    return result

def optimize_category_structure(base_dir: Path, cache: CategoryCache, dry_run: bool = False) -> None:
    """优化分类目录结构"""
    print("\n开始分析分类结构...")
    
    # 获取现有分类结构
    categories = load_existing_categories(str(base_dir / "智能分类"))
    if not categories:
        print("没有找到现有的分类结构")
        return
        
    # 打印当前结构
    print("\n当前分类结构：")
    for category, courses in categories.items():
        print(f"\n{category} ({len(courses)}个课程):")
        for course in courses:
            print(f"  - {course}")
    
    # 分析需要合并的分类
    merge_suggestions = []
    category_list = list(categories.keys())
    
    from tools.llm_api import query_llm
    
    # 分析所有分类对
    for i in range(len(category_list)):
        for j in range(i + 1, len(category_list)):
            cat1, cat2 = category_list[i], category_list[j]
            # 如果某个分类下课程较少，更倾向于合并
            should_analyze = (len(categories[cat1]) <= 2 or len(categories[cat2]) <= 2)
            
            if should_analyze:
                prompt = f"""分析以下两个技术文章分类的相似度：

分类1: {cat1}
分类1下的课程：{', '.join(categories[cat1])}

分类2: {cat2}
分类2下的课程：{', '.join(categories[cat2])}

返回格式：
{{
    "should_merge": true或false,
    "target_category": "合并后的分类名称",
    "similarity": 0.8,  # 0-1之间的相似度
    "explanation": "一句话解释合并理由"
}}

要求：
1. 分析两个分类的课程内容和主题
2. 判断是否属于同一技术领域或相近领域
3. 如果建议合并，给出最合适的分类名称（可以是现有分类名或新名称）
4. 相似度超过0.7才建议合并

只需返回一个JSON对象，不要包含其他文字。
"""
                try:
                    print(f"\n分析分类对: {cat1} - {cat2}")
                    response = query_llm(prompt)
                    print(f"LLM响应: {response}")
                    
                    # 清理响应文本，只保留JSON部分
                    response = response.strip()
                    if response.startswith('```json'):
                        response = response[7:]
                    if response.startswith('```'):
                        response = response[3:]
                    if response.endswith('```'):
                        response = response[:-3]
                    response = response.strip()
                    
                    result = json.loads(response)
                    
                    # 验证返回的JSON格式是否符合要求
                    required_fields = ['should_merge', 'target_category', 'similarity', 'explanation']
                    for field in required_fields:
                        if field not in result:
                            raise Exception(f"返回结果缺少必要字段: {field}")
                    
                    if result.get("should_merge", False) and result.get("similarity", 0) > 0.7:
                        merge_suggestions.append({
                            "source": cat1,
                            "target": cat2,
                            "new_name": result["target_category"],
                            "similarity": result["similarity"],
                            "explanation": result["explanation"]
                        })
                except json.JSONDecodeError as e:
                    print(f"JSON解析失败: {e}")
                    print(f"原始响应: {response}")
                    continue
                except Exception as e:
                    print(f"分析失败: {e}")
                    continue
    
    if not merge_suggestions:
        print("\n没有发现需要合并的分类。")
        return
    
    # 按相似度排序
    merge_suggestions.sort(key=lambda x: x["similarity"], reverse=True)
    
    # 显示合并建议
    print("\n建议的合并方案：")
    for i, suggestion in enumerate(merge_suggestions, 1):
        print(f"\n{i}. 建议合并:")
        print(f"   - 源分类: {suggestion['source']} ({len(categories[suggestion['source']])}个课程)")
        print(f"   - 目标分类: {suggestion['target']} ({len(categories[suggestion['target']])}个课程)")
        print(f"   - 建议名称: {suggestion['new_name']}")
        print(f"   - 相似度: {suggestion['similarity']:.2f}")
        print(f"   - 原因: {suggestion['explanation']}")
    
    if dry_run:
        print("\n这是演示运行，不执行实际合并操作。")
        return
    
    # 询问是否执行合并
    response = input("\n是否执行推荐的合并方案？(y/n): ")
    if response.lower() != 'y':
        print("取消合并操作。")
        return
    
    # 执行合并
    base_path = base_dir / "智能分类"
    for suggestion in merge_suggestions:
        source_dir = base_path / suggestion["source"]
        target_dir = base_path / suggestion["target"]
        new_dir = base_path / suggestion["new_name"]
        
        if not source_dir.exists() or not target_dir.exists():
            print(f"跳过: 目录不存在 ({source_dir} 或 {target_dir})")
            continue
        
        print(f"\n合并 {suggestion['source']} 到 {suggestion['new_name']}...")
        
        # 创建新目录（如果需要）
        if suggestion["new_name"] not in categories:
            new_dir.mkdir(parents=True, exist_ok=True)
        
        # 移动课程
        for course in categories[suggestion["source"]]:
            src_course = source_dir / course
            dst_course = new_dir / course
            if src_course.exists():
                try:
                    if dst_course.exists():
                        shutil.rmtree(dst_course)
                    shutil.move(str(src_course), str(dst_course))
                    print(f"  移动: {course}")
                except Exception as e:
                    print(f"  移动失败 {course}: {e}")
        
        # 移动目标分类的课程（如果新名称不同）
        if suggestion["new_name"] != suggestion["target"]:
            for course in categories[suggestion["target"]]:
                src_course = target_dir / course
                dst_course = new_dir / course
                if src_course.exists():
                    try:
                        if dst_course.exists():
                            shutil.rmtree(dst_course)
                        shutil.move(str(src_course), str(dst_course))
                        print(f"  移动: {course}")
                    except Exception as e:
                        print(f"  移动失败 {course}: {e}")
        
        # 删除旧目录
        try:
            if source_dir.exists():
                shutil.rmtree(source_dir)
            if suggestion["new_name"] != suggestion["target"] and target_dir.exists():
                shutil.rmtree(target_dir)
        except Exception as e:
            print(f"删除旧目录失败: {e}")
        
        # 更新缓存中的分类信息
        new_categories = load_existing_categories(str(base_path))
        cache.update_categories(new_categories)
    
    print("\n合并完成！")

def main(
    docs_dir: str = "server/static/docs/专栏",
    test_dir: Optional[str] = None,
    dry_run: bool = False,
    force_update: bool = False,
    optimize: bool = False
):
    """主函数"""
    # 检查依赖
    check_dependencies()
    
    docs_path = Path(docs_dir)
    if not docs_path.exists():
        raise ValueError(f"文档目录不存在: {docs_path}")
    
    # 初始化缓存
    cache = CategoryCache(docs_path / ".category_cache.json")
    
    if optimize:
        optimize_category_structure(docs_path, cache, dry_run)
        return
    
    # 加载已有的分类结构
    existing_categories = load_existing_categories(docs_path / "智能分类")
    if existing_categories:
        cache.update_categories(existing_categories)
    
    # 用于存储分类结果
    categorized = defaultdict(list)
    
    if test_dir:
        # 测试模式：只处理指定目录
        # 处理绝对路径或相对路径
        test_path = Path(test_dir)
        if test_path.is_absolute():
            # 如果是绝对路径，转换为相对于docs_path的路径
            try:
                test_path = test_path.relative_to(docs_path)
            except ValueError:
                print(f"Warning: 测试目录 {test_dir} 不在文档目录下")
                return
        
        test_path = docs_path / test_path
        if not test_path.exists():
            raise ValueError(f"测试目录不存在: {test_path}")
        
        print(f"\n测试模式：处理目录 {test_path.name}")
        result = process_article_directory(test_path, existing_categories, cache, force_update)
        if result:
            categorized[result["category"]].append({
                "title": test_path.name,
                "dirname": str(test_path.relative_to(docs_path)),  # 保存相对路径
                "confidence": result["confidence"],
                "explanation": result["explanation"]
            })
    else:
        # 正常模式：处理所有文章目录
        # 遍历所有一级目录
        for article_dir in docs_path.iterdir():
            if not article_dir.is_dir() or article_dir.name.startswith('.') or article_dir.name == "智能分类":
                continue
                
            print(f"\n处理目录: {article_dir.name}")
            
            # 如果是文章目录，直接处理
            if list(article_dir.glob("*.md")):
                result = process_article_directory(article_dir, existing_categories, cache, force_update)
                if result:
                    categorized[result["category"]].append({
                        "title": article_dir.name,
                        "dirname": str(article_dir.relative_to(docs_path)),  # 保存相对路径
                        "confidence": result["confidence"],
                        "explanation": result["explanation"]
                    })
            else:
                # 如果是系列目录，处理其下的所有文章目录
                for sub_dir in article_dir.iterdir():
                    if not sub_dir.is_dir() or sub_dir.name.startswith('.'):
                        continue
                        
                    print(f"  处理子目录: {sub_dir.name}")
                    result = process_article_directory(sub_dir, existing_categories, cache, force_update)
                    if result:
                        categorized[result["category"]].append({
                            "title": sub_dir.name,
                            "dirname": str(sub_dir.relative_to(docs_path)),  # 保存相对路径
                            "confidence": result["confidence"],
                            "explanation": result["explanation"]
                        })
    
    # 创建目录结构
    create_category_structure(docs_dir, categorized, dry_run)
    
    if dry_run:
        print("\n这是演示运行，没有实际创建文件。")
    else:
        print(f"\n分类完成！分类报告已保存到: {docs_dir}/智能分类/分类报告.md")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="智能文章分类工具")
    parser.add_argument("--docs-dir", default="server/static/docs/专栏", help="文档根目录")
    parser.add_argument("--test-dir", help="指定要测试的文章目录名称（可以是相对路径或绝对路径）")
    parser.add_argument("--dry-run", action="store_true", help="演示运行，不实际创建文件")
    parser.add_argument("--force-update", action="store_true", help="强制更新，忽略缓存")
    parser.add_argument("--optimize", action="store_true", help="优化分类结构")
    args = parser.parse_args()
    
    main(args.docs_dir, args.test_dir, args.dry_run, args.force_update, args.optimize) 
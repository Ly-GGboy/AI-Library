import os
import shutil
import re
from pathlib import Path
from typing import Dict, List, Set

# 分类规则定义
CATEGORIES = {
    "java_core": {
        "name": "Java基础",
        "keywords": ["Java", "ThreadLocal", "AQS", "线程池", "并发", "IO", "NIO", "Unsafe", "直接内存"]
    },
    "jvm": {
        "name": "JVM",
        "keywords": ["JVM", "垃圾收集", "GC", "内存", "虚拟机"]
    },
    "spring": {
        "name": "Spring生态",
        "keywords": ["Spring", "Bean", "MVC", "Boot", "MyBatis"]
    },
    "mysql": {
        "name": "MySQL",
        "keywords": ["MySQL", "InnoDB", "索引", "事务", "锁", "主从"]
    },
    "redis": {
        "name": "Redis",
        "keywords": ["Redis", "缓存", "Cache"]
    },
    "elasticsearch": {
        "name": "搜索引擎",
        "keywords": ["Elasticsearch", "搜索"]
    },
    "distributed_storage": {
        "name": "分布式存储",
        "keywords": ["存储", "PolarDB", "PolarFS", "KV"]
    },
    "distributed_system": {
        "name": "分布式系统",
        "keywords": ["分布式", "一致性", "Raft", "链路追踪", "注册中心"]
    },
    "microservice": {
        "name": "微服务",
        "keywords": ["微服务", "SpringCloud", "Eureka", "Zookeeper", "Nacos"]
    },
    "message_queue": {
        "name": "消息队列",
        "keywords": ["消息", "Kafka", "RocketMQ", "RabbitMQ", "ActiveMQ"]
    },
    "architecture": {
        "name": "架构设计",
        "keywords": ["架构", "设计", "DDD", "领域驱动", "中台"]
    },
    "performance": {
        "name": "性能优化",
        "keywords": ["性能", "优化", "调优"]
    },
    "monitoring": {
        "name": "系统监控",
        "keywords": ["监控", "日志", "追踪"]
    },
    "cloud_native": {
        "name": "云原生",
        "keywords": ["Docker", "K8s", "Kubernetes", "容器", "镜像"]
    },
    "best_practice": {
        "name": "最佳实践",
        "keywords": ["实践", "方案", "解决", "经验"]
    }
}

def sanitize_path(path: str) -> str:
    """清理路径中的特殊字符"""
    return re.sub(r'[<>:"/\\|?*]', '_', path)

def get_category(filename: str) -> str:
    """根据文件名确定分类"""
    filename = filename.lower()
    max_score = 0
    best_category = "其他"
    
    for category, info in CATEGORIES.items():
        score = 0
        for keyword in info["keywords"]:
            if keyword.lower() in filename:
                score += 1
        if score > max_score:
            max_score = score
            best_category = info["name"]
    
    return best_category

def categorize_articles(docs_dir: str) -> Dict[str, List[str]]:
    """对文章进行分类"""
    articles_dir = os.path.join(docs_dir, "文章")
    if not os.path.exists(articles_dir):
        raise ValueError(f"文章目录不存在: {articles_dir}")

    # 创建分类结果字典
    categorized = {info["name"]: [] for info in CATEGORIES.values()}
    categorized["其他"] = []

    # 遍历文章进行分类
    for filename in os.listdir(articles_dir):
        if filename == "images" or filename.startswith('.'):
            continue
        
        category = get_category(filename)
        categorized[category].append(filename)

    return categorized

def create_category_structure(docs_dir: str, categorized: Dict[str, List[str]]) -> None:
    """创建分类目录结构并移动文件"""
    articles_dir = os.path.join(docs_dir, "文章")
    new_structure_dir = os.path.join(docs_dir, "技术文章")
    
    # 创建新的目录结构
    os.makedirs(new_structure_dir, exist_ok=True)
    
    # 移动文件到对应目录
    for category, files in categorized.items():
        if not files:  # 跳过空分类
            continue
            
        category_dir = os.path.join(new_structure_dir, sanitize_path(category))
        os.makedirs(category_dir, exist_ok=True)
        
        for filename in files:
            src = os.path.join(articles_dir, filename)
            dst = os.path.join(category_dir, filename)
            if os.path.exists(src):
                shutil.copy2(src, dst)  # 使用copy2保留元数据

    # 复制images目录
    images_src = os.path.join(articles_dir, "images")
    images_dst = os.path.join(new_structure_dir, "images")
    if os.path.exists(images_src):
        shutil.copytree(images_src, images_dst, dirs_exist_ok=True)

def generate_report(categorized: Dict[str, List[str]]) -> str:
    """生成分类报告"""
    report = "# 文章分类报告\n\n"
    
    for category, files in categorized.items():
        if not files:  # 跳过空分类
            continue
            
        report += f"## {category} ({len(files)}篇)\n"
        for filename in sorted(files):
            report += f"- {filename}\n"
        report += "\n"
    
    return report

def main():
    docs_dir = "server/static/docs"
    
    # 1. 对文章进行分类
    print("正在对文章进行分类...")
    categorized = categorize_articles(docs_dir)
    
    # 2. 创建新的目录结构
    print("正在创建新的目录结构...")
    create_category_structure(docs_dir, categorized)
    
    # 3. 生成报告
    print("正在生成分类报告...")
    report = generate_report(categorized)
    
    # 保存报告
    report_path = os.path.join(docs_dir, "技术文章", "分类报告.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"\n分类完成！报告已保存到: {report_path}")
    print("新的文章结构已创建在 技术文章 目录下")
    print("原文章目录保持不变")

if __name__ == "__main__":
    main() 
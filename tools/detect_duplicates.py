import os
import sys
import json
import hashlib
import difflib
from pathlib import Path
from typing import Dict, List, Tuple, Set
from collections import defaultdict

# 添加项目根目录到Python路径
ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))

def get_content_hash(file_path: Path) -> str:
    """计算文件内容的哈希值"""
    try:
        content = file_path.read_bytes()
        return hashlib.md5(content).hexdigest()
    except Exception as e:
        print(f"Warning: Failed to hash {file_path}: {e}")
        return ""

def normalize_filename(filename: str) -> str:
    """标准化文件名以便比较"""
    # 移除所有空格、下划线和破折号
    filename = filename.replace(" ", "").replace("_", "").replace("-", "")
    # 移除常见的前缀和后缀
    filename = filename.replace("第", "").replace("讲", "").replace("课", "")
    filename = filename.replace("例", "").replace("节", "").replace("章", "")
    filename = filename.replace("完", "").replace("copy", "")
    filename = filename.replace(".md", "")
    # 替换常见的同义词
    filename = filename.replace("实战", "").replace("实践", "")
    filename = filename.replace("开发", "").replace("编程", "")
    filename = filename.replace("错误", "").replace("常见错误", "")
    filename = filename.replace("示例", "").replace("案例", "")
    # 转换为小写
    return filename.lower()

def is_similar_name(name1: str, name2: str) -> bool:
    """判断两个名称是否相似"""
    # 标准化名称
    norm1 = normalize_filename(name1)
    norm2 = normalize_filename(name2)
    
    # 完全相同
    if norm1 == norm2:
        return True
        
    # 一个是另一个的子串
    if norm1 in norm2 or norm2 in norm1:
        return True
        
    # 计算相似度
    matcher = difflib.SequenceMatcher(None, norm1, norm2)
    return matcher.ratio() > 0.8

def get_content_similarity(file1: Path, file2: Path) -> float:
    """计算两个文件内容的相似度"""
    try:
        # 首先比较文件名
        name1 = normalize_filename(file1.name)
        name2 = normalize_filename(file2.name)
        if name1 == name2:
            return 1.0
            
        # 如果文件名不完全相同，计算内容相似度
        content1 = file1.read_text(encoding='utf-8').splitlines()
        content2 = file2.read_text(encoding='utf-8').splitlines()
        matcher = difflib.SequenceMatcher(None, content1, content2)
        return matcher.ratio()
    except Exception as e:
        print(f"Warning: Failed to compare {file1} and {file2}: {e}")
        return 0.0

def find_markdown_files(directory: Path) -> List[Path]:
    """查找目录中的所有markdown文件"""
    return list(directory.glob("**/*.md"))

def analyze_course_content(course_dir: Path, max_files: int = 5) -> Dict:
    """分析课程内容，返回课程信息"""
    # 递归查找所有markdown文件
    md_files = list(course_dir.glob("**/*.md"))
    if not md_files:
        return {}
    
    # 选择前max_files个文件
    selected_files = md_files[:max_files]
    content_hashes = [get_content_hash(f) for f in selected_files]
    
    return {
        "path": str(course_dir),
        "name": course_dir.name,
        "files": [str(f) for f in selected_files],
        "filenames": [f.name for f in selected_files],  # 添加文件名列表
        "content_hashes": content_hashes,
        "size": sum(f.stat().st_size for f in selected_files)
    }

def detect_duplicates(
    classified_dir: Path,
    new_dir: Path,
    similarity_threshold: float = 0.8,
    min_similar_files: int = 2
) -> Tuple[List[Dict], List[str]]:
    """检测重复的课程"""
    print("\n开始检测重复课程...")
    
    # 分析已分类的课程
    classified_courses = []
    
    print("\n正在扫描已分类课程...")
    # 递归遍历所有子目录
    for category_dir in classified_dir.rglob("*"):
        if not category_dir.is_dir() or category_dir.name.startswith('.'):
            continue
            
        # 检查是否是课程目录（包含markdown文件）
        md_files = list(category_dir.glob("*.md"))
        if md_files:
            course_info = analyze_course_content(category_dir)
            if course_info:
                # 记录分类路径（相对于classified_dir的路径）
                try:
                    course_info["category"] = str(category_dir.relative_to(classified_dir).parent)
                except ValueError:
                    course_info["category"] = ""
                classified_courses.append(course_info)
                print(f"已扫描: {course_info['name']} ({len(course_info['files'])} 个文件)")
    
    print(f"\n已分析 {len(classified_courses)} 个已分类课程")
    
    # 分析新课程
    new_courses = []
    duplicates = []
    
    print("\n开始分析新课程...")
    # 递归遍历所有子目录查找新课程
    for course_dir in new_dir.rglob("*"):
        if not course_dir.is_dir() or course_dir.name.startswith('.'):
            continue
            
        # 检查是否是课程目录（包含markdown文件）
        md_files = list(course_dir.glob("*.md"))
        if not md_files:
            continue
            
        course_info = analyze_course_content(course_dir)
        if not course_info:
            continue
            
        new_courses.append(course_info)
        print(f"\n分析新课程: {course_info['name']}")
        
        # 检查每个已分类的课程
        for classified in classified_courses:
            similar_files = 0
            total_similarity = 0.0
            debug_info = []
            
            # 比较每个文件
            for i, new_file in enumerate(course_info["files"]):
                if i >= len(classified["files"]):
                    break
                    
                new_filename = course_info["filenames"][i]
                classified_filename = classified["filenames"][i]
                
                # 比较哈希值
                if course_info["content_hashes"][i] == classified["content_hashes"][i]:
                    similar_files += 1
                    total_similarity += 1.0
                    debug_info.append(f"内容完全匹配: {new_filename} vs {classified_filename}")
                    continue
                    
                # 如果哈希值不同，计算内容相似度
                similarity = get_content_similarity(
                    Path(new_file),
                    Path(classified["files"][i])
                )
                
                if similarity >= similarity_threshold:
                    similar_files += 1
                    total_similarity += similarity
                    debug_info.append(f"内容相似 ({similarity:.2%}): {new_filename} vs {classified_filename}")
            
            # 如果相似文件数量达到阈值，认为是重复课程
            if similar_files >= min_similar_files:
                avg_similarity = total_similarity / similar_files
                duplicates.append({
                    "new_course": course_info,
                    "existing_course": classified,
                    "similarity": avg_similarity,
                    "similar_files": similar_files,
                    "match_type": "exact" if avg_similarity == 1.0 else "similar",
                    "debug_info": debug_info
                })
                print(f"发现重复:")
                print(f"- 已有课程: {classified['name']} ({classified['category']})")
                print(f"- 相似文件数: {similar_files}")
                print(f"- 平均相似度: {avg_similarity:.2%}")
                print("匹配详情:")
                for info in debug_info:
                    print(f"  {info}")
    
    print(f"\n已分析 {len(new_courses)} 个新课程")
    print(f"发现 {len(duplicates)} 个重复课程")
    
    # 生成移除脚本
    remove_script = []
    remove_script.append("#!/bin/bash")
    remove_script.append("\n# 自动生成的重复课程移除脚本")
    remove_script.append("# 请在执行前仔细检查要删除的目录\n")
    
    for dup in duplicates:
        remove_script.append(f"# {dup['new_course']['name']}")
        remove_script.append(f"# - 与已有课程 '{dup['existing_course']['name']}' ({dup['existing_course']['category']}) 重复")
        remove_script.append(f"# - 相似度: {dup['similarity']:.2%}")
        remove_script.append(f"# - 相似文章数: {dup['similar_files']} 篇")
        for info in dup['debug_info']:
            remove_script.append(f"# - {info}")
        remove_script.append(f"rm -rf \"{dup['new_course']['path']}\"\n")
    
    return duplicates, remove_script

def generate_report(
    duplicates: List[Dict],
    remove_script: List[str],
    output_dir: Path
) -> None:
    """生成重复课程报告"""
    # 创建输出目录
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成报告
    report = ["# 重复课程检测报告\n"]
    
    # 添加统计信息
    report.append("## 统计信息")
    report.append(f"- 发现重复课程：{len(duplicates)} 个\n")
    
    # 添加重复课程详情
    report.append("## 重复课程详情")
    for dup in duplicates:
        report.append(f"\n### {dup['new_course']['name']}")
        report.append(f"- 路径：{dup['new_course']['path']}")
        report.append(f"- 重复类型：{'完全重复' if dup['match_type'] == 'exact' else '内容相似'}")
        report.append(f"- 平均相似度：{dup['similarity']:.2%}")
        report.append(f"- 相似文章数：{dup['similar_files']} 篇")
        report.append("\n比对的文件：")
        for f in dup['new_course']['files']:
            report.append(f"- {Path(f).name}")
        
        report.append("\n与已有课程：")
        report.append(f"- 名称：{dup['existing_course']['name']}")
        report.append(f"- 分类：{dup['existing_course']['category']}")
        report.append(f"- 路径：{dup['existing_course']['path']}")
        report.append("\n比对的文件：")
        for f in dup['existing_course']['files']:
            report.append(f"- {Path(f).name}")
    
    # 保存报告
    report_path = output_dir / "重复课程报告.md"
    report_path.write_text("\n".join(report), encoding='utf-8')
    print(f"\n报告已保存到：{report_path}")
    
    # 保存移除脚本
    script_path = output_dir / "remove_duplicates.sh"
    script_path.write_text("\n".join(remove_script), encoding='utf-8')
    script_path.chmod(0o755)  # 添加执行权限
    print(f"移除脚本已保存到：{script_path}")

def main(
    classified_dir: str = "server/static/docs/智能分类",
    new_dir: str = "server/static/docs/专栏",
    similarity_threshold: float = 0.9,
    min_similar_files: int = 2
):
    """主函数"""
    classified_path = Path(classified_dir)
    new_path = Path(new_dir)
    
    if not classified_path.exists():
        raise ValueError(f"已分类课程目录不存在：{classified_path}")
    if not new_path.exists():
        raise ValueError(f"新课程目录不存在：{new_path}")
    
    # 检测重复课程
    duplicates, remove_script = detect_duplicates(
        classified_path,
        new_path,
        similarity_threshold,
        min_similar_files
    )
    
    # 生成报告
    output_dir = new_path / "重复课程检测"
    generate_report(duplicates, remove_script, output_dir)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="重复课程检测工具")
    parser.add_argument("--classified-dir", default="server/static/docs/智能分类",
                      help="已分类课程的目录")
    parser.add_argument("--new-dir", default="server/static/docs/专栏",
                      help="新课程的目录")
    parser.add_argument("--similarity-threshold", type=float, default=0.9,
                      help="相似度阈值，超过此值视为重复（0-1之间）")
    parser.add_argument("--min-similar-files", type=int, default=2,
                      help="判定为重复所需的最少相似文章数")
    args = parser.parse_args()
    
    main(args.classified_dir, args.new_dir, args.similarity_threshold, args.min_similar_files) 
#!/usr/bin/env python3
import os
import sys
from pathlib import Path
from typing import List, Tuple, Set
from collections import defaultdict

def is_empty_course(course_dir: Path) -> Tuple[bool, str]:
    """
    检查课程目录是否为空
    返回: (是否为空, 原因)
    """
    # 检查目录是否存在
    if not course_dir.exists():
        return True, "目录不存在"
        
    # 查找所有markdown和pdf文件
    md_files = list(course_dir.glob("**/*.md"))
    pdf_files = list(course_dir.glob("**/*.pdf"))
    
    # 如果既没有markdown文件也没有pdf文件，认为是空课程
    if not md_files and not pdf_files:
        return True, "没有markdown或PDF文件"
        
    # 如果只有一个markdown文件且大小为0，且没有pdf文件，也认为是空课程
    if len(md_files) == 1 and len(pdf_files) == 0 and md_files[0].stat().st_size == 0:
        return True, f"只有一个空的markdown文件: {md_files[0].name}"
        
    return False, ""

def find_empty_courses(base_dir: Path) -> List[Tuple[Path, str]]:
    """
    查找所有空的课程目录
    返回: [(目录路径, 空原因)]
    """
    empty_courses = []
    
    # 遍历所有子目录
    for course_dir in base_dir.iterdir():
        if not course_dir.is_dir() or course_dir.name.startswith('.'):
            continue
            
        is_empty, reason = is_empty_course(course_dir)
        if is_empty:
            empty_courses.append((course_dir, reason))
            
    return empty_courses

def generate_cleanup_script(empty_courses: List[Tuple[Path, str]], output_dir: Path) -> None:
    """生成清理脚本"""
    script_content = [
        "#!/bin/bash",
        "\n# 自动生成的空课程清理脚本",
        "# 请在执行前仔细检查要删除的目录\n"
    ]
    
    for course_dir, reason in empty_courses:
        script_content.append(f"# {course_dir.name}")
        script_content.append(f"# 原因: {reason}")
        script_content.append(f"rm -rf \"{course_dir}\"\n")
        
    # 创建输出目录
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 写入清理脚本
    script_path = output_dir / "clean_empty_courses.sh"
    script_path.write_text("\n".join(script_content))
    script_path.chmod(0o755)  # 添加执行权限
    
def generate_report(empty_courses: List[Tuple[Path, str]], output_dir: Path) -> None:
    """生成清理报告"""
    report_content = [
        "# 空课程清理报告\n",
        f"## 发现 {len(empty_courses)} 个空课程\n"
    ]
    
    for course_dir, reason in empty_courses:
        report_content.extend([
            f"### {course_dir.name}",
            f"- 路径: {course_dir}",
            f"- 原因: {reason}",
            ""
        ])
        
    # 写入报告
    report_path = output_dir / "空课程清理报告.md"
    report_path.write_text("\n".join(report_content))

def get_base_name(file_path: Path) -> str:
    """获取文件的基础名称（不含扩展名）"""
    return file_path.stem

def clean_redundant_files(course_dir: Path) -> List[Tuple[Path, str]]:
    """
    清理冗余文件
    - 如果有md文件，删除同名的pdf、html和mp3文件
    - 如果只有pdf文件，删除同名的html和mp3文件
    返回: [(文件路径, 删除原因)]
    """
    to_delete = []
    
    # 获取所有文件并按基础名称分组
    files_by_name = defaultdict(list)
    for file_path in course_dir.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in ['.md', '.pdf', '.html', '.mp3']:
            files_by_name[get_base_name(file_path)].append(file_path)
    
    # 处理每组同名文件
    for base_name, files in files_by_name.items():
        # 获取不同类型的文件
        md_files = [f for f in files if f.suffix.lower() == '.md']
        pdf_files = [f for f in files if f.suffix.lower() == '.pdf']
        html_files = [f for f in files if f.suffix.lower() == '.html']
        mp3_files = [f for f in files if f.suffix.lower() == '.mp3']
        
        # 如果有markdown文件，删除其他格式
        if md_files:
            for f in pdf_files + html_files + mp3_files:
                to_delete.append((f, f"存在markdown文件 {md_files[0].name}"))
        # 如果没有markdown但有PDF，删除html和mp3
        elif pdf_files:
            for f in html_files + mp3_files:
                to_delete.append((f, f"存在PDF文件 {pdf_files[0].name}"))
    
    return to_delete

def generate_redundant_cleanup_script(redundant_files: List[Tuple[Path, str]], output_dir: Path) -> None:
    """生成冗余文件清理脚本"""
    script_content = [
        "#!/bin/bash",
        "\n# 自动生成的冗余文件清理脚本",
        "# 请在执行前仔细检查要删除的文件\n"
    ]
    
    for file_path, reason in redundant_files:
        script_content.append(f"# {file_path.name}")
        script_content.append(f"# 原因: {reason}")
        script_content.append(f"rm -f \"{file_path}\"\n")
        
    # 写入清理脚本
    script_path = output_dir / "clean_redundant_files.sh"
    script_path.write_text("\n".join(script_content))
    script_path.chmod(0o755)  # 添加执行权限

def generate_redundant_report(redundant_files: List[Tuple[Path, str]], output_dir: Path) -> None:
    """生成冗余文件清理报告"""
    report_content = [
        "# 冗余文件清理报告\n",
        f"## 发现 {len(redundant_files)} 个冗余文件\n"
    ]
    
    # 按目录组织文件
    files_by_dir = defaultdict(list)
    for file_path, reason in redundant_files:
        files_by_dir[file_path.parent].append((file_path, reason))
    
    # 生成报告内容
    for dir_path, files in files_by_dir.items():
        report_content.extend([
            f"### 目录: {dir_path.name}",
            f"路径: {dir_path}",
            "要删除的文件:",
            ""
        ])
        for file_path, reason in files:
            report_content.extend([
                f"- {file_path.name}",
                f"  - 原因: {reason}",
                ""
            ])
    
    # 写入报告
    report_path = output_dir / "冗余文件清理报告.md"
    report_path.write_text("\n".join(report_content))

def main():
    if len(sys.argv) != 2:
        print("Usage: python clean_empty_courses.py <articles_dir>")
        sys.exit(1)
        
    articles_dir = Path(sys.argv[1])
    if not articles_dir.exists():
        print(f"Error: Directory not found: {articles_dir}")
        sys.exit(1)
        
    # 创建输出目录
    output_dir = articles_dir / "清理检测"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. 检查空课程
    print(f"\n开始检查空课程...")
    empty_courses = find_empty_courses(articles_dir)
    
    if empty_courses:
        print(f"\n发现 {len(empty_courses)} 个空课程:")
        for course_dir, reason in empty_courses:
            print(f"- {course_dir.name}")
            print(f"  原因: {reason}")
            
        # 生成空课程报告和清理脚本
        generate_report(empty_courses, output_dir)
        generate_cleanup_script(empty_courses, output_dir)
        
        print(f"\n空课程报告已保存到：{output_dir}/空课程清理报告.md")
        print(f"空课程清理脚本已保存到：{output_dir}/clean_empty_courses.sh")
    else:
        print("没有发现空课程")
    
    # 2. 检查冗余文件
    print(f"\n开始检查冗余文件...")
    all_redundant_files = []
    
    # 遍历所有课程目录
    for course_dir in articles_dir.iterdir():
        if not course_dir.is_dir() or course_dir.name.startswith('.'):
            continue
            
        redundant_files = clean_redundant_files(course_dir)
        all_redundant_files.extend(redundant_files)
    
    if all_redundant_files:
        print(f"\n发现 {len(all_redundant_files)} 个冗余文件")
        
        # 生成冗余文件报告和清理脚本
        generate_redundant_report(all_redundant_files, output_dir)
        generate_redundant_cleanup_script(all_redundant_files, output_dir)
        
        print(f"\n冗余文件报告已保存到：{output_dir}/冗余文件清理报告.md")
        print(f"冗余文件清理脚本已保存到：{output_dir}/clean_redundant_files.sh")
    else:
        print("没有发现冗余文件")
    
if __name__ == "__main__":
    main() 
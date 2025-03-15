#!/usr/bin/env python3
import os
import re
from pathlib import Path

def ensure_dir(directory):
    """确保目录存在，如果不存在则创建"""
    Path(directory).mkdir(parents=True, exist_ok=True)

def sanitize_filename(filename):
    """清理文件名，移除不合法字符"""
    # 替换Windows和Unix系统都不支持的文件名字符
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # 移除前后空格
    filename = filename.strip()
    # 确保文件名不为空
    return filename if filename else 'untitled'

def split_markdown(input_file):
    """将markdown文件按章节拆分"""
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading file {input_file}: {e}")
        return

    # 获取文件夹名（使用原文件名，不包含扩展名）
    folder_name = os.path.splitext(os.path.basename(input_file))[0]
    base_dir = os.path.dirname(input_file)
    output_dir = os.path.join(base_dir, folder_name)
    
    # 创建输出目录
    ensure_dir(output_dir)

    # 使用正则表达式匹配标题
    # 匹配 # 开头的标题（一级标题）
    chapters = re.split(r'\n(?=# (?![#]))', content)
    
    # 处理每个章节
    for chapter in chapters:
        if not chapter.strip():
            continue
            
        # 提取章节标题
        title_match = re.match(r'# (.*?)(?:\n|$)', chapter)
        if title_match:
            title = title_match.group(1).strip()
            # 清理文件名
            filename = sanitize_filename(title)
            
            # 计算到 images 目录的相对路径
            relative_to_root = os.path.relpath(base_dir, output_dir)
            images_path = os.path.join(relative_to_root, 'images')
            
            # 替换图片路径
            chapter = re.sub(
                r'!\[([^\]]*)\]\(images/([^)]+)\)',
                rf'![\1]({images_path}/\2)',
                chapter
            )
            
            # 创建文件
            output_file = os.path.join(output_dir, f"{filename}.md")
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(chapter.strip() + '\n')
                print(f"Created: {output_file}")
            except Exception as e:
                print(f"Error writing file {output_file}: {e}")

def process_directory(directory):
    """处理指定目录下的所有markdown文件"""
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.md'):
                input_file = os.path.join(root, file)
                print(f"\nProcessing: {input_file}")
                split_markdown(input_file)

if __name__ == '__main__':
    # 处理 server/static/docs/极客时间 目录下的所有markdown文件
    docs_dir = 'server/static/docs/极客时间'
    process_directory(docs_dir) 
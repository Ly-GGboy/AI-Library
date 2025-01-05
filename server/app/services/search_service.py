import os
from typing import List, Dict
import re
from datetime import datetime
import aiofiles

class SearchService:
    def __init__(self):
        self.docs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static", "docs")
        os.makedirs(self.docs_dir, exist_ok=True)

    async def search(self, query: str, limit: int = 10) -> List[Dict]:
        """搜索文档"""
        results = []
        query = query.lower()
        
        for root, _, files in os.walk(self.docs_dir):
            for file in files:
                if not file.endswith('.md'):
                    continue
                    
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, self.docs_dir)
                
                try:
                    async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                        content = await f.read()
                        
                    # 搜索标题和内容
                    title = os.path.splitext(file)[0]
                    matches = []
                    
                    # 标题匹配
                    if query in title.lower():
                        matches.append({
                            "type": "title",
                            "text": title,
                            "line": 0
                        })
                    
                    # 内容匹配
                    lines = content.split('\n')
                    for i, line in enumerate(lines, 1):
                        if query in line.lower():
                            # 获取匹配行的上下文
                            context_start = max(0, i - 2)
                            context_end = min(len(lines), i + 2)
                            context = '\n'.join(lines[context_start:context_end])
                            
                            matches.append({
                                "type": "content",
                                "text": context,
                                "line": i
                            })
                            
                            # 限制每个文件的匹配数
                            if len(matches) >= 3:
                                break
                    
                    if matches:
                        results.append({
                            "path": rel_path.replace('\\', '/'),
                            "name": file,
                            "matches": matches,
                            "last_modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                        })
                        
                        # 达到总数限制时停止搜索
                        if len(results) >= limit:
                            break
                            
                except Exception as e:
                    print(f"Error processing file {file_path}: {str(e)}")
                    continue
                    
            if len(results) >= limit:
                break
        
        # 按匹配数量和最后修改时间排序
        results.sort(key=lambda x: (len(x["matches"]), x["last_modified"]), reverse=True)
        return results

    async def get_suggestions(self, query: str, limit: int = 5) -> List[str]:
        """获取搜索建议"""
        suggestions = set()
        query = query.lower()
        
        for root, _, files in os.walk(self.docs_dir):
            for file in files:
                if not file.endswith('.md'):
                    continue
                    
                # 从文件名中提取建议
                name = os.path.splitext(file)[0]
                if query in name.lower():
                    suggestions.add(name)
                
                # 如果已经收集足够的建议，就停止
                if len(suggestions) >= limit:
                    break
                    
            if len(suggestions) >= limit:
                break
        
        return list(suggestions)[:limit] 
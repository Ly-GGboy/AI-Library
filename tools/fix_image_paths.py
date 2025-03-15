import os
import re
from pathlib import Path

def fix_image_paths(docs_dir):
    """Fix image paths in markdown files to use relative paths correctly."""
    docs_path = Path(docs_dir)
    
    # Regular expression to match markdown image syntax
    img_pattern = re.compile(r'!\[([^\]]*)\]\(images/([^)]+)\)')
    
    # Walk through all directories
    for root, _, files in os.walk(docs_path):
        root_path = Path(root)
        
        # Only process markdown files
        for file in files:
            if not file.endswith('.md'):
                continue
                
            file_path = root_path / file
            
            # Calculate relative path to images directory
            relative_to_root = os.path.relpath(docs_path, root_path)
            new_image_path = os.path.join(relative_to_root, 'images')
            
            # Read the file content
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Replace image paths
                new_content = img_pattern.sub(
                    rf'![\1]({new_image_path}/\2)',
                    content
                )
                
                # Only write if content changed
                if new_content != content:
                    print(f'Fixing image paths in {file_path}')
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                        
            except Exception as e:
                print(f'Error processing {file_path}: {e}')

if __name__ == '__main__':
    docs_dir = 'server/static/docs/极客时间'
    fix_image_paths(docs_dir) 
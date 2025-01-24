# extract_translations.py
import os
import re
import json
from pathlib import Path


def sanitize_filename(path):
    """将路径转换为安全的文件名"""
    return str(path).replace(os.sep, "__").replace(".", "_")


def get_relative_path(input_path):
    """安全获取相对路径"""
    try:
        return input_path.relative_to(Path.cwd())
    except ValueError:
        return input_path.absolute()


def extract_translations():
    output_dir = Path('translations')
    output_dir.mkdir(exist_ok=True)

    pattern1 = re.compile(r'^\s*#\s*"(.*?)".*?$')
    pattern2 = re.compile(r'^\s*old\s+"(.*?)"')

    for root, _, files in os.walk('.'):
        for file in files:
            if file.endswith('.rpy'):
                input_path = Path(root) / file

                # 生成安全文件名
                relative_path = get_relative_path(input_path)
                safe_name = sanitize_filename(relative_path) + '.json'
                output_path = output_dir / safe_name

                translations = {}

                with open(input_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        # 处理第一种格式
                        match1 = pattern1.search(line)
                        if match1 and not line.strip().startswith('translate'):
                            original = match1.group(1)
                            translations[original] = ""
                            continue

                        # 处理第二种格式
                        match2 = pattern2.search(line)
                        if match2:
                            original = match2.group(1)
                            translations[original] = ""

                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(translations, f, indent=2, ensure_ascii=False)


if __name__ == '__main__':
    extract_translations()
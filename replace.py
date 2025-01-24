import re
import json
from pathlib import Path


# ================= 修复后的标签检查逻辑 =================
def check_text_tags(s):
    """基于Ren'Py的文本标签检查逻辑（修复大小写敏感问题）"""
    stack = []
    pos = 0
    length = len(s)

    SELF_CLOSING_TAGS = {
        'br', 'w', 'p', 'nw', 'fast', 'slow', 'done', 'wait',
        'nobr', 'alt', 'art', 'rt', 'rb', 'vbar', '^'
    }

    while pos < length:
        if s[pos] == '{':
            end = s.find('}', pos + 1)
            if end == -1:
                return "未闭合的标签"

            full_tag = s[pos + 1:end].strip()
            closing = full_tag.startswith('/')

            # 统一转换为小写处理
            if closing:
                tag_name = full_tag[1:].strip().split()[0].lower()
            else:
                tag_name = full_tag.split()[0].lower()

            if closing:
                if not stack:
                    return f"多余的闭合标签 {{{full_tag}}}"
                expected = stack[-1]
                if expected != tag_name:
                    return f"标签不匹配，期望闭合 {expected} 但找到 {tag_name}"
                stack.pop()
            else:
                if tag_name in SELF_CLOSING_TAGS:
                    pass
                elif any(tag_name.startswith(prefix) for prefix in ['w=', 'size=']):
                    pass
                elif tag_name in {'q', 'b', 'i', 'u', 'a', 'font', 'color', 'size',
                                  'alpha', 'k', 'cps', 's', 'plain', 'noalt'}:
                    stack.append(tag_name)
                else:
                    return f"未知的标签 {{{full_tag}}}"

            pos = end + 1
        else:
            pos += 1

    if stack:
        return f"未闭合的标签：{' '.join(stack)}"

    return None


# ================= 路径转换逻辑（保持之前版本） =================
def reverse_filename(safe_name):
    """路径转换函数（双策略尝试 + Windows处理）"""
    base = safe_name.replace("_translated.json", "")

    # 公共替换
    common = base.replace("__", "/").replace("_rpy", ".rpy")

    # 生成两种可能路径
    path_v1 = Path(common.replace("8_0", "8.0"))  # 精确替换
    path_v2 = Path(common.replace("_", "."))  # 全局替换

    # 优先选择存在的路径
    final_path = path_v1 if path_v1.exists() else path_v2

    # Windows绝对路径修复
    if final_path.is_absolute() and not final_path.exists():
        try:
            current_drive = Path.cwd().drive
            fixed_path = Path(final_path.as_posix().replace('/', current_drive + '/', 1))
            if fixed_path.exists():
                return fixed_path
        except Exception as e:
            print(f"路径修复失败: {e}")

    return final_path.resolve()


# ================= 改进的翻译应用逻辑 =================
def is_valid_translation(text):
    """改进的翻译有效性检查"""
    # 标签检查
    tag_error = check_text_tags(text)
    if tag_error:
        print(f"标签错误：{tag_error}")
        return False

    # 格式字符串检查（保持不变）
    # ...
    return True


def apply_translations():
    # 保持原有逻辑，增加调试信息
    translations_dir = Path("translations_out")
    pattern = re.compile(
        r'(^#.*?\n)'
        r'(translate\s+.*?:\n)'
        r'(\s*#\s*")(.*?)("\n)'
        r'(\s*")(.*?)(")',
        flags=re.M | re.DOTALL
    )

    for trans_file in translations_dir.glob("*_translated.json"):
        original_path = reverse_filename(trans_file.name)

        if not original_path.exists():
            print(f"路径不存在：{original_path}")
            continue

        with open(trans_file, "r", encoding="utf-8") as f:
            translations = json.load(f)

        with open(original_path, "r+", encoding="utf-8") as f:
            content = f.read()

            def replace_translation(match):
                original = match.group(4)
                translated = translations.get(original, match.group(7))

                # 新增调试日志
                print(f"\n处理原文：{original}")
                print(f"原始翻译：{translated}")

                translated = translated.replace('"', "'")

                # 检查前输出标签状态
                print(f"检查前标签状态：{translated}")
                if not is_valid_translation(translated):
                    print(f"无效翻译，保留原文：{original[:50]}...")
                    translated = original
                else:
                    print("标签检查通过")

                return (
                    f"{match.group(1)}{match.group(2)}"
                    f"{match.group(3)}{original}{match.group(5)}"
                    f"{match.group(6)}{translated}{match.group(8)}"
                )

            new_content = pattern.sub(replace_translation, content)

            f.seek(0)
            f.write(new_content)
            f.truncate()

        print(f"成功更新：{original_path}")


if __name__ == "__main__":
    apply_translations()
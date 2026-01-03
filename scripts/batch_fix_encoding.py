"""
批量修复所有scripts中的编码问题
"""
import re
import sys
from pathlib import Path

# 先修复自己的编码问题！
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
from utils.encoding_fix import setup_encoding
setup_encoding()
scripts_dir = project_root / "scripts"

# 旧的编码处理代码模式
old_pattern = r"""# 设置UTF-8编码输出（Windows兼容）
if sys\.platform\.startswith\('win'\):
    import io
    sys\.stdout = io\.TextIOWrapper\(sys\.stdout\.buffer, encoding='utf-8'\)
    sys\.stderr = io\.TextIOWrapper\(sys\.stderr\.buffer, encoding='utf-8'\)

# 添加项目根目录到Python路径
project_root = Path\(__file__\)\.parent\.parent
sys\.path\.insert\(0, str\(project_root\)\)"""

# 新的编码处理代码
new_code = """# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# ========== 编码修复（必须在所有其他导入之前）==========
from utils.encoding_fix import setup_encoding
setup_encoding()
# ======================================================"""

# 处理所有run_*.py文件
run_files = list(scripts_dir.glob("run_*.py"))

for file_path in run_files:
    print(f"处理文件: {file_path.name}")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 检查是否已经应用了新的编码修复
    if 'from utils.encoding_fix import setup_encoding' in content:
        print(f"  ✓ 已应用编码修复，跳过")
        continue

    # 替换旧的编码处理
    if re.search(old_pattern, content, re.MULTILINE):
        content = re.sub(old_pattern, new_code, content, flags=re.MULTILINE)
        print(f"  ✓ 替换了旧的编码处理代码")
    else:
        # 如果没有旧代码，尝试在path.insert之后添加
        pattern = r"(sys\.path\.insert\(0, str\(project_root\)\))"
        replacement = r"\1\n\n# ========== 编码修复（必须在所有其他导入之前）==========\nfrom utils.encoding_fix import setup_encoding\nsetup_encoding()\n# ======================================================"
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            print(f"  ✓ 添加了编码修复代码")
        else:
            print(f"  ⚠️ 无法找到插入点，跳过")
            continue

    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"  ✓ 已保存")

print("\n✅ 批量修复完成！")

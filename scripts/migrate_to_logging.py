"""
将项目中的print语句迁移到logging模块的脚本
"""
import re
from pathlib import Path
from typing import List, Tuple


def add_logger_import(content: str, module_name: str) -> Tuple[str, bool]:
    """
    添加logger导入语句

    Returns:
        (updated_content, was_modified)
    """
    # 检查是否已经有logger导入
    if 'from utils.logger import get_logger' in content or 'logger = get_logger' in content:
        return content, False

    # 查找最后一个import语句的位置
    import_pattern = r'(from .+ import .+|import .+)'
    imports = list(re.finditer(import_pattern, content))

    if imports:
        last_import = imports[-1]
        insert_pos = last_import.end()

        # 在最后一个import后添加logger导入
        logger_import = f"\nfrom utils.logger import get_logger\n\nlogger = get_logger(__name__)\n"
        new_content = content[:insert_pos] + logger_import + content[insert_pos:]
        return new_content, True

    return content, False


def migrate_print_to_logger(file_path: Path, dry_run: bool = False) -> int:
    """
    迁移单个文件中的print到logger

    Returns:
        替换的print语句数量
    """
    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content
        changes = 0

        # 添加logger导入
        content, import_added = add_logger_import(content, file_path.stem)
        if import_added:
            changes += 1

        # 替换print语句为logger
        # 模式1: print(f"xxx") -> logger.info(f"xxx")
        # 模式2: print("xxx") -> logger.info("xxx")

        def replace_print(match):
            nonlocal changes
            indent = match.group(1)
            content_to_log = match.group(2)

            # 检查是否包含特殊前缀来判断日志级别
            if '✓' in content_to_log or '✅' in content_to_log or '完成' in content_to_log:
                level = 'info'
            elif '⚠️' in content_to_log or '警告' in content_to_log:
                level = 'warning'
            elif '❌' in content_to_log or '错误' in content_to_log or '失败' in content_to_log:
                level = 'error'
            elif '📊' in content_to_log or '🔬' in content_to_log or '🎯' in content_to_log:
                level = 'info'
            else:
                level = 'info'

            changes += 1
            return f'{indent}logger.{level}({content_to_log})'

        # 匹配print语句
        pattern = r'(\s*)print\((.*?)\)(?:\s*#.*)?$'
        content = re.sub(pattern, replace_print, content, flags=re.MULTILINE)

        # 如果有改变且不是dry run，则写入文件
        if content != original_content and not dry_run:
            file_path.write_text(content, encoding='utf-8')
            print(f"OK {file_path.relative_to(Path.cwd())}: {changes} changes")
        elif content != original_content:
            print(f"[DRY RUN] {file_path.relative_to(Path.cwd())}: {changes} changes")

        return changes

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return 0


def main():
    """主函数"""
    project_root = Path(__file__).parent.parent

    # 要迁移的目录
    dirs_to_migrate = [
        project_root / "core",
        project_root / "ai",
        project_root / "storage",
        project_root / "scripts",
        project_root / "utils",
    ]

    print("="*70)
    print("迁移print语句到logging模块")
    print("="*70)

    total_files = 0
    total_changes = 0

    for directory in dirs_to_migrate:
        if not directory.exists():
            continue

        print(f"\n处理目录: {directory.relative_to(project_root)}")
        py_files = list(directory.glob("*.py"))

        for py_file in py_files:
            if py_file.name in ['__init__.py', 'logger.py', 'migrate_to_logging.py']:
                continue

            changes = migrate_print_to_logger(py_file, dry_run=False)
            if changes > 0:
                total_files += 1
                total_changes += changes

    print("\n" + "="*70)
    print(f"迁移完成: {total_files} 个文件, {total_changes} 处改动")
    print("="*70)


if __name__ == "__main__":
    main()

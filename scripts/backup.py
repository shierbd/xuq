#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目备份脚本
用法: python scripts/backup.py
"""

import os
import sys
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

# 设置输出编码为UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def create_backup():
    """创建完整备份"""

    # 1. 生成时间戳
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"backup-{timestamp}"
    backup_dir = Path(f"backups/{backup_name}")

    print(f"[备份] 开始备份: {backup_name}")

    # 2. 创建备份目录
    backup_dir.mkdir(parents=True, exist_ok=True)

    # 3. 备份数据库
    print("[备份] 备份数据库...")
    if Path("data/products.db").exists():
        shutil.copy2("data/products.db", backup_dir / "products.db")
        print("   [OK] 数据库已备份")
    else:
        print("   [WARN] 数据库文件不存在")

    # 4. 备份数据目录
    print("[备份] 备份数据文件...")
    if Path("data").exists():
        # 定义忽略函数，跳过特殊文件和临时文件
        def ignore_files(dir, files):
            ignore_list = []
            for f in files:
                # 跳过Windows特殊文件名
                if f.lower() in ['nul', 'con', 'prn', 'aux', 'com1', 'com2', 'lpt1', 'lpt2']:
                    ignore_list.append(f)
                # 跳过临时文件
                elif f.endswith('.tmp') or f.endswith('.temp'):
                    ignore_list.append(f)
            return ignore_list

        try:
            shutil.copytree("data", backup_dir / "data",
                          ignore=ignore_files, dirs_exist_ok=True)
            print("   [OK] 数据文件已备份")
        except Exception as e:
            print(f"   [WARN] 数据文件备份部分失败: {e}")
    else:
        print("   [WARN] 数据目录不存在")

    # 5. 备份环境配置
    print("[备份] 备份环境配置...")
    if Path(".env").exists():
        shutil.copy2(".env", backup_dir / ".env")
        print("   [OK] 环境配置已备份")
    else:
        print("   [WARN] .env文件不存在")

    # 6. 备份依赖清单
    print("[备份] 备份依赖清单...")
    try:
        with open(backup_dir / "requirements-frozen.txt", "w") as f:
            subprocess.run(["pip", "freeze"], stdout=f, check=True)
        print("   [OK] Python依赖已备份")
    except Exception as e:
        print(f"   [WARN] Python依赖备份失败: {e}")

    # 7. 创建Git备份分支
    print("[备份] 创建Git备份分支...")
    try:
        branch_name = f"backup-{timestamp}"

        # 检查是否有未提交的更改
        result = subprocess.run(["git", "status", "--porcelain"],
                              capture_output=True, text=True)

        if result.stdout.strip():
            # 有未提交的更改，先提交
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m",
                          f"backup: 自动备份 {timestamp}\n\nCo-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"],
                          check=True)

        # 创建备份分支
        subprocess.run(["git", "branch", branch_name], check=True)

        # 获取当前commit
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()

        print(f"   [OK] Git分支已创建: {branch_name}")
        print(f"   [INFO] Git提交: {commit[:8]}")

        git_commit = commit
    except Exception as e:
        print(f"   [WARN] Git备份失败: {e}")
        git_commit = "N/A"

    # 8. 创建备份信息文件
    print("[备份] 创建备份信息...")
    with open(backup_dir / "BACKUP_INFO.txt", "w", encoding="utf-8") as f:
        f.write(f"备份时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"备份名称: {backup_name}\n")
        f.write(f"Git提交: {git_commit}\n")
        f.write(f"备份路径: {backup_dir.absolute()}\n")
    print("   [OK] 备份信息已创建")

    # 9. 创建压缩包
    print("[备份] 创建压缩包...")
    try:
        shutil.make_archive(f"backups/{backup_name}", "zip", backup_dir)
        zip_size = Path(f"backups/{backup_name}.zip").stat().st_size / (1024 * 1024)
        print(f"   [OK] 压缩包已创建 ({zip_size:.1f} MB)")
    except Exception as e:
        print(f"   [WARN] 压缩包创建失败: {e}")

    print(f"\n[SUCCESS] 备份完成！")
    print(f"\n[INFO] 备份位置:")
    print(f"   - 目录: {backup_dir.absolute()}")
    print(f"   - 压缩包: backups/{backup_name}.zip")
    print(f"\n[INFO] 恢复命令:")
    print(f"   python scripts/restore.py {backup_name}")

    return backup_name

if __name__ == "__main__":
    try:
        create_backup()
    except KeyboardInterrupt:
        print("\n\n[CANCEL] 备份已取消")
    except Exception as e:
        print(f"\n\n[ERROR] 备份失败: {e}")
        import traceback
        traceback.print_exc()

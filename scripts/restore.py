#!/usr/bin/env python3
"""
项目恢复脚本
用法: python scripts/restore.py backup-20260201_143022
或者: python scripts/restore.py --list  # 列出所有备份
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

def list_backups():
    """列出所有备份"""
    backups_dir = Path("backups")
    if not backups_dir.exists():
        print("❌ 没有找到备份目录")
        return []

    backups = sorted([d.name for d in backups_dir.iterdir() if d.is_dir()],
                    reverse=True)

    if not backups:
        print("❌ 没有找到任何备份")
        return []

    print("\n📦 可用的备份:\n")
    for i, backup in enumerate(backups, 1):
        info_file = backups_dir / backup / "BACKUP_INFO.txt"
        if info_file.exists():
            info = info_file.read_text(encoding="utf-8")
            lines = info.split("\n")
            backup_time = lines[0].replace("备份时间: ", "") if len(lines) > 0 else "未知"
            print(f"{i}. {backup}")
            print(f"   时间: {backup_time}")
        else:
            print(f"{i}. {backup}")
        print()

    return backups

def restore_backup(backup_name):
    """从备份恢复"""

    backup_dir = Path(f"backups/{backup_name}")

    if not backup_dir.exists():
        print(f"❌ 备份不存在: {backup_dir}")
        print("\n💡 提示: 使用 'python scripts/restore.py --list' 查看所有备份")
        return False

    print(f"🔄 准备恢复备份: {backup_name}\n")

    # 1. 读取备份信息
    info_file = backup_dir / "BACKUP_INFO.txt"
    if info_file.exists():
        print("📋 备份信息:")
        print("-" * 50)
        print(info_file.read_text(encoding="utf-8"))
        print("-" * 50)
    else:
        print("⚠️ 未找到备份信息文件")

    # 2. 确认恢复
    print("\n⚠️  警告: 恢复操作将覆盖当前数据！")
    print("⚠️  建议先备份当前状态（如果需要）")
    confirm = input("\n确认要恢复此备份吗？(输入 'yes' 继续): ")

    if confirm.lower() != "yes":
        print("❌ 恢复已取消")
        return False

    print("\n🔄 开始恢复...\n")

    # 3. 恢复数据库
    print("📦 恢复数据库...")
    db_backup = backup_dir / "products.db"
    if db_backup.exists():
        # 确保data目录存在
        Path("data").mkdir(exist_ok=True)
        shutil.copy2(db_backup, "data/products.db")
        print("   ✅ 数据库已恢复")
    else:
        print("   ⚠️ 备份中没有数据库文件")

    # 4. 恢复数据目录
    print("📦 恢复数据文件...")
    data_backup = backup_dir / "data"
    if data_backup.exists():
        # 删除现有data目录（保留备份）
        if Path("data").exists():
            print("   📁 备份当前数据目录...")
            if Path("data-old").exists():
                shutil.rmtree("data-old")
            shutil.move("data", "data-old")

        # 恢复数据目录
        shutil.copytree(data_backup, "data")
        print("   ✅ 数据文件已恢复")
        print("   💡 旧数据已保存到 data-old/")
    else:
        print("   ⚠️ 备份中没有数据目录")

    # 5. 恢复环境配置
    print("📦 恢复环境配置...")
    env_backup = backup_dir / ".env"
    if env_backup.exists():
        # 备份当前.env
        if Path(".env").exists():
            shutil.copy2(".env", ".env.old")
            print("   💡 当前.env已备份到 .env.old")

        shutil.copy2(env_backup, ".env")
        print("   ✅ 环境配置已恢复")
    else:
        print("   ⚠️ 备份中没有.env文件")

    # 6. 恢复依赖（可选）
    print("📦 恢复Python依赖...")
    requirements_backup = backup_dir / "requirements-frozen.txt"
    if requirements_backup.exists():
        restore_deps = input("   是否恢复Python依赖？(yes/no，默认no): ")
        if restore_deps.lower() == "yes":
            try:
                subprocess.run(["pip", "install", "-r",
                              str(requirements_backup)], check=True)
                print("   ✅ Python依赖已恢复")
            except Exception as e:
                print(f"   ⚠️ 依赖恢复失败: {e}")
        else:
            print("   ⏭️  跳过依赖恢复")
    else:
        print("   ⚠️ 备份中没有依赖清单")

    print("\n✅ 恢复完成！\n")
    print("🚀 下一步:")
    print("1. 启动后端: python -m uvicorn api.main:app --reload --port 8000")
    print("2. 启动前端: cd frontend && npm run dev")
    print("3. 访问: http://localhost:5173")
    print("\n💡 提示:")
    print("- 旧数据已保存到 data-old/ 目录")
    print("- 旧配置已保存到 .env.old 文件")

    return True

def restore_from_git(branch_name):
    """从Git分支恢复"""
    print(f"🔄 从Git分支恢复: {branch_name}\n")

    try:
        # 检查分支是否存在
        result = subprocess.run(["git", "branch", "--list", branch_name],
                              capture_output=True, text=True)

        if not result.stdout.strip():
            print(f"❌ Git分支不存在: {branch_name}")
            return False

        # 确认切换
        print("⚠️  警告: 将切换到备份分支，当前未提交的更改可能丢失！")
        confirm = input("确认要切换分支吗？(输入 'yes' 继续): ")

        if confirm.lower() != "yes":
            print("❌ 操作已取消")
            return False

        # 切换分支
        subprocess.run(["git", "checkout", branch_name], check=True)
        print(f"✅ 已切换到分支: {branch_name}")

        # 显示当前状态
        print("\n📋 当前状态:")
        subprocess.run(["git", "log", "-1", "--oneline"])

        return True

    except Exception as e:
        print(f"❌ Git恢复失败: {e}")
        return False

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法:")
        print("  python scripts/restore.py <backup_name>  # 恢复指定备份")
        print("  python scripts/restore.py --list         # 列出所有备份")
        print("  python scripts/restore.py --git <branch> # 从Git分支恢复")
        print()
        list_backups()
        sys.exit(1)

    command = sys.argv[1]

    if command == "--list":
        list_backups()
    elif command == "--git":
        if len(sys.argv) < 3:
            print("❌ 请指定Git分支名称")
            print("用法: python scripts/restore.py --git <branch_name>")
            sys.exit(1)
        restore_from_git(sys.argv[2])
    else:
        restore_backup(command)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ 操作已取消")
    except Exception as e:
        print(f"\n\n❌ 恢复失败: {e}")
        import traceback
        traceback.print_exc()

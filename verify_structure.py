"""
快速验证脚本
检查项目结构和导入是否正常
"""
import sys
from pathlib import Path

# 添加scripts到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "scripts"))

print("=" * 60)
print("项目结构验证".center(60))
print("=" * 60)

# 1. 检查目录结构
print("\n1. 检查目录结构...")
required_dirs = [
    "data/raw",
    "data/processed",
    "data/results",
    "data/baseline",
    "scripts/core",
    "scripts/tools",
    "scripts/selectors",
    "scripts/lib",
    "docs",
    "output"
]

all_dirs_exist = True
for dir_path in required_dirs:
    full_path = project_root / dir_path
    exists = full_path.exists()
    status = "[OK]" if exists else "[FAIL]"
    print(f"  {status} {dir_path}")
    if not exists:
        all_dirs_exist = False

# 2. 检查核心文件
print("\n2. 检查核心文件...")
required_files = [
    "scripts/lib/config.py",
    "scripts/lib/utils.py",
    "scripts/core/step_A2_merge_csv.py",
    "scripts/core/step_A3_clustering.py",
    "scripts/core/step_B3_cluster_stageB.py",
    "README.md",
    "requirements.txt",
    ".gitignore"
]

all_files_exist = True
for file_path in required_files:
    full_path = project_root / file_path
    exists = full_path.exists()
    status = "[OK]" if exists else "[FAIL]"
    print(f"  {status} {file_path}")
    if not exists:
        all_files_exist = False

# 3. 检查Python导入
print("\n3. 检查Python导入...")
import_tests = [
    ("lib.config", "A3_CONFIG"),
    ("lib.utils", "setup_logging"),
    ("lib.utils", "print_section"),
]

all_imports_ok = True
for module_name, attr_name in import_tests:
    try:
        module = __import__(module_name, fromlist=[attr_name])
        getattr(module, attr_name)
        print(f"  [OK] from {module_name} import {attr_name}")
    except Exception as e:
        print(f"  [FAIL] from {module_name} import {attr_name}: {e}")
        all_imports_ok = False

# 4. 检查配置
print("\n4. 检查配置...")
try:
    from lib.config import (
        DATA_DIR, DATA_RAW_DIR, DATA_PROCESSED_DIR,
        DATA_RESULTS_DIR, DATA_BASELINE_DIR,
        MERGED_FILE, CLUSTERS_FILE
    )

    print(f"  [OK] DATA_DIR: {DATA_DIR}")
    print(f"  [OK] DATA_RAW_DIR: {DATA_RAW_DIR}")
    print(f"  [OK] MERGED_FILE: {MERGED_FILE}")
    print(f"  [OK] CLUSTERS_FILE: {CLUSTERS_FILE}")
    config_ok = True
except Exception as e:
    print(f"  [FAIL] Configuration import failed: {e}")
    config_ok = False

# 5. 检查基准文件
print("\n5. 检查基准输出...")
baseline_files = [
    "data/baseline/cluster_summary_A3.csv",
    "data/baseline/BASELINE_METRICS.md",
]

baseline_ok = True
for file_path in baseline_files:
    full_path = project_root / file_path
    exists = full_path.exists()
    status = "[OK]" if exists else "[FAIL]"
    print(f"  {status} {file_path}")
    if not exists:
        baseline_ok = False

# 总结
print("\n" + "=" * 60)
print("验证结果".center(60))
print("=" * 60)

checks = [
    ("目录结构", all_dirs_exist),
    ("核心文件", all_files_exist),
    ("Python导入", all_imports_ok),
    ("配置检查", config_ok),
    ("基准文件", baseline_ok),
]

all_passed = all(result for _, result in checks)

for check_name, result in checks:
    status = "[PASS]" if result else "[FAIL]"
    print(f"{check_name:12s}: {status}")

print("\n" + "=" * 60)
if all_passed:
    print("[SUCCESS] All checks passed! Project structure is valid.".center(60))
    sys.exit(0)
else:
    print("[ERROR] Some checks failed. Please review errors above.".center(60))
    sys.exit(1)

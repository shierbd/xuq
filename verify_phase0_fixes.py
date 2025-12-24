"""
验证Phase 0修复
"""
import sys
import io
from pathlib import Path

# Set UTF-8 encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("="*70)
print("Phase 0 修复验证")
print("="*70)

# Test 1: Check if Phrase model can be imported
print("\n1. 测试 Phrase 模型导入...")
try:
    from storage.models import Phrase
    print("   ✅ Phrase 模型导入成功")
except Exception as e:
    print(f"   ❌ Phrase 模型导入失败: {e}")

# Test 2: Check if experiment B result exists
print("\n2. 检查实验B结果文件...")
result_file = project_root / 'data' / 'phase0_results' / 'experiment_b_result.json'
if result_file.exists():
    print("   ✅ 实验B结果文件存在")

    # Load and display result
    import json
    with open(result_file, 'r', encoding='utf-8') as f:
        result = json.load(f)

    print(f"\n   实验B结果:")
    print(f"   - 短语总数: {result['total_phrases']:,}")
    print(f"   - Token总数: {result['token_count']}")
    print(f"   - 覆盖率: {result['coverage_rate']:.1%}")
    print(f"   - 建议: {result['recommendation']}")
else:
    print("   ❌ 实验B结果文件不存在")

# Test 3: Test UI page can load experiment result
print("\n3. 测试UI页面加载实验结果...")
try:
    from ui.pages import phase0_baseline
    result = phase0_baseline.load_experiment_result('b')
    if result:
        print("   ✅ UI页面成功加载实验B结果")
        print(f"   - 覆盖率: {result['coverage_rate']:.1%}")
    else:
        print("   ⚠️  实验B结果为None")
except Exception as e:
    print(f"   ❌ UI页面加载失败: {e}")

# Test 4: Test prerequisite check
print("\n4. 测试前置条件检查...")
try:
    from ui.pages import phase0_baseline
    issues = phase0_baseline.check_prerequisites()
    if not issues:
        print("   ✅ 前置条件检查通过（无问题）")
    else:
        print(f"   ⚠️  发现 {len(issues)} 个问题:")
        for issue in issues:
            print(f"      {issue}")
except Exception as e:
    print(f"   ❌ 前置条件检查失败: {e}")

print("\n" + "="*70)
print("验证完成！")
print("="*70)

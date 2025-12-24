"""
测试Phase 0 Web UI集成
验证页面能否正常加载
"""
import sys
import io
from pathlib import Path

# Set UTF-8 encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_phase0_page_import():
    """测试Phase 0页面是否可以正常导入"""
    try:
        from ui.pages import phase0_baseline
        print("✅ Phase 0页面导入成功")
        return True
    except Exception as e:
        print(f"❌ Phase 0页面导入失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_render_function():
    """测试render函数是否存在"""
    try:
        from ui.pages import phase0_baseline
        if hasattr(phase0_baseline, 'render'):
            print("✅ render函数存在")
            return True
        else:
            print("❌ render函数不存在")
            return False
    except Exception as e:
        print(f"❌ 检查render函数失败: {str(e)}")
        return False


def test_load_experiment_result():
    """测试加载实验结果函数"""
    try:
        from ui.pages import phase0_baseline
        result = phase0_baseline.load_experiment_result('a')
        if result is None:
            print("✅ load_experiment_result函数正常（结果为None表示文件不存在）")
        else:
            print(f"✅ load_experiment_result函数正常（加载了实验A结果）")
        return True
    except Exception as e:
        print(f"❌ load_experiment_result函数测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_check_prerequisites():
    """测试前置条件检查函数"""
    try:
        from ui.pages import phase0_baseline
        issues = phase0_baseline.check_prerequisites()
        print(f"✅ check_prerequisites函数正常（发现{len(issues)}个问题）")
        for issue in issues:
            print(f"   {issue}")
        return True
    except Exception as e:
        print(f"❌ check_prerequisites函数测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("="*70)
    print("Phase 0 Web UI集成测试")
    print("="*70)

    tests = [
        ("页面导入", test_phase0_page_import),
        ("render函数", test_render_function),
        ("加载实验结果", test_load_experiment_result),
        ("前置条件检查", test_check_prerequisites),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n测试: {test_name}")
        print("-"*70)
        results.append(test_func())

    print("\n" + "="*70)
    print("测试总结")
    print("="*70)
    passed = sum(results)
    total = len(results)
    print(f"通过: {passed}/{total}")

    if passed == total:
        print("\n✅ 所有测试通过！Phase 0 Web UI集成成功")
        print("\n📌 下一步：")
        print("   1. 重启Web UI: streamlit run web_ui.py")
        print("   2. 在侧边栏选择'📊 Phase 0: 基线测量'")
        print("   3. 开始运行实验")
    else:
        print(f"\n❌ 有{total - passed}个测试失败，请检查错误信息")
        sys.exit(1)

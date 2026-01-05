"""
Phase 2D UI 前端测试脚本
测试数据加载和显示功能
"""
import sys
from pathlib import Path
import json

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_data_files():
    """测试数据文件是否存在且格式正确"""
    print("="*70)
    print("Phase 2D UI 前端测试".center(70))
    print("="*70)

    results = {
        'templates': {'status': '❌', 'details': ''},
        'variables': {'status': '❌', 'details': ''},
        'products': {'status': '❌', 'details': ''},
        'ui_page': {'status': '❌', 'details': ''}
    }

    # 测试1: discovered_templates.json
    print("\n[测试 1/4] 检查模板文件...")
    templates_file = project_root / 'outputs' / 'discovered_templates.json'

    try:
        if not templates_file.exists():
            results['templates']['details'] = f"文件不存在: {templates_file}"
        else:
            with open(templates_file, 'r', encoding='utf-8') as f:
                templates = json.load(f)

            if not isinstance(templates, list):
                results['templates']['details'] = f"格式错误: 应该是列表，实际是 {type(templates)}"
            elif len(templates) == 0:
                results['templates']['details'] = "模板列表为空"
            else:
                # 验证数据结构
                required_fields = ['anchor', 'template_pattern', 'match_count', 'example_phrases']
                sample = templates[0]
                missing = [f for f in required_fields if f not in sample]

                if missing:
                    results['templates']['details'] = f"缺少字段: {missing}"
                else:
                    results['templates']['status'] = '✅'
                    results['templates']['details'] = f"发现 {len(templates)} 个模板，最高频次 {max(t['match_count'] for t in templates)}"

                    print(f"  ✅ 文件存在: {templates_file.name}")
                    print(f"  ✅ 模板数量: {len(templates)}")
                    print(f"  ✅ Top 3 模板:")
                    for i, t in enumerate(sorted(templates, key=lambda x: x['match_count'], reverse=True)[:3], 1):
                        print(f"     {i}. {t['template_pattern']} - {t['match_count']} 次")

    except Exception as e:
        results['templates']['details'] = f"加载失败: {str(e)}"

    if results['templates']['status'] == '❌':
        print(f"  ❌ {results['templates']['details']}")

    # 测试2: variable_extraction_results.json
    print("\n[测试 2/4] 检查变量文件...")
    variables_file = project_root / 'outputs' / 'variable_extraction_results.json'

    try:
        if not variables_file.exists():
            results['variables']['details'] = f"文件不存在: {variables_file}"
        else:
            with open(variables_file, 'r', encoding='utf-8') as f:
                variables_data = json.load(f)

            required_fields = ['statistics', 'top_variables']
            missing = [f for f in required_fields if f not in variables_data]

            if missing:
                results['variables']['details'] = f"缺少字段: {missing}"
            else:
                stats = variables_data['statistics']
                top_vars = variables_data['top_variables']

                results['variables']['status'] = '✅'
                results['variables']['details'] = f"{len(top_vars)} 个有效变量，保留率 {len(top_vars)/stats['unique_variables']*100:.1f}%"

                print(f"  ✅ 文件存在: {variables_file.name}")
                print(f"  ✅ 总匹配数: {stats['total_matches']}")
                print(f"  ✅ 唯一变量: {stats['unique_variables']}")
                print(f"  ✅ 有效变量: {len(top_vars)}")
                print(f"  ✅ Top 3 变量:")
                for i, v in enumerate(top_vars[:3], 1):
                    print(f"     {i}. \"{v['variable_text']}\" - 频次 {v['frequency']}, 模板 {v['template_match_count']}")

    except Exception as e:
        results['variables']['details'] = f"加载失败: {str(e)}"

    if results['variables']['status'] == '❌':
        print(f"  ❌ {results['variables']['details']}")

    # 测试3: product_entities.json
    print("\n[测试 3/4] 检查产品文件...")
    products_file = project_root / 'outputs' / 'product_entities.json'

    try:
        if not products_file.exists():
            results['products']['details'] = f"文件不存在: {products_file}"
        else:
            with open(products_file, 'r', encoding='utf-8') as f:
                products_data = json.load(f)

            required_fields = ['total_products', 'products', 'statistics']
            missing = [f for f in required_fields if f not in products_data]

            if missing:
                results['products']['details'] = f"缺少字段: {missing}"
            else:
                products = products_data['products']
                stats = products_data['statistics']

                results['products']['status'] = '✅'
                results['products']['details'] = f"{len(products)} 个产品，平均价值 {stats['avg_commercial_value']:.1f}"

                print(f"  ✅ 文件存在: {products_file.name}")
                print(f"  ✅ 产品总数: {len(products)}")
                print(f"  ✅ 平均商业价值: {stats['avg_commercial_value']:.1f}/100")
                print(f"  ✅ 高价值产品: {stats['high_value_products']}")
                print(f"  ✅ 类别分布: {stats['categories']}")
                print(f"  ✅ Top 3 产品:")
                for i, p in enumerate(products[:3], 1):
                    print(f"     {i}. {p['product_name']} - {p['category']} - 价值 {p['commercial_value']}/100")

    except Exception as e:
        results['products']['details'] = f"加载失败: {str(e)}"

    if results['products']['status'] == '❌':
        print(f"  ❌ {results['products']['details']}")

    # 测试4: UI页面文件
    print("\n[测试 4/4] 检查UI页面...")
    ui_file = project_root / 'ui' / 'pages' / 'phase2d_templates.py'

    try:
        if not ui_file.exists():
            results['ui_page']['details'] = f"文件不存在: {ui_file}"
        else:
            with open(ui_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 检查关键函数和中文化
            checks = {
                'render_page函数': 'def render_page():' in content,
                '加载模板函数': 'def load_templates()' in content,
                '中文标题': '数据驱动的模板发现与产品提取' in content,
                '中文Tab': '发现的模板' in content and '识别的产品' in content,
                '中文筛选器': '最小频次' in content and '按类别筛选' in content,
            }

            failed_checks = [k for k, v in checks.items() if not v]

            if failed_checks:
                results['ui_page']['details'] = f"检查失败: {failed_checks}"
            else:
                results['ui_page']['status'] = '✅'
                results['ui_page']['details'] = "页面结构完整，已中文化"

                print(f"  ✅ 文件存在: {ui_file.name}")
                print(f"  ✅ 文件大小: {len(content)} 字符")
                print(f"  ✅ 所有必要函数和中文化检查通过")

    except Exception as e:
        results['ui_page']['details'] = f"检查失败: {str(e)}"

    if results['ui_page']['status'] == '❌':
        print(f"  ❌ {results['ui_page']['details']}")

    # 总结
    print("\n" + "="*70)
    print("测试总结".center(70))
    print("="*70)

    total_tests = len(results)
    passed_tests = sum(1 for r in results.values() if r['status'] == '✅')

    print(f"\n通过: {passed_tests}/{total_tests}")

    for test_name, result in results.items():
        print(f"  {result['status']} {test_name}: {result['details']}")

    print("\n" + "="*70)

    if passed_tests == total_tests:
        print("✅ 所有测试通过！前端已准备就绪。".center(70))
        print(f"\n访问 http://localhost:8501 并选择 '🎯 Phase 2D: 模板发现'".center(70))
    else:
        print(f"❌ {total_tests - passed_tests} 个测试失败，请检查上述错误。".center(70))

    print("="*70)

    return passed_tests == total_tests


if __name__ == "__main__":
    success = test_data_files()
    sys.exit(0 if success else 1)

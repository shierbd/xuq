"""
Reddit板块分析功能 - 端到端测试

测试场景：
1. 数据导入：导入真实的Reddit板块Excel文件
2. 查看导入结果：验证数据是否正确导入
3. AI分析：批量分析板块（使用默认配置）
4. 查看分析结果：验证标签和评分是否生成
5. 标签统计：查看标签分布
6. 数据导出：导出分析结果

运行方式：
    python tests/test_reddit_e2e.py
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.reddit_analyzer import RedditAnalyzer
from storage.reddit_repository import RedditSubredditRepository, AIPromptConfigRepository
import time


def print_section(title):
    """打印测试章节标题"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_1_import_data():
    """测试1: 数据导入"""
    print_section("测试1: 数据导入")

    analyzer = RedditAnalyzer()

    # 使用真实的测试文件
    test_file = r"C:\Users\32941\Downloads\合并表格_20260108_130513.xlsx"

    print(f"导入文件: {test_file}")
    print("开始导入...")

    start_time = time.time()

    result = analyzer.import_from_excel(
        file_path=test_file,
        batch_id="e2e_test_batch",
        skip_duplicates=True
    )

    elapsed_time = time.time() - start_time

    print(f"\n导入耗时: {elapsed_time:.2f}秒")

    if result['success']:
        print("[OK] 导入成功")
        print(f"  - 导入数量: {result['data']['imported_count']}")
        print(f"  - 跳过数量: {result['data']['skipped_count']}")
        print(f"  - 错误数量: {result['data']['error_count']}")
        print(f"  - 批次ID: {result['data']['batch_id']}")
        return True
    else:
        print(f"[ERROR] 导入失败: {result['message']}")
        for error in result['errors']:
            print(f"  - {error}")
        return False


def test_2_verify_import():
    """测试2: 验证导入结果"""
    print_section("测试2: 验证导入结果")

    with RedditSubredditRepository() as repo:
        # 查询导入的数据
        result = repo.query(
            filters={'batch_id': 'e2e_test_batch'},
            limit=10
        )

        total = result['total']
        data = result['data']

        print(f"查询到 {total} 条记录")

        if total > 0:
            print("\n前5条记录:")
            for i, record in enumerate(data[:5], 1):
                print(f"\n{i}. {record['name']}")
                print(f"   订阅数: {record['subscribers']:,}")
                print(f"   状态: {record['ai_analysis_status']}")
                if record['description']:
                    desc = record['description'][:50] + "..." if len(record['description']) > 50 else record['description']
                    print(f"   描述: {desc}")

            print("\n[OK] 数据导入验证通过")
            return True
        else:
            print("[ERROR] 没有找到导入的数据")
            return False


def test_3_check_config():
    """测试3: 检查AI配置"""
    print_section("测试3: 检查AI配置")

    with AIPromptConfigRepository() as repo:
        config = repo.get_default_config('reddit_analysis')

        if config:
            print("[OK] 找到默认配置")
            print(f"  - 配置ID: {config['config_id']}")
            print(f"  - 配置名称: {config['config_name']}")
            print(f"  - 温度参数: {config['temperature']}")
            print(f"  - 最大Token: {config['max_tokens']}")
            print(f"  - 是否启用: {config['is_active']}")
            print(f"  - 是否默认: {config['is_default']}")
            return True
        else:
            print("[ERROR] 没有找到默认配置")
            return False


def test_4_analyze_subreddits():
    """测试4: AI分析板块（仅分析前3个）"""
    print_section("测试4: AI分析板块")

    analyzer = RedditAnalyzer()

    # 获取待分析的板块（限制为3个用于测试）
    with RedditSubredditRepository() as repo:
        pending = repo.get_by_status('pending', limit=3)

    if not pending:
        print("[WARN] 没有待分析的板块")
        return True

    print(f"找到 {len(pending)} 个待分析的板块")
    print("开始分析...")

    subreddit_ids = [s['subreddit_id'] for s in pending]

    start_time = time.time()

    result = analyzer.analyze_subreddits(
        subreddit_ids=subreddit_ids,
        batch_size=3
    )

    elapsed_time = time.time() - start_time

    print(f"\n分析耗时: {elapsed_time:.2f}秒")

    if result['success']:
        print("[OK] 分析成功")
        print(f"  - 成功数量: {result['data']['analyzed_count']}")
        print(f"  - 失败数量: {result['data']['failed_count']}")

        if result['data']['results']:
            print("\n分析结果:")
            for r in result['data']['results']:
                print(f"\n  {r['name']}")
                print(f"    标签: {', '.join(filter(None, r['tags']))}")
                print(f"    评分: {r['importance_score']}")

        return True
    else:
        print(f"[ERROR] 分析失败: {result['message']}")
        for error in result['errors']:
            print(f"  - {error}")
        return False


def test_5_view_results():
    """测试5: 查看分析结果"""
    print_section("测试5: 查看分析结果")

    analyzer = RedditAnalyzer()

    result = analyzer.query_subreddits(
        filters={'status': ['completed']},
        sort_by='importance_score',
        sort_order='desc',
        limit=10
    )

    if result['success']:
        total = result['data']['total']
        data = result['data']['data']

        print(f"[OK] 查询成功，共 {total} 条已完成分析的记录")

        if data:
            print("\n分析结果（按重要性排序）:")
            for i, record in enumerate(data, 1):
                print(f"\n{i}. {record['name']}")
                print(f"   订阅数: {record['subscribers']:,}")
                print(f"   标签: {record['tag1']}, {record['tag2']}, {record['tag3']}")
                print(f"   重要性: {record['importance_score']}/5")
                print(f"   置信度: {record['ai_confidence']}%")

        return True
    else:
        print(f"[ERROR] 查询失败: {result['message']}")
        return False


def test_6_tag_statistics():
    """测试6: 标签统计"""
    print_section("测试6: 标签统计")

    analyzer = RedditAnalyzer()

    result = analyzer.get_tag_statistics()

    if result['success']:
        tag_counts = result['data']['tag_counts']
        total_tags = result['data']['total_tags']

        print(f"[OK] 共 {total_tags} 个不同的标签")

        if tag_counts:
            # 按频率排序
            sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)

            print("\n标签统计（前10个）:")
            for i, (tag, count) in enumerate(sorted_tags[:10], 1):
                print(f"{i:2d}. {tag:20s} : {count:3d} 次")

        return True
    else:
        print(f"[ERROR] 获取标签统计失败: {result['message']}")
        return False


def test_7_export_data():
    """测试7: 数据导出"""
    print_section("测试7: 数据导出")

    analyzer = RedditAnalyzer()

    output_path = "test_reddit_export.csv"

    result = analyzer.export_to_csv(
        filters={'status': ['completed']},
        output_path=output_path
    )

    if result['success']:
        print("[OK] 导出成功")
        print(f"  - 文件路径: {result['data']['file_path']}")
        print(f"  - 记录数量: {result['data']['record_count']}")
        return True
    else:
        print(f"[ERROR] 导出失败: {result['message']}")
        return False


def test_8_cleanup():
    """测试8: 清理测试数据"""
    print_section("测试8: 清理测试数据")

    with RedditSubredditRepository() as repo:
        # 查询测试批次的数据
        test_data = repo.get_by_batch('e2e_test_batch')

        if test_data:
            print(f"找到 {len(test_data)} 条测试数据")
            print("是否删除测试数据？(y/n): ", end='')

            # 自动跳过清理（保留数据供查看）
            print("n (自动跳过)")
            print("[INFO] 保留测试数据供查看")
            return True
        else:
            print("[INFO] 没有找到测试数据")
            return True


def main():
    """主测试流程"""
    print("\n" + "=" * 60)
    print("  Reddit板块分析功能 - 端到端测试")
    print("=" * 60)

    tests = [
        ("数据导入", test_1_import_data),
        ("验证导入结果", test_2_verify_import),
        ("检查AI配置", test_3_check_config),
        ("AI分析板块", test_4_analyze_subreddits),
        ("查看分析结果", test_5_view_results),
        ("标签统计", test_6_tag_statistics),
        ("数据导出", test_7_export_data),
        ("清理测试数据", test_8_cleanup),
    ]

    results = []

    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n[ERROR] 测试异常: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

        time.sleep(1)  # 测试间隔

    # 打印测试总结
    print_section("测试总结")

    passed = sum(1 for _, success in results if success)
    total = len(results)

    print(f"\n测试结果: {passed}/{total} 通过\n")

    for name, success in results:
        status = "[OK]" if success else "[FAIL]"
        print(f"{status} {name}")

    print("\n" + "=" * 60)

    if passed == total:
        print("  所有测试通过！")
    else:
        print(f"  {total - passed} 个测试失败")

    print("=" * 60)

    return 0 if passed == total else 1


if __name__ == "__main__":
    exit(main())

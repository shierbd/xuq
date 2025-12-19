"""
Phase 1: 数据导入
将原始关键词数据导入数据库

运行方式：
    python scripts/run_phase1_import.py [--round-id 1] [--dry-run]

参数：
    --round-id: 数据轮次ID（默认为1）
    --dry-run: 试运行模式，不实际插入数据库，仅展示统计信息
"""
import sys
import argparse
from pathlib import Path

# 设置UTF-8编码输出（Windows兼容）
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import RAW_DATA_DIR, PROCESSED_DATA_DIR
from core.data_integration import DataIntegration
from storage.repository import PhraseRepository, test_database_connection
from storage.models import create_all_tables


def run_phase1_import(round_id: int = 1, dry_run: bool = False):
    """
    执行Phase 1数据导入

    Args:
        round_id: 数据轮次ID
        dry_run: 是否为试运行模式
    """
    print("\n" + "="*70)
    print("Phase 1: 数据导入".center(70))
    print("="*70)

    # 1. 测试数据库连接
    print("\n【步骤1】测试数据库连接...")
    if not test_database_connection():
        print("\n❌ 数据库连接失败！请检查配置。")
        print("提示：")
        print("  1. 确保MySQL/MariaDB服务已启动")
        print("  2. 检查 .env 文件中的数据库配置")
        print("  3. 确保数据库已创建（运行: python -c 'from storage.models import create_all_tables; create_all_tables()'）")
        return False

    # 2. 确保数据表已创建
    print("\n【步骤2】检查数据表...")
    try:
        create_all_tables()
        print("✓ 数据表检查完成")
    except Exception as e:
        print(f"⚠️  数据表创建警告: {str(e)}")

    # 3. 数据整合与清洗
    print("\n【步骤3】数据整合与清洗...")
    integrator = DataIntegration(RAW_DATA_DIR)
    df = integrator.merge_and_clean(round_id=round_id)

    if df.empty:
        print("\n❌ 没有可导入的数据！")
        return False

    # 保存清洗后的数据到processed目录
    processed_file = PROCESSED_DATA_DIR / f'integrated_round{round_id}.csv'
    PROCESSED_DATA_DIR.mkdir(exist_ok=True)
    df.to_csv(processed_file, index=False, encoding='utf-8-sig')
    print(f"\n💾 清洗后的数据已保存到: {processed_file}")

    # 4. 准备数据库插入格式
    print("\n【步骤4】准备数据库插入格式...")
    records = integrator.prepare_for_database(df)

    # 5. 插入数据库
    if dry_run:
        print("\n【试运行模式】跳过数据库插入")
        print(f"✓ 预计插入 {len(records)} 条记录")
        print("\n示例记录（前3条）:")
        for i, record in enumerate(records[:3], 1):
            print(f"\n记录 {i}:")
            for key, value in record.items():
                print(f"  {key}: {value}")
    else:
        print("\n【步骤5】插入数据库...")
        with PhraseRepository() as repo:
            # 检查当前记录数
            current_count = repo.get_phrase_count()
            print(f"当前phrases表记录数: {current_count}")

            # 批量插入
            inserted_count = repo.bulk_insert_phrases(records, batch_size=1000)

            # 检查插入后记录数
            new_count = repo.get_phrase_count()
            print(f"\n插入后phrases表记录数: {new_count}")
            print(f"实际新增记录: {new_count - current_count}")

            # 显示统计信息
            print("\n【数据库统计】")
            stats = repo.get_statistics()
            print(f"总记录数: {stats['total_count']}")
            print(f"\n按数据源分布:")
            for source, count in stats['by_source'].items():
                print(f"  {source}: {count}")
            print(f"\n按处理状态分布:")
            for status, count in stats['by_status'].items():
                print(f"  {status}: {count}")
            print(f"\n按轮次分布:")
            for round_num, count in stats['by_round'].items():
                print(f"  Round {round_num}: {count}")

    # 6. 完成
    print("\n" + "="*70)
    print("✅ Phase 1 数据导入完成！".center(70))
    print("="*70)

    print("\n📊 导入摘要:")
    print(f"  - 轮次ID: {round_id}")
    print(f"  - 清洗后记录数: {len(df)}")
    print(f"  - 插入记录数: {len(records)}")
    if not dry_run:
        print(f"  - 数据库总记录数: {new_count}")
    print(f"  - 清洗数据保存位置: {processed_file}")

    print("\n📌 下一步:")
    print("  运行 Phase 2: python scripts/run_phase2_clustering.py")

    return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Phase 1: 数据导入')
    parser.add_argument(
        '--round-id',
        type=int,
        default=1,
        help='数据轮次ID（默认为1）'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='试运行模式，不实际插入数据库'
    )

    args = parser.parse_args()

    try:
        success = run_phase1_import(round_id=args.round_id, dry_run=args.dry_run)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

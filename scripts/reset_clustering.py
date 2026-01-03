"""
重置聚类结果脚本
用于清除之前的聚类结果，重新开始Phase 2聚类

使用方法：
    python scripts/reset_clustering.py --round-id=1
"""
import sys
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# ========== 编码修复（必须在所有其他导入之前）==========
from utils.encoding_fix import setup_encoding
setup_encoding()
# ======================================================

from storage.repository import PhraseRepository, ClusterMetaRepository
from storage.models import Phrase
from utils.logger import get_logger

logger = get_logger(__name__)


def reset_clustering(round_id: int = 1):
    """
    重置指定轮次的聚类结果

    Args:
        round_id: 数据轮次ID
    """
    print("\n" + "="*70)
    print("重置聚类结果".center(70))
    print("="*70)

    print(f"\n轮次ID: {round_id}")
    print("\n⚠️  警告: 此操作将清除所有聚类结果，包括：")
    print("  - phrases表的cluster_id_A字段")
    print("  - cluster_meta表的所有记录")
    print("  - phrases表的processed_status将重置为'unseen'")

    # 确认操作
    response = input("\n确认执行重置操作？(yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("❌ 操作已取消")
        return False

    # 1. 重置phrases表
    print("\n【步骤1】重置phrases表...")
    with PhraseRepository() as repo:
        # 统计所有记录数（不按轮次过滤，重置所有）
        count = repo.session.query(Phrase).count()

        print(f"找到 {count:,} 条记录")

        # 重置cluster_id_A和processed_status
        updated = repo.session.query(Phrase).update({
            'cluster_id_A': -1,
            'processed_status': 'unseen'
        })

        repo.session.commit()
        print(f"✓ 已重置 {updated:,} 条记录的cluster_id_A和processed_status")

    # 2. 清空cluster_meta表
    print("\n【步骤2】清空cluster_meta表...")
    with ClusterMetaRepository() as repo:
        from sqlalchemy import text
        deleted = repo.session.execute(
            text("DELETE FROM cluster_meta WHERE cluster_level = 'A'")
        )
        repo.session.commit()
        print(f"✓ 已删除 {deleted.rowcount} 条聚类元数据记录")

    print("\n" + "="*70)
    print("✅ 聚类结果重置完成！".center(70))
    print("="*70)

    print("\n现在可以重新运行Phase 2聚类：")
    print("  python scripts/run_phase2_clustering.py --min-cluster-size=100 --min-samples=10")

    return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='重置聚类结果')
    parser.add_argument(
        '--round-id',
        type=int,
        default=1,
        help='数据轮次ID（默认为1）'
    )

    args = parser.parse_args()

    try:
        success = reset_clustering(round_id=args.round_id)
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

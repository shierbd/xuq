"""
查看Phase 1导入结果
显示数据库中的统计信息和样本数据
"""
import sys
import os

# 设置UTF-8编码输出（Windows兼容）
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from storage.repository import PhraseRepository
from storage.models import Phrase

def view_phase1_results():
    """查看Phase 1导入结果"""
    print("\n" + "="*70)
    print("Phase 1 数据导入结果".center(70))
    print("="*70)

    with PhraseRepository() as repo:
        # 1. 总体统计
        print("\n【总体统计】")
        stats = repo.get_statistics()
        print(f"总记录数: {stats['total_count']:,}")

        print(f"\n按数据源分布:")
        for source, count in stats['by_source'].items():
            percentage = (count / stats['total_count']) * 100
            print(f"  {source:20s}: {count:>7,} ({percentage:>5.1f}%)")

        print(f"\n按处理状态分布:")
        for status, count in stats['by_status'].items():
            print(f"  {status:20s}: {count:>7,}")

        print(f"\n聚类状态:")
        print(f"  已分配大组(A): {stats['clustered_A']:,}")
        print(f"  已分配小组(B): {stats['clustered_B']:,}")
        print(f"  已关联需求: {stats['mapped_to_demand']:,}")

        # 2. 高频短语Top 20
        print(f"\n【高频短语 Top 20】")
        print(f"{'排名':<5} {'短语':<50} {'频次':>10} {'搜索量':>10}")
        print("-" * 80)

        top_phrases = repo.session.query(Phrase).order_by(
            Phrase.frequency.desc()
        ).limit(20).all()

        for idx, phrase in enumerate(top_phrases, 1):
            phrase_text = phrase.phrase[:48] + '..' if len(phrase.phrase) > 50 else phrase.phrase
            print(f"{idx:<5} {phrase_text:<50} {phrase.frequency:>10,} {phrase.volume:>10,}")

        # 3. 各数据源样本
        print(f"\n【各数据源样本 (前5条)】")
        for source in ['semrush', 'dropdown', 'related_search']:
            print(f"\n{source.upper()}:")
            samples = repo.session.query(Phrase).filter(
                Phrase.source_type == source
            ).limit(5).all()

            for phrase in samples:
                print(f"  - {phrase.phrase} (频次:{phrase.frequency}, 搜索量:{phrase.volume})")

        # 4. 数据文件位置
        print(f"\n【数据文件位置】")
        print(f"  数据库: MySQL - keyword_clustering.phrases")
        print(f"  CSV文件: data/processed/integrated_round1.csv")
        print(f"  原始数据: data/raw/")

        print("\n" + "="*70)
        print(f"数据已准备就绪，可以运行 Phase 2 进行聚类分析")
        print("="*70)

if __name__ == "__main__":
    try:
        view_phase1_results()
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

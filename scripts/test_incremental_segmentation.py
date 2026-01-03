"""
测试增量分词功能
验证增量分词是否正确合并新旧数据
"""
import sys
from pathlib import Path
from collections import Counter

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from storage.repository import PhraseRepository
from storage.word_segment_repository import WordSegmentRepository
from utils.keyword_segmentation import load_and_segment_incrementally
from utils.stopwords import load_stopwords

def test_incremental_segmentation():
    """测试增量分词功能"""

    print("=" * 70)
    print("测试增量分词功能")
    print("=" * 70)

    # 1. 检查数据库状态
    print("\n[1] 检查数据库状态...")
    with PhraseRepository() as repo:
        stats = repo.get_statistics()
        total_count = stats.get('total_count', 0)
        by_round = stats.get('by_round', {})

        print(f"   总关键词数: {total_count:,}")
        print(f"   轮次分布:")
        for round_id, count in sorted(by_round.items()):
            print(f"      Round {round_id}: {count:,}")

    if not by_round:
        print("\n[ERROR] 数据库中没有数据，无法测试")
        return

    # 2. 检查已有分词结果
    print("\n[2] 检查已有分词结果...")
    with WordSegmentRepository() as ws_repo:
        seg_stats = ws_repo.get_statistics()
        print(f"   已分词的单词数: {seg_stats.get('total_words', 0):,}")
        print(f"   总频次: {seg_stats.get('total_frequency', 0):,}")

        # 获取批次历史
        batches = ws_repo.get_batch_history(limit=5)
        if batches:
            print(f"\n   最近的分词批次:")
            for batch in batches:
                print(f"      批次 {batch.batch_id}: {batch.batch_date.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"         状态: {batch.status}, 处理: {batch.phrase_count} phrases -> {batch.word_count} words")

    # 3. 准备增量分词测试
    print("\n[3] 执行增量分词测试...")

    # 获取最新的round
    latest_round = max(by_round.keys())
    print(f"   目标Round: {latest_round}")
    print(f"   将处理 {by_round[latest_round]:,} 条新短语")

    # 加载停用词
    stopwords_file = project_root / "config" / "stopwords_en.txt"
    stopwords = load_stopwords(stopwords_file)
    print(f"   停用词数量: {len(stopwords)}")

    # 执行增量分词
    print("\n   开始增量分词...")
    import time
    start_time = time.time()

    try:
        (
            merged_word_counter,
            merged_word_to_seeds,
            merged_ngram_counter,
            merged_ngram_to_seeds,
            phrases_count
        ) = load_and_segment_incrementally(
            round_ids=[latest_round],
            stopwords=stopwords,
            extract_ngrams=True,
            min_ngram_frequency=3
        )

        duration = time.time() - start_time

        print(f"\n[SUCCESS] 增量分词完成！耗时: {duration:.2f}秒")
        print(f"\n[4] 分词结果统计:")
        print(f"   处理的短语数: {phrases_count:,}")
        print(f"   单词总数: {len(merged_word_counter):,}")
        print(f"   单词总频次: {sum(merged_word_counter.values()):,}")
        print(f"   短语总数: {len(merged_ngram_counter):,}")
        print(f"   短语总频次: {sum(merged_ngram_counter.values()):,}")

        # 显示高频单词示例
        print(f"\n   高频单词 Top 10:")
        for word, count in merged_word_counter.most_common(10):
            seeds = merged_word_to_seeds.get(word, set())
            print(f"      {word}: {count} (来源: {len(seeds)} 个seed_word)")

        # 显示高频短语示例
        if merged_ngram_counter:
            print(f"\n   高频短语 Top 10:")
            for ngram, count in merged_ngram_counter.most_common(10):
                seeds = merged_ngram_to_seeds.get(ngram, set())
                print(f"      {ngram}: {count} (来源: {len(seeds)} 个seed_word)")

        # 5. 保存到数据库（测试模式，使用独立batch）
        print(f"\n[5] 保存到数据库...")
        with WordSegmentRepository() as ws_repo:
            batch_id = ws_repo.create_batch(
                phrase_count=phrases_count,
                notes=f"[测试] 增量分词Round{latest_round}"
            )

            new_words, new_ngrams = ws_repo.save_word_segments(
                word_counter=merged_word_counter,
                batch_id=batch_id,
                ngram_counter=merged_ngram_counter
            )

            ws_repo.complete_batch(
                batch_id=batch_id,
                word_count=len(merged_word_counter) + len(merged_ngram_counter),
                new_word_count=new_words + new_ngrams,
                duration_seconds=int(duration)
            )

            print(f"   批次ID: {batch_id}")
            print(f"   新增单词: {new_words:,}")
            print(f"   新增短语: {new_ngrams:,}")
            print(f"   [OK] 保存成功")

        print("\n" + "=" * 70)
        print("[SUCCESS] 增量分词功能测试通过！")
        print("=" * 70)

    except Exception as e:
        print(f"\n[ERROR] 增量分词失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_incremental_segmentation()

# -*- coding: utf-8 -*-
"""
测试翻译速度优化
对比优化前后的速度差异
"""
import sys
import time
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.translation import translate_words_batch, TRANSLATION_AVAILABLE

def main():
    if not TRANSLATION_AVAILABLE:
        print("翻译功能不可用")
        return

    # 测试词汇（50个常见的工具类词汇）
    test_words = [
        "calculator", "converter", "generator", "simulator", "editor",
        "viewer", "downloader", "uploader", "manager", "tracker",
        "analyzer", "optimizer", "scanner", "detector", "monitor",
        "dashboard", "planner", "scheduler", "organizer", "reminder",
        "timer", "counter", "recorder", "player", "browser",
        "reader", "writer", "translator", "formatter", "validator",
        "compressor", "extractor", "installer", "updater", "checker",
        "builder", "compiler", "debugger", "profiler", "tester",
        "explorer", "finder", "searcher", "filter", "sorter",
        "merger", "splitter", "joiner", "parser", "renderer"
    ]

    print("=" * 60)
    print("翻译速度测试")
    print("=" * 60)
    print(f"\n测试词汇数量: {len(test_words)} 个")
    print("\n优化策略:")
    print("  - 将多个词用换行符连接")
    print("  - 一次性翻译整批（100个/批）")
    print("  - 大幅减少网络请求次数")
    print("\n开始测试...\n")

    # 计时开始
    start_time = time.time()

    # 执行翻译
    results = translate_words_batch(test_words, batch_size=100, delay=0.3)

    # 计时结束
    end_time = time.time()
    elapsed_time = end_time - start_time

    print(f"\n翻译结果样例（前10个）:")
    for i, (en, cn) in enumerate(list(results.items())[:10]):
        print(f"  {i+1:2}. {en:15} -> {cn}")

    print("\n" + "=" * 60)
    print("性能统计:")
    print(f"  总词数: {len(test_words)}")
    print(f"  耗时: {elapsed_time:.2f} 秒")
    print(f"  平均速度: {len(test_words)/elapsed_time:.1f} 词/秒")
    print("=" * 60)

    # 性能评估
    words_per_sec = len(test_words) / elapsed_time
    if words_per_sec > 20:
        print("\n✅ 性能优秀！翻译速度很快")
    elif words_per_sec > 10:
        print("\n✓ 性能良好")
    else:
        print("\n⚠️  速度较慢，可能受网络影响")

    print(f"\n估算: 翻译1000个词大约需要 {1000/words_per_sec:.1f} 秒")

if __name__ == "__main__":
    main()

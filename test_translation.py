# -*- coding: utf-8 -*-
"""
简单的翻译功能测试
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.translation import (
    translate_single_word,
    translate_words_batch,
    TRANSLATION_AVAILABLE
)

def main():
    print("=" * 50)
    print("翻译功能测试")
    print("=" * 50)

    if not TRANSLATION_AVAILABLE:
        print("翻译功能不可用")
        print("请运行: pip install deep-translator")
        return

    print("\n已安装 deep-translator")
    print("使用 Google Translate 进行翻译\n")

    # 测试单词翻译
    print("【单词翻译测试】")
    test_word = "calculator"
    result = translate_single_word(test_word)
    print(f"{test_word} -> {result}")

    # 测试批量翻译
    print("\n【批量翻译测试】")
    test_words = [
        "calculator", "dashboard", "simulator",
        "converter", "editor", "viewer"
    ]

    print(f"翻译 {len(test_words)} 个词...")
    results = translate_words_batch(test_words, batch_size=10, delay=0.2)

    print("\n翻译结果:")
    for en, cn in results.items():
        print(f"  {en:15} -> {cn}")

    print("\n翻译功能测试完成!")
    print("=" * 50)

if __name__ == "__main__":
    main()

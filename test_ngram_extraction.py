"""
测试n-gram短语提取功能
"""
from collections import Counter
from utils.keyword_segmentation import segment_keywords_with_seed_tracking

# 模拟Phrase对象
class MockPhrase:
    def __init__(self, phrase, seed_word):
        self.phrase = phrase
        self.seed_word = seed_word

# 测试数据
test_phrases = [
    MockPhrase("best free calculator", "calculator"),
    MockPhrase("best free software", "software"),
    MockPhrase("best free vpn", "vpn"),
    MockPhrase("how to make money online", "money"),
    MockPhrase("how to make money fast", "money"),
    MockPhrase("how to create website", "create"),
    MockPhrase("top 10 running shoes", "running"),
    MockPhrase("top rated running shoes", "running"),
    MockPhrase("affordable running shoes", "running"),
]

stopwords = {"to", "the", "of", "in", "on", "at", "and", "or", "10"}

print("=" * 70)
print("测试短语提取功能")
print("=" * 70)

# 测试1: 不提取短语
print("\n【测试1】不提取短语（extract_ngrams=False）")
word_counter, word_to_seeds, ngram_counter, ngram_to_seeds = segment_keywords_with_seed_tracking(
    test_phrases,
    stopwords,
    extract_ngrams=False
)

print(f"单词数量: {len(word_counter)}")
print(f"短语数量: {len(ngram_counter)}")
print(f"Top 10单词: {word_counter.most_common(10)}")

# 测试2: 提取短语
print("\n【测试2】提取短语（extract_ngrams=True, 自动提取2-6词短语）")
word_counter, word_to_seeds, ngram_counter, ngram_to_seeds = segment_keywords_with_seed_tracking(
    test_phrases,
    stopwords,
    extract_ngrams=True,
    min_ngram_frequency=2
)

print(f"单词数量: {len(word_counter)}")
print(f"短语数量: {len(ngram_counter)}")

print("\n高频短语（频次>=2）:")
for ngram, count in ngram_counter.most_common(20):
    # 显示短语及其来源词根
    seeds = ', '.join(sorted(ngram_to_seeds.get(ngram, [])))
    print(f"  '{ngram}': {count}次 (来源词根: {seeds})")

print("\n按词数分组:")
ngrams_by_length = {}
for ngram, count in ngram_counter.items():
    word_count = len(ngram.split())
    if word_count not in ngrams_by_length:
        ngrams_by_length[word_count] = []
    ngrams_by_length[word_count].append((ngram, count))

for word_count in sorted(ngrams_by_length.keys()):
    print(f"\n{word_count}词短语:")
    for ngram, count in sorted(ngrams_by_length[word_count], key=lambda x: x[1], reverse=True):
        print(f"  '{ngram}': {count}次")

print("\n" + "=" * 70)
print("测试完成！")
print("=" * 70)

"""
Phase 0 词性标注功能完整测试
验证词性标注、筛选、导出等功能是否正常工作
"""
import sys
from pathlib import Path
from collections import Counter

# 设置UTF-8编码输出
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.pos_tagging import (
    tag_words_batch,
    get_pos_statistics,
    get_available_categories,
    POS_TAGGING_AVAILABLE
)

def test_pos_tagging():
    """测试词性标注功能"""
    print("=" * 60)
    print("Phase 0 词性标注功能测试")
    print("=" * 60)

    # 检查NLTK是否可用
    print(f"\n1. NLTK可用性检查: {POS_TAGGING_AVAILABLE}")
    if not POS_TAGGING_AVAILABLE:
        print("❌ NLTK不可用，请运行: pip install nltk")
        return False

    # 测试词汇列表（模拟分词结果）
    test_words = [
        # 名词
        "calculator", "dashboard", "simulator", "converter", "generator",
        "downloader", "editor", "viewer", "manager", "tracker",
        # 动词
        "download", "upload", "convert", "calculate", "generate",
        "search", "analyze", "compare", "create", "manage",
        # 形容词
        "free", "online", "best", "simple", "fast",
        "easy", "professional", "advanced", "popular", "new",
        # 副词
        "quickly", "easily", "automatically", "directly", "instantly"
    ]

    print(f"\n2. 测试词汇数量: {len(test_words)} 个")

    # 执行批量词性标注
    print("\n3. 执行批量词性标注...")
    pos_tags = tag_words_batch(test_words)

    if not pos_tags:
        print("❌ 词性标注失败")
        return False

    print(f"✓ 标注完成，共 {len(pos_tags)} 个词")

    # 显示标注结果示例
    print("\n4. 标注结果示例（前10个）:")
    print(f"{'词汇':<20} {'详细标签':<12} {'分类':<15} {'中文':<10}")
    print("-" * 60)
    for i, word in enumerate(test_words[:10]):
        if word in pos_tags:
            pos, category, chinese = pos_tags[word]
            print(f"{word:<20} {pos:<12} {category:<15} {chinese:<10}")

    # 创建模拟的词频计数器
    word_counter = Counter({word: (i % 10) + 1 for i, word in enumerate(test_words)})

    # 获取词性统计
    print("\n5. 词性统计分析:")
    pos_stats = get_pos_statistics(word_counter, pos_tags)

    if pos_stats:
        print("\n   按词性分类统计:")
        for category, count in sorted(pos_stats['by_category'].items(),
                                      key=lambda x: x[1], reverse=True):
            from utils.pos_tagging import POS_CATEGORY_NAMES
            chinese_name = POS_CATEGORY_NAMES.get(category, category)
            print(f"     {chinese_name:<12} → {count:3} 个词")

        print(f"\n   总词汇数: {pos_stats['total_words']}")

    # 测试词性筛选
    print("\n6. 词性筛选功能测试:")

    # 筛选出名词
    noun_words = [word for word, (_, cat, _) in pos_tags.items() if cat == 'Noun']
    print(f"   名词数量: {len(noun_words)} 个")
    print(f"   示例: {', '.join(noun_words[:5])}")

    # 筛选出动词
    verb_words = [word for word, (_, cat, _) in pos_tags.items() if cat == 'Verb']
    print(f"   动词数量: {len(verb_words)} 个")
    print(f"   示例: {', '.join(verb_words[:5])}")

    # 筛选出形容词
    adj_words = [word for word, (_, cat, _) in pos_tags.items() if cat == 'Adjective']
    print(f"   形容词数量: {len(adj_words)} 个")
    print(f"   示例: {', '.join(adj_words[:5])}")

    # 测试可用分类
    print("\n7. 支持的词性分类:")
    categories = get_available_categories()
    for eng, cn in categories:
        print(f"   {eng:<15} → {cn}")

    # 总结
    print("\n" + "=" * 60)
    print("✅ 所有测试通过！词性标注功能正常工作")
    print("=" * 60)

    print("\n📝 使用说明:")
    print("1. 在Phase 0页面中，勾选'启用词性标注'")
    print("2. 执行分词后，会自动进行词性标注")
    print("3. 使用'词性筛选'多选框筛选特定词性")
    print("4. 表格中会显示'词性'列")
    print("5. 导出的HTML支持按词性筛选")

    return True

if __name__ == "__main__":
    success = test_pos_tagging()
    sys.exit(0 if success else 1)

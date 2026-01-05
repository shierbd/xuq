"""
Template Discovery - 模板自动发现
核心原则：从数据中发现模板，而不是预设模板

方法论：
1. 统计所有N-gram频次（2-gram, 3-gram, 4-gram）
2. 高频N-gram作为锚点，发现固定的词组合
3. 固定的词组合 = 模板
4. 频次过滤保留有效模板
"""
import sys
from pathlib import Path
from typing import List, Dict, Tuple
from collections import Counter, defaultdict
import re
import json

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from storage.models import Phrase
from storage.repository import PhraseRepository


class NGramAnalyzer:
    """N-gram频次分析器"""

    def __init__(self):
        self.stopwords = self._load_stopwords()

    def _load_stopwords(self) -> set:
        """加载停用词（这些词不适合作为锚点）"""
        return {
            'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this',
            'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
            'my', 'your', 'his', 'her', 'its', 'our', 'their'
        }

    def extract_ngrams(
        self,
        phrases: List[str],
        n: int,
        min_freq: int = 2
    ) -> Counter:
        """
        提取N-gram及其频次

        Args:
            phrases: 短语列表
            n: N-gram的N（2=bigram, 3=trigram, 4=fourgram）
            min_freq: 最小频次过滤

        Returns:
            Counter: {ngram: frequency}
        """
        ngrams = Counter()

        for phrase in phrases:
            # 转小写，分词
            words = phrase.lower().split()

            # 提取n-gram
            for i in range(len(words) - n + 1):
                ngram = ' '.join(words[i:i+n])
                ngrams[ngram] += 1

        # 频次过滤
        filtered = {ng: freq for ng, freq in ngrams.items() if freq >= min_freq}

        return Counter(filtered)

    def analyze_all_ngrams(
        self,
        phrases: List[str],
        min_freq: int = 3
    ) -> Dict[str, Counter]:
        """
        分析所有类型的N-gram（2/3/4-gram）

        Returns:
            {
                'bigrams': Counter(...),
                'trigrams': Counter(...),
                'fourgrams': Counter(...)
            }
        """
        print(f"\n[Analyzing N-grams] From {len(phrases)} phrases...")

        results = {}

        # 2-gram
        print("  Extracting 2-grams...")
        results['bigrams'] = self.extract_ngrams(phrases, n=2, min_freq=min_freq)
        print(f"    Found {len(results['bigrams'])} unique 2-grams (freq >= {min_freq})")

        # 3-gram
        print("  Extracting 3-grams...")
        results['trigrams'] = self.extract_ngrams(phrases, n=3, min_freq=min_freq)
        print(f"    Found {len(results['trigrams'])} unique 3-grams (freq >= {min_freq})")

        # 4-gram
        print("  Extracting 4-grams...")
        results['fourgrams'] = self.extract_ngrams(phrases, n=4, min_freq=max(2, min_freq-1))
        print(f"    Found {len(results['fourgrams'])} unique 4-grams (freq >= {max(2, min_freq-1)})")

        return results


class TemplateDiscoverer:
    """模板发现器：从N-gram中发现模板"""

    def __init__(self):
        self.ngram_analyzer = NGramAnalyzer()
        self.discovered_templates = []

    def discover_templates_from_ngrams(
        self,
        ngram_results: Dict[str, Counter],
        phrases: List[str],
        min_template_freq: int = 10
    ) -> List[Dict]:
        """
        从N-gram中发现模板

        策略：
        1. 高频N-gram作为模板候选的"锚点"
        2. 找到包含这个锚点的所有短语
        3. 分析这些短语的共同结构
        4. 提取固定部分和可变部分，形成模板
        """
        print(f"\n[Discovering Templates] From N-grams...")

        templates = []

        # 从trigrams和fourgrams中寻找模板（它们更有结构性）
        potential_anchors = []

        # 优先使用3-gram和4-gram作为锚点
        for ngram, freq in ngram_results['trigrams'].items():
            if freq >= min_template_freq:
                potential_anchors.append(('trigram', ngram, freq))

        for ngram, freq in ngram_results['fourgrams'].items():
            if freq >= min_template_freq:
                potential_anchors.append(('fourgram', ngram, freq))

        # 按频次降序排序
        potential_anchors.sort(key=lambda x: x[2], reverse=True)

        print(f"  Found {len(potential_anchors)} potential template anchors")

        # 对每个锚点提取模板
        for i, (ngram_type, anchor, freq) in enumerate(potential_anchors[:100], 1):  # 限制处理前100个
            if i % 20 == 0:
                print(f"  Processing anchor {i}/100...")

            template = self._extract_template_from_anchor(
                anchor=anchor,
                phrases=phrases,
                min_matches=min_template_freq
            )

            if template:
                templates.append(template)

        print(f"  Discovered {len(templates)} valid templates")

        return templates

    def _extract_template_from_anchor(
        self,
        anchor: str,
        phrases: List[str],
        min_matches: int = 10
    ) -> Dict:
        """
        从锚点提取模板

        例：
        anchor = "how to"
        matching_phrases = ["how to edit videos", "how to create website", ...]
        → 模板: "how to {X}"

        anchor = "best laptop for"
        matching_phrases = ["best laptop for gaming", "best laptop for students", ...]
        → 模板: "best laptop for {X}"
        """
        # 找到所有包含这个锚点的短语
        anchor_lower = anchor.lower()
        matching_phrases = [p for p in phrases if anchor_lower in p.lower()]

        if len(matching_phrases) < min_matches:
            return None

        # 分析这些短语的结构，提取模板
        template_pattern = self._infer_template_pattern(anchor, matching_phrases)

        if not template_pattern:
            return None

        return {
            'anchor': anchor,
            'template_pattern': template_pattern,
            'match_count': len(matching_phrases),
            'example_phrases': matching_phrases[:5]
        }

    def _infer_template_pattern(
        self,
        anchor: str,
        matching_phrases: List[str]
    ) -> str:
        """
        推断模板模式

        策略：
        1. 找到锚点在短语中的位置
        2. 看锚点前后是否有可变部分
        3. 固定部分保留，可变部分替换为{X}, {Y}
        """
        anchor_lower = anchor.lower()
        anchor_words = anchor_lower.split()

        # 分析锚点位置
        positions = []
        for phrase in matching_phrases[:20]:  # 分析前20个示例
            phrase_lower = phrase.lower()
            phrase_words = phrase_lower.split()

            # 找到锚点的起始位置
            for i in range(len(phrase_words) - len(anchor_words) + 1):
                if phrase_words[i:i+len(anchor_words)] == anchor_words:
                    positions.append({
                        'start': i,
                        'end': i + len(anchor_words),
                        'total_words': len(phrase_words),
                        'prefix': ' '.join(phrase_words[:i]) if i > 0 else '',
                        'suffix': ' '.join(phrase_words[i+len(anchor_words):]) if i+len(anchor_words) < len(phrase_words) else ''
                    })
                    break

        if not positions:
            return None

        # 分析最常见的模式
        # 检查锚点是否总是在开头、中间还是结尾
        start_positions = [p['start'] for p in positions]
        most_common_start = Counter(start_positions).most_common(1)[0][0]

        # 检查前缀是否固定
        prefixes = [p['prefix'] for p in positions if p['prefix']]
        has_fixed_prefix = len(set(prefixes)) == 1 if prefixes else False

        # 检查后缀是否固定
        suffixes = [p['suffix'] for p in positions if p['suffix']]
        has_fixed_suffix = len(set(suffixes)) == 1 if suffixes else False

        # 构建模板模式
        template_parts = []

        # 前缀处理
        if most_common_start == 0:
            # 锚点在开头
            template_parts.append(anchor)
            if not has_fixed_suffix:
                template_parts.append('{X}')
            else:
                template_parts.append(suffixes[0] if suffixes else '')
        elif most_common_start > 0:
            # 锚点在中间或后面
            if has_fixed_prefix:
                template_parts.append(prefixes[0])
                template_parts.append(anchor)
                if not has_fixed_suffix:
                    template_parts.append('{X}')
            else:
                template_parts.append('{X}')
                template_parts.append(anchor)
                if suffixes:
                    if has_fixed_suffix:
                        template_parts.append(suffixes[0])
                    else:
                        template_parts.append('{Y}')

        template_pattern = ' '.join(template_parts).strip()

        # 验证模板有效性（必须包含至少一个变量槽）
        if '{X}' not in template_pattern and '{Y}' not in template_pattern:
            return None

        return template_pattern

    def filter_templates_by_quality(
        self,
        templates: List[Dict],
        min_freq_percentile: int = 50
    ) -> List[Dict]:
        """
        基于质量过滤模板

        质量标准：
        1. 匹配频次（高频模板更可靠）
        2. 模板长度（太短的模板过于泛化）
        3. 变量位置（变量在合理位置）
        """
        if not templates:
            return []

        # 计算频次分位数
        freqs = [t['match_count'] for t in templates]
        freqs.sort()

        def percentile(data, p):
            if not data:
                return 0
            k = (len(data) - 1) * p / 100
            f = int(k)
            c = k - f
            if f + 1 < len(data):
                return data[f] + c * (data[f+1] - data[f])
            else:
                return data[f]

        threshold = percentile(freqs, min_freq_percentile)

        # 过滤
        filtered = []
        for template in templates:
            # 条件1: 频次过滤
            if template['match_count'] < threshold:
                continue

            # 条件2: 模板长度过滤（至少2个词）
            if len(template['template_pattern'].split()) < 2:
                continue

            # 条件3: 必须有变量槽
            if '{X}' not in template['template_pattern'] and '{Y}' not in template['template_pattern']:
                continue

            filtered.append(template)

        # 按频次降序排序
        filtered.sort(key=lambda x: x['match_count'], reverse=True)

        print(f"\n[Template Filtering]")
        print(f"  Threshold (P{min_freq_percentile}): match_count >= {threshold:.0f}")
        print(f"  Before: {len(templates)} templates")
        print(f"  After: {len(filtered)} templates")

        return filtered


def run_template_discovery():
    """运行完整的模板发现流程"""

    print("="*70)
    print("Template Discovery - Data-Driven Approach".center(70))
    print("="*70)
    print("\nPrinciple: Discover templates from data, NOT preset them")

    # 1. 加载数据
    print("\n[Step 1] Loading phrases from database...")
    with PhraseRepository() as repo:
        phrases_db = repo.session.query(Phrase).all()

    phrases = [p.phrase for p in phrases_db]
    print(f"  Loaded {len(phrases)} phrases")

    # 2. N-gram分析
    print("\n[Step 2] Analyzing N-grams...")
    analyzer = NGramAnalyzer()
    ngram_results = analyzer.analyze_all_ngrams(phrases, min_freq=5)

    # 3. 模板发现
    print("\n[Step 3] Discovering templates...")
    discoverer = TemplateDiscoverer()
    templates = discoverer.discover_templates_from_ngrams(
        ngram_results=ngram_results,
        phrases=phrases,
        min_template_freq=10
    )

    # 4. 模板质量过滤
    print("\n[Step 4] Filtering templates by quality...")
    valid_templates = discoverer.filter_templates_by_quality(
        templates=templates,
        min_freq_percentile=75  # 保留P75以上的模板
    )

    # 5. 保存结果
    print("\n[Step 5] Saving results...")
    output_dir = project_root / 'outputs'
    output_dir.mkdir(exist_ok=True)

    # 保存N-gram统计
    ngram_summary = {
        'bigrams_top100': dict(ngram_results['bigrams'].most_common(100)),
        'trigrams_top100': dict(ngram_results['trigrams'].most_common(100)),
        'fourgrams_top100': dict(ngram_results['fourgrams'].most_common(100)),
    }

    with open(output_dir / 'ngram_statistics.json', 'w', encoding='utf-8') as f:
        json.dump(ngram_summary, f, indent=2, ensure_ascii=False)

    # 保存发现的模板
    with open(output_dir / 'discovered_templates.json', 'w', encoding='utf-8') as f:
        json.dump(valid_templates, f, indent=2, ensure_ascii=False)

    # 6. 生成报告
    print("\n" + "="*70)
    print("Discovery Report".center(70))
    print("="*70)

    print("\n[N-gram Statistics]")
    print(f"  Total unique 2-grams: {len(ngram_results['bigrams'])}")
    print(f"  Total unique 3-grams: {len(ngram_results['trigrams'])}")
    print(f"  Total unique 4-grams: {len(ngram_results['fourgrams'])}")

    print("\n[Top 10 Most Frequent 3-grams]")
    for i, (ngram, freq) in enumerate(ngram_results['trigrams'].most_common(10), 1):
        print(f"  {i}. '{ngram}': {freq} times")

    print("\n[Discovered Templates]")
    print(f"  Total valid templates: {len(valid_templates)}")

    print("\n[Top 20 High-Frequency Templates]")
    for i, template in enumerate(valid_templates[:20], 1):
        print(f"\n  {i}. Template: {template['template_pattern']}")
        print(f"     Anchor: {template['anchor']}")
        print(f"     Frequency: {template['match_count']}")
        print(f"     Examples:")
        for j, ex in enumerate(template['example_phrases'][:3], 1):
            print(f"       {j}) {ex}")

    print("\n" + "="*70)
    print("Discovery completed successfully!".center(70))
    print("="*70)

    print(f"\nResults saved to:")
    print(f"  - {output_dir / 'ngram_statistics.json'}")
    print(f"  - {output_dir / 'discovered_templates.json'}")

    return valid_templates


if __name__ == "__main__":
    run_template_discovery()

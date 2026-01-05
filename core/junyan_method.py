"""
君言方法 - 长尾变量提取
完全按照君言的"电商产品快速提取"方法实现

核心步骤：
1. 【提取模板】从种子词中发现搜索模板
2. 【提取变量】从模板中提取目标变量
3. 【质量分析】分析首字/末字，识别脏数据
4. 【循环迭代】变量可作为新种子词
"""
import re
from collections import Counter, defaultdict
from typing import List, Dict, Set, Tuple


class JunyanTemplateExtractor:
    """君言方法 - 步骤1：从种子词提取模板"""

    def __init__(self, phrases: List[str]):
        """
        Args:
            phrases: 全部长尾词数据
        """
        self.phrases = phrases
        self.phrase_lower = [p.lower() for p in phrases]

    def extract_templates_from_seeds(
        self,
        seed_words: List[str],
        min_frequency: int = 5
    ) -> List[Dict]:
        """
        从种子词中提取模板

        Args:
            seed_words: 种子词列表（人工挑选的，确定正确的目标词）
            min_frequency: 模板最小出现频次

        Returns:
            [
                {
                    'template_pattern': '闲鱼上卖{X}',
                    'frequency': 200,
                    'example_phrases': ['闲鱼上卖手机', ...],
                    'matched_seeds': ['手机', '衣服', ...]
                }
            ]
        """
        print("\n" + "="*70)
        print("君言方法 - 步骤1：从种子词提取模板".center(70))
        print("="*70)

        print(f"\n[输入] 种子词数量: {len(seed_words)}")
        print(f"[输入] 短语总数: {len(self.phrases)}")
        print(f"[参数] 最小频次: {min_frequency}")

        # 存储所有模板模式
        template_patterns = Counter()  # {模板模式: 出现次数}
        template_examples = defaultdict(list)  # {模板模式: [示例短语]}
        template_seeds = defaultdict(set)  # {模板模式: {匹配的种子词}}

        # 对每个种子词进行处理
        for i, seed in enumerate(seed_words, 1):
            if i % 10 == 0 or i == len(seed_words):
                print(f"  处理种子词 {i}/{len(seed_words)}: \"{seed}\"")

            seed_lower = seed.lower()

            # 找到包含该种子词的所有短语
            matched_phrases = []
            for j, phrase_l in enumerate(self.phrase_lower):
                if seed_lower in phrase_l:
                    matched_phrases.append((self.phrases[j], phrase_l))

            if not matched_phrases:
                continue

            # 将种子词替换为占位符{X}，得到模板模式
            for original_phrase, phrase_l in matched_phrases:
                # 找到种子词的位置
                pattern = phrase_l.replace(seed_lower, '{X}')

                # 统计模板
                template_patterns[pattern] += 1
                template_seeds[pattern].add(seed)

                # 保存示例（最多5个）
                if len(template_examples[pattern]) < 5:
                    template_examples[pattern].append(original_phrase)

        # 按频次排序，过滤低频模板
        templates = []
        for pattern, freq in template_patterns.most_common():
            if freq < min_frequency:
                break

            templates.append({
                'template_pattern': pattern,
                'frequency': freq,
                'example_phrases': template_examples[pattern],
                'matched_seeds': sorted(list(template_seeds[pattern]))
            })

        print(f"\n[结果] 发现模板数: {len(templates)}")
        if templates:
            print(f"[结果] 最高频次: {templates[0]['frequency']}")
            print(f"\n[Top 10 模板]:")
            for i, t in enumerate(templates[:10], 1):
                print(f"  {i}. \"{t['template_pattern']}\" - 频次: {t['frequency']}, 种子词: {len(t['matched_seeds'])}个")

        return templates


class JunyanVariableExtractor:
    """君言方法 - 步骤2：从模板提取变量"""

    def __init__(self, phrases: List[str]):
        """
        Args:
            phrases: 全部长尾词数据
        """
        self.phrases = phrases
        self.phrase_lower = [p.lower() for p in phrases]

    def extract_variables_from_templates(
        self,
        templates: List[str],
        min_frequency: int = 3,
        stop_words: List[str] = None
    ) -> Dict:
        """
        从模板中提取变量

        Args:
            templates: 模板列表（人工筛选的高质量模板）
            min_frequency: 变量最小出现频次
            stop_words: 停用词列表（用于过滤脏数据）

        Returns:
            {
                'variables': [
                    {
                        'variable_text': '手机',
                        'frequency': 500,
                        'template_match_count': 8,
                        'matched_templates': ['闲鱼上卖{X}', ...]
                    }
                ],
                'quality_analysis': {
                    'first_char_freq': {'手': 200, '电': 150, ...},
                    'last_char_freq': {'机': 180, '器': 120, ...},
                    'template_variable_map': {
                        '闲鱼上卖{X}': ['手机', '电脑', ...],
                        ...
                    }
                }
            }
        """
        print("\n" + "="*70)
        print("君言方法 - 步骤2：从模板提取变量".center(70))
        print("="*70)

        print(f"\n[输入] 模板数量: {len(templates)}")
        print(f"[输入] 短语总数: {len(self.phrases)}")
        print(f"[参数] 最小频次: {min_frequency}")
        print(f"[参数] 停用词数: {len(stop_words) if stop_words else 0}")

        if stop_words is None:
            stop_words = []
        stop_words_set = set(w.lower() for w in stop_words)

        # 存储变量
        variable_freq = Counter()  # {变量: 出现次数}
        variable_templates = defaultdict(set)  # {变量: {匹配的模板}}
        template_variable_map = defaultdict(list)  # {模板: [变量列表]}

        # 首字/末字统计
        first_char_freq = Counter()
        last_char_freq = Counter()

        # 对每个模板进行处理
        for i, template in enumerate(templates, 1):
            print(f"  处理模板 {i}/{len(templates)}: \"{template}\"")

            # 将模板转换为正则表达式
            regex_pattern = self._template_to_regex(template)
            if not regex_pattern:
                continue

            regex = re.compile(regex_pattern, re.IGNORECASE)

            # 匹配所有短语
            matched_count = 0
            for phrase_l in self.phrase_lower:
                match = regex.search(phrase_l)
                if match:
                    # 提取变量
                    variable = match.group(1).strip()

                    # 过滤空变量和停用词
                    if not variable or variable in stop_words_set:
                        continue

                    # 过滤过短的变量
                    if len(variable) < 2:
                        continue

                    # 统计
                    variable_freq[variable] += 1
                    variable_templates[variable].add(template)

                    # 记录模板-变量映射
                    if variable not in template_variable_map[template]:
                        template_variable_map[template].append(variable)

                    # 统计首字/末字
                    if len(variable) > 0:
                        first_char_freq[variable[0]] += 1
                        last_char_freq[variable[-1]] += 1

                    matched_count += 1

            print(f"    匹配到 {matched_count} 条数据")

        # 过滤低频变量
        valid_variables = []
        for var, freq in variable_freq.most_common():
            if freq < min_frequency:
                break

            valid_variables.append({
                'variable_text': var,
                'frequency': freq,
                'template_match_count': len(variable_templates[var]),
                'matched_templates': sorted(list(variable_templates[var]))
            })

        print(f"\n[结果] 提取变量总数: {len(variable_freq)}")
        print(f"[结果] 有效变量数（频次>={min_frequency}）: {len(valid_variables)}")

        if valid_variables:
            print(f"\n[Top 10 变量]:")
            for i, v in enumerate(valid_variables[:10], 1):
                print(f"  {i}. \"{v['variable_text']}\" - 频次: {v['frequency']}, 模板: {v['template_match_count']}个")

        # 质量分析
        quality_analysis = {
            'first_char_freq': dict(first_char_freq.most_common(50)),
            'last_char_freq': dict(last_char_freq.most_common(50)),
            'template_variable_map': {t: vars[:20] for t, vars in template_variable_map.items()}  # 每个模板只保存前20个变量
        }

        print(f"\n[质量分析]")
        print(f"  首字Top5: {list(first_char_freq.most_common(5))}")
        print(f"  末字Top5: {list(last_char_freq.most_common(5))}")

        return {
            'variables': valid_variables,
            'quality_analysis': quality_analysis
        }

    def _template_to_regex(self, template: str) -> str:
        """
        将模板转换为正则表达式

        Args:
            template: 模板字符串，如 "闲鱼上卖{X}"

        Returns:
            正则表达式字符串
        """
        # 转义特殊字符
        escaped = re.escape(template)

        # 替换{X}为捕获组
        # re.escape会把{X}转义为\{X\}，我们需要替换回(.+?)
        pattern = escaped.replace(r'\{X\}', '(.+?)')

        # 如果{X}在末尾，使用贪婪匹配
        if pattern.endswith('(.+?)'):
            pattern = pattern[:-5] + '(.+)'

        return pattern


class JunyanQualityAnalyzer:
    """君言方法 - 步骤3：质量分析"""

    @staticmethod
    def analyze_noise_patterns(quality_analysis: Dict) -> Dict:
        """
        分析噪音模式，识别需要添加到停用词的字符

        Args:
            quality_analysis: 质量分析结果

        Returns:
            {
                'high_freq_first_chars': ['的', '了', ...],
                'high_freq_last_chars': ['上', '的', ...],
                'suggested_stop_words': [...]
            }
        """
        first_char_freq = quality_analysis['first_char_freq']
        last_char_freq = quality_analysis['last_char_freq']

        # 常见的无意义字符
        meaningless_chars = set(['的', '了', '在', '和', '与', '或', '上', '下', '中', '是', '有'])

        # 高频无意义首字
        high_freq_first = [
            char for char, freq in first_char_freq.items()
            if char in meaningless_chars and freq > 50
        ]

        # 高频无意义末字
        high_freq_last = [
            char for char, freq in last_char_freq.items()
            if char in meaningless_chars and freq > 50
        ]

        return {
            'high_freq_first_chars': high_freq_first,
            'high_freq_last_chars': high_freq_last,
            'suggested_stop_words': list(set(high_freq_first + high_freq_last))
        }

"""
Variable Extractor - 变量提取器
核心原则：用发现的模板提取变量，而不是预设变量
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


class VariableExtractor:
    """变量提取器：从发现的模板中提取变量"""

    def __init__(self, discovered_templates: List[Dict]):
        """
        Args:
            discovered_templates: 从template_discovery.py发现的模板列表
        """
        self.templates = discovered_templates
        self.variable_matches = []  # 所有变量匹配结果

    def extract_variables_from_all_phrases(
        self,
        phrases: List[str],
        phrase_volumes: Dict[str, int] = None
    ) -> Dict:
        """
        从所有短语中提取变量

        Args:
            phrases: 短语列表
            phrase_volumes: 短语搜索量字典 {phrase: volume}

        Returns:
            {
                'variable_matches': [...],  # 所有匹配结果
                'variable_freq': {...},     # 变量频次
                'variable_templates': {...},  # 变量匹配了哪些模板
                'statistics': {...}
            }
        """
        print("\n" + "="*70)
        print("Phase 5: Variable Extraction from Discovered Templates".center(70))
        print("="*70)

        if phrase_volumes is None:
            phrase_volumes = {p: 0 for p in phrases}

        print(f"\n[Processing] Applying {len(self.templates)} templates to {len(phrases)} phrases...")

        # 对每个模板提取变量
        for i, template in enumerate(self.templates, 1):
            if i % 5 == 0:
                print(f"  Processing template {i}/{len(self.templates)}...")

            matches = self._apply_template_to_phrases(
                template=template,
                phrases=phrases,
                phrase_volumes=phrase_volumes
            )

            self.variable_matches.extend(matches)

        print(f"  [OK] Total variable matches: {len(self.variable_matches)}")

        # 统计分析
        results = self._analyze_variables()

        return results

    def _apply_template_to_phrases(
        self,
        template: Dict,
        phrases: List[str],
        phrase_volumes: Dict[str, int]
    ) -> List[Dict]:
        """对短语应用模板，提取变量"""
        matches = []

        # 将模板模式转换为正则表达式
        pattern = template['template_pattern']
        regex_pattern, capture_info = self._template_to_regex(pattern)

        if not regex_pattern:
            return matches

        regex = re.compile(regex_pattern, re.IGNORECASE)

        for phrase in phrases:
            match = regex.search(phrase.lower())
            if match:
                # 提取变量值
                variables = {}
                for i, group in enumerate(match.groups(), 1):
                    slot = f"slot_{i}"
                    variables[slot] = group.strip()

                # 分解短语为：前缀、变量、后缀
                decomposition = self._decompose_phrase(phrase, match, pattern, capture_info)

                matches.append({
                    'phrase': phrase,
                    'phrase_lower': phrase.lower(),
                    'volume': phrase_volumes.get(phrase, 0),
                    'template_anchor': template['anchor'],
                    'template_pattern': pattern,
                    'variables': variables,
                    # 新增：详细分解
                    'prefix': decomposition['prefix'],
                    'suffix': decomposition['suffix'],
                    'middle_parts': decomposition['middle_parts'],  # 中间穿插的固定部分
                    'variable_positions': decomposition['variable_positions']
                })

        return matches

    def _template_to_regex(self, template_pattern: str) -> Tuple[str, Dict]:
        """
        将模板模式转换为正则表达式

        例：
        "best way to {X}" → (r"best way to (.+)", {'X': {'position': 0, 'prefix': 'best way to ', 'suffix': ''}})
        "{X} books in order" → (r"(.+?) books in order", {'X': {'position': 0, 'prefix': '', 'suffix': ' books in order'}})

        Returns:
            (regex_pattern, capture_info)
        """
        # 分析模板结构
        parts = re.split(r'(\{[XYZ]\})', template_pattern)

        capture_info = {}
        variable_count = 0
        regex_parts = []

        for i, part in enumerate(parts):
            if part in ['{X}', '{Y}', '{Z}']:
                var_name = part[1]  # X, Y, or Z

                # 判断是否是最后一个变量
                is_last_variable = i == len(parts) - 1 or all(p.strip() == '' for p in parts[i+1:])

                if is_last_variable:
                    regex_parts.append('(.+)')  # 贪婪匹配
                else:
                    regex_parts.append('(.+?)')  # 非贪婪匹配

                # 记录捕获信息
                capture_info[var_name] = {
                    'position': variable_count,
                    'prefix': ''.join(parts[:i]),
                    'suffix': ''.join(parts[i+1:])
                }
                variable_count += 1
            else:
                # 转义正则表达式特殊字符
                escaped = re.escape(part)
                regex_parts.append(escaped)

        pattern = ''.join(regex_parts)

        return pattern, capture_info

    def _decompose_phrase(self, phrase: str, match: re.Match, template_pattern: str, capture_info: Dict) -> Dict:
        """
        分解短语为前缀、后缀、中间固定部分

        Args:
            phrase: 原始短语
            match: 正则匹配对象
            template_pattern: 模板模式
            capture_info: 捕获信息

        Returns:
            {
                'prefix': 前缀文本,
                'suffix': 后缀文本,
                'middle_parts': [中间固定部分列表],
                'variable_positions': [(start, end, var_name), ...]
            }
        """
        # 获取匹配的开始和结束位置
        match_start = match.start()
        match_end = match.end()

        # 前缀：匹配之前的内容
        prefix = phrase[:match_start]

        # 后缀：匹配之后的内容
        suffix = phrase[match_end:]

        # 分析模板中的固定部分
        parts = re.split(r'\{[XYZ]\}', template_pattern)
        fixed_parts = [p for p in parts if p.strip()]  # 非空的固定部分

        # 提取变量位置
        variable_positions = []
        for i, group in enumerate(match.groups()):
            var_start = match.start(i + 1)
            var_end = match.end(i + 1)
            # 找到对应的变量名
            var_name = None
            for name, info in capture_info.items():
                if info['position'] == i:
                    var_name = name
                    break
            variable_positions.append((var_start, var_end, var_name or f"var_{i}"))

        return {
            'prefix': prefix,
            'suffix': suffix,
            'middle_parts': fixed_parts[1:-1] if len(fixed_parts) > 2 else [],  # 中间穿插的固定部分
            'variable_positions': variable_positions
        }

    def _analyze_variables(self) -> Dict:
        """分析提取的变量"""
        print("\n[Step 2] Analyzing extracted variables...")

        # 统计变量频次
        variable_freq = Counter()
        variable_templates = defaultdict(set)  # 变量匹配了哪些模板
        variable_volumes = Counter()  # 变量的总搜索量

        for match in self.variable_matches:
            for slot, value in match['variables'].items():
                # 归一化变量值
                normalized_value = value.lower().strip()

                # 跳过过短的变量（可能是噪音）
                if len(normalized_value) < 2:
                    continue

                variable_freq[normalized_value] += 1
                variable_templates[normalized_value].add(match['template_anchor'])
                variable_volumes[normalized_value] += match['volume']

        # 转换为字典（set不能JSON序列化）
        variable_template_count = {
            var: len(templates)
            for var, templates in variable_templates.items()
        }

        # 计算交叉验证分数
        cross_validation_scores = {
            var: freq * variable_template_count[var]
            for var, freq in variable_freq.items()
        }

        # 计算百分位数
        freq_values = list(variable_freq.values())
        freq_values.sort()

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

        stats = {
            'total_matches': len(self.variable_matches),
            'unique_variables': len(variable_freq),
            'variable_freq_p25': percentile(freq_values, 25),
            'variable_freq_p50': percentile(freq_values, 50),
            'variable_freq_p75': percentile(freq_values, 75),
            'variable_freq_p90': percentile(freq_values, 90),
            'variable_freq_max': max(freq_values) if freq_values else 0,
        }

        print(f"  Total variable matches: {stats['total_matches']}")
        print(f"  Unique variables extracted: {stats['unique_variables']}")
        print(f"  Variable frequency P50: {stats['variable_freq_p50']}")
        print(f"  Variable frequency P75: {stats['variable_freq_p75']}")

        return {
            'variable_matches': self.variable_matches,
            'variable_freq': dict(variable_freq),
            'variable_template_count': variable_template_count,
            'variable_volumes': dict(variable_volumes),
            'cross_validation_scores': cross_validation_scores,
            'statistics': stats
        }

    def filter_high_quality_variables(
        self,
        extraction_results: Dict,
        min_freq: int = 3,
        min_templates: int = 2
    ) -> List[Dict]:
        """
        过滤高质量变量

        质量标准（交叉验证）：
        1. 出现频次 >= min_freq
        2. 匹配模板数 >= min_templates
        """
        print("\n" + "="*70)
        print("Phase 6: Variable Cross-Validation".center(70))
        print("="*70)

        print(f"\n[Filtering] High-quality variables...")
        print(f"  Criteria: freq >= {min_freq}, templates >= {min_templates}")

        variable_freq = extraction_results['variable_freq']
        variable_template_count = extraction_results['variable_template_count']
        variable_volumes = extraction_results['variable_volumes']
        cross_validation_scores = extraction_results['cross_validation_scores']

        valid_variables = []

        for var, freq in variable_freq.items():
            # 条件1: 频次过滤
            if freq < min_freq:
                continue

            # 条件2: 交叉验证（匹配多个模板）
            template_count = variable_template_count.get(var, 0)
            if template_count < min_templates:
                continue

            valid_variables.append({
                'variable_text': var,
                'frequency': freq,
                'template_match_count': template_count,
                'total_volume': variable_volumes.get(var, 0),
                'cross_validation_score': cross_validation_scores.get(var, 0)
            })

        # 按交叉验证分数降序排序
        valid_variables.sort(key=lambda x: x['cross_validation_score'], reverse=True)

        print(f"\n[Result]")
        print(f"  Before filtering: {len(variable_freq)} variables")
        print(f"  After filtering: {len(valid_variables)} variables")
        print(f"  Retention rate: {len(valid_variables)/len(variable_freq)*100:.1f}%")

        return valid_variables


def run_variable_extraction_pipeline():
    """运行完整的变量提取流程"""

    print("="*70)
    print("Variable Extraction Pipeline - Data-Driven Approach".center(70))
    print("="*70)
    print("\nPrinciple: Extract variables from DISCOVERED templates")

    # 1. 加载发现的模板
    print("\n[Step 1] Loading discovered templates...")
    templates_file = project_root / 'outputs' / 'discovered_templates.json'

    if not templates_file.exists():
        print(f"  [ERROR] Template file not found: {templates_file}")
        print("  Please run core/template_discovery.py first!")
        return

    with open(templates_file, 'r', encoding='utf-8') as f:
        templates = json.load(f)

    print(f"  Loaded {len(templates)} discovered templates")

    # 2. 加载短语数据
    print("\n[Step 2] Loading phrases from database...")
    with PhraseRepository() as repo:
        phrases_db = repo.session.query(Phrase).all()

    phrases = [p.phrase for p in phrases_db]
    phrase_volumes = {p.phrase: p.volume for p in phrases_db}

    print(f"  Loaded {len(phrases)} phrases")

    # 3. 提取变量
    print("\n[Step 3] Extracting variables...")
    extractor = VariableExtractor(discovered_templates=templates)
    extraction_results = extractor.extract_variables_from_all_phrases(
        phrases=phrases,
        phrase_volumes=phrase_volumes
    )

    # 4. 交叉验证过滤
    valid_variables = extractor.filter_high_quality_variables(
        extraction_results=extraction_results,
        min_freq=3,      # 至少出现3次
        min_templates=2  # 至少匹配2个模板
    )

    # 5. 保存结果
    print("\n[Step 4] Saving results...")
    output_dir = project_root / 'outputs'
    output_dir.mkdir(exist_ok=True)

    # 保存汇总结果（用于统计和概览）
    summary = {
        'statistics': extraction_results['statistics'],
        'top_variables': valid_variables[:200],  # 只保存Top 200
    }

    with open(output_dir / 'variable_extraction_results.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    # 保存所有详细匹配数据（用于详细数据展示）
    print("  Saving detailed matches data...")
    detailed_matches = {
        'total_matches': len(extractor.variable_matches),
        'matches': extractor.variable_matches  # 包含所有字段：phrase, template, prefix, suffix, variables等
    }

    with open(output_dir / 'detailed_matches.json', 'w', encoding='utf-8') as f:
        json.dump(detailed_matches, f, indent=2, ensure_ascii=False)

    print(f"  Saved {len(extractor.variable_matches)} detailed matches")

    # 6. 生成报告
    print("\n" + "="*70)
    print("Variable Extraction Report".center(70))
    print("="*70)

    stats = extraction_results['statistics']

    print("\n[Extraction Statistics]")
    print(f"  Total phrase matches: {stats['total_matches']}")
    print(f"  Unique variables extracted: {stats['unique_variables']}")

    print("\n[Variable Frequency Distribution]")
    print(f"  P25: {stats['variable_freq_p25']}")
    print(f"  P50 (median): {stats['variable_freq_p50']}")
    print(f"  P75: {stats['variable_freq_p75']}")
    print(f"  P90: {stats['variable_freq_p90']}")
    print(f"  Max: {stats['variable_freq_max']}")

    print("\n[High-Quality Variables (Cross-Validated)]")
    print(f"  Total valid variables: {len(valid_variables)}")

    print("\n[Top 30 Variables by Cross-Validation Score]")
    for i, var in enumerate(valid_variables[:30], 1):
        print(f"\n  {i}. \"{var['variable_text']}\"")
        print(f"     Frequency: {var['frequency']}")
        print(f"     Template matches: {var['template_match_count']}")
        print(f"     Total volume: {var['total_volume']}")
        print(f"     Cross-validation score: {var['cross_validation_score']}")

    print("\n" + "="*70)
    print("Variable extraction completed successfully!".center(70))
    print("="*70)

    print(f"\nResults saved to:")
    print(f"  - {output_dir / 'variable_extraction_results.json'}")

    return valid_variables


if __name__ == "__main__":
    run_variable_extraction_pipeline()

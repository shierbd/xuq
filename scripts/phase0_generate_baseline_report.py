"""
Phase 0 - 基线报告生成器
Baseline Report Generator

功能：聚合4个实验的结果，生成完整的基线报告和优化建议

创建日期：2025-12-23
"""

import json
import io
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
import sys

# Set UTF-8 encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def load_experiment_result(experiment_letter: str) -> Optional[Dict]:
    """
    加载实验结果

    Args:
        experiment_letter: 'a', 'b', 'c', 'd'

    Returns:
        实验结果字典，如果文件不存在则返回None
    """
    result_file = project_root / 'data' / 'phase0_results' / f'experiment_{experiment_letter}_result.json'

    if not result_file.exists():
        return None

    with open(result_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_phase_recommendations(results: Dict[str, Dict]) -> Dict[str, Dict]:
    """
    根据实验结果生成Phase 1-3的优化建议

    Args:
        results: 包含所有实验结果的字典

    Returns:
        优化建议字典
    """
    recommendations = {}

    # Phase 1: 聚类质量评分 + 辅助筛选
    exp_a = results.get('a')
    if exp_a:
        if exp_a.get('recommendation') == 'need_optimization':
            recommendations['phase1_cluster_scoring'] = {
                'priority': 'high',
                'reason': f"聚类审核{exp_a.get('recommendation_detail')}",
                'actions': [
                    '实施聚类质量评分算法',
                    '添加LLM预评估功能',
                    '在Web UI中显示推荐簇'
                ]
            }
        elif exp_a.get('recommendation') == 'moderate':
            recommendations['phase1_cluster_scoring'] = {
                'priority': 'medium',
                'reason': f"聚类审核{exp_a.get('recommendation_detail')}",
                'actions': [
                    '可考虑添加简单的排序功能',
                    'LLM预评估作为可选功能'
                ]
            }
        else:
            recommendations['phase1_cluster_scoring'] = {
                'priority': 'low',
                'reason': f"聚类审核{exp_a.get('recommendation_detail')}",
                'actions': ['暂不需要优化']
            }

    # Phase 2.1: 词级规范化去重
    exp_c = results.get('c')
    if exp_c:
        if exp_c.get('recommendation') == 'need_canonicalization':
            recommendations['phase2_1_canonicalization'] = {
                'priority': 'high',
                'reason': f"冗余率{exp_c.get('recommendation_detail')}",
                'actions': [
                    '实施词级规范化算法',
                    '仅去除articles (a/an/the)',
                    '保留意图词和语义介词',
                    '添加canonical_forms表'
                ]
            }
        elif exp_c.get('recommendation') == 'moderate':
            recommendations['phase2_1_canonicalization'] = {
                'priority': 'medium',
                'reason': f"冗余率{exp_c.get('recommendation_detail')}",
                'actions': [
                    '可考虑轻量级去重',
                    '先在小规模数据上测试'
                ]
            }
        else:
            recommendations['phase2_1_canonicalization'] = {
                'priority': 'low',
                'reason': f"冗余率{exp_c.get('recommendation_detail')}",
                'actions': ['暂不需要规范化去重']
            }

    # Phase 2.2: 模板-变量迭代扩展
    exp_b = results.get('b')
    if exp_b:
        if exp_b.get('recommendation') == 'need_expansion':
            recommendations['phase2_2_template_variable'] = {
                'priority': 'high',
                'reason': f"Token覆盖率{exp_b.get('recommendation_detail')}",
                'actions': [
                    '实施词级模板-变量迭代算法',
                    '从现有26个token作为种子',
                    '扩展到200-500个特征词',
                    '用LLM辅助分类'
                ],
                'target': '覆盖率达到80%以上'
            }
        elif exp_b.get('recommendation') == 'moderate':
            recommendations['phase2_2_template_variable'] = {
                'priority': 'medium',
                'reason': f"Token覆盖率{exp_b.get('recommendation_detail')}",
                'actions': [
                    '可考虑适度扩展',
                    '目标扩展到100-200个'
                ]
            }
        else:
            recommendations['phase2_2_template_variable'] = {
                'priority': 'low',
                'reason': f"Token覆盖率{exp_b.get('recommendation_detail')}",
                'actions': ['当前词库充足，暂不需要扩展']
            }

    # Phase 3: 搜索意图分类框架
    exp_d = results.get('d')
    if exp_d:
        if exp_d.get('recommendation') == 'similar_to_junyan':
            recommendations['phase3_intent_framework'] = {
                'priority': 'high',
                'reason': f"意图分布{exp_d.get('recommendation_detail')}",
                'actions': [
                    '实施意图分类框架',
                    '采用君言式分类体系',
                    '聚焦find_tool类需求',
                    '添加意图×产品类型视图'
                ]
            }
        elif exp_d.get('recommendation') == 'different_pattern':
            recommendations['phase3_intent_framework'] = {
                'priority': 'medium',
                'reason': f"意图分布{exp_d.get('recommendation_detail')}",
                'actions': [
                    '实施意图分类，但采用均衡策略',
                    '不过度聚焦某单一意图',
                    '考虑多维度分析视图'
                ]
            }
        else:
            recommendations['phase3_intent_framework'] = {
                'priority': 'medium',
                'reason': f"意图分布{exp_d.get('recommendation_detail')}",
                'actions': [
                    '实施意图分类作为辅助功能',
                    '提供多维度分析能力'
                ]
            }

    return recommendations


def generate_markdown_report(results: Dict[str, Dict], recommendations: Dict[str, Dict]) -> str:
    """
    生成Markdown格式的报告

    Args:
        results: 实验结果
        recommendations: 优化建议

    Returns:
        Markdown文本
    """
    report_lines = []

    # 标题和概述
    report_lines.extend([
        "# 英文关键词聚类系统基线报告",
        f"> **生成日期**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "> ",
        "> **Phase 0目标**: 通过4个实验测量当前系统能力，识别真实问题，为后续优化提供证据基础",
        "",
        "---",
        "",
        "## 📊 执行摘要",
        ""
    ])

    # 快速结论
    report_lines.extend([
        "### 核心发现",
        ""
    ])

    exp_a = results.get('a')
    if exp_a:
        report_lines.append(f"- **聚类审核效率**: {exp_a.get('recommendation_detail')}")

    exp_b = results.get('b')
    if exp_b:
        report_lines.append(f"- **Token覆盖率**: {exp_b.get('recommendation_detail')}")

    exp_c = results.get('c')
    if exp_c:
        report_lines.append(f"- **冗余率**: {exp_c.get('recommendation_detail')}")

    exp_d = results.get('d')
    if exp_d:
        report_lines.append(f"- **意图分布**: {exp_d.get('recommendation_detail')}")

    report_lines.extend([
        "",
        "### 优先级建议",
        ""
    ])

    # 按优先级排序建议
    high_priority = [k for k, v in recommendations.items() if v.get('priority') == 'high']
    medium_priority = [k for k, v in recommendations.items() if v.get('priority') == 'medium']
    low_priority = [k for k, v in recommendations.items() if v.get('priority') == 'low']

    if high_priority:
        report_lines.append("🔴 **高优先级** (1-2周内实施):")
        for key in high_priority:
            rec = recommendations[key]
            report_lines.append(f"- {key}: {rec['reason']}")
        report_lines.append("")

    if medium_priority:
        report_lines.append("🟡 **中优先级** (1个月内考虑):")
        for key in medium_priority:
            rec = recommendations[key]
            report_lines.append(f"- {key}: {rec['reason']}")
        report_lines.append("")

    if low_priority:
        report_lines.append("🟢 **低优先级** (暂不实施):")
        for key in low_priority:
            rec = recommendations[key]
            report_lines.append(f"- {key}: {rec['reason']}")
        report_lines.append("")

    # 详细实验结果
    report_lines.extend([
        "---",
        "",
        "## 📋 实验结果详情",
        ""
    ])

    # 实验A
    if exp_a:
        report_lines.extend([
            "### 实验A：聚类审核效率测量",
            "",
            "**目标**: 测量从60-100个簇中筛选10-15个所需的时间和准确率",
            "",
            "**结果**:",
            f"- 簇总数: {exp_a.get('cluster_count', 'N/A')}",
            f"- 审核簇数: {exp_a.get('reviewed_count', 'N/A')}",
            f"- 选中簇数: {exp_a.get('selected_count', 'N/A')}",
            f"- 审核时间: {exp_a.get('time_minutes', 0):.1f} 分钟",
            f"- 主观感受: {exp_a.get('subjective', 'N/A')}",
            f"- 遗漏簇数: {exp_a.get('missed_count', 0)}",
            f"- 遗漏率: {exp_a.get('missed_rate', 0):.1%}",
            "",
            "**判断标准**:",
            "- ✅ 通过: 时间<60min 且 遗漏率<10%",
            "- ⚠️ 中等: 时间60-120min 或 遗漏率10-30%",
            "- ❌ 需优化: 时间>120min 或 遗漏率>30%",
            "",
            f"**结论**: {exp_a.get('recommendation_detail')}",
            ""
        ])

    # 实验B
    if exp_b:
        report_lines.extend([
            "### 实验B：Token覆盖率测量",
            "",
            "**目标**: 测量当前26个token覆盖了多少短语",
            "",
            "**结果**:",
            f"- 短语总数: {exp_b.get('total_phrases', 0):,}",
            f"- Token总数: {exp_b.get('token_count', 0)}",
            f"- 被覆盖短语: {exp_b.get('covered_count', 0):,}",
            f"- 未覆盖短语: {exp_b.get('uncovered_count', 0):,}",
            f"- 覆盖率: {exp_b.get('coverage_rate', 0):.1%}",
            "",
            "**当前Token列表**:",
        ])

        tokens = exp_b.get('tokens', [])
        for i, token in enumerate(tokens, 1):
            report_lines.append(f"  {i}. {token}")

        report_lines.extend([
            "",
            "**判断标准**:",
            "- ✅ 充足: 覆盖率≥80%",
            "- ⚠️ 中等: 覆盖率60-80%",
            "- ❌ 不足: 覆盖率≤60%",
            "",
            f"**结论**: {exp_b.get('recommendation_detail')}",
            ""
        ])

    # 实验C
    if exp_c:
        report_lines.extend([
            "### 实验C：同义冗余率测量",
            "",
            "**目标**: 测量同一需求的不同表达占比",
            "",
            "**结果**:",
            f"- 抽样数量: {exp_c.get('sample_size', 0):,}",
            f"- 同义组数: {exp_c.get('synonym_groups_count', 0)}",
            f"- 同义短语数: {exp_c.get('phrases_in_groups', 0)}",
            f"- 冗余率: {exp_c.get('redundancy_rate', 0):.1%}",
            "",
            "**判断标准**:",
            "- ✅ 可接受: 冗余率<10%",
            "- ⚠️ 中等: 冗余率10-20%",
            "- ❌ 需处理: 冗余率>20%",
            "",
            f"**结论**: {exp_c.get('recommendation_detail')}",
            ""
        ])

    # 实验D
    if exp_d:
        report_lines.extend([
            "### 实验D：搜索意图分布统计",
            "",
            "**目标**: 统计英文关键词的搜索意图分布",
            "",
            "**结果**:",
            f"- 抽样数量: {exp_d.get('sample_size', 0):,}",
            "",
            "**意图分布**:",
        ])

        intent_dist = exp_d.get('intent_distribution', {})
        for intent_key, stats in intent_dist.items():
            report_lines.append(f"- {intent_key}: {stats.get('count', 0)} ({stats.get('percentage', 0):.1%})")

        report_lines.extend([
            "",
            "**判断标准**:",
            "- 类似君言: find_tool>70%",
            "- 不同模式: find_tool<40%",
            "- 中等分布: 40-70%",
            "",
            f"**结论**: {exp_d.get('recommendation_detail')}",
            ""
        ])

    # 优化建议详情
    report_lines.extend([
        "---",
        "",
        "## 🎯 优化建议详情",
        ""
    ])

    for key, rec in recommendations.items():
        priority_emoji = {
            'high': '🔴',
            'medium': '🟡',
            'low': '🟢'
        }.get(rec.get('priority'), '⚪')

        report_lines.extend([
            f"### {priority_emoji} {key}",
            "",
            f"**优先级**: {rec.get('priority')}",
            f"**原因**: {rec.get('reason')}",
            "",
            "**行动项**:",
        ])

        for action in rec.get('actions', []):
            report_lines.append(f"- {action}")

        if 'target' in rec:
            report_lines.append(f"\n**目标**: {rec['target']}")

        report_lines.append("")

    # 实施时间线
    report_lines.extend([
        "---",
        "",
        "## 📅 建议实施时间线",
        ""
    ])

    if high_priority:
        report_lines.extend([
            "### 第1-2周：高优先级任务",
            ""
        ])
        for key in high_priority:
            rec = recommendations[key]
            report_lines.append(f"**{key}**:")
            for action in rec.get('actions', []):
                report_lines.append(f"- {action}")
            report_lines.append("")

    if medium_priority:
        report_lines.extend([
            "### 第3-4周：中优先级任务",
            ""
        ])
        for key in medium_priority:
            rec = recommendations[key]
            report_lines.append(f"**{key}**:")
            for action in rec.get('actions', []):
                report_lines.append(f"- {action}")
            report_lines.append("")

    # 结论
    report_lines.extend([
        "---",
        "",
        "## 📌 总结",
        "",
        "### 核心原则",
        "",
        "1. **证据驱动**: 所有优化建议都基于Phase 0实测数据",
        "2. **问题导向**: 只优化有实际问题的模块",
        "3. **渐进迭代**: 一次优化一个模块，保持系统稳定",
        "4. **保持优势**: 不破坏现有MVP的优势（HDBSCAN、LLM、Streamlit）",
        "",
        "### 下一步行动",
        ""
    ])

    if high_priority:
        report_lines.append(f"1. 优先实施: {', '.join(high_priority)}")
    if medium_priority:
        report_lines.append(f"2. 后续考虑: {', '.join(medium_priority)}")
    if low_priority:
        report_lines.append(f"3. 暂不实施: {', '.join(low_priority)}")

    report_lines.extend([
        "",
        "---",
        "",
        f"**报告生成时间**: {datetime.now().isoformat()}",
        "**Phase 0状态**: 完成 ✅"
    ])

    return '\n'.join(report_lines)


def run_baseline_report_generator():
    """
    执行基线报告生成
    """
    print("\n" + "="*70)
    print("Phase 0 - 基线报告生成")
    print("="*70)

    # 1. 加载所有实验结果
    print("\n1. 加载实验结果...")

    results = {}
    for exp_letter in ['a', 'b', 'c', 'd']:
        result = load_experiment_result(exp_letter)
        if result:
            results[exp_letter] = result
            print(f"✓ 实验{exp_letter.upper()}结果已加载")
        else:
            print(f"⚠️  实验{exp_letter.upper()}结果未找到")

    if not results:
        print("\n❌ 没有找到任何实验结果，请先运行实验A-D")
        sys.exit(1)

    print(f"\n✓ 成功加载 {len(results)}/4 个实验结果")

    # 2. 生成优化建议
    print("\n2. 生成优化建议...")

    recommendations = generate_phase_recommendations(results)

    print(f"✓ 生成 {len(recommendations)} 项优化建议")

    # 3. 生成Markdown报告
    print("\n3. 生成Markdown报告...")

    markdown_content = generate_markdown_report(results, recommendations)

    # 4. 保存报告
    docs_dir = project_root / 'docs'
    docs_dir.mkdir(parents=True, exist_ok=True)

    report_file = docs_dir / f'英文关键词系统基线报告-{datetime.now().strftime("%Y%m%d")}.md'

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(markdown_content)

    print(f"✓ 报告已保存到: {report_file}")

    # 5. 显示摘要
    print("\n" + "="*70)
    print("Phase 0 基线报告摘要")
    print("="*70)

    print("\n实验完成情况:")
    for exp_letter in ['a', 'b', 'c', 'd']:
        status = "✅ 完成" if exp_letter in results else "⚠️ 未完成"
        print(f"  实验{exp_letter.upper()}: {status}")

    print("\n优化建议优先级分布:")
    priority_count = {
        'high': sum(1 for v in recommendations.values() if v.get('priority') == 'high'),
        'medium': sum(1 for v in recommendations.values() if v.get('priority') == 'medium'),
        'low': sum(1 for v in recommendations.values() if v.get('priority') == 'low')
    }

    print(f"  🔴 高优先级: {priority_count['high']} 项")
    print(f"  🟡 中优先级: {priority_count['medium']} 项")
    print(f"  🟢 低优先级: {priority_count['low']} 项")

    print(f"\n报告文件: {report_file}")
    print("="*70)

    return {
        'report_file': str(report_file),
        'experiments_completed': len(results),
        'recommendations': recommendations
    }


if __name__ == "__main__":
    try:
        result = run_baseline_report_generator()

        print("\n✅ Phase 0 基线报告生成完成！")
        print(f"\n📄 请查看报告: {result['report_file']}")
        print(f"\n📌 下一步：根据报告中的高优先级建议开始实施优化")

    except KeyboardInterrupt:
        print("\n\n⚠️  操作被中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 报告生成出错: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

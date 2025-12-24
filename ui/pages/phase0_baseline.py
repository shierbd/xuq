"""
Phase 0: 基线测量页面
系统能力测量与优化建议生成
"""
import streamlit as st
import json
import sys
from pathlib import Path
from datetime import datetime
import subprocess
import time

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from storage.repository import PhraseRepository, ClusterMetaRepository, TokenRepository


def load_experiment_result(experiment_letter: str):
    """加载实验结果"""
    result_file = project_root / 'data' / 'phase0_results' / f'experiment_{experiment_letter}_result.json'

    if not result_file.exists():
        return None

    try:
        with open(result_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"加载实验{experiment_letter.upper()}结果失败: {str(e)}")
        return None


def check_prerequisites():
    """检查前置条件"""
    issues = []

    try:
        # 检查是否有短语数据
        with PhraseRepository() as phrase_repo:
            phrase_count = phrase_repo.get_phrase_count()
            if phrase_count == 0:
                issues.append("❌ 没有短语数据，请先运行Phase 1导入数据")

        # 检查是否有聚类结果
        with ClusterMetaRepository() as cluster_repo:
            clusters_A = cluster_repo.get_all_clusters('A')
            if not clusters_A:
                issues.append("❌ 没有大组聚类结果，请先运行Phase 2")

        # 检查是否有Token
        with TokenRepository() as token_repo:
            tokens = token_repo.get_all_tokens()
            if not tokens:
                issues.append("⚠️ 没有Token数据（实验B需要），可继续但实验B会失败")

    except Exception as e:
        issues.append(f"❌ 检查前置条件时出错: {str(e)}")

    return issues


def render_experiment_status(exp_letter: str, result: dict):
    """渲染实验状态卡片"""
    exp_names = {
        'a': '聚类审核效率',
        'b': 'Token覆盖率',
        'c': '同义冗余率',
        'd': '搜索意图分布'
    }

    if result:
        rec = result.get('recommendation', 'unknown')
        rec_emoji = {
            'ok': '✅',
            'sufficient': '✅',
            'moderate': '⚠️',
            'need_optimization': '🔴',
            'need_expansion': '🔴',
            'need_canonicalization': '🔴',
            'similar_to_junyan': '✅',
            'different_pattern': 'ℹ️'
        }.get(rec, '❓')

        status_text = f"{rec_emoji} 已完成"
        status_color = "green" if rec_emoji == '✅' else ("orange" if rec_emoji == '⚠️' else "red")

        st.markdown(f"""
        <div style="background-color: #f0f2f6; padding: 1rem; border-radius: 10px; border-left: 5px solid {status_color};">
            <h4>实验{exp_letter.upper()}: {exp_names[exp_letter]}</h4>
            <p style="color: {status_color}; font-weight: bold;">{status_text}</p>
            <p style="font-size: 0.9em;">{result.get('recommendation_detail', 'N/A')}</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background-color: #f0f2f6; padding: 1rem; border-radius: 10px; border-left: 5px solid gray;">
            <h4>实验{exp_letter.upper()}: {exp_names[exp_letter]}</h4>
            <p style="color: gray; font-weight: bold;">⏸️ 未运行</p>
        </div>
        """, unsafe_allow_html=True)


def render_experiment_a_ui():
    """实验A: 聚类审核效率的UI"""
    st.markdown("### 📋 实验A: 聚类审核效率测量")

    result = load_experiment_result('a')

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("""
        **目标**: 测量从60-100个簇中筛选10-15个所需的时间和准确率

        **判断标准**:
        - ✅ 通过: 时间<60min 且 遗漏率<10%
        - ⚠️ 中等: 时间60-120min 或 遗漏率10-30%
        - ❌ 需优化: 时间>120min 或 遗漏率>30%

        **操作**: 运行脚本后会进入交互模式，需要人工审核和选择簇
        """)

    with col2:
        if st.button("🚀 运行实验A", type="primary", use_container_width=True):
            st.info("请在终端中运行: `python scripts/phase0_experiment_a_cluster_review.py`")
            st.warning("⚠️ 此实验需要交互式操作，请在命令行中运行")

    if result:
        st.markdown("---")
        st.markdown("#### 📊 实验结果")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("审核时间", f"{result.get('time_minutes', 0):.1f} 分钟")
        with col2:
            st.metric("簇总数", result.get('cluster_count', 0))
        with col3:
            st.metric("选中簇数", result.get('selected_count', 0))
        with col4:
            st.metric("遗漏率", f"{result.get('missed_rate', 0):.1%}")

        st.markdown(f"**主观感受**: {result.get('subjective', 'N/A')}")
        st.markdown(f"**判断**: {result.get('recommendation_detail', 'N/A')}")


def render_experiment_b_ui():
    """实验B: Token覆盖率的UI"""
    st.markdown("### 🔍 实验B: Token覆盖率测量")

    result = load_experiment_result('b')

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("""
        **目标**: 测量当前26个token覆盖了多少短语

        **判断标准**:
        - ✅ 充足: 覆盖率≥80%
        - ⚠️ 中等: 覆盖率60-80%
        - ❌ 不足: 覆盖率≤60%

        **操作**: 自动运行，无需人工干预（约5-10分钟）
        """)

    with col2:
        if st.button("🚀 运行实验B", type="primary", use_container_width=True):
            with st.spinner("正在运行实验B..."):
                try:
                    script_path = project_root / 'scripts' / 'phase0_experiment_b_token_coverage.py'
                    proc_result = subprocess.run(
                        [sys.executable, str(script_path)],
                        capture_output=True,
                        text=True,
                        timeout=600
                    )

                    if proc_result.returncode == 0:
                        st.success("✅ 实验B完成！")
                        time.sleep(1)  # 等待文件写入完成
                        st.rerun()
                    else:
                        st.error(f"❌ 实验B执行失败:\n{proc_result.stderr}")
                except Exception as e:
                    st.error(f"❌ 运行实验B出错: {str(e)}")

    if result:
        st.markdown("---")
        st.markdown("#### 📊 实验结果")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("短语总数", f"{result.get('total_phrases', 0):,}")
        with col2:
            st.metric("Token总数", result.get('token_count', 0))
        with col3:
            st.metric("被覆盖短语", f"{result.get('covered_count', 0):,}")
        with col4:
            st.metric("覆盖率", f"{result.get('coverage_rate', 0):.1%}")

        st.markdown(f"**判断**: {result.get('recommendation_detail', 'N/A')}")

        # 显示Token列表
        with st.expander("📋 查看当前Token列表"):
            tokens = result.get('tokens', [])
            cols = st.columns(4)
            for i, token in enumerate(tokens):
                with cols[i % 4]:
                    st.markdown(f"• {token}")


def render_experiment_c_ui():
    """实验C: 同义冗余率的UI"""
    st.markdown("### 🔄 实验C: 同义冗余率测量")

    result = load_experiment_result('c')

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("""
        **目标**: 测量同一需求的不同表达占比

        **判断标准**:
        - ✅ 可接受: 冗余率<10%
        - ⚠️ 中等: 冗余率10-20%
        - ❌ 需处理: 冗余率>20%

        **操作**: 运行脚本后会进入交互模式，需要人工标注同义组
        """)

    with col2:
        if st.button("🚀 运行实验C", type="primary", use_container_width=True):
            st.info("请在终端中运行: `python scripts/phase0_experiment_c_redundancy.py`")
            st.warning("⚠️ 此实验需要交互式操作，请在命令行中运行")

    if result:
        st.markdown("---")
        st.markdown("#### 📊 实验结果")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("抽样数量", f"{result.get('sample_size', 0):,}")
        with col2:
            st.metric("同义组数", result.get('synonym_groups_count', 0))
        with col3:
            st.metric("冗余率", f"{result.get('redundancy_rate', 0):.1%}")

        st.markdown(f"**判断**: {result.get('recommendation_detail', 'N/A')}")


def render_experiment_d_ui():
    """实验D: 搜索意图分布的UI"""
    st.markdown("### 🎯 实验D: 搜索意图分布统计")

    result = load_experiment_result('d')

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("""
        **目标**: 统计英文关键词的搜索意图分布

        **判断标准**:
        - 类似君言: find_tool>70%
        - 不同模式: find_tool<40%
        - 中等分布: 40-70%

        **操作**: 运行脚本后会进入交互模式，需要人工标注意图
        """)

    with col2:
        if st.button("🚀 运行实验D", type="primary", use_container_width=True):
            st.info("请在终端中运行: `python scripts/phase0_experiment_d_intent_distribution.py`")
            st.warning("⚠️ 此实验需要交互式操作，请在命令行中运行")

    if result:
        st.markdown("---")
        st.markdown("#### 📊 实验结果")

        intent_dist = result.get('intent_distribution', {})

        # 显示意图分布图表
        import pandas as pd

        df_data = []
        for intent, stats in intent_dist.items():
            df_data.append({
                'Intent': intent,
                'Count': stats.get('count', 0),
                'Percentage': stats.get('percentage', 0)
            })

        df = pd.DataFrame(df_data)

        col1, col2 = st.columns(2)
        with col1:
            st.bar_chart(df.set_index('Intent')['Count'])
        with col2:
            for intent, stats in intent_dist.items():
                st.metric(intent, f"{stats.get('percentage', 0):.1%}")

        st.markdown(f"**判断**: {result.get('recommendation_detail', 'N/A')}")


def render_baseline_report():
    """渲染基线报告"""
    st.markdown("### 📄 基线报告")

    # 查找最新的报告文件
    docs_dir = project_root / 'docs'
    report_files = list(docs_dir.glob('英文关键词系统基线报告-*.md'))

    if not report_files:
        st.warning("⚠️ 还没有生成基线报告")

        if st.button("🚀 生成基线报告", type="primary"):
            with st.spinner("正在生成报告..."):
                try:
                    script_path = project_root / 'scripts' / 'phase0_generate_baseline_report.py'
                    result = subprocess.run(
                        [sys.executable, str(script_path)],
                        capture_output=True,
                        text=True,
                        timeout=60
                    )

                    if result.returncode == 0:
                        st.success("✅ 报告生成完成！")
                        st.rerun()
                    else:
                        st.error(f"❌ 报告生成失败:\n{result.stderr}")
                except Exception as e:
                    st.error(f"❌ 生成报告出错: {str(e)}")
    else:
        # 显示最新的报告
        latest_report = max(report_files, key=lambda p: p.stat().st_mtime)

        st.success(f"📄 最新报告: {latest_report.name}")

        try:
            with open(latest_report, 'r', encoding='utf-8') as f:
                report_content = f.read()

            st.markdown(report_content)
        except Exception as e:
            st.error(f"读取报告失败: {str(e)}")


def render():
    """渲染Phase 0页面"""
    st.markdown('<div class="main-header">📊 Phase 0: 基线测量</div>', unsafe_allow_html=True)

    st.markdown("""
    ### 🎯 Phase 0 目标

    通过4个实验测量当前系统的基线能力，识别真实问题，为后续优化提供**证据支持**。

    **核心原则**: 证据优先，再优化 —— 只优化有实际问题的模块
    """)

    # 检查前置条件
    st.markdown("---")
    st.markdown("### ✅ 前置条件检查")

    issues = check_prerequisites()
    if issues:
        for issue in issues:
            st.warning(issue)
    else:
        st.success("✅ 所有前置条件满足，可以开始Phase 0实验")

    # 实验状态概览
    st.markdown("---")
    st.markdown("### 📊 实验状态概览")

    col1, col2 = st.columns(2)

    with col1:
        render_experiment_status('a', load_experiment_result('a'))
        render_experiment_status('b', load_experiment_result('b'))

    with col2:
        render_experiment_status('c', load_experiment_result('c'))
        render_experiment_status('d', load_experiment_result('d'))

    # 实验详情（标签页）
    st.markdown("---")
    st.markdown("### 🔬 实验详情")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "实验A: 聚类审核效率",
        "实验B: Token覆盖率",
        "实验C: 同义冗余率",
        "实验D: 搜索意图分布",
        "📄 基线报告"
    ])

    with tab1:
        render_experiment_a_ui()

    with tab2:
        render_experiment_b_ui()

    with tab3:
        render_experiment_c_ui()

    with tab4:
        render_experiment_d_ui()

    with tab5:
        render_baseline_report()

    # 快速操作指南
    st.markdown("---")
    st.markdown("### 📖 快速操作指南")

    st.markdown("""
    #### 运行顺序

    1. **实验B** (自动): 点击"运行实验B"按钮（约5-10分钟）
    2. **实验A** (交互): 在终端运行 `python scripts/phase0_experiment_a_cluster_review.py`（30-120分钟）
    3. **实验C** (交互): 在终端运行 `python scripts/phase0_experiment_c_redundancy.py`（30-60分钟）
    4. **实验D** (交互): 在终端运行 `python scripts/phase0_experiment_d_intent_distribution.py`（30-60分钟）
    5. **生成报告**: 点击"生成基线报告"按钮

    #### 为什么有些实验需要在终端运行？

    实验A、C、D需要**交互式人工标注**，在命令行中操作更流畅。实验B是全自动的，可以直接在Web界面运行。

    #### 时间预估

    - 实验B: 5-10分钟（自动）
    - 实验A: 30-120分钟（取决于簇数量）
    - 实验C: 30-60分钟（标注1000条）
    - 实验D: 30-60分钟（标注1000条）
    - **总计**: 约2-4小时
    """)


if __name__ == "__main__":
    render()

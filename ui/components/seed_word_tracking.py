"""
词根追溯视图
展示原始词根及其扩展出的关键词
"""
import streamlit as st
import pandas as pd
from pathlib import Path
import sys

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from storage.repository import PhraseRepository


def render_seed_word_tracking():
    """渲染词根追溯界面"""
    st.title("🌱 词根追溯 - Seed Word Tracking")

    st.markdown("""
    **功能说明**：
    - 查看哪些原始词根扩展出了哪些关键词
    - 评估每个词根的扩词效果
    - 发现高价值词根，优化下一轮扩词策略
    ---
    """)

    # 加载词根扩展数据
    with st.spinner("正在加载词根数据..."):
        try:
            with PhraseRepository() as repo:
                # 获取词根扩展统计
                seed_expansion = repo.get_seed_word_expansion()
                all_seeds = list(seed_expansion.keys())

                if not all_seeds:
                    st.warning("⚠️ 未找到词根数据。请确保导入数据时填写了seed_word字段。")
                    return

        except Exception as e:
            st.error(f"❌ 加载数据失败: {str(e)}")
            import traceback
            st.error(traceback.format_exc())
            return

    # ========== 1. 总体统计 ==========
    st.header("1️⃣ 总体统计")

    col1, col2, col3 = st.columns(3)
    total_seeds = len(all_seeds)
    total_expansions = sum(data['count'] for data in seed_expansion.values())
    avg_expansion = total_expansions / total_seeds if total_seeds > 0 else 0

    col1.metric("词根总数", f"{total_seeds:,}")
    col2.metric("扩展词总数", f"{total_expansions:,}")
    col3.metric("平均扩展数", f"{avg_expansion:.1f}")

    # ========== 2. 词根排行榜 ==========
    st.header("2️⃣ 词根扩展排行")

    # 准备数据
    seed_df = pd.DataFrame([
        {
            '词根': seed,
            '扩展词数': data['count'],
            '轮次分布': ', '.join([f"R{r}:{c}" for r, c in sorted(data['by_round'].items())]),
            '来源分布': ', '.join([f"{s}:{c}" for s, c in data['by_source'].items()])
        }
        for seed, data in seed_expansion.items()
    ])

    # 按扩展词数降序排列
    seed_df = seed_df.sort_values('扩展词数', ascending=False)

    # 排序选项
    col1, col2 = st.columns([2, 1])
    with col1:
        sort_by = st.selectbox(
            "排序方式",
            options=['扩展词数（降序）', '词根（字母序）'],
            index=0
        )

    with col2:
        top_n = st.number_input(
            "显示数量",
            min_value=10,
            max_value=len(seed_df),
            value=min(50, len(seed_df)),
            step=10
        )

    # 应用排序
    if sort_by == '词根（字母序）':
        seed_df = seed_df.sort_values('词根')
    else:
        seed_df = seed_df.sort_values('扩展词数', ascending=False)

    # 显示表格
    st.dataframe(seed_df.head(top_n), width='stretch', height=400)

    # 导出功能
    csv = seed_df.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="📄 下载完整词根列表（CSV）",
        data=csv,
        file_name="seed_word_expansion.csv",
        mime="text/csv"
    )

    # ========== 3. 词根详情查看 ==========
    st.header("3️⃣ 词根详情查看")

    # 选择词根
    selected_seed = st.selectbox(
        "选择要查看的词根",
        options=sorted(all_seeds),
        help="选择一个词根查看其扩展出的所有关键词"
    )

    if selected_seed:
        st.subheader(f"🔍 词根: {selected_seed}")

        # 显示统计
        seed_data = seed_expansion[selected_seed]
        col1, col2, col3 = st.columns(3)
        col1.metric("扩展词总数", seed_data['count'])
        col2.metric("涉及轮次", len(seed_data['by_round']))
        col3.metric("数据来源", len(seed_data['by_source']))

        # 轮次筛选
        col1, col2 = st.columns([1, 1])
        with col1:
            available_rounds = sorted(seed_data['by_round'].keys())
            selected_round = st.selectbox(
                "筛选轮次（可选）",
                options=["全部轮次"] + [f"轮次 {r}" for r in available_rounds],
                index=0
            )

        with col2:
            display_limit = st.number_input(
                "显示数量",
                min_value=10,
                max_value=1000,
                value=100,
                step=10
            )

        # 提取轮次编号
        round_filter = None
        if selected_round != "全部轮次":
            round_filter = int(selected_round.split()[1])

        # 加载扩展词
        with st.spinner("正在加载扩展词..."):
            with PhraseRepository() as repo:
                expanded_phrases = repo.get_phrases_by_seed_word(
                    seed_word=selected_seed,
                    round_num=round_filter,
                    limit=display_limit
                )

        if expanded_phrases:
            # 显示扩展词列表
            phrases_df = pd.DataFrame([
                {
                    '关键词': p.phrase,
                    '频次': p.frequency or 0,
                    '轮次': p.first_seen_round,
                    '来源': p.source_type or '未知',
                    '搜索量': p.volume or 0
                }
                for p in expanded_phrases
            ])

            st.dataframe(phrases_df, width='stretch', height=400)

            # 导出当前词根的扩展词
            csv_detail = phrases_df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label=f"📄 下载 {selected_seed} 的扩展词（CSV）",
                data=csv_detail,
                file_name=f"expansion_{selected_seed}.csv",
                mime="text/csv"
            )
        else:
            st.info("未找到扩展词数据")

    # ========== 4. 使用说明 ==========
    with st.expander("💡 使用技巧"):
        st.markdown("""
        ### 如何使用词根追溯？

        1. **评估扩词效果**
           - 查看哪些词根扩展出最多相关词
           - 扩展数 > 100 通常表示高价值词根

        2. **发现问题**
           - 扩展数异常多（>500）可能表示词根过于宽泛
           - 扩展数太少（<10）可能表示词根过于小众

        3. **优化策略**
           - 选择扩展数适中（50-200）的词根继续深挖
           - 导出高价值词根列表，用于下一轮扩词

        4. **数据导出**
           - 导出词根列表 → 外部工具扩词 → Phase 1导入
           - 导出特定词根的扩展词 → 分析相关性
        """)


if __name__ == "__main__":
    render_seed_word_tracking()

"""
Phase 2E: 君言方法 - 长尾变量提取
UI界面实现
"""
import streamlit as st
import json
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from storage.repository import PhraseRepository
from storage.models import Phrase
from storage.word_segment_repository import WordSegmentRepository
from core.junyan_method import (
    JunyanTemplateExtractor,
    JunyanVariableExtractor,
    JunyanQualityAnalyzer
)
from utils.keyword_segmentation import segment_keywords
from collections import Counter


def load_all_phrases():
    """加载所有短语数据"""
    try:
        with PhraseRepository() as repo:
            phrases_db = repo.session.query(Phrase).all()
            return [p.phrase for p in phrases_db]
    except Exception as e:
        st.error(f"加载数据失败: {str(e)}")
        return []


def render():
    """渲染君言方法页面"""
    st.title("🎯 Phase 2E: 君言方法 - 长尾变量提取")

    st.markdown("""
    ### 💡 君言方法核心思路

    基于用户搜索特征的**模板-变量双向提取法**：

    1. **步骤1：提取模板** ← 从少量种子词中发现搜索模板
    2. **步骤2：提取变量** ← 用模板从大量数据中提取变量
    3. **质量分析** ← 分析首字/末字，识别脏数据
    4. **循环迭代** ← 变量可作为新种子词，重复步骤1

    **核心原则**：
    - 种子词要**人工挑选**，确保在目标场景下一定正确
    - 模板要**人工筛选**，确保{X}位置大概率是目标数据
    - 交叉验证：变量能匹配多个模板 = 质量高
    """)

    st.markdown("---")

    # 加载数据
    if 'junyan_phrases' not in st.session_state:
        with st.spinner("正在加载短语数据..."):
            st.session_state.junyan_phrases = load_all_phrases()

    phrases = st.session_state.junyan_phrases
    st.info(f"📊 当前数据量: {len(phrases):,} 条短语")

    # Tab区域
    tab0, tab1, tab2, tab3 = st.tabs([
        "🔍 步骤0：获取种子词",
        "📝 步骤1：提取模板",
        "🎯 步骤2：提取变量",
        "📊 质量分析"
    ])

    # ========================================================================
    # Tab 0: 获取种子词（通过分词）
    # ========================================================================
    with tab0:
        st.header("🔍 步骤0：从长尾词分词获取种子词")

        st.markdown("""
        **操作说明**：
        1. 系统会对所有长尾词进行自动分词
        2. 统计词频，展示高频词汇
        3. **人工筛选**：勾选确定正确的词作为种子词
        4. 自动填充到【步骤1】的种子词输入框

        **筛选标准**：
        - ✅ 确定在目标场景下一定正确（如商品名、品牌名、类目名）
        - ✅ 具有代表性，能代表一类事物
        - ❌ 避免通用词（如：the, of, 的, 了）
        - ❌ 避免无意义词
        """)

        col1, col2 = st.columns([1, 1])

        with col1:
            min_word_freq = st.slider(
                "词频筛选阈值",
                min_value=1,
                max_value=100,
                value=10,
                help="只显示出现次数>=此值的词"
            )

        with col2:
            max_display = st.number_input(
                "最多显示词数",
                min_value=50,
                max_value=1000,
                value=200,
                step=50,
                help="显示Top N个高频词"
            )

        load_btn = st.button(
            "📥 从Phase 0加载分词结果",
            type="primary",
            use_container_width=True
        )

        if load_btn:
            # Check if segmentation results exist
            with st.spinner("正在检查分词结果..."):
                with WordSegmentRepository() as ws_repo:
                    stats = ws_repo.get_statistics()
                    total_words = stats.get('total_words', 0)

                if total_words == 0:
                    st.error("❌ 未找到分词结果！请先前往 **Phase 0 Tab 1** 执行分词")
                else:
                    st.info(f"📊 当前分词结果：{total_words:,} 个词/短语")

                    with st.spinner(f"正在从Phase 0加载分词结果..."):
                        # Load words and phrases from word_segments table
                        with WordSegmentRepository() as ws_repo:
                            word_counter, ngram_counter, _, _, _, _ = ws_repo.load_segmentation_results(
                                min_word_frequency=min_word_freq,
                                min_ngram_frequency=min_word_freq
                            )

                        # Merge words and phrases as candidate seed words
                        all_candidates = Counter()
                        all_candidates.update(word_counter)
                        all_candidates.update(ngram_counter)

                        # Filter by length (at least 2 characters)
                        filtered_candidates = [
                            (word, freq)
                            for word, freq in all_candidates.most_common()
                            if len(word) >= 2
                        ]

                        # Save to session_state
                        st.session_state.candidate_seeds = filtered_candidates[:max_display]

                    st.success(f"✅ 已加载 {len(all_candidates):,} 个候选种子词（包括单词和短语），筛选后显示 {len(st.session_state.candidate_seeds)} 个")

        # 显示候选种子词
        if 'candidate_seeds' in st.session_state:
            candidate_seeds = st.session_state.candidate_seeds

            st.markdown("---")
            st.subheader(f"📋 候选种子词（{len(candidate_seeds)} 个）")

            st.markdown("""
            **操作提示**：
            - 勾选你认为正确的种子词
            - 建议选择10-30个
            - 点击"应用选择"按钮，自动填充到步骤1
            """)

            # 选择框
            selected_seeds = []

            # 分列展示
            cols_per_row = 3
            rows = (len(candidate_seeds) + cols_per_row - 1) // cols_per_row

            for row in range(min(rows, 20)):  # 最多显示20行，避免太长
                cols = st.columns(cols_per_row)

                for col_idx in range(cols_per_row):
                    word_idx = row * cols_per_row + col_idx
                    if word_idx < len(candidate_seeds):
                        word, freq = candidate_seeds[word_idx]

                        with cols[col_idx]:
                            is_selected = st.checkbox(
                                f"**{word}** ({freq}次)",
                                key=f"seed_select_{word_idx}"
                            )
                            if is_selected:
                                selected_seeds.append(word)

            # 应用按钮
            if selected_seeds:
                st.markdown("---")
                st.success(f"已选择 {len(selected_seeds)} 个种子词")

                if st.button("✅ 应用选择到步骤1", type="primary"):
                    # 保存到session_state
                    st.session_state.selected_seed_words = selected_seeds
                    st.success("✅ 已自动填充到步骤1！请切换到【步骤1：提取模板】Tab")

                # 预览
                with st.expander("🔍 预览选择的种子词"):
                    st.write(", ".join(selected_seeds))

    # ========================================================================
    # Tab 1: 提取模板
    # ========================================================================
    with tab1:
        st.header("📝 步骤1：从种子词提取模板")

        st.markdown("""
        **操作说明**：
        1. 在下方输入框中，每行输入一个种子词（或从【步骤0】自动填充）
        2. 种子词要求：**确定在目标场景下一定正确**（如商品名、类目名等）
        3. 建议：先输入10-20个种子词测试效果
        4. 点击"开始提取模板"按钮执行
        """)

        # 自动填充从步骤0选择的种子词
        default_seeds = ""
        if 'selected_seed_words' in st.session_state:
            default_seeds = "\n".join(st.session_state.selected_seed_words)
            st.success(f"✅ 已自动填充 {len(st.session_state.selected_seed_words)} 个种子词（来自步骤0）")

        col1, col2 = st.columns([2, 1])

        with col1:
            seed_words_input = st.text_area(
                "种子词列表（每行一个）",
                value=default_seeds,
                placeholder="示例：\nandroid\niphone\npixel\nsamsung\nhuawei",
                height=200,
                help="人工挑选的、确定正确的目标词"
            )

        with col2:
            min_template_freq = st.number_input(
                "模板最小频次",
                min_value=1,
                value=5,
                help="模板至少出现多少次才保留"
            )

            extract_btn = st.button(
                "🚀 开始提取模板",
                type="primary",
                use_container_width=True
            )

        if extract_btn:
            # 解析种子词
            seed_words = [
                line.strip()
                for line in seed_words_input.strip().split('\n')
                if line.strip()
            ]

            if not seed_words:
                st.error("请输入种子词！")
            elif not phrases:
                st.error("请先加载短语数据！")
            else:
                with st.spinner(f"正在从 {len(seed_words)} 个种子词中提取模板..."):
                    # 执行提取
                    extractor = JunyanTemplateExtractor(phrases)
                    templates = extractor.extract_templates_from_seeds(
                        seed_words=seed_words,
                        min_frequency=min_template_freq
                    )

                    # 保存到session_state
                    st.session_state.junyan_templates = templates

                st.success(f"✅ 提取完成！发现 {len(templates)} 个模板")

        # 显示结果
        if 'junyan_templates' in st.session_state:
            templates = st.session_state.junyan_templates

            st.markdown("---")
            st.subheader(f"📋 发现的模板（{len(templates)} 个）")

            # 筛选器
            col1, col2 = st.columns(2)
            with col1:
                min_freq_filter = st.slider(
                    "筛选：最小频次",
                    min_value=1,
                    max_value=max(t['frequency'] for t in templates) if templates else 100,
                    value=5
                )

            filtered = [t for t in templates if t['frequency'] >= min_freq_filter]

            st.markdown(f"**显示 {len(filtered)} 个模板（频次 >= {min_freq_filter}）**")

            # 选择框：用于后续提取变量
            selected_templates = []

            for i, template in enumerate(filtered, 1):
                with st.expander(
                    f"**{i}. {template['template_pattern']}** "
                    f"（频次: {template['frequency']}, 种子词: {len(template['matched_seeds'])}个）",
                    expanded=(i <= 5)
                ):
                    col1, col2 = st.columns([3, 2])

                    with col1:
                        st.markdown(f"**模板模式**: `{template['template_pattern']}`")
                        st.markdown(f"**出现频次**: {template['frequency']}")
                        st.markdown(f"**匹配种子词** ({len(template['matched_seeds'])}个): {', '.join(template['matched_seeds'][:10])}")

                    with col2:
                        # 选择checkbox
                        is_selected = st.checkbox(
                            "✅ 选择此模板用于提取变量",
                            key=f"template_select_{i}"
                        )
                        if is_selected:
                            selected_templates.append(template['template_pattern'])

                    st.markdown("**示例短语**:")
                    for j, example in enumerate(template['example_phrases'][:5], 1):
                        st.text(f"  {j}. {example}")

            # 保存选择的模板
            if selected_templates:
                st.session_state.selected_templates = selected_templates
                st.success(f"已选择 {len(selected_templates)} 个模板")

                # 显示选择的模板
                with st.expander("📝 查看选择的模板"):
                    for i, t in enumerate(selected_templates, 1):
                        st.text(f"{i}. {t}")

    # ========================================================================
    # Tab 2: 提取变量
    # ========================================================================
    with tab2:
        st.header("🎯 步骤2：从模板提取变量")

        st.markdown("""
        **操作说明**：
        1. 在下方输入框中，每行输入一个模板（或从步骤1选择）
        2. 模板格式：用`{X}`表示变量位置，如 `best way to {X}`
        3. 可选：添加停用词，过滤脏数据
        4. 点击"开始提取变量"按钮执行
        """)

        # 自动填充从步骤1选择的模板
        default_templates = ""
        if 'selected_templates' in st.session_state:
            default_templates = "\n".join(st.session_state.selected_templates)

        col1, col2 = st.columns([2, 1])

        with col1:
            templates_input = st.text_area(
                "模板列表（每行一个，用{X}表示变量）",
                value=default_templates,
                placeholder="示例：\nbest way to {X}\n{X} books in order\nwhat channel is {X} game on",
                height=200,
                help="人工筛选的高质量模板"
            )

        with col2:
            min_var_freq = st.number_input(
                "变量最小频次",
                min_value=1,
                value=3,
                help="变量至少出现多少次才保留"
            )

            stop_words_input = st.text_area(
                "停用词（每行一个）",
                placeholder="示例：\n的\n了\n在",
                height=100,
                help="用于过滤脏数据"
            )

            extract_var_btn = st.button(
                "🚀 开始提取变量",
                type="primary",
                use_container_width=True
            )

        if extract_var_btn:
            # 解析模板
            templates = [
                line.strip()
                for line in templates_input.strip().split('\n')
                if line.strip() and '{X}' in line
            ]

            # 解析停用词
            stop_words = [
                line.strip()
                for line in stop_words_input.strip().split('\n')
                if line.strip()
            ] if stop_words_input.strip() else []

            if not templates:
                st.error("请输入至少一个模板（必须包含{X}）！")
            elif not phrases:
                st.error("请先加载短语数据！")
            else:
                with st.spinner(f"正在从 {len(templates)} 个模板中提取变量..."):
                    # 执行提取
                    extractor = JunyanVariableExtractor(phrases)
                    result = extractor.extract_variables_from_templates(
                        templates=templates,
                        min_frequency=min_var_freq,
                        stop_words=stop_words
                    )

                    # 保存到session_state
                    st.session_state.junyan_variables = result['variables']
                    st.session_state.junyan_quality = result['quality_analysis']

                st.success(f"✅ 提取完成！发现 {len(result['variables'])} 个有效变量")

        # 显示结果
        if 'junyan_variables' in st.session_state:
            variables = st.session_state.junyan_variables

            st.markdown("---")
            st.subheader(f"📋 提取的变量（{len(variables)} 个）")

            # 统计
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("变量总数", len(variables))
            with col2:
                avg_freq = sum(v['frequency'] for v in variables) / len(variables) if variables else 0
                st.metric("平均频次", f"{avg_freq:.1f}")
            with col3:
                avg_templates = sum(v['template_match_count'] for v in variables) / len(variables) if variables else 0
                st.metric("平均匹配模板数", f"{avg_templates:.1f}")

            # 筛选器
            col1, col2 = st.columns(2)
            with col1:
                min_freq_filter = st.slider(
                    "筛选：最小频次",
                    min_value=1,
                    max_value=max(v['frequency'] for v in variables) if variables else 100,
                    value=3,
                    key="var_freq_filter"
                )
            with col2:
                min_template_filter = st.slider(
                    "筛选：最小模板数",
                    min_value=1,
                    max_value=max(v['template_match_count'] for v in variables) if variables else 10,
                    value=2,
                    key="var_template_filter"
                )

            filtered_vars = [
                v for v in variables
                if v['frequency'] >= min_freq_filter and v['template_match_count'] >= min_template_filter
            ]

            st.markdown(f"**显示 {len(filtered_vars)} 个变量**")

            # 表格展示
            import pandas as pd

            df_data = []
            for i, var in enumerate(filtered_vars, 1):
                df_data.append({
                    '序号': i,
                    '变量': var['variable_text'],
                    '频次': var['frequency'],
                    '匹配模板数': var['template_match_count'],
                    '匹配模板': ', '.join(var['matched_templates'][:3]) + ('...' if len(var['matched_templates']) > 3 else '')
                })

            df = pd.DataFrame(df_data)

            st.dataframe(
                df,
                use_container_width=True,
                height=400,
                hide_index=True
            )

            # CSV导出
            csv = df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 下载变量列表为CSV",
                data=csv,
                file_name="junyan_variables.csv",
                mime="text/csv"
            )

            # 保存为JSON
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 保存结果到outputs目录"):
                    output_dir = project_root / 'outputs'
                    output_dir.mkdir(exist_ok=True)

                    output_data = {
                        'total_variables': len(variables),
                        'variables': variables,
                        'quality_analysis': st.session_state.junyan_quality
                    }

                    output_file = output_dir / 'junyan_variables.json'
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(output_data, f, indent=2, ensure_ascii=False)

                    st.success(f"✅ 已保存到 {output_file}")

    # ========================================================================
    # Tab 3: 质量分析
    # ========================================================================
    with tab3:
        st.header("📊 质量分析")

        if 'junyan_quality' not in st.session_state:
            st.warning("请先在【步骤2】中提取变量！")
        else:
            quality = st.session_state.junyan_quality

            st.markdown("""
            **质量分析说明**：
            - **首字/末字频次**：识别高频无意义字符，用于添加停用词
            - **模板-变量映射**：查看每个模板提取了哪些变量
            """)

            # 首字分析
            st.subheader("🔤 变量首字频次分析")
            first_char_freq = quality['first_char_freq']

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Top 20 首字**:")
                for i, (char, freq) in enumerate(list(first_char_freq.items())[:20], 1):
                    st.text(f"{i}. '{char}' - {freq} 次")

            with col2:
                # 噪音识别
                analyzer = JunyanQualityAnalyzer()
                noise_analysis = analyzer.analyze_noise_patterns(quality)

                st.markdown("**⚠️ 高频无意义首字（建议添加停用词）**:")
                if noise_analysis['high_freq_first_chars']:
                    for char in noise_analysis['high_freq_first_chars']:
                        st.warning(f"'{char}' - {first_char_freq[char]} 次")
                else:
                    st.success("未发现明显噪音")

            st.markdown("---")

            # 末字分析
            st.subheader("🔤 变量末字频次分析")
            last_char_freq = quality['last_char_freq']

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Top 20 末字**:")
                for i, (char, freq) in enumerate(list(last_char_freq.items())[:20], 1):
                    st.text(f"{i}. '{char}' - {freq} 次")

            with col2:
                st.markdown("**⚠️ 高频无意义末字（建议添加停用词）**:")
                if noise_analysis['high_freq_last_chars']:
                    for char in noise_analysis['high_freq_last_chars']:
                        st.warning(f"'{char}' - {last_char_freq[char]} 次")
                else:
                    st.success("未发现明显噪音")

            st.markdown("---")

            # 模板-变量映射
            st.subheader("🔗 模板-变量映射")
            template_variable_map = quality['template_variable_map']

            for template, variables in template_variable_map.items():
                with st.expander(f"**{template}** - 提取了 {len(variables)} 个变量"):
                    st.markdown(f"**前20个变量**: {', '.join(variables[:20])}")

    # 底部说明
    st.markdown("---")
    st.info("""
    **💡 君言方法使用建议**：

    1. **种子词选择**：确保种子词在目标场景下一定正确，质量>数量
    2. **模板筛选**：人工检查Top模板，选择{X}位置大概率是目标数据的
    3. **停用词优化**：根据质量分析的首字/末字频次，添加停用词过滤脏数据
    4. **循环迭代**：从提取的高质量变量中选择新种子词，重复步骤1-2
    5. **多轮迭代**：通常2-3轮迭代可以获得最佳结果
    """)


if __name__ == "__main__":
    render()

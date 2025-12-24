"""
Phase 0: 关键词扩展与分词工具
从数据库读取已导入的关键词进行分词、停用词管理和频次分析
"""
import streamlit as st
import pandas as pd
from pathlib import Path
import sys

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.keyword_segmentation import (
    segment_keywords,
    segment_keywords_with_seed_tracking,
    get_sorted_words,
    clean_keywords,
    get_statistics
)
from utils.stopwords import (
    load_stopwords,
    save_stopwords,
    add_stopword,
    remove_stopword,
    reset_to_default,
    get_stopwords_info
)
from utils.translation import translate_words_batch, TRANSLATION_AVAILABLE
from utils.pos_tagging import (
    tag_words_batch,
    get_pos_statistics,
    get_available_categories,
    POS_TAGGING_AVAILABLE
)
from storage.repository import PhraseRepository, SeedWordRepository
from storage.word_segment_repository import WordSegmentRepository
from ui.components.seed_word_tracking import render_seed_word_tracking


# 配置
STOPWORDS_FILE = PROJECT_ROOT / "config" / "stopwords_en.txt"


def main():
    st.title("📝 Phase 0: 关键词扩展与分词工具")

    # 创建Tab导航
    tab1, tab2 = st.tabs(["🌱 词根追溯", "✂️ 分词与筛选"])

    # ========== Tab 1: 词根追溯 ==========
    with tab1:
        render_seed_word_tracking()

    # ========== Tab 2: 分词与筛选 ==========
    with tab2:
        render_segmentation_tab()


def render_segmentation_tab():
    """渲染分词与筛选tab的内容"""
    st.markdown("""
    ---
    **使用说明**:

    本工具用于关键词扩展的迭代循环中，工作流程如下：
    1. **Phase 1: 数据导入** - 导入初始关键词CSV
    2. **Phase 0: 关键词扩展**（本页面）- 分词、筛选高频词
    3. **手动操作** - 使用高频词去外部工具（Google Autocomplete、相关搜索等）获取扩展词
    4. **Phase 1: 数据导入** - 导入扩展后的关键词
    5. **Phase 0: 关键词扩展** - 再次分词筛选
    6. 重复步骤3-5，直到满意
    7. **Phase 2: 大组聚类** - 开始正式的聚类分析

    **核心功能**:
    - 从数据库读取已导入的关键词进行分词
    - 交互式停用词管理（添加、删除、重置）
    - 支持排序、翻译（可选）、导出（HTML/CSV/复制）
    - 单轮次处理，由用户手动控制迭代轮次
    """)

    # 初始化 Session State
    if 'stopwords' not in st.session_state:
        st.session_state.stopwords = load_stopwords(STOPWORDS_FILE)

    if 'word_counter' not in st.session_state:
        st.session_state.word_counter = None

    if 'translations' not in st.session_state:
        st.session_state.translations = {}

    if 'pos_tags' not in st.session_state:
        st.session_state.pos_tags = {}

    if 'selected_words' not in st.session_state:
        st.session_state.selected_words = set()

    if 'word_to_seeds' not in st.session_state:
        st.session_state.word_to_seeds = {}

    if 'keywords_cache' not in st.session_state:
        st.session_state.keywords_cache = None

    if 'phrases_cache' not in st.session_state:
        st.session_state.phrases_cache = None

    # ========== 1. 从数据库加载关键词 ==========
    st.header("1️⃣ 加载数据库关键词")

    # 使用缓存避免每次rerun都重新加载
    if st.session_state.keywords_cache is None:
        load_data = True
    else:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.success(f"✓ 已加载 {len(st.session_state.keywords_cache)} 条关键词（使用缓存）")
        with col2:
            if st.button("🔄 重新加载", help="从数据库重新加载数据"):
                st.session_state.keywords_cache = None
                st.session_state.word_counter = None
                st.session_state.translations = {}
                st.session_state.pos_tags = {}
                st.session_state.selected_words = set()
                st.rerun()
        load_data = False

    if load_data:
        try:
            with PhraseRepository() as repo:
                # 获取统计信息
                stats = repo.get_statistics()
                total_count = stats.get('total_count', 0)

                if total_count == 0:
                    st.warning("⚠️ 数据库中没有关键词数据，请先在 Phase 1 中导入数据")
                    return

                by_source = stats.get('by_source', {})

                # 显示数据库统计
                col1, col2, col3 = st.columns(3)
                col1.metric("数据库总词数", f"{total_count:,}")
                col2.metric("数据来源数", len(by_source))
                col3.metric("状态", "已就绪")

                # 数据源筛选
                if by_source:
                    st.subheader("📊 数据源筛选")

                    # 显示各来源统计
                    source_df = pd.DataFrame([
                        {"来源": source or "未知", "数量": count}
                        for source, count in by_source.items()
                    ])
                    st.dataframe(source_df, width='stretch')

                    # 选择数据源
                    available_sources = ["全部数据"] + [s or "未知" for s in by_source.keys()]
                    selected_source = st.selectbox(
                        "选择要分词的数据源",
                        options=available_sources,
                        help="选择特定来源的数据进行分词，或选择'全部数据'"
                    )

                    # 根据选择加载数据
                    if selected_source == "全部数据":
                        # 加载所有数据（分页加载以避免内存问题）
                        all_phrases = []
                        page = 1
                        page_size = 10000

                        with st.spinner("正在加载数据..."):
                            while True:
                                phrases, total = repo.get_phrases_paginated(page=page, page_size=page_size)
                                if not phrases:
                                    break
                                all_phrases.extend(phrases)
                                page += 1
                                if len(all_phrases) >= total:
                                    break

                        keywords = [p.phrase for p in all_phrases]
                        # 同时缓存完整的phrases对象（用于获取seed_word）
                        st.session_state.phrases_cache = all_phrases
                        st.info(f"✓ 已选择全部数据，共 {len(keywords):,} 条关键词")
                    else:
                        # 加载指定来源的数据
                        source_type = None if selected_source == "未知" else selected_source
                        all_phrases = []
                        page = 1
                        page_size = 10000

                        with st.spinner("正在加载数据..."):
                            while True:
                                phrases, total = repo.get_phrases_paginated(
                                    page=page,
                                    page_size=page_size,
                                    filters={'source_type': source_type}
                                )
                                if not phrases:
                                    break
                                all_phrases.extend(phrases)
                                page += 1
                                if len(all_phrases) >= total:
                                    break

                        keywords = [p.phrase for p in all_phrases]
                        # 同时缓存完整的phrases对象（用于获取seed_word）
                        st.session_state.phrases_cache = all_phrases
                        st.info(f"✓ 已选择来源 '{selected_source}'，共 {len(keywords):,} 条关键词")
                else:
                    # 没有来源信息，加载所有数据
                    all_phrases = []
                    page = 1
                    page_size = 10000

                    with st.spinner("正在加载数据..."):
                        while True:
                            phrases, total = repo.get_phrases_paginated(page=page, page_size=page_size)
                            if not phrases:
                                break
                            all_phrases.extend(phrases)
                            page += 1
                            if len(all_phrases) >= total:
                                break

                    keywords = [p.phrase for p in all_phrases]
                    # 同时缓存完整的phrases对象（用于获取seed_word）
                    st.session_state.phrases_cache = all_phrases
                    st.info(f"📊 共加载 {len(keywords):,} 条关键词")

                # 缓存加载的数据
                st.session_state.keywords_cache = keywords

        except Exception as e:
            st.error(f"❌ 加载数据库数据失败: {str(e)}")
            import traceback
            st.error(traceback.format_exc())
            return
    else:
        # 使用缓存的数据
        keywords = st.session_state.keywords_cache

    # ========== 2. 停用词管理 ==========
    st.header("2️⃣ 停用词管理")

    tab1, tab2 = st.tabs(["查看停用词", "管理停用词"])

    with tab1:
        stopwords_info = get_stopwords_info(st.session_state.stopwords)

        col1, col2, col3 = st.columns(3)
        col1.metric("停用词数量", stopwords_info['total'])
        col2.metric("是否为默认", "是" if stopwords_info['is_default'] else "否")

        st.write("**当前停用词（前50个）**:")
        st.code(', '.join(sorted(list(st.session_state.stopwords))[:50]))

    with tab2:
        st.subheader("添加停用词")
        new_word = st.text_input("输入要添加的停用词（小写）")
        if st.button("➕ 添加"):
            if new_word:
                st.session_state.stopwords = add_stopword(
                    st.session_state.stopwords,
                    new_word
                )
                save_stopwords(st.session_state.stopwords, STOPWORDS_FILE)
                st.success(f"✓ 已添加停用词: {new_word}")
                st.rerun()

        st.subheader("删除停用词")
        words_to_remove = st.multiselect(
            "选择要删除的停用词",
            options=sorted(list(st.session_state.stopwords))
        )
        if st.button("➖ 删除选中"):
            if words_to_remove:
                for word in words_to_remove:
                    st.session_state.stopwords = remove_stopword(
                        st.session_state.stopwords,
                        word
                    )
                save_stopwords(st.session_state.stopwords, STOPWORDS_FILE)
                st.success(f"✓ 已删除 {len(words_to_remove)} 个停用词")
                st.rerun()

        st.subheader("重置为默认")
        if st.button("🔄 重置停用词"):
            st.session_state.stopwords = reset_to_default(STOPWORDS_FILE)
            st.success("✓ 已重置为默认停用词")
            st.rerun()

    # ========== 3. 执行分词 ==========
    st.header("3️⃣ 执行分词")

    # 清理关键词
    keywords_cleaned = clean_keywords(keywords)
    st.info(f"✓ 清理后剩余 {len(keywords_cleaned)} 条关键词")

    # 分词配置
    col1, col2, col3 = st.columns(3)
    with col1:
        min_frequency = st.number_input(
            "最小频次",
            min_value=1,
            value=2,
            help="只显示出现次数 >= 此值的词"
        )

    with col2:
        sort_by = st.selectbox(
            "排序方式",
            options=['frequency', 'alphabetical', 'length'],
            format_func=lambda x: {
                'frequency': '按频次降序',
                'alphabetical': '按字母升序',
                'length': '按词长度降序'
            }[x]
        )

    with col3:
        enable_pos_tagging = st.checkbox(
            "启用词性标注",
            value=True,
            disabled=not POS_TAGGING_AVAILABLE,
            help="使用NLTK进行英文词性标注"
        )
        if not POS_TAGGING_AVAILABLE:
            st.info("ℹ️ 词性标注需要安装 nltk 库")

    if st.button("🚀 开始分词", type="primary"):
        with st.spinner("正在分词..."):
            # 执行分词（使用带seed追踪的版本）
            if st.session_state.phrases_cache:
                # 使用带seed追踪的分词
                word_counter, word_to_seeds = segment_keywords_with_seed_tracking(
                    st.session_state.phrases_cache,
                    st.session_state.stopwords
                )
                st.session_state.word_to_seeds = word_to_seeds
            else:
                # 降级到普通分词（如果没有phrases_cache）
                word_counter = segment_keywords(
                    keywords_cleaned,
                    st.session_state.stopwords
                )
                st.session_state.word_to_seeds = {}

            st.session_state.word_counter = word_counter

            # 词性标注
            if enable_pos_tagging and POS_TAGGING_AVAILABLE:
                with st.spinner("正在进行词性标注..."):
                    words_list = list(word_counter.keys())
                    st.session_state.pos_tags = tag_words_batch(words_list)

            # 获取统计
            stats = get_statistics(word_counter)

            # 显示统计
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("唯一词数", stats['total_unique_words'])
            col2.metric("总出现次数", stats['total_occurrences'])
            col3.metric("平均频次", stats['avg_frequency'])

            # 词性统计
            if st.session_state.pos_tags:
                pos_stats = get_pos_statistics(word_counter, st.session_state.pos_tags)
                noun_count = pos_stats.get('by_category', {}).get('Noun', 0)
                col4.metric("名词数量", noun_count)

            st.success("✓ 分词完成！")

    # ========== 4. 显示结果 ==========
    if st.session_state.word_counter is not None:
        st.header("4️⃣ 分词结果")

        # 排序
        sorted_words = get_sorted_words(
            st.session_state.word_counter,
            sort_by=sort_by,
            min_frequency=min_frequency
        )

        # 创建DataFrame
        df_words = pd.DataFrame(sorted_words, columns=['词汇', '频次'])

        # 添加词性列
        if st.session_state.pos_tags:
            df_words['词性'] = df_words['词汇'].map(
                lambda w: st.session_state.pos_tags.get(w, ('UNKNOWN', 'Other', '未知'))[2]
            )
            df_words['词性分类'] = df_words['词汇'].map(
                lambda w: st.session_state.pos_tags.get(w, ('UNKNOWN', 'Other', '未知'))[1]
            )

        # 添加词根状态列（该词是否作为seed_word使用）
        with st.spinner("正在查询词根状态..."):
            with PhraseRepository() as repo:
                words_list = df_words['词汇'].tolist()
                seed_status = repo.get_words_seed_status(words_list)

        df_words['是否为词根'] = df_words['词汇'].map(
            lambda w: '是' if seed_status.get(w, 0) > 0 else '否'
        )
        df_words['作为词根的扩展数'] = df_words['词汇'].map(
            lambda w: seed_status.get(w, 0)
        )

        # 添加原始词根列（该词出现在哪些seed_word的短语中）
        if st.session_state.word_to_seeds:
            def format_seeds(word, max_show=5):
                """格式化词根显示，只显示前几个"""
                seeds = sorted(st.session_state.word_to_seeds.get(word, ['unknown']))
                if len(seeds) <= max_show:
                    return ', '.join(seeds)
                else:
                    shown = ', '.join(seeds[:max_show])
                    return f"{shown}... (+{len(seeds)-max_show}个)"

            df_words['来源词根'] = df_words['词汇'].map(
                lambda w: format_seeds(w, max_show=5)
            )
            df_words['来源词根数'] = df_words['词汇'].map(
                lambda w: len(st.session_state.word_to_seeds.get(w, []))
            )

        # 高级筛选区域
        st.subheader("🔍 高级筛选")

        col1, col2, col3 = st.columns(3)

        with col1:
            # 频次筛选
            st.markdown("**频次范围筛选**")
            freq_min = df_words['频次'].min()
            freq_max = df_words['频次'].max()

            freq_range = st.slider(
                "选择频次范围",
                min_value=int(freq_min),
                max_value=int(freq_max),
                value=(int(freq_min), int(freq_max)),
                help="拖动滑块筛选频次范围"
            )

            # 应用频次筛选
            df_words = df_words[
                (df_words['频次'] >= freq_range[0]) &
                (df_words['频次'] <= freq_range[1])
            ]

        with col2:
            # 词性筛选
            if st.session_state.pos_tags:
                st.markdown("**词性筛选**")
                # 获取可用的词性分类
                available_categories = get_available_categories()
                category_names = [cn for _, cn in available_categories]

                selected_pos = st.multiselect(
                    "选择要显示的词性（不选则显示全部）",
                    options=category_names,
                    help="可以选择多个词性类别进行筛选"
                )

                # 应用词性筛选
                if selected_pos:
                    # 建立中文到英文的映射
                    cn_to_en = {cn: en for en, cn in available_categories}
                    selected_en = [cn_to_en[cn] for cn in selected_pos]
                    df_words = df_words[df_words['词性分类'].isin(selected_en)]

        with col3:
            # 词根筛选
            if '是否为词根' in df_words.columns:
                st.markdown("**词根筛选**")
                exclude_seeds = st.checkbox(
                    "仅显示非词根词汇",
                    value=False,
                    help="勾选后，将隐藏那些本身作为seed_word使用的词，只显示分词后的普通词汇"
                )

                if exclude_seeds:
                    # 过滤掉是词根的词（是否为词根='是'）
                    df_words = df_words[df_words['是否为词根'] == '否']

        # 显示筛选结果
        if len(df_words) < len(sorted_words):
            st.info(f"✓ 筛选后剩余 {len(df_words)} 个词（原始 {len(sorted_words)} 个）")

        # 翻译选项
        col1, col2 = st.columns([3, 1])
        with col1:
            translate_enabled = st.checkbox(
                "显示中文翻译",
                value=False,
                disabled=not TRANSLATION_AVAILABLE,
                help="使用Google Translate进行英译中（基于deep-translator库）"
            )
            if not TRANSLATION_AVAILABLE:
                st.info("ℹ️ 翻译功能不可用：请运行 `pip install deep-translator` 安装翻译库")

        with col2:
            if translate_enabled and TRANSLATION_AVAILABLE:
                # 先从数据库加载已有翻译
                if st.button("🌐 执行翻译"):
                    with st.spinner("正在从数据库加载已有翻译..."):
                        words_to_translate = df_words['词汇'].tolist()

                        # 从word_segments表加载已有翻译
                        with WordSegmentRepository() as ws_repo:
                            existing_translations = {}
                            for word in words_to_translate:
                                ws = ws_repo.get_word_segment(word)
                                if ws and ws.translation:
                                    existing_translations[word] = ws.translation

                        # 找出需要翻译的新词
                        words_need_translation = [
                            w for w in words_to_translate
                            if w not in existing_translations
                        ]

                        if existing_translations:
                            st.info(f"✓ 从数据库加载了 {len(existing_translations)} 个已有翻译")

                        # 翻译新词
                        new_translations = {}
                        if words_need_translation:
                            with st.spinner(f"正在翻译 {len(words_need_translation)} 个新词..."):
                                new_translations = translate_words_batch(
                                    words_need_translation,
                                    batch_size=100
                                )

                            # 保存新翻译到数据库
                            if new_translations:
                                with st.spinner("正在保存翻译到数据库..."):
                                    with WordSegmentRepository() as ws_repo:
                                        for word, trans in new_translations.items():
                                            # 检查是否已存在
                                            existing = ws_repo.get_word_segment(word)
                                            if existing:
                                                # 更新翻译
                                                existing.translation = trans
                                            else:
                                                # 创建新记录（只保存word和translation）
                                                from storage.models import WordSegment
                                                from datetime import datetime
                                                new_ws = WordSegment(
                                                    word=word,
                                                    frequency=0,  # 翻译功能不记录频次
                                                    translation=trans,
                                                    created_at=datetime.utcnow()
                                                )
                                                ws_repo.session.add(new_ws)
                                        ws_repo.session.commit()
                                st.success(f"✓ 翻译了 {len(new_translations)} 个新词并已保存")
                        else:
                            st.success("✓ 所有词汇都已有翻译！")

                        # 合并翻译结果
                        st.session_state.translations = {**existing_translations, **new_translations}

        # 添加翻译列
        if translate_enabled and st.session_state.translations:
            df_words['中文'] = df_words['词汇'].map(st.session_state.translations)

        # 添加选择列
        df_words.insert(0, '选择', False)

        # 批量选择操作
        st.subheader("🎯 词汇选择")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("✅ 全选", key="select_all_btn"):
                st.session_state.selected_words = set(df_words['词汇'].tolist())
                # 不立即rerun，让data_editor更新后自动处理
        with col2:
            if st.button("❌ 全不选", key="deselect_all_btn"):
                st.session_state.selected_words = set()
        with col3:
            if st.button("🔄 反选", key="inverse_select_btn"):
                all_words = set(df_words['词汇'].tolist())
                st.session_state.selected_words = all_words - st.session_state.selected_words
        with col4:
            st.metric("已选择", len(st.session_state.selected_words))

        # 更新选择列的值
        df_words['选择'] = df_words['词汇'].apply(lambda w: w in st.session_state.selected_words)

        # 显示可编辑的表格 - 使用key参数避免不必要的刷新
        # 构建禁用列列表
        disabled_cols = ['词汇', '频次']
        if '词性' in df_words.columns:
            disabled_cols.extend(['词性', '词性分类'])
        if '中文' in df_words.columns:
            disabled_cols.append('中文')
        if '是否为词根' in df_words.columns:
            disabled_cols.extend(['是否为词根', '作为词根的扩展数'])
        if '来源词根' in df_words.columns:
            disabled_cols.extend(['来源词根', '来源词根数'])

        edited_df = st.data_editor(
            df_words,
            width='stretch',
            height=400,
            disabled=disabled_cols,
            hide_index=True,
            key="words_editor",  # 添加固定key
            column_config={
                "选择": st.column_config.CheckboxColumn(
                    "选择",
                    help="勾选要导出的词汇",
                    default=False,
                )
            }
        )

        # 更新session_state中的选择（不触发rerun）
        st.session_state.selected_words = set(edited_df[edited_df['选择']]['词汇'].tolist())

        # ========== 5. 导出功能 ==========
        st.header("5️⃣ 导出结果")

        # 导出选项
        export_selected_only = st.checkbox(
            "仅导出选中的词汇",
            value=False,
            help=f"当前已选择 {len(st.session_state.selected_words)} 个词"
        )

        # 准备导出数据
        if export_selected_only and st.session_state.selected_words:
            df_export = edited_df[edited_df['选择']].copy()
            df_export = df_export.drop(columns=['选择'])
            st.info(f"✓ 将导出 {len(df_export)} 个选中的词")
        else:
            df_export = edited_df.drop(columns=['选择']).copy()

        col1, col2, col3 = st.columns(3)

        with col1:
            # 导出CSV
            csv = df_export.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📄 下载CSV",
                data=csv,
                file_name="keywords_segmented.csv",
                mime="text/csv"
            )

        with col2:
            # 导出HTML（带筛选功能）
            html = df_export.to_html(index=False, escape=False, table_id='dataTable')

            # 构建词性筛选选项（如果有词性列）
            pos_filter_html = ""
            pos_filter_js = ""
            if '词性' in df_export.columns:
                # 获取所有唯一的词性
                unique_pos = df_export['词性'].unique().tolist()
                pos_options = ''.join([f'<option value="{pos}">{pos}</option>' for pos in sorted(unique_pos)])

                pos_filter_html = f"""
                        <div class="filter-row">
                            <span class="filter-label">词性:</span>
                            <select id="posFilter" class="filter-input" onchange="filterTable()" style="max-width: 200px;">
                                <option value="">全部词性</option>
                                {pos_options}
                            </select>
                        </div>
                """

                # 词性列的索引（假设词性列在第3列，索引为2）
                pos_col_index = df_export.columns.tolist().index('词性')

                pos_filter_js = f"""
                            // 检查词性筛选
                            var posFilter = document.getElementById('posFilter').value;
                            var posMatch = true;
                            if (posFilter && cells.length > {pos_col_index}) {{
                                var pos = cells[{pos_col_index}].textContent;
                                if (pos !== posFilter) {{
                                    posMatch = false;
                                }}
                            }}
                """

                # 修改显示逻辑
                pos_filter_js += """
                            // 显示或隐藏行
                            if (wordMatch && freqMatch && posMatch) {
                                rows[i].style.display = '';
                                visibleCount++;
                            } else {
                                rows[i].style.display = 'none';
                            }
                """
            else:
                pos_filter_js = """
                            // 显示或隐藏行
                            if (wordMatch && freqMatch) {
                                rows[i].style.display = '';
                                visibleCount++;
                            } else {
                                rows[i].style.display = 'none';
                            }
                """

            html_full = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>关键词分词结果</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                    .container {{ max-width: 1400px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                    h1 {{ color: #333; text-align: center; margin-bottom: 30px; }}
                    .filter-container {{ margin: 20px 0; padding: 20px; background-color: #f9f9f9; border-radius: 5px; border: 1px solid #ddd; }}
                    .filter-row {{ display: flex; gap: 15px; align-items: center; flex-wrap: wrap; margin-bottom: 10px; }}
                    .filter-input {{ padding: 10px; font-size: 14px; border: 1px solid #ccc; border-radius: 4px; flex: 1; min-width: 200px; }}
                    .filter-input:focus {{ outline: none; border-color: #4CAF50; }}
                    .filter-label {{ font-weight: bold; color: #555; min-width: 80px; }}
                    #resultCount {{ color: #4CAF50; font-weight: bold; font-size: 14px; }}
                    .reset-btn {{ padding: 10px 20px; background-color: #f44336; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; }}
                    .reset-btn:hover {{ background-color: #da190b; }}
                    table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
                    th, td {{ border: 1px solid #ddd; padding: 12px 8px; text-align: left; }}
                    th {{ background-color: #4CAF50; color: white; position: sticky; top: 0; z-index: 10; }}
                    tr:nth-child(even) {{ background-color: #f2f2f2; }}
                    tr:hover {{ background-color: #e8f5e9; }}
                    .table-wrapper {{ max-height: 600px; overflow-y: auto; border: 1px solid #ddd; border-radius: 5px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>📊 关键词分词结果</h1>

                    <div class="filter-container">
                        <h3 style="margin-top: 0; color: #333;">🔍 筛选工具</h3>
                        <div class="filter-row">
                            <span class="filter-label">关键词:</span>
                            <input type="text" id="wordFilter" class="filter-input"
                                   placeholder="输入关键词进行筛选..." onkeyup="filterTable()">
                        </div>
                        <div class="filter-row">
                            <span class="filter-label">最小频次:</span>
                            <input type="number" id="minFreq" class="filter-input"
                                   placeholder="最小频次" onkeyup="filterTable()" style="max-width: 150px;">
                            <span class="filter-label">最大频次:</span>
                            <input type="number" id="maxFreq" class="filter-input"
                                   placeholder="最大频次" onkeyup="filterTable()" style="max-width: 150px;">
                            <button class="reset-btn" onclick="resetFilters()">🔄 重置筛选</button>
                        </div>
                        {pos_filter_html}
                        <div style="margin-top: 15px;">
                            <span id="resultCount"></span>
                        </div>
                    </div>

                    <div class="table-wrapper">
                        {html}
                    </div>
                </div>

                <script>
                    // 筛选表格函数
                    function filterTable() {{
                        var wordFilter = document.getElementById('wordFilter').value.toLowerCase();
                        var minFreq = document.getElementById('minFreq').value;
                        var maxFreq = document.getElementById('maxFreq').value;

                        var table = document.getElementById('dataTable');
                        var rows = table.getElementsByTagName('tr');
                        var visibleCount = 0;

                        // 从第2行开始（跳过表头）
                        for (var i = 1; i < rows.length; i++) {{
                            var cells = rows[i].getElementsByTagName('td');
                            if (cells.length === 0) continue;

                            var word = cells[0].textContent.toLowerCase();
                            var frequency = parseInt(cells[1].textContent);

                            // 检查关键词筛选
                            var wordMatch = true;
                            if (wordFilter) {{
                                // 检查所有列（包括可能的中文翻译列）
                                wordMatch = false;
                                for (var j = 0; j < cells.length; j++) {{
                                    if (cells[j].textContent.toLowerCase().indexOf(wordFilter) > -1) {{
                                        wordMatch = true;
                                        break;
                                    }}
                                }}
                            }}

                            // 检查频次筛选
                            var freqMatch = true;
                            if (minFreq && frequency < parseInt(minFreq)) {{
                                freqMatch = false;
                            }}
                            if (maxFreq && frequency > parseInt(maxFreq)) {{
                                freqMatch = false;
                            }}

                            {pos_filter_js}
                        }}

                        // 更新结果计数
                        var totalRows = rows.length - 1;
                        document.getElementById('resultCount').textContent =
                            '✓ 显示 ' + visibleCount + ' / ' + totalRows + ' 条结果';
                    }}

                    // 重置筛选
                    function resetFilters() {{
                        document.getElementById('wordFilter').value = '';
                        document.getElementById('minFreq').value = '';
                        document.getElementById('maxFreq').value = '';
                        {'document.getElementById("posFilter").value = "";' if pos_filter_html else ''}
                        filterTable();
                    }}

                    // 页面加载时初始化
                    window.onload = function() {{
                        var table = document.getElementById('dataTable');
                        if (table) {{
                            var totalRows = table.getElementsByTagName('tr').length - 1;
                            document.getElementById('resultCount').textContent =
                                '✓ 显示 ' + totalRows + ' / ' + totalRows + ' 条结果';
                        }}
                    }};
                </script>
            </body>
            </html>
            """
            st.download_button(
                label="🌐 下载HTML",
                data=html_full,
                file_name="keywords_segmented.html",
                mime="text/html"
            )

        with col3:
            # 复制到剪贴板
            text_for_copy = df_export.to_string(index=False)
            st.text_area(
                "复制内容",
                value=text_for_copy,
                height=100,
                help="全选并复制文本"
            )

        # 添加到词根管理
        st.markdown("---")
        st.subheader("🌱 添加到词根管理")

        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown("""
            **将选中的词汇添加为词根（seed_word）**

            选中的词汇将被添加到词根管理系统中，后续可以：
            - 使用 🤖 批量自动分类 功能自动分配Token类别
            - 手动编辑词根的定义、商业价值等信息
            - 关联词根到需求卡片
            """)

        with col2:
            add_to_seeds_btn = st.button(
                "➕ 添加选中词汇到词根",
                type="primary",
                disabled=len(st.session_state.selected_words) == 0,
                help=f"将 {len(st.session_state.selected_words)} 个选中的词汇添加为词根"
            )

        if add_to_seeds_btn:
            add_selected_words_to_seeds()


def add_selected_words_to_seeds():
    """将选中的词汇添加到seed_words表"""
    try:
        selected_words = st.session_state.selected_words

        if not selected_words:
            st.warning("⚠️ 没有选中任何词汇")
            return

        with st.spinner(f"正在添加 {len(selected_words)} 个词汇到词根管理..."):
            imported_count = 0
            updated_count = 0
            skipped_count = 0

            with SeedWordRepository() as seed_repo:
                for word in selected_words:
                    # 检查是否已存在
                    existing = seed_repo.get_seed_word(word)

                    if existing:
                        # 已存在，只更新统计信息
                        seed_repo.update_expansion_stats(word)
                        updated_count += 1
                    else:
                        # 创建新词根（未分类状态，来源标记为phase0_selection）
                        seed_repo.create_or_update_seed_word(
                            seed_word=word,
                            token_types=None,  # 待分类
                            primary_token_type=None,  # 待分类
                            source='phase0_selection',
                            status='active'
                        )

                        # 更新统计信息
                        seed_repo.update_expansion_stats(word)
                        imported_count += 1

            # 显示结果
            st.success(f"✓ 添加完成！")

            col1, col2, col3 = st.columns(3)
            col1.metric("新增词根", imported_count)
            col2.metric("更新统计", updated_count)
            col3.metric("总处理", imported_count + updated_count)

            # 提示后续操作
            if imported_count > 0:
                st.info("""
                💡 **后续操作建议**：
                1. 进入 **🌱 词根管理** 页面
                2. 点击 **🤖 批量自动分类** 按钮，为新词根自动分配Token类别
                3. 人工复查并调整分类结果
                4. 为重要词根添加定义和商业价值
                """)

                # 清空选择
                if st.button("🔄 清空选择并继续"):
                    st.session_state.selected_words = set()
                    st.rerun()

    except Exception as e:
        st.error(f"❌ 添加失败: {str(e)}")
        import traceback
        st.error(traceback.format_exc())


if __name__ == "__main__":
    main()

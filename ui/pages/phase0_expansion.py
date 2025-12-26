"""
Phase 0: 关键词扩展与分词工具
从数据库读取已导入的关键词进行分词、停用词管理和频次分析
"""
import streamlit as st
import pandas as pd
from pathlib import Path
import sys
from collections import Counter

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
from utils.user_preferences import (
    load_phase0_preferences,
    update_phase0_preference,
    get_preferences_manager
)


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
    - **✨ 自动保存配置**：所有参数设置会自动保存，下次打开时恢复
    """)

    # 初始化 Session State（必须在配置管理区域之前）
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

    if 'ngram_counter' not in st.session_state:
        st.session_state.ngram_counter = None

    if 'ngram_to_seeds' not in st.session_state:
        st.session_state.ngram_to_seeds = {}

    if 'ngram_translations' not in st.session_state:
        st.session_state.ngram_translations = {}

    # 加载用户偏好设置
    if 'preferences' not in st.session_state:
        st.session_state.preferences = load_phase0_preferences()

    # 标记是否已从数据库加载分词结果
    if 'segmentation_loaded_from_db' not in st.session_state:
        st.session_state.segmentation_loaded_from_db = False

    # ========== 自动加载已有分词结果 ==========
    # 如果还没有分词结果，尝试从数据库加载
    if (st.session_state.word_counter is None and
        not st.session_state.segmentation_loaded_from_db):

        try:
            with WordSegmentRepository() as ws_repo:
                # 检查数据库是否有分词结果
                stats = ws_repo.get_statistics()

                if stats['total_words'] > 0:
                    # 加载分词结果（使用配置的最小频次）
                    seg_prefs = st.session_state.preferences.get('segmentation', {})
                    min_freq = seg_prefs.get('min_frequency', 2)
                    min_ngram_freq = seg_prefs.get('min_ngram_frequency', 3)

                    (
                        word_counter,
                        ngram_counter,
                        pos_tags,
                        translations,
                        ngram_translations,
                        latest_batch
                    ) = ws_repo.load_segmentation_results(
                        min_word_frequency=min_freq,
                        min_ngram_frequency=min_ngram_freq
                    )

                    # 更新Session State
                    st.session_state.word_counter = word_counter
                    st.session_state.ngram_counter = ngram_counter
                    st.session_state.pos_tags = pos_tags
                    st.session_state.translations = translations
                    st.session_state.ngram_translations = ngram_translations
                    st.session_state.segmentation_loaded_from_db = True

                    # 显示加载信息
                    st.success(
                        f"✅ 已自动加载上次分词结果：{len(word_counter):,} 个单词 + "
                        f"{len(ngram_counter):,} 个短语"
                    )

                    if latest_batch:
                        batch_date = latest_batch.batch_date.strftime('%Y-%m-%d %H:%M:%S')
                        st.info(f"📅 上次分词时间: {batch_date}")

                        # 存储批次信息用于后续比较
                        st.session_state.last_batch_phrase_count = latest_batch.phrase_count
                else:
                    # 标记已检查过，避免重复检查
                    st.session_state.segmentation_loaded_from_db = True
        except Exception as e:
            st.warning(f"⚠️ 加载分词结果失败: {str(e)}")
            st.session_state.segmentation_loaded_from_db = True

    # ========== 配置管理区域 ==========
    with st.expander("⚙️ 配置管理", expanded=False):
        st.markdown("""
        **配置说明**：
        - 所有参数（分词、筛选、翻译、导出）会自动保存到本地
        - 关闭浏览器后配置仍会保留
        - 可以手动重置为默认值
        """)

        col1, col2 = st.columns([3, 1])
        with col1:
            prefs_manager = get_preferences_manager()
            last_updated = st.session_state.preferences.get('last_updated', '未设置')
            if last_updated != '未设置':
                from datetime import datetime
                try:
                    dt = datetime.fromisoformat(last_updated)
                    last_updated = dt.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    pass
            st.info(f"📅 配置最后更新时间: {last_updated}")

        with col2:
            if st.button("🔄 重置为默认配置"):
                prefs_manager.reset_to_defaults()
                st.session_state.preferences = load_phase0_preferences()
                st.success("✓ 已重置为默认配置")
                st.rerun()

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
                st.session_state.segmentation_loaded_from_db = False  # 允许重新加载
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

    # ========== 新数据检测 ==========
    # 如果已有分词结果，检查是否有新数据导入
    if (st.session_state.segmentation_loaded_from_db and
        hasattr(st.session_state, 'last_batch_phrase_count') and
        st.session_state.last_batch_phrase_count is not None):

        current_phrase_count = len(keywords)
        last_phrase_count = st.session_state.last_batch_phrase_count

        if current_phrase_count > last_phrase_count:
            new_count = current_phrase_count - last_phrase_count
            st.warning(f"⚠️ 检测到 {new_count:,} 条新关键词，建议重新分词以获取最新结果")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 全量重新分词", help="重新分词所有数据（包括旧数据和新数据）"):
                    # 清空分词结果，触发重新分词
                    st.session_state.word_counter = None
                    st.session_state.ngram_counter = None
                    st.session_state.pos_tags = {}
                    st.session_state.translations = {}
                    st.session_state.ngram_translations = {}
                    st.session_state.segmentation_loaded_from_db = False
                    st.info("✓ 已清空分词结果，请点击下方的'开始分词'按钮")
                    st.rerun()

            with col2:
                st.info("💡 **提示**：增量分词功能开发中，目前请使用全量重新分词")

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

    # 分词配置（使用保存的偏好设置作为默认值）
    seg_prefs = st.session_state.preferences.get('segmentation', {})

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        min_frequency = st.number_input(
            "最小频次",
            min_value=1,
            value=seg_prefs.get('min_frequency', 2),
            help="只显示出现次数 >= 此值的词",
            key="min_frequency_input"
        )
        # 保存配置（如果值改变）
        if min_frequency != seg_prefs.get('min_frequency', 2):
            update_phase0_preference('segmentation', 'min_frequency', min_frequency)
            st.session_state.preferences = load_phase0_preferences()

    with col2:
        sort_by_index = ['frequency', 'alphabetical', 'length'].index(
            seg_prefs.get('sort_by', 'frequency')
        )
        sort_by = st.selectbox(
            "排序方式",
            options=['frequency', 'alphabetical', 'length'],
            index=sort_by_index,
            format_func=lambda x: {
                'frequency': '按频次降序',
                'alphabetical': '按字母升序',
                'length': '按词长度降序'
            }[x],
            key="sort_by_select"
        )
        # 保存配置（如果值改变）
        if sort_by != seg_prefs.get('sort_by', 'frequency'):
            update_phase0_preference('segmentation', 'sort_by', sort_by)
            st.session_state.preferences = load_phase0_preferences()

    with col3:
        enable_pos_tagging = st.checkbox(
            "启用词性标注",
            value=seg_prefs.get('enable_pos_tagging', True),
            disabled=not POS_TAGGING_AVAILABLE,
            help="使用NLTK进行英文词性标注",
            key="enable_pos_tagging_checkbox"
        )
        if not POS_TAGGING_AVAILABLE:
            st.info("ℹ️ 词性标注需要安装 nltk 库")
        # 保存配置（如果值改变）
        if enable_pos_tagging != seg_prefs.get('enable_pos_tagging', True):
            update_phase0_preference('segmentation', 'enable_pos_tagging', enable_pos_tagging)
            st.session_state.preferences = load_phase0_preferences()

    with col4:
        extract_ngrams = st.checkbox(
            "提取短语",
            value=seg_prefs.get('extract_ngrams', True),
            help="提取高频短语组合（如 'best free', 'how to' 等）",
            key="extract_ngrams_checkbox"
        )
        # 保存配置（如果值改变）
        if extract_ngrams != seg_prefs.get('extract_ngrams', True):
            update_phase0_preference('segmentation', 'extract_ngrams', extract_ngrams)
            st.session_state.preferences = load_phase0_preferences()

    # n-gram配置（当启用短语提取时显示）
    if extract_ngrams:
        st.markdown("**短语提取配置**")
        st.info("💡 提示：系统会自动提取所有2-6词的短语组合（数据驱动），您可以在结果页面筛选感兴趣的长度")
        min_ngram_frequency = st.number_input(
            "短语最小频次",
            min_value=2,
            value=seg_prefs.get('min_ngram_frequency', 3),
            help="只保留出现次数 >= 此值的短语（过滤噪声）",
            key="min_ngram_frequency_input"
        )
        # 保存配置（如果值改变）
        if min_ngram_frequency != seg_prefs.get('min_ngram_frequency', 3):
            update_phase0_preference('segmentation', 'min_ngram_frequency', min_ngram_frequency)
            st.session_state.preferences = load_phase0_preferences()

    if st.button("🚀 开始分词", type="primary"):
        import time
        start_time = time.time()

        with st.spinner("正在分词..."):
            # 执行分词（使用带seed追踪的版本）
            if st.session_state.phrases_cache:
                # 使用带seed追踪的分词
                word_counter, word_to_seeds, ngram_counter, ngram_to_seeds = segment_keywords_with_seed_tracking(
                    st.session_state.phrases_cache,
                    st.session_state.stopwords,
                    extract_ngrams=extract_ngrams,
                    min_ngram_frequency=min_ngram_frequency if extract_ngrams else 2
                )
                st.session_state.word_to_seeds = word_to_seeds
                st.session_state.ngram_counter = ngram_counter
                st.session_state.ngram_to_seeds = ngram_to_seeds
            else:
                # 降级到普通分词（如果没有phrases_cache）
                word_counter = segment_keywords(
                    keywords_cleaned,
                    st.session_state.stopwords
                )
                st.session_state.word_to_seeds = {}
                st.session_state.ngram_counter = Counter()
                st.session_state.ngram_to_seeds = {}

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

            # 短语统计
            if extract_ngrams and st.session_state.ngram_counter:
                st.markdown("**短语提取结果**")
                col1, col2 = st.columns(2)
                col1.metric("唯一短语数", len(st.session_state.ngram_counter))
                col2.metric("短语总出现次数", sum(st.session_state.ngram_counter.values()))

        # ========== 保存到数据库 ==========
        try:
            with st.spinner("正在保存分词结果到数据库..."):
                with WordSegmentRepository() as ws_repo:
                    # 创建批次记录
                    batch_id = ws_repo.create_batch(
                        phrase_count=len(keywords_cleaned),
                        notes=f"Phase0分词 - {len(word_counter)}词 + {len(st.session_state.ngram_counter)}短语"
                    )

                    # 保存分词结果
                    new_words, new_ngrams = ws_repo.save_word_segments(
                        word_counter=word_counter,
                        pos_tags=st.session_state.pos_tags if enable_pos_tagging else None,
                        translations=st.session_state.translations,
                        batch_id=batch_id,
                        ngram_counter=st.session_state.ngram_counter if extract_ngrams else None,
                        ngram_translations=st.session_state.ngram_translations
                    )

                    # 更新批次记录
                    duration = int(time.time() - start_time)
                    ws_repo.complete_batch(
                        batch_id=batch_id,
                        word_count=len(word_counter) + len(st.session_state.ngram_counter),
                        new_word_count=new_words + new_ngrams,
                        duration_seconds=duration
                    )

                    # 标记已保存
                    st.session_state.segmentation_loaded_from_db = True
                    st.session_state.last_batch_phrase_count = len(keywords_cleaned)

            st.success(f"✓ 分词完成并已保存！新增 {new_words} 个单词 + {new_ngrams} 个短语")

        except Exception as e:
            st.error(f"❌ 保存分词结果失败: {str(e)}")
            import traceback
            st.error(traceback.format_exc())
            st.warning("⚠️ 分词结果未保存，但您仍可以在本次会话中使用")

    # ========== 4. 显示结果 ==========
    if st.session_state.word_counter is not None:
        st.header("4️⃣ 分词结果")

        st.subheader("📊 Token分析（单词+短语）")

        # ========== 合并单词和短语数据 ==========
        # 1. 准备单词数据
        sorted_words = get_sorted_words(
            st.session_state.word_counter,
            sort_by=sort_by,
            min_frequency=min_frequency
        )

        # 创建单词DataFrame
        df_words = pd.DataFrame(sorted_words, columns=['Token', '频次'])
        df_words['词数'] = 1  # 单词的词数为1

        # 2. 准备短语数据（如果有）
        df_ngrams = pd.DataFrame()
        if st.session_state.ngram_counter and len(st.session_state.ngram_counter) > 0:
            ngram_items = [(ngram, count) for ngram, count in st.session_state.ngram_counter.items()]
            df_ngrams = pd.DataFrame(ngram_items, columns=['Token', '频次'])
            df_ngrams['词数'] = df_ngrams['Token'].map(lambda x: len(x.split()))

        # 3. 合并单词和短语
        if not df_ngrams.empty:
            df_all = pd.concat([df_words, df_ngrams], ignore_index=True)
            st.info(f"✓ 已合并 {len(df_words)} 个单词 + {len(df_ngrams)} 个短语 = {len(df_all)} 个token")
        else:
            df_all = df_words
            st.info(f"✓ 共 {len(df_all)} 个单词（未提取短语）")

        # 4. 按频次重新排序
        df_all = df_all.sort_values('频次', ascending=False).reset_index(drop=True)

        # ========== 5. 添加词性列（只对单词，短语留空） ==========
        if st.session_state.pos_tags:
            df_all['词性'] = df_all['Token'].map(
                lambda w: st.session_state.pos_tags.get(w, ('UNKNOWN', 'Other', '未知'))[2] if len(w.split()) == 1 else ''
            )
            df_all['词性分类'] = df_all['Token'].map(
                lambda w: st.session_state.pos_tags.get(w, ('UNKNOWN', 'Other', '未知'))[1] if len(w.split()) == 1 else ''
            )

        # ========== 6. 添加词根状态列 ==========
        with st.spinner("正在查询词根状态..."):
            with PhraseRepository() as repo:
                tokens_list = df_all['Token'].tolist()
                seed_status = repo.get_words_seed_status(tokens_list)

        df_all['是否为词根'] = df_all['Token'].map(
            lambda w: '是' if seed_status.get(w, 0) > 0 else '否'
        )
        df_all['作为词根的扩展数'] = df_all['Token'].map(
            lambda w: seed_status.get(w, 0)
        )

        # ========== 7. 添加来源词根列 ==========
        # 合并单词和短语的seeds信息
        all_seeds = {**st.session_state.word_to_seeds, **st.session_state.ngram_to_seeds}

        def format_seeds(token, max_show=5):
            """格式化词根显示，只显示前几个"""
            seeds = sorted(all_seeds.get(token, ['unknown']))
            if len(seeds) <= max_show:
                return ', '.join(seeds)
            else:
                shown = ', '.join(seeds[:max_show])
                return f"{shown}... (+{len(seeds)-max_show}个)"

        df_all['来源词根'] = df_all['Token'].map(
            lambda w: format_seeds(w, max_show=5)
        )
        df_all['来源词根数'] = df_all['Token'].map(
            lambda w: len(all_seeds.get(w, []))
        )

        # ========== 8. 高级筛选区域 ==========
        st.subheader("🔍 高级筛选")

        # 加载筛选偏好设置
        filter_prefs = st.session_state.preferences.get('filtering', {})

        # 如果DataFrame为空，提前返回
        if len(df_all) == 0:
            st.warning("⚠️ 没有可筛选的数据，请先执行分词")
            return

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            # 频次筛选
            st.markdown("**频次范围**")
            freq_min = int(df_all['频次'].min())
            freq_max = int(df_all['频次'].max())

            freq_range = st.slider(
                "选择频次范围",
                min_value=freq_min,
                max_value=freq_max,
                value=(freq_min, freq_max),
                help="拖动滑块筛选频次范围",
                key="freq_range_slider"
            )

            # 应用频次筛选
            df_all = df_all[
                (df_all['频次'] >= freq_range[0]) &
                (df_all['频次'] <= freq_range[1])
            ]

        with col2:
            # 词数筛选（单词=1，短语=2-6）
            st.markdown("**Token长度筛选**")
            available_word_counts = sorted(df_all['词数'].unique().tolist())

            selected_word_counts = st.multiselect(
                "选择词数",
                options=available_word_counts,
                default=available_word_counts,
                help="1=单词，2-6=短语",
                key="word_count_filter"
            )

            # 应用词数筛选
            if selected_word_counts:
                df_all = df_all[df_all['词数'].isin(selected_word_counts)]

        with col3:
            # 词性筛选（只对单词有效）
            if st.session_state.pos_tags:
                st.markdown("**词性筛选**")
                # 获取可用的词性分类
                available_categories = get_available_categories()
                category_names = [cn for _, cn in available_categories]

                selected_pos = st.multiselect(
                    "选择词性",
                    options=category_names,
                    help="仅对单词有效（短语无词性）",
                    key="pos_filter_multiselect"
                )

                # 应用词性筛选（只筛选单词，短语始终保留）
                if selected_pos:
                    # 建立中文到英文的映射
                    cn_to_en = {cn: en for en, cn in available_categories}
                    selected_en = [cn_to_en[cn] for cn in selected_pos]
                    # 筛选条件：词性匹配 OR 是短语（词数>1）
                    df_all = df_all[
                        df_all['词性分类'].isin(selected_en) | (df_all['词数'] > 1)
                    ]

        with col4:
            # 词根筛选
            st.markdown("**词根筛选**")
            exclude_seeds = st.checkbox(
                "仅显示非词根",
                value=filter_prefs.get('exclude_seeds', False),
                help="隐藏作为seed_word的token",
                key="exclude_seeds_checkbox"
            )
            # 保存配置（如果值改变）
            if exclude_seeds != filter_prefs.get('exclude_seeds', False):
                update_phase0_preference('filtering', 'exclude_seeds', exclude_seeds)
                st.session_state.preferences = load_phase0_preferences()

            if exclude_seeds:
                df_all = df_all[df_all['是否为词根'] == '否']

        # 显示筛选结果
        st.info(f"✓ 筛选后剩余 {len(df_all)} 个token")

        # 如果筛选后没有数据，提前返回
        if len(df_all) == 0:
            st.warning("筛选后没有token，请调整筛选条件")
            return

        # ========== 9. 翻译选项 ==========
        st.subheader("🌐 翻译")

        # 加载翻译偏好设置
        trans_prefs = st.session_state.preferences.get('translation', {})

        col1, col2 = st.columns([3, 1])
        with col1:
            translate_enabled = st.checkbox(
                "显示中文翻译",
                value=trans_prefs.get('translate_enabled', False),
                disabled=not TRANSLATION_AVAILABLE,
                help="使用Google Translate进行英译中（基于deep-translator库）",
                key="translate_enabled_checkbox"
            )
            if not TRANSLATION_AVAILABLE:
                st.info("ℹ️ 翻译功能不可用：请运行 `pip install deep-translator` 安装翻译库")
            # 保存配置（如果值改变）
            if translate_enabled != trans_prefs.get('translate_enabled', False):
                update_phase0_preference('translation', 'translate_enabled', translate_enabled)
                st.session_state.preferences = load_phase0_preferences()

        with col2:
            if translate_enabled and TRANSLATION_AVAILABLE:
                # 先从数据库加载已有翻译
                if st.button("🌐 执行翻译"):
                    with st.spinner("正在从数据库加载已有翻译..."):
                        tokens_to_translate = df_all['Token'].tolist()

                        # 从word_segments表加载已有翻译
                        with WordSegmentRepository() as ws_repo:
                            existing_translations = {}
                            for token in tokens_to_translate:
                                ws = ws_repo.get_word_segment(token)
                                if ws and ws.translation:
                                    existing_translations[token] = ws.translation

                        # 找出需要翻译的新token
                        tokens_need_translation = [
                            t for t in tokens_to_translate
                            if t not in existing_translations
                        ]

                        if existing_translations:
                            st.info(f"✓ 从数据库加载了 {len(existing_translations)} 个已有翻译")

                        # 翻译新token
                        new_translations = {}
                        if tokens_need_translation:
                            with st.spinner(f"正在翻译 {len(tokens_need_translation)} 个新token..."):
                                new_translations = translate_words_batch(
                                    tokens_need_translation,
                                    batch_size=100
                                )

                            # 保存新翻译到数据库
                            if new_translations:
                                with st.spinner("正在保存翻译到数据库..."):
                                    with WordSegmentRepository() as ws_repo:
                                        for token, trans in new_translations.items():
                                            # 检查是否已存在
                                            existing = ws_repo.get_word_segment(token)
                                            if existing:
                                                # 更新翻译
                                                existing.translation = trans
                                            else:
                                                # 创建新记录（只保存token和translation）
                                                from storage.models import WordSegment
                                                from datetime import datetime
                                                new_ws = WordSegment(
                                                    word=token,
                                                    frequency=0,  # 翻译功能不记录频次
                                                    translation=trans,
                                                    created_at=datetime.utcnow()
                                                )
                                                ws_repo.session.add(new_ws)
                                        ws_repo.session.commit()
                                st.success(f"✓ 翻译了 {len(new_translations)} 个新token并已保存")
                        else:
                            st.success("✓ 所有token都已有翻译！")

                        # 合并翻译结果到session state（合并单词和短语的翻译）
                        all_translations = {**st.session_state.translations, **st.session_state.ngram_translations}
                        all_translations.update(existing_translations)
                        all_translations.update(new_translations)

                        # 分别保存到对应的session state
                        for token in df_all['Token'].tolist():
                            if token in all_translations:
                                if len(token.split()) == 1:
                                    st.session_state.translations[token] = all_translations[token]
                                else:
                                    st.session_state.ngram_translations[token] = all_translations[token]

        # 添加翻译列
        if translate_enabled and (st.session_state.translations or st.session_state.ngram_translations):
            all_translations = {**st.session_state.translations, **st.session_state.ngram_translations}
            df_all['中文'] = df_all['Token'].map(all_translations)

        # ========== 10. Token选择 ==========
        st.subheader("🎯 Token选择")

        # 调试模式开关
        debug_mode = st.checkbox("🐛 开启调试模式", value=True, help="显示状态变化的详细信息")

        # 添加详细的执行追踪
        if 'debug_log' not in st.session_state:
            st.session_state.debug_log = []

        def log_debug(message):
            """记录调试信息（同时输出到页面和浏览器控制台）"""
            import datetime
            timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
            log_entry = f"[{timestamp}] {message}"
            st.session_state.debug_log.append(log_entry)
            # 只保留最近50条
            if len(st.session_state.debug_log) > 50:
                st.session_state.debug_log = st.session_state.debug_log[-50:]

            # 同时输出到浏览器控制台
            import json
            # 转义特殊字符以避免JavaScript注入问题
            safe_message = json.dumps(log_entry)
            st.components.v1.html(
                f"<script>console.log({safe_message});</script>",
                height=0
            )

        # 批量选择操作
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("✅ 全选", key="select_all_btn"):
                log_debug("🔵 用户点击【全选】按钮")
                st.session_state.selected_words = set(df_all['Token'].tolist())
                log_debug(f"   - selected_words更新为: {len(st.session_state.selected_words)} 个")
                # 设置强制重新初始化标志
                st.session_state.force_reinit_editor = True
                st.rerun()
        with col2:
            if st.button("❌ 全不选", key="deselect_all_btn"):
                log_debug("🔵 用户点击【全不选】按钮")
                st.session_state.selected_words = set()
                log_debug(f"   - selected_words清空")
                # 设置强制重新初始化标志
                st.session_state.force_reinit_editor = True
                st.rerun()
        with col3:
            if st.button("🔄 反选", key="inverse_select_btn"):
                log_debug("🔵 用户点击【反选】按钮")
                all_tokens = set(df_all['Token'].tolist())
                st.session_state.selected_words = all_tokens - st.session_state.selected_words
                log_debug(f"   - selected_words反选为: {len(st.session_state.selected_words)} 个")
                # 设置强制重新初始化标志
                st.session_state.force_reinit_editor = True
                st.rerun()
        with col4:
            st.metric("已选择", len(st.session_state.selected_words))

        # 准备显示用的DataFrame
        df_display = df_all.copy()

        # ========== 检测筛选条件变化（触发editor_df重新初始化）==========
        # 使用Token列表的hash来检测数据是否变化
        current_tokens_hash = hash(tuple(sorted(df_display['Token'].tolist())))
        if 'last_tokens_hash' not in st.session_state:
            st.session_state.last_tokens_hash = None

        # 如果Token列表发生变化（筛选条件改变），强制重新初始化
        if st.session_state.last_tokens_hash != current_tokens_hash:
            log_debug(f"🔄 检测到筛选条件变化，强制重新初始化editor_df")
            st.session_state.force_reinit_editor = True
            st.session_state.last_tokens_hash = current_tokens_hash

        # ========== 11. 显示表格 ==========
        st.subheader("📋 Token列表")

        # ========== 列顺序配置 ==========
        with st.expander("⚙️ 列显示设置", expanded=False):
            st.markdown("**自定义列的显示顺序**（通过拖动调整顺序）")
            st.info("💡 调整完顺序后，**必须点击'保存列顺序'按钮**才会生效")

            # 获取所有可用的列（除了"选择"列）
            available_columns = [col for col in df_display.columns if col != '选择']

            # 加载保存的列顺序
            display_prefs = st.session_state.preferences.get('display', {})
            saved_column_order = display_prefs.get('column_order', [])

            # 如果保存的列顺序不完整，使用默认顺序
            if set(saved_column_order) != set(available_columns):
                # 默认列顺序：中文（如果有）、Token、频次、词数、其他
                default_order = []
                if '中文' in available_columns:
                    default_order.append('中文')
                if 'Token' in available_columns:
                    default_order.append('Token')
                if '频次' in available_columns:
                    default_order.append('频次')
                if '词数' in available_columns:
                    default_order.append('词数')
                # 添加剩余的列
                for col in available_columns:
                    if col not in default_order:
                        default_order.append(col)
                saved_column_order = default_order
                # 自动保存默认顺序
                update_phase0_preference('display', 'column_order', saved_column_order)
                st.session_state.preferences = load_phase0_preferences()

            # 显示当前生效的列顺序
            st.write(f"**当前列顺序**：{' → '.join(saved_column_order[:5])}{'...' if len(saved_column_order) > 5 else ''}")

            # 使用multiselect让用户调整顺序（但不会立即应用）
            col1, col2 = st.columns([4, 1])
            with col1:
                selected_column_order = st.multiselect(
                    "调整列顺序（拖动后点击保存）",
                    options=available_columns,
                    default=saved_column_order,
                    key="column_order_multiselect",
                    help="⚠️ 调整后必须点击'保存列顺序'按钮"
                )

            with col2:
                # 检查是否有变化
                has_changes = (selected_column_order != saved_column_order)
                if st.button("💾 保存列顺序", disabled=not has_changes, help="保存当前的列顺序设置", key="save_column_order_btn"):
                    update_phase0_preference('display', 'column_order', selected_column_order)
                    st.session_state.preferences = load_phase0_preferences()
                    st.success("✓ 已保存")
                    st.rerun()

            if has_changes:
                st.caption("⚠️ 列顺序有改动但未保存，点击'保存列顺序'按钮使其生效")

        # 应用列顺序（始终使用已保存的顺序，不使用multiselect的临时值）
        final_column_order = [col for col in saved_column_order if col in df_display.columns]
        df_display = df_display[final_column_order]

        # 构建禁用列列表（所有列除了选择列都禁用编辑）
        disabled_cols = ['Token', '频次', '词数']
        if '词性' in df_display.columns:
            disabled_cols.extend(['词性', '词性分类'])
        if '中文' in df_display.columns:
            disabled_cols.append('中文')
        if '是否为词根' in df_display.columns:
            disabled_cols.extend(['是否为词根', '作为词根的扩展数'])
        if '来源词根' in df_display.columns:
            disabled_cols.extend(['来源词根', '来源词根数'])

        # ========== 关键改进：DataFrame缓存机制（避免每次rerun重新初始化）==========
        # 初始化强制重新初始化标志
        if 'force_reinit_editor' not in st.session_state:
            st.session_state.force_reinit_editor = False

        # 只在首次或强制重新初始化时创建输入DataFrame
        if 'editor_df' not in st.session_state or st.session_state.force_reinit_editor:
            log_debug("🔄 重新初始化editor_df（首次或批量操作后）")
            df_with_selection = df_display.copy()
            df_with_selection.insert(0, '选择', df_with_selection['Token'].apply(
                lambda t: t in st.session_state.selected_words
            ))
            st.session_state.editor_df = df_with_selection
            st.session_state.force_reinit_editor = False  # 重置标志
            log_debug(f"   - 初始选中数量: {df_with_selection['选择'].sum()}")
        else:
            log_debug("♻️ 使用缓存的editor_df（避免重新初始化）")

        st.caption("💡 选择完成后，点击下方的'导出'或'添加到词根'按钮进行操作")

        # 渲染data_editor - 使用缓存的DataFrame作为输入
        edited_df = st.data_editor(
            st.session_state.editor_df,  # ✅ 关键：使用缓存的DataFrame，而不是每次重新创建
            width='stretch',
            height=400,
            disabled=disabled_cols,
            hide_index=True,
            key="tokens_editor",
            column_config={
                "选择": st.column_config.CheckboxColumn(
                    "选择",
                    help="勾选要导出的token",
                    default=False,
                )
            }
        )

        log_debug(f"📊 data_editor返回 - 返回选中数量: {edited_df['选择'].sum() if '选择' in edited_df.columns else 0}")

        # 更新缓存和session_state
        st.session_state.editor_df = edited_df  # 更新缓存
        if 'Token' in edited_df.columns and '选择' in edited_df.columns:
            new_selected = set(edited_df[edited_df['选择']]['Token'].tolist())
            old_count = len(st.session_state.selected_words)
            new_count = len(new_selected)
            st.session_state.selected_words = new_selected
            log_debug(f"💾 更新selected_words: {old_count} → {new_count}")

            if debug_mode:
                st.info(f"✓ 已更新选择状态: {new_count} 个token已选中")

        # ========== 12. 导出功能 ==========
        st.header("5️⃣ 导出结果")

        # 加载导出偏好设置
        export_prefs = st.session_state.preferences.get('export', {})

        # 导出选项
        export_selected_only = st.checkbox(
            "仅导出选中的token",
            value=export_prefs.get('export_selected_only', False),
            help=f"当前已选择 {len(st.session_state.selected_words)} 个token",
            key="export_selected_only_checkbox"
        )
        # 保存配置（如果值改变）
        if export_selected_only != export_prefs.get('export_selected_only', False):
            update_phase0_preference('export', 'export_selected_only', export_selected_only)
            st.session_state.preferences = load_phase0_preferences()

        # 准备导出数据
        if export_selected_only and st.session_state.selected_words:
            df_export = edited_df[edited_df['选择']].copy()
            df_export = df_export.drop(columns=['选择'])
            st.info(f"✓ 将导出 {len(df_export)} 个选中的token")
        else:
            df_export = edited_df.drop(columns=['选择']).copy()

        col1, col2, col3 = st.columns(3)

        with col1:
            # 导出CSV
            csv = df_export.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📄 下载CSV",
                data=csv,
                file_name="tokens_segmented.csv",
                mime="text/csv"
            )

        with col2:
            # 导出HTML（带筛选功能）
            # ✅ 安全修复：启用HTML转义，防止XSS攻击
            import html as html_module
            html = df_export.to_html(index=False, escape=True, table_id='dataTable')

            # 构建词性筛选选项（如果有词性列）
            pos_filter_html = ""
            pos_filter_js = ""
            if '词性' in df_export.columns:
                # 获取所有唯一的词性
                unique_pos = df_export['词性'].unique().tolist()
                # ✅ 安全修复：对词性值进行HTML转义，防止XSS注入
                pos_options = ''.join([f'<option value="{html_module.escape(str(pos))}">{html_module.escape(str(pos))}</option>' for pos in sorted(unique_pos) if pos])

                pos_filter_html = f"""
                        <div class="filter-row">
                            <span class="filter-label">词性:</span>
                            <select id="posFilter" class="filter-input" onchange="filterTable()" style="max-width: 200px;">
                                <option value="">全部词性</option>
                                {pos_options}
                            </select>
                        </div>
                """

                # 词性列的索引
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
                <title>Token分词结果</title>
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
                    <h1>📊 Token分词结果</h1>

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
                file_name="tokens_segmented.html",
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

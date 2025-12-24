"""
词根管理页面
管理seed_word的分类、定义和需求关联
"""
import streamlit as st
import pandas as pd
from pathlib import Path
import sys
import json

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from storage.repository import SeedWordRepository, PhraseRepository, DemandRepository
from storage.word_segment_repository import WordSegmentRepository
from storage.models import SeedWord


# Token框架常量
TOKEN_TYPES = {
    'intent': '意图词（用户想要什么）',
    'action': '动作词（用户要做什么）',
    'object': '对象词（涉及什么东西）',
    'other': '其他（数字、地名、品牌等）'
}

TOKEN_TYPE_EXAMPLES = {
    'intent': '示例: best, top, cheap, free, how to, guide, tutorial',
    'action': '示例: download, buy, create, install, compare, learn',
    'object': '示例: calculator, phone, software, app, template',
    'other': '示例: 2024, windows, google, new york, python'
}

PRIORITY_LEVELS = {
    'high': '高优先级',
    'medium': '中优先级',
    'low': '低优先级'
}

STATUS_TYPES = {
    'active': '活跃',
    'paused': '暂停',
    'archived': '归档'
}


def render():
    """渲染词根管理页面"""
    st.title("🌱 词根管理")

    st.markdown("""
    **功能说明**:
    - 查看和管理所有词根（seed_word）
    - 使用Token框架对词根进行分类（intent/action/object/other）
    - 支持多分类：一个词根可以同时属于多个类别
    - 为词根添加定义、业务价值和使用场景
    - 关联词根与需求卡片
    - 查看词根的扩展统计（扩展了多少个短语）
    """)

    # 创建Tab导航
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 词根列表",
        "➕ 添加/编辑词根",
        "🔗 词根与需求关联",
        "📈 词根统计"
    ])

    # Tab 1: 词根列表
    with tab1:
        render_seed_word_list()

    # Tab 2: 添加/编辑词根
    with tab2:
        render_add_edit_seed_word()

    # Tab 3: 词根与需求关联
    with tab3:
        render_seed_demand_linking()

    # Tab 4: 词根统计
    with tab4:
        render_seed_statistics()


def render_seed_word_list():
    """渲染词根列表"""
    st.header("📊 词根列表")

    # 筛选选项
    col1, col2, col3 = st.columns(3)

    with col1:
        filter_type = st.selectbox(
            "按主要类别筛选",
            options=['全部'] + list(TOKEN_TYPES.keys()),
            format_func=lambda x: '全部类别' if x == '全部' else f"{x} - {TOKEN_TYPES.get(x, x)}"
        )

    with col2:
        filter_status = st.selectbox(
            "按状态筛选",
            options=['全部'] + list(STATUS_TYPES.keys()),
            format_func=lambda x: '全部状态' if x == '全部' else STATUS_TYPES.get(x, x)
        )

    with col3:
        verified_only = st.checkbox("仅显示已审核", value=False)

    # 从数据库加载词根
    try:
        with SeedWordRepository() as repo:
            # 根据筛选条件查询
            if filter_type == '全部':
                seeds = repo.get_all_seed_words(
                    status=None if filter_status == '全部' else filter_status,
                    verified_only=verified_only
                )
            else:
                # 先按主要类别筛选
                seeds = repo.get_all_seed_words(
                    primary_token_type=filter_type,
                    status=None if filter_status == '全部' else filter_status,
                    verified_only=verified_only
                )

        if not seeds:
            st.info("暂无词根数据。请在'添加/编辑词根'选项卡中添加词根，或从现有数据自动导入。")

            # 提供快速导入按钮
            st.markdown("---")
            st.subheader("🚀 快速导入")
            st.markdown("从phrases表中提取所有唯一的seed_word并导入到词根管理表中。")

            if st.button("📥 从Phrases表导入词根", type="primary"):
                import_seeds_from_phrases()

            return

        # 获取所有词根的翻译
        seed_words_list = [s.seed_word for s in seeds]
        translations = {}
        with WordSegmentRepository() as ws_repo:
            for word in seed_words_list:
                ws = ws_repo.get_word_segment(word)
                if ws and ws.translation:
                    translations[word] = ws.translation

        # 转换为DataFrame
        df_data = []
        for seed in seeds:
            # 解析token_types
            try:
                token_types_list = json.loads(seed.token_types) if seed.token_types else [seed.primary_token_type]
            except:
                token_types_list = [seed.primary_token_type] if seed.primary_token_type else []

            token_types_str = ', '.join([f"{t}" for t in token_types_list])

            df_data.append({
                'ID': seed.seed_id,
                '词根': seed.seed_word,
                '中文': translations.get(seed.seed_word, '-'),
                '主要类别': seed.primary_token_type or '-',
                '所有类别': token_types_str or '-',
                '扩展数': seed.expansion_count or 0,
                '总搜索量': seed.total_volume or 0,
                '平均频次': seed.avg_frequency or 0,
                '状态': STATUS_TYPES.get(seed.status, seed.status),
                '优先级': PRIORITY_LEVELS.get(seed.priority, seed.priority),
                '已审核': '✓' if seed.verified else '✗',
                '定义': seed.definition[:50] + '...' if seed.definition and len(seed.definition) > 50 else seed.definition or '-'
            })

        df = pd.DataFrame(df_data)

        # 显示统计
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("词根总数", len(seeds))
        col2.metric("已审核", sum(1 for s in seeds if s.verified))
        col3.metric("总扩展数", sum(s.expansion_count or 0 for s in seeds))
        col4.metric("平均扩展数", int(sum(s.expansion_count or 0 for s in seeds) / len(seeds)) if seeds else 0)

        st.markdown("---")

        # 显示表格
        st.dataframe(
            df,
            width='stretch',
            height=400,
            hide_index=True
        )

        # 批量操作
        st.markdown("---")
        st.subheader("⚙️ 批量操作")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("🔄 更新所有词根统计", help="从phrases表重新计算所有词根的扩展数、总搜索量等"):
                with st.spinner("正在更新统计信息..."):
                    with SeedWordRepository() as repo:
                        success_count = repo.batch_update_all_stats()
                    st.success(f"✓ 成功更新 {success_count} 个词根的统计信息")
                    st.rerun()

        with col2:
            if st.button("📥 同步新词根", help="从phrases表导入尚未添加的seed_word"):
                import_seeds_from_phrases()

        with col3:
            if st.button("🤖 批量自动分类", help="使用LLM为所有未分类词根自动分配Token类别"):
                auto_classify_seeds()

        with col4:
            # 统计没有翻译的词根数量
            untranslated_count = sum(1 for word in seed_words_list if translations.get(word, '-') == '-')
            if st.button("🌐 批量翻译", help=f"翻译没有中文的词根（{untranslated_count}个）"):
                batch_translate_seeds(seed_words_list, translations)

        # 详细查看区域
        st.markdown("---")
        st.subheader("🔍 详细查看")

        selected_seed_word = st.selectbox(
            "选择要查看详情的词根",
            options=[s.seed_word for s in seeds],
            key="detail_view_selector"
        )

        if selected_seed_word:
            show_seed_word_detail(selected_seed_word)

    except Exception as e:
        st.error(f"加载词根列表失败: {str(e)}")
        import traceback
        st.error(traceback.format_exc())


def render_add_edit_seed_word():
    """渲染添加/编辑词根"""
    st.header("➕ 添加/编辑词根")

    # 选择操作模式
    mode = st.radio(
        "选择操作",
        options=['添加新词根', '编辑现有词根'],
        horizontal=True
    )

    if mode == '编辑现有词根':
        # 加载现有词根列表
        try:
            with SeedWordRepository() as repo:
                all_seeds = repo.get_all_seed_words()

            if not all_seeds:
                st.warning("暂无词根可编辑，请先添加词根。")
                return

            selected_word = st.selectbox(
                "选择要编辑的词根",
                options=[s.seed_word for s in all_seeds]
            )

            # 加载选中词根的数据
            with SeedWordRepository() as repo:
                seed_obj = repo.get_seed_word(selected_word)

            # 解析现有数据
            try:
                existing_types = json.loads(seed_obj.token_types) if seed_obj.token_types else []
            except:
                existing_types = []

            if not existing_types and seed_obj.primary_token_type:
                existing_types = [seed_obj.primary_token_type]

        except Exception as e:
            st.error(f"加载词根数据失败: {str(e)}")
            return
    else:
        selected_word = None
        seed_obj = None
        existing_types = []

    # 表单
    with st.form("seed_word_form"):
        st.subheader("📝 基本信息")

        col1, col2 = st.columns(2)

        with col1:
            if mode == '添加新词根':
                seed_word_input = st.text_input(
                    "词根文本 *",
                    value="",
                    help="输入seed_word（英文小写）"
                )
            else:
                seed_word_input = st.text_input(
                    "词根文本",
                    value=selected_word,
                    disabled=True
                )

        with col2:
            status = st.selectbox(
                "状态",
                options=list(STATUS_TYPES.keys()),
                format_func=lambda x: STATUS_TYPES[x],
                index=list(STATUS_TYPES.keys()).index(seed_obj.status if seed_obj else 'active')
            )

        st.markdown("---")
        st.subheader("🏷️ Token分类")

        # Token类别选择（多选）
        st.markdown("**选择所有适用的类别** (可多选):")

        selected_types = []
        for token_type, description in TOKEN_TYPES.items():
            col1, col2 = st.columns([1, 3])
            with col1:
                is_checked = st.checkbox(
                    f"{token_type}",
                    value=token_type in existing_types,
                    key=f"type_{token_type}"
                )
            with col2:
                st.caption(f"{description} - {TOKEN_TYPE_EXAMPLES[token_type]}")

            if is_checked:
                selected_types.append(token_type)

        # 主要类别选择
        if selected_types:
            primary_type = st.selectbox(
                "主要类别 *",
                options=selected_types,
                format_func=lambda x: f"{x} - {TOKEN_TYPES[x]}",
                index=selected_types.index(seed_obj.primary_token_type) if seed_obj and seed_obj.primary_token_type in selected_types else 0,
                help="如果选择了多个类别，请指定主要类别用于排序和筛选"
            )
        else:
            primary_type = None
            st.warning("⚠️ 请至少选择一个Token类别")

        st.markdown("---")
        st.subheader("📖 定义与场景")

        definition = st.text_area(
            "词根定义",
            value=seed_obj.definition if seed_obj else "",
            help="解释这个词根的含义和用途",
            height=100
        )

        business_value = st.text_area(
            "商业价值",
            value=seed_obj.business_value if seed_obj else "",
            help="说明这个词根的商业价值和重要性",
            height=100
        )

        user_scenario = st.text_area(
            "用户场景",
            value=seed_obj.user_scenario if seed_obj else "",
            help="描述用户在什么场景下会使用相关关键词",
            height=100
        )

        st.markdown("---")
        st.subheader("⚙️ 其他设置")

        col1, col2, col3 = st.columns(3)

        with col1:
            priority = st.selectbox(
                "优先级",
                options=list(PRIORITY_LEVELS.keys()),
                format_func=lambda x: PRIORITY_LEVELS[x],
                index=list(PRIORITY_LEVELS.keys()).index(seed_obj.priority if seed_obj else 'medium')
            )

        with col2:
            verified = st.checkbox(
                "已审核",
                value=seed_obj.verified if seed_obj else False
            )

        with col3:
            confidence = st.selectbox(
                "置信度",
                options=['high', 'medium', 'low'],
                format_func=lambda x: {'high': '高', 'medium': '中', 'low': '低'}[x],
                index=['high', 'medium', 'low'].index(seed_obj.confidence if seed_obj else 'medium')
            )

        notes = st.text_area(
            "备注",
            value=seed_obj.notes if seed_obj else "",
            help="其他补充说明"
        )

        # 提交按钮
        submitted = st.form_submit_button(
            "💾 保存" if mode == '编辑现有词根' else "➕ 添加词根",
            type="primary"
        )

        if submitted:
            # 验证
            if not seed_word_input:
                st.error("❌ 词根文本不能为空")
                return

            if not selected_types:
                st.error("❌ 请至少选择一个Token类别")
                return

            if not primary_type:
                st.error("❌ 请选择主要类别")
                return

            # 保存
            try:
                with SeedWordRepository() as repo:
                    seed = repo.create_or_update_seed_word(
                        seed_word=seed_word_input.strip().lower(),
                        token_types=selected_types,
                        primary_token_type=primary_type,
                        definition=definition.strip() if definition else None,
                        business_value=business_value.strip() if business_value else None,
                        user_scenario=user_scenario.strip() if user_scenario else None,
                        status=status,
                        priority=priority,
                        verified=verified,
                        confidence=confidence,
                        notes=notes.strip() if notes else None
                    )

                    # 更新统计信息
                    repo.update_expansion_stats(seed_word_input.strip().lower())

                st.success(f"✓ 词根 '{seed_word_input}' {'更新' if mode == '编辑现有词根' else '添加'}成功！")
                st.rerun()

            except Exception as e:
                st.error(f"❌ 保存失败: {str(e)}")
                import traceback
                st.error(traceback.format_exc())


def render_seed_demand_linking():
    """渲染词根与需求关联"""
    st.header("🔗 词根与需求关联")

    st.markdown("""
    将词根与需求卡片关联，建立词根到需求的映射关系。
    """)

    col1, col2 = st.columns(2)

    # 选择词根
    with col1:
        st.subheader("选择词根")

        try:
            with SeedWordRepository() as repo:
                all_seeds = repo.get_all_seed_words()

            if not all_seeds:
                st.warning("暂无词根数据")
                return

            selected_seed = st.selectbox(
                "选择词根",
                options=[s.seed_word for s in all_seeds],
                key="link_seed_selector"
            )

            # 显示词根信息
            with SeedWordRepository() as repo:
                seed_obj = repo.get_seed_word(selected_seed)

            if seed_obj:
                st.info(f"**类别**: {seed_obj.primary_token_type}")
                st.info(f"**扩展数**: {seed_obj.expansion_count or 0}")
                if seed_obj.definition:
                    st.info(f"**定义**: {seed_obj.definition[:100]}...")

        except Exception as e:
            st.error(f"加载词根失败: {str(e)}")
            return

    # 选择需求
    with col2:
        st.subheader("选择需求")

        try:
            from storage.models import Demand
            with DemandRepository() as repo:
                all_demands = repo.session.query(Demand).all()

            if not all_demands:
                st.warning("暂无需求数据，请先在 Phase 5 中生成需求")
                return

            demand_options = {f"{d.demand_id}: {d.title}": d.demand_id for d in all_demands}

            selected_demand_str = st.selectbox(
                "选择需求卡片",
                options=list(demand_options.keys()),
                key="link_demand_selector"
            )

            selected_demand_id = demand_options[selected_demand_str]

            # 关联选项
            is_primary = st.checkbox(
                "设为主要关联",
                value=False,
                help="是否将此需求设为该词根的主要关联需求"
            )

            if st.button("🔗 建立关联", type="primary"):
                try:
                    with SeedWordRepository() as repo:
                        success = repo.link_demand(
                            seed_word=selected_seed,
                            demand_id=selected_demand_id,
                            is_primary=is_primary
                        )

                    if success:
                        st.success(f"✓ 已将词根 '{selected_seed}' 与需求 #{selected_demand_id} 关联")
                        st.rerun()
                    else:
                        st.error("关联失败")

                except Exception as e:
                    st.error(f"关联失败: {str(e)}")

        except Exception as e:
            st.error(f"加载需求失败: {str(e)}")
            return

    # 显示现有关联
    st.markdown("---")
    st.subheader("📋 现有关联")

    if seed_obj and seed_obj.related_demand_ids:
        try:
            demand_ids = json.loads(seed_obj.related_demand_ids)

            if demand_ids:
                st.write(f"词根 **{selected_seed}** 已关联 {len(demand_ids)} 个需求:")

                from storage.models import Demand
                with DemandRepository() as repo:
                    for demand_id in demand_ids:
                        demand = repo.session.query(Demand).filter_by(demand_id=demand_id).first()
                        if demand:
                            is_primary_mark = " 🌟 (主要)" if demand_id == seed_obj.primary_demand_id else ""
                            st.write(f"- #{demand.demand_id}: {demand.title}{is_primary_mark}")
            else:
                st.info("尚未建立关联")
        except:
            st.info("尚未建立关联")
    else:
        st.info("尚未建立关联")


def render_seed_statistics():
    """渲染词根统计"""
    st.header("📈 词根统计")

    try:
        with SeedWordRepository() as repo:
            stats = repo.get_statistics()

        # 总体统计
        st.subheader("📊 总体统计")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("词根总数", stats['total'])
        col2.metric("已审核数", stats['verified_count'])
        col3.metric("审核率", f"{stats['verified_rate']}%")

        # 按主要类别统计
        st.markdown("---")
        st.subheader("🏷️ 按主要Token类别统计")

        by_type_df = pd.DataFrame([
            {
                '类别': token_type,
                '中文名': TOKEN_TYPES[token_type],
                '数量': count
            }
            for token_type, count in stats['by_primary_type'].items()
        ])

        col1, col2 = st.columns([1, 1])

        with col1:
            st.dataframe(by_type_df, width='stretch', hide_index=True)

        with col2:
            if not by_type_df.empty:
                st.bar_chart(by_type_df.set_index('类别')['数量'])

        # 按状态统计
        st.markdown("---")
        st.subheader("📌 按状态统计")

        by_status_df = pd.DataFrame([
            {
                '状态': STATUS_TYPES.get(status, status),
                '数量': count
            }
            for status, count in stats['by_status'].items()
        ])

        st.dataframe(by_status_df, width='stretch', hide_index=True)

        # Top词根
        st.markdown("---")
        st.subheader("🏆 扩展数Top 20词根")

        with SeedWordRepository() as repo:
            all_seeds = repo.get_all_seed_words()

        top_seeds = sorted(all_seeds, key=lambda x: x.expansion_count or 0, reverse=True)[:20]

        if top_seeds:
            top_df = pd.DataFrame([
                {
                    '排名': i+1,
                    '词根': s.seed_word,
                    '主要类别': s.primary_token_type,
                    '扩展数': s.expansion_count or 0,
                    '总搜索量': s.total_volume or 0,
                    '平均频次': s.avg_frequency or 0
                }
                for i, s in enumerate(top_seeds)
            ])

            st.dataframe(top_df, width='stretch', hide_index=True)

    except Exception as e:
        st.error(f"加载统计信息失败: {str(e)}")


def show_seed_word_detail(seed_word: str):
    """显示词根详细信息"""
    try:
        with SeedWordRepository() as repo:
            seed = repo.get_seed_word(seed_word)

        if not seed:
            st.warning(f"找不到词根: {seed_word}")
            return

        # 获取翻译
        translation = '-'
        with WordSegmentRepository() as ws_repo:
            ws = ws_repo.get_word_segment(seed_word)
            if ws and ws.translation:
                translation = ws.translation

        # 解析token_types
        try:
            token_types_list = json.loads(seed.token_types) if seed.token_types else []
        except:
            token_types_list = []

        # 基本信息
        st.markdown(f"### 词根: **{seed.seed_word}** ({translation})")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("扩展数", seed.expansion_count or 0)
        col2.metric("总搜索量", seed.total_volume or 0)
        col3.metric("平均频次", seed.avg_frequency or 0)
        col4.metric("状态", STATUS_TYPES.get(seed.status, seed.status))

        # Token分类
        st.markdown("**Token分类**:")
        if token_types_list:
            types_str = ', '.join([f"`{t}` ({TOKEN_TYPES.get(t, t)})" for t in token_types_list])
            st.markdown(f"- 所有类别: {types_str}")
        st.markdown(f"- 主要类别: `{seed.primary_token_type}` ({TOKEN_TYPES.get(seed.primary_token_type, '-')})")

        # 定义与场景
        if seed.definition:
            st.markdown("**定义**:")
            st.info(seed.definition)

        if seed.business_value:
            st.markdown("**商业价值**:")
            st.info(seed.business_value)

        if seed.user_scenario:
            st.markdown("**用户场景**:")
            st.info(seed.user_scenario)

        # 其他信息
        col1, col2, col3 = st.columns(3)
        col1.write(f"**优先级**: {PRIORITY_LEVELS.get(seed.priority, seed.priority)}")
        col2.write(f"**已审核**: {'✓' if seed.verified else '✗'}")
        col3.write(f"**置信度**: {seed.confidence}")

        if seed.notes:
            st.markdown("**备注**:")
            st.caption(seed.notes)

        # 关联需求
        if seed.related_demand_ids:
            try:
                demand_ids = json.loads(seed.related_demand_ids)
                if demand_ids:
                    st.markdown("**关联需求**:")
                    from storage.models import Demand
                    with DemandRepository() as demand_repo:
                        for demand_id in demand_ids:
                            demand = demand_repo.session.query(Demand).filter_by(demand_id=demand_id).first()
                            if demand:
                                is_primary = " 🌟" if demand_id == seed.primary_demand_id else ""
                                st.write(f"- #{demand.demand_id}: {demand.title}{is_primary}")
            except:
                pass

        # 查看扩展的短语（抽样）
        st.markdown("**扩展的短语（前20个）**:")
        with PhraseRepository() as phrase_repo:
            phrases = phrase_repo.get_phrases_by_seed_word(seed_word, limit=20)

        if phrases:
            phrases_text = ', '.join([p.phrase for p in phrases])
            st.caption(phrases_text)
        else:
            st.caption("暂无扩展短语")

    except Exception as e:
        st.error(f"加载词根详情失败: {str(e)}")


def import_seeds_from_phrases():
    """从phrases表导入seed_word"""
    try:
        with st.spinner("正在从phrases表导入词根..."):
            with PhraseRepository() as phrase_repo:
                # 获取所有唯一的seed_word
                all_seed_words = phrase_repo.get_all_seed_words()

            if not all_seed_words:
                st.warning("phrases表中没有seed_word数据")
                return

            # 导入到seed_words表
            imported_count = 0
            updated_count = 0

            with SeedWordRepository() as seed_repo:
                for seed_word in all_seed_words:
                    # 检查是否已存在
                    existing = seed_repo.get_seed_word(seed_word)

                    if not existing:
                        # 创建新词根（未分类状态）
                        seed_repo.create_or_update_seed_word(
                            seed_word=seed_word,
                            token_types=None,  # 待分类
                            primary_token_type=None,  # 待分类
                            source='auto_import',
                            status='active'
                        )
                        imported_count += 1

                    # 更新统计信息（无论是否已存在）
                    seed_repo.update_expansion_stats(seed_word)
                    updated_count += 1

            st.success(f"✓ 导入完成！新增 {imported_count} 个词根，更新了 {updated_count} 个词根的统计信息。")

            # 询问是否自动分类
            if imported_count > 0:
                st.info("💡 新导入的词根尚未分类，建议使用'🤖 批量自动分类'功能为它们自动分配Token类别。")

            st.rerun()

    except Exception as e:
        st.error(f"导入失败: {str(e)}")
        import traceback
        st.error(traceback.format_exc())


def auto_classify_seeds():
    """使用LLM自动分类词根"""
    try:
        # 获取未分类的词根
        with SeedWordRepository() as repo:
            all_seeds = repo.get_all_seed_words()

            # 筛选未分类的词根（primary_token_type为None）
            unclassified = [s for s in all_seeds if not s.primary_token_type]

        if not unclassified:
            st.info("✓ 所有词根都已分类，无需处理")
            return

        st.info(f"发现 {len(unclassified)} 个未分类词根，开始自动分类...")

        # 提取词根文本
        seed_words = [s.seed_word for s in unclassified]

        # 使用LLM批量分类
        from ai.client import LLMClient

        with st.spinner(f"正在使用LLM分类 {len(seed_words)} 个词根..."):
            llm = LLMClient()
            classification_results = llm.batch_classify_tokens(seed_words, batch_size=50)

        # 保存分类结果
        success_count = 0

        with st.spinner("正在保存分类结果..."):
            with SeedWordRepository() as repo:
                for result in classification_results:
                    seed_word = result.get('token')
                    token_type = result.get('token_type', 'other')
                    confidence = result.get('confidence', 'medium')

                    if seed_word:
                        # 更新词根分类
                        repo.create_or_update_seed_word(
                            seed_word=seed_word,
                            token_types=[token_type],  # 单分类
                            primary_token_type=token_type,
                            confidence=confidence,
                            verified=False  # LLM分类未经人工审核
                        )
                        success_count += 1

        st.success(f"✓ 自动分类完成！成功分类 {success_count} 个词根")
        st.info("💡 LLM分类结果已标记为'未审核'，建议人工复查并调整")
        st.rerun()

    except Exception as e:
        st.error(f"自动分类失败: {str(e)}")
        import traceback
        st.error(traceback.format_exc())


def batch_translate_seeds(seed_words_list, existing_translations):
    """批量翻译词根（使用AI）"""
    try:
        # 找出需要翻译的词根（所有词根都用AI重新翻译，确保准确性）
        words_to_translate = [
            word for word in seed_words_list
            if existing_translations.get(word, '-') == '-'
        ]

        if not words_to_translate:
            st.info("✓ 所有词根都已有翻译！")

            # 提供选项：是否要用AI重新翻译所有词根
            st.markdown("---")
            st.markdown("**🔄 重新翻译选项**")
            st.markdown("使用AI重新翻译所有词根，以获得更准确、更符合SEO语境的翻译。")

            if st.button("🤖 使用AI重新翻译所有词根", help="用AI重新翻译所有词根，替换现有翻译"):
                words_to_translate = seed_words_list
            else:
                return

        st.info(f"发现 {len(words_to_translate)} 个词根需要翻译...")

        # 使用AI翻译
        from ai.client import LLMClient

        with st.spinner(f"正在使用AI翻译 {len(words_to_translate)} 个词根..."):
            llm = LLMClient()
            new_translations = llm.batch_translate_seed_words(words_to_translate, batch_size=50)

            # 保存到数据库
            if new_translations:
                with WordSegmentRepository() as ws_repo:
                    for word, trans in new_translations.items():
                        # 检查是否已存在
                        existing = ws_repo.get_word_segment(word)
                        if existing:
                            # 更新翻译
                            existing.translation = trans
                        else:
                            # 创建新记录
                            from storage.models import WordSegment
                            from datetime import datetime
                            new_ws = WordSegment(
                                word=word,
                                frequency=0,
                                translation=trans,
                                created_at=datetime.utcnow()
                            )
                            ws_repo.session.add(new_ws)
                    ws_repo.session.commit()

        st.success(f"✓ AI翻译完成！成功翻译 {len(new_translations)} 个词根")
        st.info("💡 AI翻译更准确、更符合SEO语境，已保存到数据库")
        st.rerun()

    except Exception as e:
        st.error(f"批量翻译失败: {str(e)}")
        import traceback
        st.error(traceback.format_exc())


if __name__ == "__main__":
    render()

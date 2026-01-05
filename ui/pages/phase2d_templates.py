"""
Phase 2D: Template Discovery Results Viewer
展示数据驱动发现的搜索模板和产品实体
"""
import streamlit as st
import json
from pathlib import Path
from typing import Dict, List

# 项目根目录
project_root = Path(__file__).parent.parent.parent


def load_templates() -> Dict:
    """加载发现的模板"""
    file_path = project_root / 'outputs' / 'discovered_templates.json'
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def load_products() -> Dict:
    """加载识别的产品"""
    file_path = project_root / 'outputs' / 'product_entities.json'
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def load_variables() -> Dict:
    """加载变量提取结果"""
    file_path = project_root / 'outputs' / 'variable_extraction_results.json'
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def load_detailed_matches() -> Dict:
    """加载详细匹配数据"""
    file_path = project_root / 'outputs' / 'detailed_matches.json'
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'total_matches': 0, 'matches': []}


def load_all_phrases() -> List[Dict]:
    """加载所有原始短语数据"""
    from storage.repository import PhraseRepository
    from storage.models import Phrase

    try:
        with PhraseRepository() as repo:
            phrases = repo.session.query(Phrase).all()
            return [{
                'phrase': p.phrase,
                'volume': p.volume,
                'source': p.source,
                'status': p.status
            } for p in phrases]
    except Exception as e:
        st.error(f"加载原始数据失败: {str(e)}")
        return []


def render_page():
    """渲染页面"""
    st.title("📊 Phase 2D: 数据驱动的模板发现与产品提取")
    st.markdown("---")

    # 加载数据
    templates = load_templates()
    products_data = load_products()
    variables_data = load_variables()
    detailed_data = load_detailed_matches()  # 新增：加载详细匹配数据

    # 概览统计
    st.header("🎯 数据概览")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "发现的模板数",
            len(templates),
            help="高频搜索模板（从125K短语中自然涌现）"
        )

    with col2:
        total_vars = variables_data.get('statistics', {}).get('unique_variables', 0) if variables_data else 0
        valid_vars = len(variables_data.get('top_variables', [])) if variables_data else 0
        st.metric(
            "有效变量数",
            f"{valid_vars}/{total_vars}",
            help="通过交叉验证的高质量变量"
        )

    with col3:
        total_products = products_data.get('total_products', 0)
        st.metric(
            "识别的产品数",
            total_products,
            help="DeepSeek AI识别的真实产品/工具"
        )

    with col4:
        high_value = products_data.get('statistics', {}).get('high_value_products', 0)
        st.metric(
            "高价值产品数",
            high_value,
            help="商业价值≥70的产品"
        )

    st.markdown("---")

    # Tab区域
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔍 发现的模板",
        "🎁 识别的产品",
        "📈 提取统计",
        "📋 详细数据"  # 新增Tab
    ])

    # Tab 1: 模板展示
    with tab1:
        st.header("发现的搜索模板")
        st.markdown("*这些模板是从数据中发现的，并非预设！*")

        if not templates:
            st.warning("未找到模板数据。请先运行 `python core/template_discovery.py`")
        else:
            # 筛选器
            col1, col2 = st.columns([1, 1])
            with col1:
                min_freq = st.slider(
                    "最小频次",
                    min_value=1,
                    max_value=max(t['match_count'] for t in templates),
                    value=10
                )

            # 过滤模板
            filtered_templates = [t for t in templates if t['match_count'] >= min_freq]

            st.markdown(f"**显示 {len(filtered_templates)} 个模板（频次 >= {min_freq}）**")

            # 展示模板
            for i, template in enumerate(filtered_templates, 1):
                with st.expander(
                    f"**{i}. {template['template_pattern']}** - "
                    f"（出现 {template['match_count']} 次）",
                    expanded=(i <= 5)
                ):
                    st.markdown(f"**锚点词**: `{template['anchor']}`")
                    st.markdown(f"**频次**: {template['match_count']} 次")

                    st.markdown("**示例短语**:")
                    for j, example in enumerate(template['example_phrases'][:5], 1):
                        st.text(f"  {j}. {example}")

    # Tab 2: 产品展示
    with tab2:
        st.header("DeepSeek AI识别的产品")

        if not products_data or products_data.get('total_products', 0) == 0:
            st.warning("未找到产品数据。请先运行 `python core/product_identifier.py`")
        else:
            products = products_data.get('products', [])

            # 统计信息
            st.markdown(f"**产品总数**: {len(products)}")
            st.markdown(f"**平均商业价值**: {products_data['statistics']['avg_commercial_value']:.1f}/100")

            # 类别分布
            categories = products_data['statistics']['categories']
            if categories:
                st.markdown("**类别分布**:")
                for category, count in categories.items():
                    st.text(f"  • {category}: {count} 个产品")

            st.markdown("---")

            # 筛选器
            col1, col2 = st.columns([1, 1])
            with col1:
                selected_category = st.selectbox(
                    "按类别筛选",
                    ["全部"] + list(categories.keys())
                )

            with col2:
                min_value = st.slider(
                    "最低商业价值",
                    min_value=0,
                    max_value=100,
                    value=0
                )

            # 过滤产品
            filtered_products = products
            if selected_category != "全部":
                filtered_products = [p for p in filtered_products if p['category'] == selected_category]
            filtered_products = [p for p in filtered_products if p['commercial_value'] >= min_value]

            st.markdown(f"**显示 {len(filtered_products)} 个产品**")

            # 展示产品
            for i, product in enumerate(filtered_products, 1):
                with st.container():
                    st.markdown(f"### {i}. {product['product_name']}")

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("类别", product['category'])
                    with col2:
                        st.metric("商业价值", f"{product['commercial_value']}/100")
                    with col3:
                        st.metric("频次", product['frequency'])

                    st.markdown(f"**描述**: {product['description']}")

                    col1, col2 = st.columns(2)
                    with col1:
                        st.text(f"模板匹配数: {product['template_match_count']}")
                    with col2:
                        if product['total_volume'] > 0:
                            st.text(f"总搜索量: {product['total_volume']:,}")

                    st.markdown("---")

    # Tab 3: 统计信息
    with tab3:
        st.header("提取统计")

        # 模板统计
        if templates:
            st.subheader("📊 模板发现统计")

            col1, col2 = st.columns(2)
            with col1:
                st.metric("发现的模板总数", len(templates))
                st.metric("最高频次", max(t['match_count'] for t in templates))

            with col2:
                total_matches = sum(t['match_count'] for t in templates)
                st.metric("模板匹配总次数", total_matches)
                st.metric("平均频次", f"{total_matches/len(templates):.1f}")

            # 频次分布
            st.markdown("**频次分布**:")
            freq_bins = {"1-10": 0, "11-50": 0, "51-100": 0, "100+": 0}
            for t in templates:
                freq = t['match_count']
                if freq <= 10:
                    freq_bins["1-10"] += 1
                elif freq <= 50:
                    freq_bins["11-50"] += 1
                elif freq <= 100:
                    freq_bins["51-100"] += 1
                else:
                    freq_bins["100+"] += 1

            for bin_range, count in freq_bins.items():
                st.text(f"  {bin_range} 次出现: {count} 个模板")

        st.markdown("---")

        # 变量统计
        if variables_data:
            st.subheader("📊 变量提取统计")
            stats = variables_data.get('statistics', {})

            col1, col2 = st.columns(2)
            with col1:
                st.metric("短语匹配总数", stats.get('total_matches', 0))
                st.metric("提取的唯一变量数", stats.get('unique_variables', 0))

            with col2:
                st.metric("有效变量数（交叉验证）", len(variables_data.get('top_variables', [])))
                retention = len(variables_data.get('top_variables', [])) / max(stats.get('unique_variables', 1), 1) * 100
                st.metric("保留率", f"{retention:.1f}%")

        st.markdown("---")

        # 产品统计
        if products_data and products_data.get('total_products', 0) > 0:
            st.subheader("📊 产品识别统计")

            col1, col2 = st.columns(2)
            with col1:
                st.metric("识别的产品总数", products_data['total_products'])
                st.metric("平均商业价值", f"{products_data['statistics']['avg_commercial_value']:.1f}")

            with col2:
                st.metric("高价值产品（≥70）", products_data['statistics']['high_value_products'])

            st.markdown("**类别分布**:")
            for category, count in products_data['statistics']['categories'].items():
                st.text(f"  • {category}: {count} 个产品")

    # Tab 4: 详细数据展示（表格形式）
    with tab4:
        st.header("📋 数据表格视图")

        # 数据视图选择
        data_view = st.radio(
            "选择数据视图",
            ["模板匹配数据 (3,513条)", "全部原始数据 (125,315条)"],
            horizontal=True
        )

        st.markdown("---")

        if data_view == "模板匹配数据 (3,513条)":
            # 显示匹配数据
            if not detailed_data['matches']:
                st.warning("未找到详细匹配数据。请先运行 `python core/variable_extractor.py`")
            else:
                matches = detailed_data['matches']

                st.markdown(f"**数据说明**: 从125,315条原始短语中匹配到25个模板的{len(matches)}条数据")
                st.markdown("---")

                # 筛选器
                st.subheader("🔍 筛选条件")

                col1, col2, col3 = st.columns(3)

                with col1:
                    # 按模板筛选
                    all_templates = sorted(set(m['template_pattern'] for m in matches))
                    selected_templates = st.multiselect(
                        "按模板筛选 (可多选)",
                        ["全部"] + all_templates,
                        default=["全部"]
                    )

                with col2:
                    # 按关键词筛选
                    keyword_filter = st.text_input(
                        "按关键词筛选",
                        placeholder="输入关键词...",
                        help="支持部分匹配，大小写不敏感"
                    )

                with col3:
                    # 按频次筛选
                    min_volume = st.number_input(
                        "最低搜索量",
                        min_value=0,
                        value=0
                    )

                # 应用筛选
                filtered_matches = matches

                # 筛选1: 模板
                if "全部" not in selected_templates and selected_templates:
                    filtered_matches = [m for m in filtered_matches if m['template_pattern'] in selected_templates]

                # 筛选2: 关键词
                if keyword_filter:
                    filtered_matches = [m for m in filtered_matches if keyword_filter.lower() in m['phrase_lower']]

                # 筛选3: 频次
                if min_volume > 0:
                    filtered_matches = [m for m in filtered_matches if m['volume'] >= min_volume]

                st.markdown(f"**筛选后数据量**: {len(filtered_matches)} 条")
                st.markdown("---")

                # 转换为DataFrame格式
                import pandas as pd

                table_data = []
                for i, match in enumerate(filtered_matches, 1):
                    # 提取第一个变量
                    first_var = list(match['variables'].values())[0] if match['variables'] else ''

                    # 变量位置信息
                    var_pos_str = ''
                    if match.get('variable_positions'):
                        var_pos_str = ', '.join([f"{v[2]}:[{v[0]}:{v[1]}]" for v in match['variable_positions']])

                    table_data.append({
                        '序号': i,
                        '原始短语': match['phrase'],
                        '搜索量': match['volume'],
                        '模板': match['template_pattern'],
                        '锚点': match['template_anchor'],
                        '提取变量': first_var,
                        '前缀': match.get('prefix', ''),
                        '后缀': match.get('suffix', ''),
                        '变量位置': var_pos_str
                    })

                df = pd.DataFrame(table_data)

                # 显示表格（支持排序、搜索）
                st.dataframe(
                    df,
                    use_container_width=True,
                    height=600,
                    hide_index=True
                )

                # 下载按钮
                csv = df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 下载当前筛选结果为CSV",
                    data=csv,
                    file_name="template_matches.csv",
                    mime="text/csv"
                )

        else:
            # 显示全部原始数据
            st.markdown(f"**数据说明**: 所有125,315条原始短语数据")
            st.markdown("---")

            # 加载原始数据（带缓存）
            with st.spinner("正在加载全部原始数据..."):
                all_phrases = load_all_phrases()

            if not all_phrases:
                st.error("无法加载原始数据")
            else:
                st.markdown(f"**数据总量**: {len(all_phrases):,} 条")

                # 筛选器
                st.subheader("🔍 筛选条件")

                col1, col2 = st.columns(2)

                with col1:
                    keyword_filter = st.text_input(
                        "按关键词筛选短语",
                        placeholder="输入关键词...",
                        key="all_phrases_keyword"
                    )

                with col2:
                    min_volume_all = st.number_input(
                        "最低搜索量",
                        min_value=0,
                        value=0,
                        key="all_phrases_volume"
                    )

                # 应用筛选
                filtered_phrases = all_phrases

                if keyword_filter:
                    filtered_phrases = [p for p in filtered_phrases if keyword_filter.lower() in p['phrase'].lower()]

                if min_volume_all > 0:
                    filtered_phrases = [p for p in filtered_phrases if p['volume'] >= min_volume_all]

                st.markdown(f"**筛选后数据量**: {len(filtered_phrases):,} 条")
                st.markdown("---")

                # 转换为DataFrame
                import pandas as pd

                df_all = pd.DataFrame(filtered_phrases)
                df_all.insert(0, '序号', range(1, len(df_all) + 1))

                # 重命名列为中文
                df_all = df_all.rename(columns={
                    'phrase': '原始短语',
                    'volume': '搜索量',
                    'source': '来源',
                    'status': '状态'
                })

                # 显示表格
                st.dataframe(
                    df_all,
                    use_container_width=True,
                    height=600,
                    hide_index=True
                )

                # 下载按钮
                csv_all = df_all.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 下载当前筛选结果为CSV",
                    data=csv_all,
                    file_name="all_phrases.csv",
                    mime="text/csv"
                )

    # 数据源信息
    st.markdown("---")
    st.info("""
    **数据驱动的方法论**:
    1. 对125,315个短语进行N-gram频次分析
    2. 从高频模式中发现模板（P75阈值）
    3. 使用发现的模板提取变量
    4. 交叉验证（变量必须匹配≥2个模板）
    5. 使用DeepSeek AI进行产品识别

    **详细数据Tab说明**:
    - 展示所有3,513条匹配数据
    - 支持按模板、关键词、搜索量筛选
    - 完整显示：原始短语、模板、前缀、后缀、变量位置
    - 支持分页浏览
    """)


if __name__ == "__main__":
    render_page()

"""
数据查看与管理页面
提供HTML导出功能，方便浏览器翻译
"""
import streamlit as st
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from storage.repository import (
    PhraseRepository, ClusterMetaRepository,
    DemandRepository, TokenRepository
)
from storage.models import Demand


def export_clusters_to_html(clusters, filename="clusters_view.html"):
    """导出聚类数据为HTML"""
    output_dir = project_root / "data" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    html_path = output_dir / filename

    # 准备数据
    data = []
    for c in clusters:
        data.append({
            "ID": c.cluster_id,
            "Size": c.size,
            "Main Theme": c.main_theme or "No theme",
            "Example Phrases": c.example_phrases or "No examples",
            "Selected": "✅ Yes" if c.is_selected else "❌ No",
            "Score": c.selection_score or 0
        })

    df = pd.DataFrame(data)

    # 生成HTML
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Cluster View - {datetime.now().strftime('%Y-%m-%d %H:%M')}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
                background-color: #f5f5f5;
            }}
            h1 {{
                color: #1f77b4;
                border-bottom: 3px solid #1f77b4;
                padding-bottom: 10px;
            }}
            .info {{
                background-color: #e3f2fd;
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                background-color: white;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            th {{
                background-color: #1f77b4;
                color: white;
                padding: 12px;
                text-align: left;
                position: sticky;
                top: 0;
            }}
            td {{
                padding: 10px;
                border-bottom: 1px solid #ddd;
            }}
            tr:hover {{
                background-color: #f5f5f5;
            }}
            .selected {{
                background-color: #c8e6c9;
            }}
            .phrases {{
                max-width: 600px;
                word-wrap: break-word;
            }}
        </style>
    </head>
    <body>
        <h1>🔄 Cluster View</h1>
        <div class="info">
            <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Total Clusters:</strong> {len(clusters)}</p>
            <p><strong>Selected:</strong> {sum(1 for c in clusters if c.is_selected)}</p>
            <p><strong>💡 Tip:</strong> Use your browser's built-in translation feature (right-click → Translate) to translate this page.</p>
        </div>
        {df.to_html(index=False, escape=False, classes='data-table')}
    </body>
    </html>
    """

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    return html_path


def export_demands_to_html(demands, filename="demands_view.html"):
    """导出需求数据为HTML"""
    output_dir = project_root / "data" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    html_path = output_dir / filename

    # 准备数据
    data = []
    for d in demands:
        data.append({
            "ID": d.demand_id,
            "Title": d.title or "No title",
            "Description": d.description or "No description",
            "User Scenario": d.user_scenario or "No scenario",
            "Type": d.demand_type or "unknown",
            "Business Value": d.business_value or "unknown",
            "Status": d.status,
            "Source Cluster A": d.source_cluster_A,
            "Source Cluster B": d.source_cluster_B
        })

    df = pd.DataFrame(data)

    # 生成HTML
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Demand Cards View - {datetime.now().strftime('%Y-%m-%d %H:%M')}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
                background-color: #f5f5f5;
            }}
            h1 {{
                color: #1f77b4;
                border-bottom: 3px solid #1f77b4;
                padding-bottom: 10px;
            }}
            .info {{
                background-color: #e3f2fd;
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
            }}
            .card {{
                background-color: white;
                border-radius: 10px;
                padding: 20px;
                margin: 20px 0;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }}
            .card h2 {{
                color: #1f77b4;
                margin-top: 0;
            }}
            .meta {{
                display: flex;
                gap: 20px;
                margin: 15px 0;
                flex-wrap: wrap;
            }}
            .meta-item {{
                background-color: #f5f5f5;
                padding: 8px 15px;
                border-radius: 5px;
            }}
            .meta-label {{
                font-weight: bold;
                color: #666;
            }}
            .high-value {{
                background-color: #c8e6c9;
            }}
            .medium-value {{
                background-color: #fff9c4;
            }}
            .low-value {{
                background-color: #ffccbc;
            }}
        </style>
    </head>
    <body>
        <h1>📊 Demand Cards View</h1>
        <div class="info">
            <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Total Demands:</strong> {len(demands)}</p>
            <p><strong>💡 Tip:</strong> Use your browser's built-in translation feature (right-click → Translate) to translate this page.</p>
        </div>
    """

    # 添加卡片
    for d in demands:
        value_class = ""
        if d.business_value == "high":
            value_class = "high-value"
        elif d.business_value == "medium":
            value_class = "medium-value"
        elif d.business_value == "low":
            value_class = "low-value"

        html_content += f"""
        <div class="card">
            <h2>#{d.demand_id}: {d.title or 'No title'}</h2>
            <div class="meta">
                <div class="meta-item {value_class}">
                    <span class="meta-label">Business Value:</span> {d.business_value or 'unknown'}
                </div>
                <div class="meta-item">
                    <span class="meta-label">Type:</span> {d.demand_type or 'unknown'}
                </div>
                <div class="meta-item">
                    <span class="meta-label">Status:</span> {d.status}
                </div>
                <div class="meta-item">
                    <span class="meta-label">Source:</span> Cluster A-{d.source_cluster_A} → B-{d.source_cluster_B}
                </div>
            </div>
            <div style="margin: 15px 0;">
                <strong>Description:</strong>
                <p>{d.description or 'No description'}</p>
            </div>
            <div style="margin: 15px 0;">
                <strong>User Scenario:</strong>
                <p>{d.user_scenario or 'No scenario'}</p>
            </div>
        </div>
        """

    html_content += """
    </body>
    </html>
    """

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    return html_path


def export_tokens_to_html(tokens, filename="tokens_view.html"):
    """导出Token数据为HTML"""
    output_dir = project_root / "data" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    html_path = output_dir / filename

    # 按类型分组
    by_type = {}
    for t in tokens:
        if t.token_type not in by_type:
            by_type[t.token_type] = []
        by_type[t.token_type].append(t)

    # 生成HTML
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Tokens View - {datetime.now().strftime('%Y-%m-%d %H:%M')}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
                background-color: #f5f5f5;
            }}
            h1 {{
                color: #1f77b4;
                border-bottom: 3px solid #1f77b4;
                padding-bottom: 10px;
            }}
            h2 {{
                color: #1f77b4;
                margin-top: 30px;
            }}
            .info {{
                background-color: #e3f2fd;
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
            }}
            .type-section {{
                background-color: white;
                padding: 20px;
                margin: 20px 0;
                border-radius: 10px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .token-list {{
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
                margin-top: 15px;
            }}
            .token-item {{
                background-color: #e3f2fd;
                padding: 8px 15px;
                border-radius: 5px;
                display: inline-block;
            }}
            .token-text {{
                font-weight: bold;
                color: #1565c0;
            }}
            .token-count {{
                color: #666;
                font-size: 0.9em;
                margin-left: 5px;
            }}
            .intent {{ background-color: #c8e6c9; }}
            .action {{ background-color: #fff9c4; }}
            .object {{ background-color: #bbdefb; }}
            .other {{ background-color: #f5f5f5; }}
        </style>
    </head>
    <body>
        <h1>🏷️ Tokens View</h1>
        <div class="info">
            <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Total Tokens:</strong> {len(tokens)}</p>
            <p><strong>💡 Tip:</strong> Use your browser's built-in translation feature (right-click → Translate) to translate this page.</p>
        </div>
    """

    # 按类型显示
    for token_type, token_list in sorted(by_type.items()):
        html_content += f"""
        <div class="type-section">
            <h2>{token_type.upper()} ({len(token_list)} tokens)</h2>
            <div class="token-list">
        """

        # 按频次排序
        sorted_tokens = sorted(token_list, key=lambda t: t.in_phrase_count, reverse=True)

        for t in sorted_tokens:
            html_content += f"""
                <div class="token-item {token_type}">
                    <span class="token-text">{t.token_text}</span>
                    <span class="token-count">({t.in_phrase_count})</span>
                </div>
            """

        html_content += """
            </div>
        </div>
        """

    html_content += """
    </body>
    </html>
    """

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    return html_path


def render():
    st.markdown('<div class="main-header">📊 数据查看与管理</div>', unsafe_allow_html=True)

    st.markdown("""
    ### 功能说明

    集中查看所有数据，并支持导出为HTML格式，方便使用浏览器翻译功能。

    **💡 使用浏览器翻译**:
    - Chrome: 右键 → "翻译为中文"
    - Edge: 右键 → "翻译"
    - Firefox: 需要安装翻译插件
    """)

    st.markdown("---")

    # 数据类型选择
    data_type = st.selectbox(
        "选择要查看的数据类型",
        ["大组聚类 (Clusters Level A)",
         "小组聚类 (Clusters Level B)",
         "需求卡片 (Demands)",
         "关键词 (Tokens)",
         "短语 (Phrases)"]
    )

    st.markdown("---")

    # 根据类型显示不同内容
    if "大组聚类" in data_type:
        st.markdown("## 🔄 大组聚类数据")

        try:
            with ClusterMetaRepository() as repo:
                clusters = repo.get_all_clusters('A')

                if clusters:
                    st.metric("大组总数", len(clusters))

                    # 筛选选项
                    col1, col2 = st.columns(2)

                    with col1:
                        show_selected_only = st.checkbox("仅显示已选中", value=False)

                    with col2:
                        min_size = st.slider("最小大小", 0, 200, 0)

                    # 应用筛选
                    filtered = clusters
                    if show_selected_only:
                        filtered = [c for c in filtered if c.is_selected]
                    if min_size > 0:
                        filtered = [c for c in filtered if c.size >= min_size]

                    st.markdown(f"**显示: {len(filtered)} / {len(clusters)}**")

                    # 显示表格
                    data = []
                    for c in filtered:
                        data.append({
                            "ID": c.cluster_id,
                            "大小": c.size,
                            "主题": c.main_theme or "(无)",
                            "示例短语": (c.example_phrases[:80] + "...") if c.example_phrases and len(c.example_phrases) > 80 else c.example_phrases,
                            "已选中": "✅" if c.is_selected else "❌",
                            "打分": c.selection_score or 0
                        })

                    df = pd.DataFrame(data)
                    st.dataframe(df, use_container_width=True, height=400)

                    # 导出按钮
                    col1, col2, col3 = st.columns([1, 1, 2])

                    with col1:
                        if st.button("📤 导出为HTML", type="primary", use_container_width=True):
                            html_path = export_clusters_to_html(filtered)
                            st.success(f"✅ 已导出到: {html_path}")
                            st.info("💡 在浏览器中打开该文件，然后右键选择'翻译'即可查看中文版本")

                    with col2:
                        if html_path := (project_root / "data" / "output" / "clusters_view.html"):
                            if html_path.exists():
                                with open(html_path, 'r', encoding='utf-8') as f:
                                    st.download_button(
                                        "⬇️ 下载HTML",
                                        f.read(),
                                        file_name="clusters_view.html",
                                        mime="text/html",
                                        use_container_width=True
                                    )

                else:
                    st.info("ℹ️ 还没有大组聚类数据，请先运行 Phase 2")

        except Exception as e:
            st.error(f"❌ 加载失败: {str(e)}")

    elif "小组聚类" in data_type:
        st.markdown("## 🔄 小组聚类数据")

        # 调试信息
        st.info(f"正在加载小组聚类数据... (选择的类型: {data_type})")

        try:
            with ClusterMetaRepository() as repo:
                clusters = repo.get_all_clusters('B')

                # 显示加载的数据量
                st.success(f"成功从数据库加载了 {len(clusters)} 个小组聚类")

                if clusters:
                    st.metric("小组总数", len(clusters))

                    # 按大组分组
                    by_parent = {}
                    for c in clusters:
                        parent_id = c.cluster_id // 10000
                        if parent_id not in by_parent:
                            by_parent[parent_id] = []
                        by_parent[parent_id].append(c)

                    # 显示统计信息
                    st.markdown("### 📊 按大组分布")
                    stats_data = []
                    for parent_id in sorted(by_parent.keys()):
                        stats_data.append({
                            "大组ID": parent_id,
                            "小组数量": len(by_parent[parent_id]),
                            "总短语数": sum(c.size for c in by_parent[parent_id])
                        })

                    stats_df = pd.DataFrame(stats_data)
                    # 支持排序和横向滚动
                    st.dataframe(
                        stats_df,
                        use_container_width=False,
                        width=1200,
                        hide_index=True,
                        column_config={
                            "大组ID": st.column_config.NumberColumn(
                                "大组ID",
                                help="大组的唯一标识符",
                                format="%d",
                                width="medium"
                            ),
                            "小组数量": st.column_config.NumberColumn(
                                "小组数量",
                                help="该大组包含的小组数量",
                                format="%d",
                                width="medium"
                            ),
                            "总短语数": st.column_config.NumberColumn(
                                "总短语数",
                                help="该大组所有小组的短语总数",
                                format="%d",
                                width="medium"
                            ),
                        }
                    )

                    st.markdown("---")

                    # 批量导出功能
                    st.markdown("### 📦 批量导出小组数据")

                    col1, col2 = st.columns([3, 1])

                    # 多选大组
                    parent_ids_list = sorted(by_parent.keys())

                    # 初始化状态变量
                    if 'select_all_trigger' not in st.session_state:
                        st.session_state.select_all_trigger = False
                    if 'parent_group_multiselect' not in st.session_state:
                        st.session_state.parent_group_multiselect = []

                    # 处理全选触发器（在widget创建之前）
                    if st.session_state.select_all_trigger:
                        st.session_state.parent_group_multiselect = parent_ids_list
                        st.session_state.select_all_trigger = False

                    with col1:
                        selected_parents = st.multiselect(
                            "选择要导出的大组（可多选）",
                            options=parent_ids_list,
                            format_func=lambda x: f"大组 {x} ({len(by_parent[x])} 个小组, {sum(c.size for c in by_parent[x])} 个短语)",
                            help="按住Ctrl/Cmd键可以选择多个大组",
                            key="parent_group_multiselect"
                        )

                    with col2:
                        # 快速选择按钮
                        if st.button("✅ 全选", use_container_width=True):
                            st.session_state.select_all_trigger = True
                            st.rerun()

                    if selected_parents:
                        st.info(f"已选择 **{len(selected_parents)}** 个大组，共 **{sum(len(by_parent[pid]) for pid in selected_parents)}** 个小组")

                        col1, col2, col3 = st.columns([1, 1, 2])

                        # 初始化导出状态
                        if 'last_batch_export' not in st.session_state:
                            st.session_state.last_batch_export = None

                        with col1:
                            if st.button("📤 批量导出HTML", type="primary", use_container_width=True):
                                # 收集所有选中大组的小组
                                all_selected_clusters = []
                                for pid in sorted(selected_parents):
                                    all_selected_clusters.extend(by_parent[pid])

                                # 导出为一个HTML文件
                                html_path = export_clusters_to_html(
                                    all_selected_clusters,
                                    filename=f"clusters_B_batch_{len(selected_parents)}groups.html"
                                )
                                # 保存到session_state
                                st.session_state.last_batch_export = html_path
                                st.success(f"✅ 已导出 {len(selected_parents)} 个大组的所有小组")
                                st.info("💡 使用下方按钮打开或下载HTML文件")

                        with col2:
                            if st.button("📂 分别导出HTML", use_container_width=True):
                                # 为每个大组单独导出
                                export_count = 0
                                export_paths = []
                                for pid in sorted(selected_parents):
                                    small_clusters = by_parent[pid]
                                    html_path = export_clusters_to_html(
                                        small_clusters,
                                        filename=f"clusters_B_parent_{pid}.html"
                                    )
                                    export_paths.append(html_path)
                                    export_count += 1

                                st.success(f"✅ 已分别导出 {export_count} 个HTML文件")
                                st.info(f"💡 文件位置: data/output/ 目录")

                        # 如果有最近导出的文件，显示操作按钮
                        if st.session_state.last_batch_export:
                            html_path = st.session_state.last_batch_export
                            if html_path.exists():
                                st.markdown("---")
                                st.markdown("### 📁 最近导出的文件")

                                action_col1, action_col2, action_col3 = st.columns([1, 1, 2])

                                with action_col1:
                                    if st.button("🌐 在浏览器打开", use_container_width=True):
                                        import webbrowser
                                        webbrowser.open(str(html_path))
                                        st.success("✅ 已在浏览器中打开")

                                with action_col2:
                                    with open(html_path, 'r', encoding='utf-8') as f:
                                        st.download_button(
                                            "⬇️ 下载HTML",
                                            f.read(),
                                            file_name=html_path.name,
                                            mime="text/html",
                                            use_container_width=True
                                        )

                                with action_col3:
                                    st.caption(f"文件: {html_path.name}")

                    st.markdown("---")
                    st.markdown("### 🔍 查看小组详情")

                    # 选择大组
                    parent_options = {f"大组 {pid} ({len(by_parent[pid])} 个小组)": pid
                                     for pid in sorted(by_parent.keys())}

                    selected_label = st.selectbox(
                        "选择大组查看其小组",
                        options=list(parent_options.keys())
                    )

                    if selected_label:
                        parent_id = parent_options[selected_label]
                        small_clusters = by_parent[parent_id]

                        st.info(f"大组 **{parent_id}** 包含 **{len(small_clusters)}** 个小组，共 **{sum(c.size for c in small_clusters)}** 个短语")

                        # 显示表格
                        data = []
                        for c in sorted(small_clusters, key=lambda x: x.size, reverse=True):
                            data.append({
                                "小组ID": c.cluster_id,
                                "大小": c.size,
                                "主题": c.main_theme or "(无)",
                                "示例短语": (c.example_phrases[:80] + "...") if c.example_phrases and len(c.example_phrases) > 80 else c.example_phrases,
                            })

                        df = pd.DataFrame(data)
                        # 支持排序和横向滚动
                        st.dataframe(
                            df,
                            use_container_width=True,
                            height=400,
                            hide_index=True,
                            column_config={
                                "小组ID": st.column_config.NumberColumn(
                                    "小组ID",
                                    help="小组的唯一标识符",
                                    format="%d"
                                ),
                                "大小": st.column_config.NumberColumn(
                                    "大小",
                                    help="该小组包含的短语数量",
                                    format="%d"
                                ),
                                "主题": st.column_config.TextColumn(
                                    "主题",
                                    help="AI生成的主题标签",
                                    width="medium"
                                ),
                                "示例短语": st.column_config.TextColumn(
                                    "示例短语",
                                    help="该小组的代表性短语示例",
                                    width="large"
                                ),
                            }
                        )

                        # 导出按钮
                        col1, col2 = st.columns([1, 3])
                        with col1:
                            if st.button("📤 导出当前大组为HTML", type="primary", use_container_width=True):
                                html_path = export_clusters_to_html(
                                    small_clusters,
                                    filename=f"clusters_B_parent_{parent_id}.html"
                                )
                                st.success(f"已导出到: {html_path}")

                else:
                    st.info("还没有小组聚类数据，请先运行 Phase 4")

        except Exception as e:
            st.error(f"加载失败: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

    elif "需求卡片" in data_type:
        st.markdown("## 📊 需求卡片数据")

        try:
            with DemandRepository() as repo:
                demands = repo.session.query(Demand).all()

                if demands:
                    st.metric("需求总数", len(demands))

                    # 筛选选项
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        type_filter = st.multiselect(
                            "类型",
                            options=["tool", "content", "service", "education", "other"],
                            default=[]
                        )

                    with col2:
                        value_filter = st.multiselect(
                            "商业价值",
                            options=["high", "medium", "low", "unknown"],
                            default=[]
                        )

                    with col3:
                        status_filter = st.multiselect(
                            "状态",
                            options=["idea", "validated", "in_progress", "archived"],
                            default=[]
                        )

                    # 应用筛选
                    filtered = demands
                    if type_filter:
                        filtered = [d for d in filtered if d.demand_type in type_filter]
                    if value_filter:
                        filtered = [d for d in filtered if d.business_value in value_filter]
                    if status_filter:
                        filtered = [d for d in filtered if d.status in status_filter]

                    st.markdown(f"**显示: {len(filtered)} / {len(demands)}**")

                    # 显示卡片
                    for d in filtered[:10]:  # 只显示前10个
                        with st.expander(f"#{d.demand_id}: {d.title or 'No title'}"):
                            col1, col2 = st.columns([1, 3])
                            with col1:
                                st.markdown(f"**类型**: {d.demand_type}")
                                st.markdown(f"**价值**: {d.business_value}")
                                st.markdown(f"**状态**: {d.status}")
                            with col2:
                                st.markdown(f"**描述**: {d.description or 'No description'}")
                                st.markdown(f"**场景**: {d.user_scenario or 'No scenario'}")

                    if len(filtered) > 10:
                        st.info(f"⚠️ 只显示前10个，共 {len(filtered)} 个。请导出HTML查看全部。")

                    # 导出按钮
                    col1, col2, col3 = st.columns([1, 1, 2])

                    with col1:
                        if st.button("📤 导出为HTML", type="primary", use_container_width=True):
                            html_path = export_demands_to_html(filtered)
                            st.success(f"✅ 已导出到: {html_path}")
                            st.info("💡 在浏览器中打开该文件，然后右键选择'翻译'即可查看中文版本")

                    with col2:
                        if html_path := (project_root / "data" / "output" / "demands_view.html"):
                            if html_path.exists():
                                with open(html_path, 'r', encoding='utf-8') as f:
                                    st.download_button(
                                        "⬇️ 下载HTML",
                                        f.read(),
                                        file_name="demands_view.html",
                                        mime="text/html",
                                        use_container_width=True
                                    )

                else:
                    st.info("ℹ️ 还没有需求卡片，请先运行 Phase 4")

        except Exception as e:
            st.error(f"❌ 加载失败: {str(e)}")

    elif "关键词" in data_type:
        st.markdown("## 🏷️ Token数据")

        try:
            with TokenRepository() as repo:
                tokens = repo.get_all_tokens()

                if tokens:
                    st.metric("Token总数", len(tokens))

                    # 筛选选项
                    col1, col2 = st.columns(2)

                    with col1:
                        type_filter = st.multiselect(
                            "Token类型",
                            options=["intent", "action", "object", "other"],
                            default=[]
                        )

                    with col2:
                        min_freq = st.slider("最小频次", 0, 50, 0)

                    # 应用筛选
                    filtered = tokens
                    if type_filter:
                        filtered = [t for t in filtered if t.token_type in type_filter]
                    if min_freq > 0:
                        filtered = [t for t in filtered if t.in_phrase_count >= min_freq]

                    # 按类型分组显示
                    by_type = {}
                    for t in filtered:
                        if t.token_type not in by_type:
                            by_type[t.token_type] = []
                        by_type[t.token_type].append(t)

                    st.markdown(f"**显示: {len(filtered)} / {len(tokens)}**")

                    for token_type, token_list in sorted(by_type.items()):
                        with st.expander(f"{token_type.upper()} ({len(token_list)} tokens)"):
                            # 按频次排序
                            sorted_tokens = sorted(token_list, key=lambda t: t.in_phrase_count, reverse=True)

                            # 显示为标签云样式
                            tokens_html = "<div style='display: flex; flex-wrap: wrap; gap: 10px;'>"
                            for t in sorted_tokens[:50]:  # 只显示前50个
                                tokens_html += f"<span style='background-color: #e3f2fd; padding: 5px 10px; border-radius: 5px;'>{t.token_text} ({t.in_phrase_count})</span>"
                            tokens_html += "</div>"
                            st.markdown(tokens_html, unsafe_allow_html=True)

                            if len(sorted_tokens) > 50:
                                st.info(f"⚠️ 只显示前50个，共 {len(sorted_tokens)} 个。")

                    # 导出按钮
                    col1, col2, col3 = st.columns([1, 1, 2])

                    with col1:
                        if st.button("📤 导出为HTML", type="primary", use_container_width=True):
                            html_path = export_tokens_to_html(filtered)
                            st.success(f"✅ 已导出到: {html_path}")
                            st.info("💡 在浏览器中打开该文件，然后右键选择'翻译'即可查看中文版本")

                    with col2:
                        if html_path := (project_root / "data" / "output" / "tokens_view.html"):
                            if html_path.exists():
                                with open(html_path, 'r', encoding='utf-8') as f:
                                    st.download_button(
                                        "⬇️ 下载HTML",
                                        f.read(),
                                        file_name="tokens_view.html",
                                        mime="text/html",
                                        use_container_width=True
                                    )

                else:
                    st.info("ℹ️ 还没有Token数据，请先运行 Phase 5")

        except Exception as e:
            st.error(f"❌ 加载失败: {str(e)}")

    elif "短语" in data_type:
        st.markdown("## 📝 短语数据")

        try:
            with PhraseRepository() as repo:
                stats = repo.get_statistics()

                st.metric("短语总数", f"{stats.get('total_count', 0):,}")

                # 采样显示
                st.warning("⚠️ 短语数据量较大，仅显示采样数据")

                sample_size = st.slider("采样数量", 100, 10000, 1000, 100)

                if st.button("📊 加载采样数据", type="primary"):
                    from storage.models import Phrase
                    phrases = repo.session.query(Phrase).limit(sample_size).all()

                    data = []
                    for p in phrases:
                        data.append({
                            "短语": p.phrase,
                            "来源": p.data_source,
                            "大组": p.cluster_id_A if p.cluster_id_A else "未分配",
                            "小组": p.cluster_id_B if p.cluster_id_B else "未分配",
                            "状态": p.processed_status
                        })

                    df = pd.DataFrame(data)
                    st.dataframe(df, use_container_width=True, height=400)

        except Exception as e:
            st.error(f"❌ 加载失败: {str(e)}")

    st.markdown("---")

    # 使用说明
    with st.expander("📖 使用说明"):
        st.markdown("""
        ### HTML导出功能

        **为什么需要HTML导出？**
        - 英文内容可以在浏览器中直接翻译
        - 格式美观，易于阅读和分享
        - 可以离线查看

        **如何使用浏览器翻译？**

        1. **Chrome浏览器**:
           - 打开HTML文件
           - 右键点击页面 → 选择"翻译为中文"
           - 或点击地址栏右侧的翻译图标

        2. **Edge浏览器**:
           - 打开HTML文件
           - 右键点击页面 → 选择"翻译"
           - 或点击地址栏右侧的翻译图标

        3. **Firefox浏览器**:
           - 需要先安装翻译插件（如Google Translate）
           - 然后使用插件功能翻译页面

        ### 数据筛选

        每种数据类型都提供了筛选功能：
        - **聚类**: 按大小、选中状态筛选
        - **需求**: 按类型、商业价值、状态筛选
        - **Token**: 按类型、频次筛选
        - **短语**: 采样显示（数据量太大）

        ### 文件位置

        所有导出的HTML文件保存在：
        ```
        data/output/
        ├── clusters_view.html   # 聚类数据
        ├── demands_view.html    # 需求数据
        └── tokens_view.html     # Token数据
        ```
        """)

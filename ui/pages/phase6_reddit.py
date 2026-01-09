"""
Phase 6: Reddit板块分析与标注系统

功能：
1. 数据导入（CSV/Excel）
2. AI配置管理
3. 板块列表查看与编辑
4. 标签管理与统计
5. 数据导出
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
import tempfile

from core.reddit_analyzer import RedditAnalyzer


def render():
    """渲染Reddit板块分析页面"""
    st.title("🔍 Reddit板块分析与标注系统")

    # 创建选项卡
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📥 数据导入",
        "⚙️ AI配置",
        "📊 板块列表",
        "🏷️ 标签管理",
        "📤 数据导出"
    ])

    # 初始化分析器
    analyzer = RedditAnalyzer()

    # Tab 1: 数据导入
    with tab1:
        render_import_tab(analyzer)

    # Tab 2: AI配置
    with tab2:
        render_config_tab(analyzer)

    # Tab 3: 板块列表
    with tab3:
        render_list_tab(analyzer)

    # Tab 4: 标签管理
    with tab4:
        render_tags_tab(analyzer)

    # Tab 5: 数据导出
    with tab5:
        render_export_tab(analyzer)


def render_import_tab(analyzer: RedditAnalyzer):
    """渲染数据导入选项卡"""
    st.header("数据导入")

    st.markdown("""
    **文件格式要求**:
    - 支持CSV或Excel文件
    - 无列名，按列顺序识别：
      1. 第1列：板块名称（如 r/Python）
      2. 第2列：板块描述
      3. 第3列：订阅人数
    - 描述为空的板块将被跳过AI分析
    """)

    # 文件上传
    uploaded_file = st.file_uploader(
        "上传CSV或Excel文件",
        type=['csv', 'xlsx', 'xls'],
        help="选择包含Reddit板块数据的文件"
    )

    # 批次ID
    batch_id = st.text_input(
        "导入批次ID（可选）",
        placeholder="留空自动生成",
        help="用于标识本次导入的数据批次"
    )

    # 去重选项
    skip_duplicates = st.checkbox(
        "跳过重复记录（按板块名称去重）",
        value=True,
        help="如果板块名称已存在，保留订阅数最多的记录"
    )

    # 导入按钮
    if st.button("开始导入", type="primary", disabled=not uploaded_file):
        if uploaded_file:
            with st.spinner("正在导入..."):
                # 保存临时文件
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
                    tmp_file.write(uploaded_file.getbuffer())
                    temp_path = tmp_file.name

                # 导入数据
                file_type = 'csv' if uploaded_file.name.endswith('.csv') else 'excel'

                if file_type == 'csv':
                    result = analyzer.import_from_csv(
                        temp_path,
                        batch_id=batch_id if batch_id else None,
                        skip_duplicates=skip_duplicates
                    )
                else:
                    result = analyzer.import_from_excel(
                        temp_path,
                        batch_id=batch_id if batch_id else None,
                        skip_duplicates=skip_duplicates
                    )

                # 显示结果
                if result['success']:
                    st.success(result['message'])

                    col1, col2, col3 = st.columns(3)
                    col1.metric("导入成功", result['data']['imported_count'])
                    col2.metric("跳过（描述为空）", result['data']['skipped_count'])
                    col3.metric("错误", result['data']['error_count'])

                    st.info(f"批次ID: {result['data']['batch_id']}")
                else:
                    st.error(result['message'])
                    if result['errors']:
                        for error in result['errors']:
                            st.error(f"- {error}")


def render_config_tab(analyzer: RedditAnalyzer):
    """渲染AI配置选项卡"""
    st.header("AI配置管理")

    # 获取配置列表
    configs_result = analyzer.get_prompt_configs(active_only=False)

    if not configs_result['success']:
        st.error(configs_result['message'])
        return

    configs = configs_result['data']

    if not configs:
        st.warning("没有可用的配置")
        return

    # 配置选择
    config_names = [c['config_name'] for c in configs]
    selected_config_name = st.selectbox("选择配置", config_names)

    # 获取选中的配置
    selected_config = next(c for c in configs if c['config_name'] == selected_config_name)

    # 配置编辑
    st.subheader("配置详情")

    config_name = st.text_input("配置名称", value=selected_config['config_name'])

    prompt_template = st.text_area(
        "提示词模板",
        value=selected_config['prompt_template'],
        height=300,
        help="使用 {name}, {description}, {subscribers} 作为变量占位符"
    )

    system_message = st.text_area(
        "系统消息",
        value=selected_config['system_message'] or '',
        height=100,
        help="定义AI的角色和行为"
    )

    col1, col2 = st.columns(2)
    temperature = col1.slider(
        "温度参数",
        0.0, 2.0,
        float(selected_config['temperature']),
        0.1,
        help="控制输出的随机性，越高越随机"
    )
    max_tokens = col2.number_input(
        "最大Token数",
        100, 10000,
        selected_config['max_tokens'],
        help="限制AI响应的长度"
    )

    col3, col4 = st.columns(2)
    is_active = col3.checkbox("启用", value=selected_config['is_active'])
    is_default = col4.checkbox("设为默认", value=selected_config['is_default'])

    description = st.text_area(
        "配置说明",
        value=selected_config['description'] or '',
        height=100
    )

    # 保存按钮
    if st.button("保存配置"):
        config_data = {
            'config_name': config_name,
            'prompt_template': prompt_template,
            'system_message': system_message,
            'temperature': temperature,
            'max_tokens': max_tokens,
            'is_active': is_active,
            'is_default': is_default,
            'description': description
        }

        result = analyzer.save_prompt_config(
            config_data,
            config_id=selected_config['config_id']
        )

        if result['success']:
            st.success(result['message'])
            st.rerun()
        else:
            st.error(result['message'])


def render_list_tab(analyzer: RedditAnalyzer):
    """渲染板块列表选项卡"""
    st.header("板块列表")

    # 筛选器
    col1, col2, col3 = st.columns(3)

    with col1:
        status_filter = st.multiselect(
            "分析状态",
            ['pending', 'processing', 'completed', 'failed', 'skipped'],
            default=['completed']
        )

    with col2:
        # 获取所有标签
        all_tags = analyzer.get_all_tags()
        tag_filter = st.multiselect("标签筛选", all_tags)

    with col3:
        score_range = st.slider("重要性评分", 1, 5, (1, 5))

    # 排序
    sort_by = st.selectbox(
        "排序方式",
        ['created_at', 'subscribers', 'importance_score'],
        format_func=lambda x: {
            'created_at': '创建时间',
            'subscribers': '订阅人数',
            'importance_score': '重要性评分'
        }[x]
    )

    # 查询数据
    filters = {
        'status': status_filter,
        'tags': tag_filter,
        'importance_score_min': score_range[0],
        'importance_score_max': score_range[1]
    }

    result = analyzer.query_subreddits(
        filters=filters,
        sort_by=sort_by,
        sort_order='desc',
        limit=100
    )

    if not result['success']:
        st.error(result['message'])
        return

    total = result['data']['total']
    data = result['data']['data']

    st.info(f"共找到 {total} 条记录，显示前 {len(data)} 条")

    if not data:
        st.warning("没有符合条件的数据")
        return

    # 转换为DataFrame
    df = pd.DataFrame(data)

    # 选择要显示的列
    display_columns = [
        'subreddit_id', 'name', 'subscribers',
        'tag1', 'tag2', 'tag3',
        'importance_score', 'ai_analysis_status'
    ]

    df_display = df[display_columns].copy()

    # 数据表格（可编辑）
    edited_df = st.data_editor(
        df_display,
        column_config={
            "subreddit_id": st.column_config.NumberColumn("ID", disabled=True),
            "name": st.column_config.TextColumn("板块名称", disabled=True),
            "subscribers": st.column_config.NumberColumn("订阅数", disabled=True),
            "tag1": st.column_config.TextColumn("标签1"),
            "tag2": st.column_config.TextColumn("标签2"),
            "tag3": st.column_config.TextColumn("标签3"),
            "importance_score": st.column_config.NumberColumn(
                "评分",
                min_value=1,
                max_value=5
            ),
            "ai_analysis_status": st.column_config.SelectboxColumn(
                "状态",
                options=['pending', 'completed', 'failed', 'skipped']
            )
        },
        hide_index=True,
        use_container_width=True,
        num_rows="fixed"
    )

    # 操作按钮
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("批量分析"):
            # 获取pending状态的板块
            pending_ids = df[df['ai_analysis_status'] == 'pending']['subreddit_id'].tolist()

            if not pending_ids:
                st.warning("没有待分析的板块")
            else:
                with st.spinner(f"正在分析 {len(pending_ids)} 个板块..."):
                    result = analyzer.analyze_subreddits(
                        subreddit_ids=pending_ids,
                        batch_size=10
                    )

                    if result['success']:
                        st.success(result['message'])
                        st.rerun()
                    else:
                        st.error(result['message'])

    with col2:
        if st.button("保存修改"):
            st.info("保存功能开发中...")

    with col3:
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            "导出CSV",
            data=csv,
            file_name=f"reddit_subreddits_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )


def render_tags_tab(analyzer: RedditAnalyzer):
    """渲染标签管理选项卡"""
    st.header("标签管理")

    # 标签统计
    tag_stats_result = analyzer.get_tag_statistics()

    if not tag_stats_result['success']:
        st.error(tag_stats_result['message'])
        return

    tag_counts = tag_stats_result['data']['tag_counts']

    if not tag_counts:
        st.warning("还没有标签数据")
        return

    st.subheader("标签统计")

    # 标签云（使用columns显示）
    sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)

    # 显示前20个标签
    for i in range(0, min(20, len(sorted_tags)), 4):
        cols = st.columns(4)
        for j, (tag, count) in enumerate(sorted_tags[i:i+4]):
            cols[j].metric(tag, count)

    # 按标签查看板块
    st.subheader("按标签查看板块")

    selected_tag = st.selectbox(
        "选择标签",
        [t[0] for t in sorted_tags]
    )

    if selected_tag:
        result = analyzer.query_subreddits(
            filters={'tags': [selected_tag]},
            limit=100
        )

        if result['success']:
            data = result['data']['data']
            if data:
                df = pd.DataFrame(data)
                st.dataframe(
                    df[['name', 'subscribers', 'tag1', 'tag2', 'tag3', 'importance_score']],
                    use_container_width=True
                )
            else:
                st.info("该标签下没有板块")


def render_export_tab(analyzer: RedditAnalyzer):
    """渲染数据导出选项卡"""
    st.header("数据导出")

    # 导出格式
    export_format = st.radio("导出格式", ['CSV', 'Excel'])

    # 筛选条件
    st.subheader("筛选条件")

    export_status = st.multiselect(
        "状态",
        ['pending', 'completed', 'failed', 'skipped'],
        default=['completed']
    )

    all_tags = analyzer.get_all_tags()
    export_tags = st.multiselect("标签", all_tags)

    # 导出按钮
    if st.button("生成导出文件", type="primary"):
        filters = {
            'status': export_status,
            'tags': export_tags
        }

        with st.spinner("正在生成导出文件..."):
            result = analyzer.export_to_csv(
                filters=filters
            )

            if result['success']:
                st.success(result['message'])

                # 读取文件并提供下载
                file_path = result['data']['file_path']
                with open(file_path, 'rb') as f:
                    file_data = f.read()

                st.download_button(
                    "下载CSV文件",
                    data=file_data,
                    file_name=f"reddit_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            else:
                st.error(result['message'])


# ==================== 便捷导入 ====================
__all__ = ['render']

"""
Phase 5: 需求生成页面
"""
import streamlit as st
import subprocess
import sys
from pathlib import Path
import pandas as pd

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from storage.repository import ClusterMetaRepository, DemandRepository


def render():
    st.markdown('<div class="main-header">📊 Phase 5: 需求生成</div>', unsafe_allow_html=True)

    st.markdown("""
    ### 功能说明

    对选中的大组进行小组聚类，并使用LLM生成需求卡片初稿。

    **流程**:
    1. 加载选中大组的所有短语
    2. 执行小组聚类（Level B）
    3. 对每个小组调用LLM生成需求卡片
    4. 保存到数据库和导出CSV

    **输出**: 20-50个需求卡片初稿
    """)

    st.markdown("---")

    # 显示当前状态
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📊 当前状态")

        try:
            with ClusterMetaRepository() as cluster_repo:
                selected_A = cluster_repo.get_selected_clusters('A')
                clusters_B = cluster_repo.get_all_clusters('B')

                st.metric("选中大组", len(selected_A))
                st.metric("已有小组", len(clusters_B))

                if selected_A:
                    total_phrases = sum(c.size for c in selected_A)
                    st.text(f"总短语数: {total_phrases:,}")

            with DemandRepository() as demand_repo:
                from storage.models import Demand
                all_demands = demand_repo.session.query(Demand).all()
                st.metric("需求卡片", len(all_demands))

                if all_demands:
                    by_status = {}
                    for d in all_demands:
                        by_status[d.status] = by_status.get(d.status, 0) + 1

                    st.markdown("**按状态分布:**")
                    for status, count in by_status.items():
                        st.text(f"  {status}: {count}")

        except Exception as e:
            st.error(f"无法获取状态: {str(e)}")

    with col2:
        st.markdown("### ⚙️ 聚类参数")

        min_cluster_size_B = st.slider(
            "小组最小大小",
            min_value=3,
            max_value=20,
            value=5,
            help="小组聚类的最小大小"
        )

        min_samples_B = st.slider(
            "小组最小样本数",
            min_value=1,
            max_value=5,
            value=2,
            help="小组聚类的最小样本数"
        )

        st.markdown("### 🧪 高级选项")

        # 框架模式开关（推荐启用）
        use_framework = st.checkbox(
            "🔥 启用框架模式（推荐）",
            value=True,
            help="使用Phase 5提取的Token框架指导需求生成，提升30-50%质量。需先运行Phase 5。"
        )

        if use_framework:
            st.info("ℹ️ 框架模式已启用，将利用intent/action/object tokens指导LLM生成更准确的需求卡片")

        skip_llm = st.checkbox(
            "跳过LLM（仅聚类）",
            value=False,
            help="仅执行聚类，不生成需求卡片"
        )

        use_test_limit = st.checkbox("限制处理大组数", value=False)

        test_limit = 0
        if use_test_limit:
            test_limit = st.number_input(
                "最多处理N个大组",
                min_value=1,
                max_value=50,
                value=2,
                help="用于测试，仅处理前N个选中的大组"
            )

    st.markdown("---")

    # 预期结果提示
    st.markdown("### 🎯 预期结果")

    try:
        with ClusterMetaRepository() as cluster_repo:
            selected_A = cluster_repo.get_selected_clusters('A')

            if selected_A:
                process_count = min(len(selected_A), test_limit) if test_limit > 0 else len(selected_A)
                avg_phrases = sum(c.size for c in selected_A) // len(selected_A)

                # 使用实际的滑块值估算
                estimated_B_per_A = avg_phrases // min_cluster_size_B
                estimated_B_total = estimated_B_per_A * process_count

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.info(f"**处理大组**: {process_count}")
                with col2:
                    st.info(f"**预计小组**: {estimated_B_total}")
                with col3:
                    st.info(f"**预计需求**: {estimated_B_total}")

                if not skip_llm:
                    estimated_cost = estimated_B_total * 0.003  # 估算每个需求$0.003
                    st.warning(f"💰 预计API成本: ${estimated_cost:.2f} (OpenAI GPT-4o-mini)")
            else:
                st.warning("⚠️ 未选中任何大组，请先完成 Phase 3 筛选")

    except Exception as e:
        st.error(f"无法估算: {str(e)}")

    st.markdown("---")

    # 操作按钮
    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        start_button = st.button("🚀 开始生成", type="primary", use_container_width=True)

    with col2:
        if st.button("🔄 刷新状态", use_container_width=True):
            st.rerun()

    # 执行Phase 4
    if start_button:
        try:
            with ClusterMetaRepository() as cluster_repo:
                selected_A = cluster_repo.get_selected_clusters('A')

                if not selected_A:
                    st.error("❌ 未选中任何大组，请先完成 Phase 3")
                    return
        except Exception as e:
            st.error(f"❌ 检查失败: {str(e)}")
            return

        st.markdown("### 📝 执行日志")

        # 构建命令
        script_path = project_root / "scripts" / "run_phase4_demands.py"

        cmd = [
            sys.executable,
            str(script_path),
            f"--min-cluster-size={min_cluster_size_B}",
            f"--min-samples={min_samples_B}"
        ]

        if skip_llm:
            cmd.append("--skip-llm")

        if use_framework:
            cmd.append("--use-framework")

        if use_test_limit:
            cmd.append(f"--test-limit={test_limit}")

        # 显示命令
        st.code(" ".join(cmd), language="bash")

        # 执行
        with st.spinner("正在执行，这可能需要几分钟..."):
            try:
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                    encoding='utf-8',  # 强制使用UTF-8编码
                    errors='replace'   # 遇到无法解码的字符替换为?
                )

                # 创建日志输出区域
                log_container = st.empty()
                log_lines = []

                # 实时读取输出
                for line in process.stdout:
                    log_lines.append(line.strip())
                    log_container.text_area(
                        "输出日志",
                        "\n".join(log_lines[-50:]),
                        height=400
                    )

                process.wait()

                if process.returncode == 0:
                    st.success("✅ Phase 4 完成！")
                    st.balloons()

                    # 显示结果统计
                    with ClusterMetaRepository() as cluster_repo:
                        clusters_B = cluster_repo.get_all_clusters('B')
                        st.metric("生成小组数", len(clusters_B))

                    with DemandRepository() as demand_repo:
                        from storage.models import Demand
                        demands = demand_repo.session.query(Demand).all()
                        st.metric("需求卡片数", len(demands))

                    # 检查输出文件
                    output_file = project_root / "data" / "output" / "demands_draft.csv"
                    if output_file.exists():
                        st.info(f"📄 需求CSV: {output_file}")
                        st.markdown("**下一步**: 打开CSV进行人工审核")
                else:
                    st.error(f"❌ 执行失败，退出代码: {process.returncode}")

            except Exception as e:
                st.error(f"❌ 执行出错: {str(e)}")

    st.markdown("---")

    # 查看已生成的需求
    st.markdown("## 📋 已生成的需求卡片")

    try:
        with DemandRepository() as demand_repo:
            from storage.models import Demand
            demands = demand_repo.session.query(Demand).all()

            if demands:
                st.markdown(f"**找到 {len(demands)} 个需求卡片**")

                # 显示需求表格
                demand_data = []
                for d in demands:
                    demand_data.append({
                        "ID": d.demand_id,
                        "标题": d.title[:50] + "..." if d.title and len(d.title) > 50 else d.title,
                        "类型": d.demand_type,
                        "商业价值": d.business_value or "unknown",
                        "状态": d.status,
                        "来源大组": d.source_cluster_A,
                        "来源小组": d.source_cluster_B
                    })

                df = pd.DataFrame(demand_data)

                # 筛选器
                col1, col2, col3 = st.columns(3)

                with col1:
                    type_filter = st.multiselect(
                        "按类型筛选",
                        options=["全部"] + list(df["类型"].unique()),
                        default=["全部"]
                    )

                with col2:
                    value_filter = st.multiselect(
                        "按商业价值筛选",
                        options=["全部", "high", "medium", "low", "unknown"],
                        default=["全部"]
                    )

                with col3:
                    status_filter = st.multiselect(
                        "按状态筛选",
                        options=["全部"] + list(df["状态"].unique()),
                        default=["全部"]
                    )

                # 应用筛选
                filtered_df = df.copy()

                if "全部" not in type_filter:
                    filtered_df = filtered_df[filtered_df["类型"].isin(type_filter)]

                if "全部" not in value_filter:
                    filtered_df = filtered_df[filtered_df["商业价值"].isin(value_filter)]

                if "全部" not in status_filter:
                    filtered_df = filtered_df[filtered_df["状态"].isin(status_filter)]

                # 显示表格
                st.dataframe(
                    filtered_df,
                    use_container_width=True,
                    height=400
                )

                # 查看详情
                st.markdown("### 🔍 查看需求详情")

                demand_id = st.number_input(
                    "输入需求ID查看详情",
                    min_value=1,
                    value=1,
                    step=1
                )

                if st.button("查看详情"):
                    demand = demand_repo.session.query(Demand).filter(
                        Demand.demand_id == demand_id
                    ).first()

                    if demand:
                        st.markdown(f"### {demand.title}")
                        st.markdown(f"**类型**: {demand.demand_type}")
                        st.markdown(f"**商业价值**: {demand.business_value}")
                        st.markdown(f"**状态**: {demand.status}")
                        st.markdown("---")
                        st.markdown(f"**描述**: {demand.description}")
                        st.markdown("---")
                        st.markdown(f"**用户场景**: {demand.user_scenario}")
                        st.markdown("---")
                        st.markdown(f"**来源**: 大组 {demand.source_cluster_A} → 小组 {demand.source_cluster_B}")
                    else:
                        st.warning(f"⚠️ 未找到需求ID: {demand_id}")

            else:
                st.info("ℹ️ 还没有生成需求卡片，请先运行 Phase 4")

    except Exception as e:
        st.error(f"❌ 加载需求失败: {str(e)}")

    # 使用说明
    with st.expander("📖 使用说明"):
        st.markdown("""
        ### Phase 4 流程

        1. **小组聚类**: 对每个选中大组内的短语再次聚类
        2. **LLM生成**: 对每个小组调用LLM生成需求卡片
        3. **保存结果**: 更新数据库和导出CSV

        ### 参数说明

        **小组最小大小** (min_cluster_size):
        - 默认: 5
        - 增大 → 更少、更大的小组
        - 减小 → 更多、更小的小组

        **跳过LLM**:
        - 勾选后仅执行聚类，不调用LLM
        - 用于测试聚类效果
        - 成本: $0

        ### 人工审核

        1. 打开 `data/output/demands_draft.csv`
        2. 检查并修改：
           - title（标题）
           - description（描述）
           - user_scenario（用户场景）
           - demand_type（类型）
           - business_value（商业价值: high/medium/low）
           - status（validated/archived）
        3. 🔒 **不要修改**: demand_id, source_cluster_A, source_cluster_B

        ### 输出文件

        - `data/output/demands_draft.csv` - 需求卡片CSV
        - `data/output/phase4_demands_report.txt` - 统计报告
        """)

    # 故障排查
    with st.expander("🔧 故障排查"):
        st.markdown("""
        ### 常见问题

        **Q: 未选中任何大组**
        - 前往 Phase 3 完成聚类筛选
        - 确认至少选中了1个大组

        **Q: 生成的需求数量为0**
        - 检查是否勾选了"跳过LLM"
        - 如果勾选，需求卡片不会生成（仅聚类）
        - 取消勾选后重新运行

        **Q: API调用失败**
        - 检查 config/settings.py 中的LLM配置
        - 确认API密钥正确
        - 确认API配额充足

        **Q: 小组数量太多/太少**
        - 调整"小组最小大小"参数
        - 太多（>15个/大组）→ 增大到8-10
        - 太少（<3个/大组）→ 减小到3-4

        **Q: 需求质量不高**
        - AI生成的需求需要人工审核
        - 在CSV中修改不满意的需求
        - 考虑调整Prompt（在 ai/prompts.py）
        """)

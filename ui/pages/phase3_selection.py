"""
Phase 3: 聚类筛选页面
"""
import streamlit as st
import subprocess
import sys
from pathlib import Path
import pandas as pd
import json

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from storage.repository import ClusterMetaRepository
from core.intent_classification import IntentClassifier


def render():
    st.markdown('<div class="main-header">✅ Phase 3: 聚类筛选</div>', unsafe_allow_html=True)

    st.markdown("""
    ### 功能说明

    对Phase 2生成的大组进行人工筛选，选出有价值的聚类进行后续处理。

    **流程**:
    1. 导出大组聚类报告（CSV + HTML）
    2. 人工打分（1-5分，4-5分为选中）
    3. 导入选择结果到数据库

    **目标**: 选出10-15个高价值大组
    """)

    st.markdown("---")

    # 显示当前聚类状态
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📊 聚类状态")

        try:
            with ClusterMetaRepository() as repo:
                clusters_A = repo.get_all_clusters('A')
                selected_clusters = repo.get_selected_clusters('A')

                st.metric("大组总数", len(clusters_A))
                st.metric("已选中", len(selected_clusters))
                st.metric("未选中", len(clusters_A) - len(selected_clusters))

                if clusters_A:
                    sizes = [c.size for c in clusters_A]
                    st.text(f"平均大小: {sum(sizes)//len(sizes):,}")
                    st.text(f"总覆盖短语: {sum(sizes):,}")

        except Exception as e:
            st.error(f"无法获取聚类状态: {str(e)}")

    with col2:
        st.markdown("### 🎯 质量评分统计")

        try:
            with ClusterMetaRepository() as repo:
                clusters_A = repo.get_all_clusters('A')

                # 统计质量等级分布
                quality_counts = {'excellent': 0, 'good': 0, 'fair': 0, 'poor': 0}
                scored_count = 0
                total_score = 0

                for c in clusters_A:
                    if c.quality_level:
                        quality_counts[c.quality_level] += 1
                        scored_count += 1
                    if c.quality_score:
                        total_score += c.quality_score

                if scored_count > 0:
                    st.metric("已评分簇数", scored_count)
                    st.metric("平均质量分", f"{total_score/scored_count:.1f}/100")

                    st.markdown("**质量分布**:")
                    st.text(f"[★★★] Excellent: {quality_counts['excellent']}")
                    st.text(f"[★★ ] Good:      {quality_counts['good']}")
                    st.text(f"[★  ] Fair:      {quality_counts['fair']}")
                    st.text(f"[   ] Poor:      {quality_counts['poor']}")
                else:
                    st.info("尚未运行质量评分")
                    st.markdown("""
                    运行命令:
                    ```bash
                    python scripts/run_phase1_scoring.py --level A
                    ```
                    """)
        except Exception as e:
            st.warning(f"无法加载质量评分: {str(e)}")

    # 添加意图分析统计
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🎯 意图分析统计")

        try:
            with ClusterMetaRepository() as repo:
                clusters_A = repo.get_all_clusters('A')

                # 统计意图分布
                intent_counts = {}
                intent_analyzed_count = 0
                balanced_count = 0

                classifier = IntentClassifier()

                for c in clusters_A:
                    if c.dominant_intent:
                        intent_counts[c.dominant_intent] = intent_counts.get(c.dominant_intent, 0) + 1
                        intent_analyzed_count += 1

                        if c.is_intent_balanced:
                            balanced_count += 1

                if intent_analyzed_count > 0:
                    st.metric("已分析簇数", intent_analyzed_count)
                    st.metric("意图均衡簇", f"{balanced_count} ({balanced_count/intent_analyzed_count*100:.1f}%)")

                    st.markdown("**意图分布**:")
                    for intent, count in sorted(intent_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
                        label = classifier.get_intent_label(intent)
                        st.text(f"{label:12s}: {count:3d} ({count/intent_analyzed_count*100:.1f}%)")
                else:
                    st.info("尚未运行意图分析")
                    st.markdown("""
                    运行命令:
                    ```bash
                    python scripts/run_phase3_intent_analysis.py --level A
                    ```
                    """)
        except Exception as e:
            st.warning(f"无法加载意图分析: {str(e)}")

    with col2:
        st.markdown("### 📈 意图分析建议")

        st.markdown("""
        **基于Phase 0测量结果**:

        - find_tool占比11.6%（分散模式）
        - 建议采用**均衡策略**
        - 不过度聚焦单一意图

        **意图均衡簇特点**:
        - 包含多种用户意图
        - 适合多维度分析
        - 商业价值更全面

        **使用建议**:
        - 关注意图均衡的簇
        - 提供多元化的解决方案
        """)

    st.markdown("---")

    # 步骤1: 导出报告
    st.markdown("## 步骤1: 导出聚类报告")

    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        export_button = st.button("📤 导出报告", type="primary", use_container_width=True)

    with col2:
        use_llm = st.checkbox("使用LLM生成主题标签", value=True)

    if export_button:
        st.markdown("### 📝 执行日志")

        script_path = project_root / "scripts" / "run_phase3_selection.py"

        cmd = [sys.executable, str(script_path)]

        if not use_llm:
            cmd.append("--skip-llm")

        st.code(" ".join(cmd), language="bash")

        with st.spinner("正在生成报告..."):
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

                log_container = st.empty()
                log_lines = []

                for line in process.stdout:
                    log_lines.append(line.strip())
                    log_container.text_area("输出日志", "\n".join(log_lines[-30:]), height=300)

                process.wait()

                if process.returncode == 0:
                    st.success("✅ 报告生成完成！")

                    output_dir = project_root / "data" / "output"
                    csv_file = output_dir / "clusters_levelA.csv"
                    html_file = output_dir / "cluster_selection_report.html"

                    if csv_file.exists():
                        st.info(f"📄 CSV报告: {csv_file}")

                    if html_file.exists():
                        st.info(f"🌐 HTML报告: {html_file}")

                    st.markdown("**下一步**: 打开CSV文件进行人工打分")
                else:
                    st.error(f"❌ 报告生成失败，退出代码: {process.returncode}")

            except Exception as e:
                st.error(f"❌ 执行出错: {str(e)}")

    st.markdown("---")

    # 步骤1.5: 导出HTML用于翻译
    st.markdown("## 步骤1.5: 导出HTML用于翻译")

    st.markdown("""
    💡 **如果您需要翻译英文短语**，可以导出为HTML，然后在浏览器中翻译查看。
    """)

    col1, col2 = st.columns([1, 3])

    with col1:
        export_html_button = st.button("🌐 导出为HTML（可翻译）", type="secondary", use_container_width=True)

    if export_html_button:
        try:
            with ClusterMetaRepository() as repo:
                clusters_A = repo.get_all_clusters('A')

                if not clusters_A:
                    st.warning("⚠️ 未找到聚类数据")
                else:
                    # 生成HTML内容
                    html_rows = []
                    for c in clusters_A:
                        selected_mark = "✅ 已选中" if c.is_selected else "❌ 未选中"
                        html_rows.append(f"""
                        <tr>
                            <td>{c.cluster_id}</td>
                            <td>{c.size}</td>
                            <td>{c.main_theme or '(未生成)'}</td>
                            <td>{c.example_phrases}</td>
                            <td>{selected_mark}</td>
                            <td>{c.selection_score or 0}</td>
                        </tr>
                        """)

                    html_content = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <title>聚类筛选 - 可翻译版本</title>
                        <style>
                            body {{ font-family: Arial, sans-serif; margin: 20px; }}
                            h1 {{ color: #333; }}
                            table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
                            th {{ background-color: #4CAF50; color: white; padding: 12px; text-align: left; position: sticky; top: 0; }}
                            td {{ border: 1px solid #ddd; padding: 8px; }}
                            tr:nth-child(even) {{ background-color: #f2f2f2; }}
                            tr:hover {{ background-color: #ddd; }}
                            .tip {{ background-color: #fff3cd; padding: 15px; border-left: 6px solid #ffc107; margin-bottom: 20px; }}
                        </style>
                    </head>
                    <body>
                        <h1>Phase 3: 聚类筛选报告</h1>
                        <div class="tip">
                            <strong>💡 如何翻译：</strong>
                            <ol>
                                <li>右键点击页面</li>
                                <li>选择"翻译为中文"（Chrome/Edge浏览器）</li>
                                <li>所有英文短语会自动翻译！</li>
                            </ol>
                            <p><strong>查看完后，返回Web UI进行在线筛选</strong></p>
                        </div>
                        <table>
                            <thead>
                                <tr>
                                    <th>Cluster ID</th>
                                    <th>Size</th>
                                    <th>Main Theme</th>
                                    <th>Example Phrases</th>
                                    <th>Status</th>
                                    <th>Score</th>
                                </tr>
                            </thead>
                            <tbody>
                                {''.join(html_rows)}
                            </tbody>
                        </table>
                    </body>
                    </html>
                    """

                    # 保存HTML文件
                    output_dir = project_root / "data" / "output"
                    output_dir.mkdir(exist_ok=True)
                    html_file = output_dir / "clusters_for_translation.html"

                    with open(html_file, 'w', encoding='utf-8') as f:
                        f.write(html_content)

                    st.success(f"✅ HTML文件已生成！")

                    # 添加下载按钮
                    st.download_button(
                        label="📥 下载并打开HTML文件",
                        data=html_content,
                        file_name="clusters_for_translation.html",
                        mime="text/html",
                        use_container_width=True,
                        type="primary"
                    )

                    st.info(f"📂 文件也已保存到: {html_file}")
                    st.markdown("""
                    **下一步：**
                    1. 点击上方"📥 下载并打开HTML文件"按钮
                    2. 在浏览器中打开下载的文件
                    3. 右键 → 翻译为中文
                    4. 查看并记录想要选中的cluster_id
                    5. 返回Web UI，在下方"在线筛选"部分输入cluster_id
                    """)

        except Exception as e:
            st.error(f"❌ 导出失败: {str(e)}")

    st.markdown("---")

    # 步骤2: 查看和编辑报告
    st.markdown("## 步骤2: 在线查看和筛选")

    try:
        with ClusterMetaRepository() as repo:
            clusters_A = repo.get_all_clusters('A')

            if clusters_A:
                st.markdown(f"**找到 {len(clusters_A)} 个大组聚类**")

                # 显示推荐的高分簇
                st.markdown("### ⭐ 推荐关注的聚类（Top 10）")

                scored_clusters = [c for c in clusters_A if c.quality_score is not None]
                if scored_clusters:
                    # 按质量分排序，取前10个
                    top_clusters = sorted(scored_clusters, key=lambda x: x.quality_score, reverse=True)[:10]

                    top_data = []
                    for rank, c in enumerate(top_clusters, 1):
                        quality_mark = {
                            'excellent': '[★★★]',
                            'good': '[★★ ]',
                            'fair': '[★  ]',
                            'poor': '[   ]'
                        }.get(c.quality_level, '[???]')

                        top_data.append({
                            "排名": rank,
                            "ID": c.cluster_id,
                            "质量": quality_mark,
                            "评分": f"{c.quality_score}/100",
                            "大小": c.size,
                            "主题": c.main_theme or "(未生成)",
                            "已选": "✅" if c.is_selected else "❌"
                        })

                    st.dataframe(pd.DataFrame(top_data), use_container_width=True, height=300)

                    st.markdown("""
                    💡 **建议**: 上述聚类自动评分较高，建议优先审核。您可以直接在下方"快速操作"中输入ID进行选中。
                    """)
                else:
                    st.info("尚未进行质量评分，运行 `python scripts/run_phase1_scoring.py --level A` 进行自动评分")

                st.markdown("---")

                # 显示聚类表格
                cluster_data = []
                classifier = IntentClassifier()

                for c in clusters_A:
                    quality_mark = ""
                    quality_score_str = "-"

                    if c.quality_level:
                        quality_mark = {
                            'excellent': '[★★★]',
                            'good': '[★★ ]',
                            'fair': '[★  ]',
                            'poor': '[   ]'
                        }.get(c.quality_level, '[???]')

                    if c.quality_score is not None:
                        quality_score_str = f"{c.quality_score}"

                    # 意图信息
                    intent_label = "-"
                    intent_balanced = ""
                    if c.dominant_intent:
                        intent_label = classifier.get_intent_label(c.dominant_intent)
                        if c.is_intent_balanced:
                            intent_balanced = "✓均衡"

                    cluster_data.append({
                        "cluster_id": c.cluster_id,
                        "质量评级": quality_mark,
                        "质量分": quality_score_str,
                        "意图": intent_label,
                        "均衡": intent_balanced,
                        "大小": c.size,
                        "主题": c.main_theme or "(未生成)",
                        "示例短语": c.example_phrases[:100] + "..." if c.example_phrases and len(c.example_phrases) > 100 else c.example_phrases,
                        "已选中": "✅" if c.is_selected else "❌",
                        "打分": c.selection_score or 0
                    })

                df = pd.DataFrame(cluster_data)

                # 筛选器
                col1, col2, col3, col4, col5, col6 = st.columns(6)

                with col1:
                    size_filter = st.selectbox(
                        "按大小筛选",
                        ["全部", "大型(>100)", "中型(50-100)", "小型(<50)"]
                    )

                with col2:
                    status_filter = st.selectbox(
                        "按状态筛选",
                        ["全部", "已选中", "未选中"]
                    )

                with col3:
                    quality_filter = st.selectbox(
                        "按质量筛选",
                        ["全部", "Excellent", "Good", "Fair", "Poor", "未评分"]
                    )

                with col4:
                    intent_filter = st.selectbox(
                        "按意图筛选",
                        ["全部", "寻找工具", "学习教程", "解决问题", "寻找免费资源", "比较选择", "其他意图", "未分析"]
                    )

                with col5:
                    balance_filter = st.selectbox(
                        "按均衡度筛选",
                        ["全部", "均衡", "非均衡"]
                    )

                with col6:
                    sort_by = st.selectbox(
                        "排序方式",
                        ["按质量分降序", "按大小降序", "按cluster_id", "按打分降序", "按意图置信度降序"]
                    )

                # 应用筛选
                filtered_df = df.copy()

                if size_filter == "大型(>100)":
                    filtered_df = filtered_df[filtered_df["大小"] > 100]
                elif size_filter == "中型(50-100)":
                    filtered_df = filtered_df[(filtered_df["大小"] >= 50) & (filtered_df["大小"] <= 100)]
                elif size_filter == "小型(<50)":
                    filtered_df = filtered_df[filtered_df["大小"] < 50]

                if status_filter == "已选中":
                    filtered_df = filtered_df[filtered_df["已选中"] == "✅"]
                elif status_filter == "未选中":
                    filtered_df = filtered_df[filtered_df["已选中"] == "❌"]

                if quality_filter == "Excellent":
                    filtered_df = filtered_df[filtered_df["质量评级"] == "[★★★]"]
                elif quality_filter == "Good":
                    filtered_df = filtered_df[filtered_df["质量评级"] == "[★★ ]"]
                elif quality_filter == "Fair":
                    filtered_df = filtered_df[filtered_df["质量评级"] == "[★  ]"]
                elif quality_filter == "Poor":
                    filtered_df = filtered_df[filtered_df["质量评级"] == "[   ]"]
                elif quality_filter == "未评分":
                    filtered_df = filtered_df[filtered_df["质量评级"] == ""]

                if intent_filter != "全部":
                    if intent_filter == "未分析":
                        filtered_df = filtered_df[filtered_df["意图"] == "-"]
                    else:
                        filtered_df = filtered_df[filtered_df["意图"] == intent_filter]

                if balance_filter == "均衡":
                    filtered_df = filtered_df[filtered_df["均衡"] == "✓均衡"]
                elif balance_filter == "非均衡":
                    filtered_df = filtered_df[filtered_df["均衡"] == ""]

                if sort_by == "按质量分降序":
                    # 将质量分转为数字排序
                    filtered_df['_sort_quality'] = filtered_df["质量分"].apply(lambda x: int(x) if x != "-" else -1)
                    filtered_df = filtered_df.sort_values("_sort_quality", ascending=False)
                    filtered_df = filtered_df.drop(columns=['_sort_quality'])
                elif sort_by == "按大小降序":
                    filtered_df = filtered_df.sort_values("大小", ascending=False)
                elif sort_by == "按cluster_id":
                    filtered_df = filtered_df.sort_values("cluster_id")
                elif sort_by == "按打分降序":
                    filtered_df = filtered_df.sort_values("打分", ascending=False)
                elif sort_by == "按意图置信度降序":
                    # 需要添加意图置信度列用于排序
                    # 先创建一个临时列存储置信度数据
                    intent_confidence_map = {}
                    for c in clusters_A:
                        if c.dominant_intent_confidence:
                            intent_confidence_map[c.cluster_id] = c.dominant_intent_confidence
                        else:
                            intent_confidence_map[c.cluster_id] = 0

                    filtered_df['_intent_confidence'] = filtered_df["cluster_id"].apply(lambda x: intent_confidence_map.get(x, 0))
                    filtered_df = filtered_df.sort_values("_intent_confidence", ascending=False)
                    filtered_df = filtered_df.drop(columns=['_intent_confidence'])

                # 显示表格
                st.dataframe(
                    filtered_df,
                    use_container_width=True,
                    height=400
                )

                # 快速操作
                st.markdown("### 🎯 快速操作")

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**选中聚类**")
                    select_ids = st.text_area(
                        "输入要选中的cluster_id（支持逗号、换行、空格分隔）",
                        placeholder="例如:\n1174\n1244\n1269\n或: 1174,1244,1269\n或: 1174 1244 1269",
                        height=150
                    )

                    if st.button("✅ 标记为选中", use_container_width=True):
                        if select_ids:
                            # 支持多种分隔符：换行、逗号、空格
                            import re
                            ids_text = re.split(r'[,\s\n]+', select_ids.strip())
                            ids = [int(x.strip()) for x in ids_text if x.strip()]
                            try:
                                with ClusterMetaRepository() as repo:
                                    for cid in ids:
                                        repo.update_selection(cid, 'A', True, 5)
                                st.success(f"已选中 {len(ids)} 个聚类")
                                st.rerun()
                            except Exception as e:
                                st.error(f"更新失败: {str(e)}")

                with col2:
                    st.markdown("**取消选中**")
                    deselect_ids = st.text_area(
                        "输入要取消的cluster_id（支持逗号、换行、空格分隔）",
                        placeholder="例如:\n2\n4\n6\n或: 2,4,6\n或: 2 4 6",
                        height=150
                    )

                    if st.button("❌ 取消选中", use_container_width=True):
                        if deselect_ids:
                            # 支持多种分隔符：换行、逗号、空格
                            import re
                            ids_text = re.split(r'[,\s\n]+', deselect_ids.strip())
                            ids = [int(x.strip()) for x in ids_text if x.strip()]
                            try:
                                with ClusterMetaRepository() as repo:
                                    for cid in ids:
                                        repo.update_selection(cid, 'A', False, 0)
                                st.success(f"已取消 {len(ids)} 个聚类")
                                st.rerun()
                            except Exception as e:
                                st.error(f"更新失败: {str(e)}")

            else:
                st.warning("⚠️ 未找到大组聚类，请先运行 Phase 2")

    except Exception as e:
        st.error(f"❌ 加载聚类数据失败: {str(e)}")

    st.markdown("---")

    # 步骤3: 导入选择结果（如果使用CSV编辑）
    st.markdown("## 步骤3: 从CSV导入选择结果（可选）")

    st.markdown("""
    如果您在CSV文件中编辑了 `is_selected` 和 `selection_score` 列，可以在此导入。
    """)

    col1, col2 = st.columns([2, 1])

    with col1:
        csv_path = st.text_input(
            "CSV文件路径",
            value="data/output/clusters_levelA.csv",
            help="相对于项目根目录的路径"
        )

    with col2:
        import_button = st.button("📥 导入CSV", type="secondary", use_container_width=True)

    if import_button:
        full_path = project_root / csv_path

        if not full_path.exists():
            st.error(f"❌ 文件不存在: {full_path}")
        else:
            script_path = project_root / "scripts" / "import_selection.py"

            cmd = [sys.executable, str(script_path), str(full_path)]

            st.code(" ".join(cmd), language="bash")

            with st.spinner("正在导入..."):
                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        check=True
                    )

                    st.success("✅ 导入完成！")
                    st.text(result.stdout)
                    st.rerun()

                except subprocess.CalledProcessError as e:
                    st.error(f"❌ 导入失败: {e.stderr}")

    # 使用说明
    with st.expander("📖 使用说明"):
        st.markdown("""
        ### 筛选流程

        **方法1: 在线筛选（推荐）**
        1. 在上方表格查看所有聚类
        2. 使用筛选器定位感兴趣的聚类
        3. 使用"快速操作"选中或取消聚类
        4. 直接更新到数据库

        **方法2: CSV编辑**
        1. 点击"导出报告"生成CSV
        2. 在Excel/CSV编辑器中打开文件
        3. 编辑 `is_selected` 列（TRUE/FALSE）
        4. 编辑 `selection_score` 列（1-5分）
        5. 保存后使用"导入CSV"

        ### 打分标准（1-5分）

        - **5分**: 非常值得做，商业价值高
        - **4分**: 值得做，有明确需求
        - **3分**: 可以考虑，需求模糊
        - **2分**: 价值不大
        - **1分**: 不值得做

        **选中规则**: 4-5分为选中，1-3分为不选中

        ### 输出文件

        - `data/output/clusters_levelA.csv` - 聚类报告CSV
        - `data/output/cluster_selection_report.html` - HTML可视化报告
        """)

    # 故障排查
    with st.expander("🔧 故障排查"):
        st.markdown("""
        ### 常见问题

        **Q: 报告中没有主题标签**
        - 需要勾选"使用LLM生成主题标签"
        - 确认LLM API配置正确
        - 或手动查看示例短语判断主题

        **Q: CSV导入失败**
        - 确认文件路径正确
        - 确认CSV格式未损坏（必须包含 cluster_id 列）
        - 确认 is_selected 列值为 TRUE/FALSE
        - 确认 selection_score 列为数字（1-5）

        **Q: 在线筛选不生效**
        - 点击"刷新"按钮重新加载数据
        - 确认cluster_id输入正确（数字，逗号分隔）
        - 检查数据库连接是否正常
        """)

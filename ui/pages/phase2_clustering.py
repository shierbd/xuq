"""
Phase 2: 大组聚类页面
"""
import streamlit as st
import subprocess
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from storage.repository import PhraseRepository, ClusterMetaRepository
from storage.models import Phrase


def render():
    st.markdown('<div class="main-header">🔄 Phase 2: 大组聚类</div>', unsafe_allow_html=True)

    st.markdown("""
    ### 功能说明

    使用HDBSCAN算法对所有短语进行语义聚类，生成60-100个大组。

    **算法**: HDBSCAN (Hierarchical Density-Based Spatial Clustering)
    **Embedding模型**: all-MiniLM-L6-v2 (384维)

    **输出**:
    - `phrases.cluster_id_A` 更新
    - `cluster_meta` 表填充（Level A）
    - Embedding缓存文件
    """)

    st.markdown("---")

    # 配置区域
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### ⚙️ 聚类参数")

        min_cluster_size = st.slider(
            "最小聚类大小 (min_cluster_size)",
            min_value=10,
            max_value=100,
            value=30,
            step=5,
            help="簇必须包含的最小短语数。增大此值会得到更少、更大的簇"
        )

        min_samples = st.slider(
            "最小样本数 (min_samples)",
            min_value=1,
            max_value=10,
            value=3,
            help="核心点的最小邻居数。增大此值会得到更紧密的簇"
        )

        st.markdown("### 💾 缓存选项")

        use_cache = st.checkbox(
            "使用Embedding缓存",
            value=True,
            help="如果存在缓存文件，直接加载而不重新计算"
        )

        force_recalculate = st.checkbox(
            "强制重新计算Embeddings",
            value=False,
            help="忽略缓存，重新计算所有Embeddings"
        )

        st.markdown("### 🧪 测试选项")

        use_test_limit = st.checkbox("使用测试限制", value=False)

        test_limit = 0
        if use_test_limit:
            test_limit = st.number_input(
                "测试短语数量",
                min_value=100,
                max_value=10000,
                value=1000,
                step=100
            )

    with col2:
        st.markdown("### 📊 当前状态")

        try:
            with PhraseRepository() as repo:
                stats = repo.get_statistics()
                total_phrases = stats.get('total_count', 0)
                st.metric("短语总数", f"{total_phrases:,}")

                # 计算未聚类的短语数
                unclustered = repo.session.query(Phrase).filter(
                    Phrase.cluster_id_A.is_(None)
                ).count()
                st.metric("未聚类短语", f"{unclustered:,}")

            with ClusterMetaRepository() as cluster_repo:
                clusters_A = cluster_repo.get_all_clusters('A')
                st.metric("已有大组数", len(clusters_A))

                if clusters_A:
                    st.markdown("**现有大组统计:**")
                    sizes = [c.size for c in clusters_A]
                    st.text(f"  平均大小: {sum(sizes)//len(sizes):,}")
                    st.text(f"  最大: {max(sizes):,}")
                    st.text(f"  最小: {min(sizes):,}")

            # 检查缓存文件
            cache_dir = project_root / "data" / "cache"
            cache_files = list(cache_dir.glob("embeddings_round*.npz")) if cache_dir.exists() else []

            st.markdown("**Embedding缓存:**")
            if cache_files:
                st.success(f"✅ 找到 {len(cache_files)} 个缓存文件")
                for cache_file in cache_files:
                    st.text(f"  {cache_file.name}")
            else:
                st.warning("⚠️ 无缓存文件，需要计算Embeddings")

        except Exception as e:
            st.error(f"无法获取状态: {str(e)}")

    st.markdown("---")

    # 参数预览
    st.markdown("### 🎯 当前配置预览")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.info(f"**最小聚类大小**: {min_cluster_size}")
    with col2:
        st.info(f"**最小样本数**: {min_samples}")
    with col3:
        st.info(f"**使用缓存**: {'是' if use_cache and not force_recalculate else '否'}")

    # 预期结果提示
    st.markdown("""
    **预期结果**:
    - 聚类太多（>100个）→ 增大 `min_cluster_size` 和 `min_samples`
    - 聚类太少（<40个）→ 减小 `min_cluster_size` 和 `min_samples`
    - 噪音点过多（>40%）→ 减小 `min_samples`
    """)

    st.markdown("---")

    # 操作按钮
    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        start_button = st.button("🚀 开始聚类", type="primary", use_container_width=True)

    with col2:
        if st.button("🔄 刷新状态", use_container_width=True):
            st.rerun()

    # 执行聚类
    if start_button:
        st.markdown("### 📝 执行日志")

        # 构建命令
        script_path = project_root / "scripts" / "run_phase2_clustering.py"

        cmd = [
            sys.executable,
            str(script_path),
            f"--min-cluster-size={min_cluster_size}",
            f"--min-samples={min_samples}"
        ]

        if use_cache and not force_recalculate:
            cmd.append("--use-cache")

        if force_recalculate:
            cmd.append("--force-recalculate")

        if use_test_limit:
            cmd.append(f"--test-limit={test_limit}")

        # 显示命令
        st.code(" ".join(cmd), language="bash")

        # 执行
        with st.spinner("正在执行聚类，这可能需要几分钟..."):
            try:
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
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
                    st.success("✅ Phase 2 聚类完成！")
                    st.balloons()

                    # 显示结果统计
                    with ClusterMetaRepository() as cluster_repo:
                        clusters_A = cluster_repo.get_all_clusters('A')
                        st.metric("生成大组数", len(clusters_A))

                        sizes = [c.size for c in clusters_A]
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("平均大小", f"{sum(sizes)//len(sizes):,}")
                        with col2:
                            st.metric("最大组", f"{max(sizes):,}")
                        with col3:
                            st.metric("最小组", f"{min(sizes):,}")

                    st.info("📊 下一步: 前往 Phase 3 进行人工筛选")
                else:
                    st.error(f"❌ 聚类失败，退出代码: {process.returncode}")

            except Exception as e:
                st.error(f"❌ 执行出错: {str(e)}")

    # 使用说明
    with st.expander("📖 使用说明"):
        st.markdown("""
        ### 聚类流程

        1. **加载数据**: 从数据库加载所有短语
        2. **计算Embeddings**: 使用Sentence Transformer模型（可缓存）
        3. **HDBSCAN聚类**: 基于密度的层次聚类
        4. **保存结果**: 更新数据库和生成CSV报告

        ### 参数调整建议

        **min_cluster_size** (最小聚类大小):
        - 默认: 30
        - 增大 → 更少、更大的簇（适合数据量大时）
        - 减小 → 更多、更小的簇（适合发现细粒度模式）

        **min_samples** (最小样本数):
        - 默认: 3
        - 增大 → 更紧密、更保守的簇（噪音点更多）
        - 减小 → 更松散、更激进的簇（噪音点更少）

        ### 性能优化

        - **首次运行**: 需要计算Embeddings，时间较长（5万条约需5-10分钟）
        - **后续运行**: 使用缓存，仅需聚类计算（5万条约需1-2分钟）
        - **测试模式**: 使用1000条数据快速验证参数效果

        ### 输出文件

        - `data/output/clusters_levelA.csv` - 大组聚类报告
        - `data/cache/embeddings_round1.npz` - Embeddings缓存
        """)

    # 故障排查
    with st.expander("🔧 故障排查"):
        st.markdown("""
        ### 常见问题

        **Q: 内存不足 (MemoryError)**
        - 使用测试限制先运行小数据量
        - 减小 `EMBEDDING_BATCH_SIZE`（在 config/settings.py）
        - 关闭其他占用内存的程序

        **Q: 聚类结果不理想**
        - 簇太多（>100）: 增大 min_cluster_size 到 40-50
        - 簇太少（<40）: 减小 min_cluster_size 到 20-25
        - 噪音点太多（>50%）: 减小 min_samples 到 2

        **Q: Embedding计算很慢**
        - 首次计算是正常的（一次性）
        - 确保勾选"使用Embedding缓存"
        - 考虑使用GPU加速（需安装torch-cuda）

        **Q: 缓存文件损坏**
        - 勾选"强制重新计算Embeddings"
        - 或手动删除 `data/cache/` 目录下的缓存文件
        """)

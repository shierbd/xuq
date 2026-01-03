"""
Phase 1: 数据导入页面
"""
import streamlit as st
import subprocess
import sys
from pathlib import Path
import threading
import time

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from storage.repository import PhraseRepository


def render():
    st.markdown('<div class="main-header">📥 Phase 1: 数据导入</div>', unsafe_allow_html=True)

    st.markdown("""
    ### 功能说明

    从原始CSV文件导入关键词数据到数据库。支持以下数据源：
    - SEMRUSH导出的CSV文件
    - 下拉词CSV文件
    - 相关搜索Excel文件

    **输出**: phrases表填充数据
    """)

    st.markdown("---")

    # 配置区域
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📁 数据源选择")

        data_sources = st.multiselect(
            "选择要导入的数据源",
            ["SEMRUSH", "下拉词", "相关搜索"],
            default=["SEMRUSH", "下拉词", "相关搜索"]
        )

        st.markdown("### ⚙️ 参数配置")

        round_id = st.number_input(
            "Round ID",
            min_value=1,
            value=1,
            help="数据轮次标识"
        )

        dry_run = st.checkbox(
            "试运行模式（不写入数据库）",
            value=False,
            help="勾选后只检查数据，不实际导入到数据库"
        )

    with col2:
        st.markdown("### 📊 当前数据库状态")

        try:
            with PhraseRepository() as repo:
                stats = repo.get_statistics()

                st.metric("短语总数", f"{stats.get('total_count', 0):,}")

                if stats.get('by_source'):
                    st.markdown("**按来源分布:**")
                    for source, count in stats['by_source'].items():
                        st.text(f"  {source}: {count:,}")

                if stats.get('by_status'):
                    st.markdown("**按状态分布:**")
                    for status, count in stats['by_status'].items():
                        st.text(f"  {status}: {count:,}")
        except Exception as e:
            st.error(f"无法获取数据库状态: {str(e)}")

    st.markdown("---")

    # 操作区域
    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        start_button = st.button("🚀 开始导入", type="primary", use_container_width=True)

    with col2:
        if st.button("🔄 刷新统计", use_container_width=True):
            st.rerun()

    with col3:
        st.markdown("")

    # 执行导入
    if start_button:
        if not data_sources:
            st.warning("请至少选择一个数据源")
        else:
            st.markdown("### 📝 执行日志")

            # 构建命令
            script_path = project_root / "scripts" / "run_phase1_import.py"

            cmd = [sys.executable, str(script_path), f"--round-id={round_id}"]

            # 数据源参数
            source_map = {
                "SEMRUSH": "semrush",
                "下拉词": "dropdown",
                "相关搜索": "related"
            }
            sources_arg = ",".join([source_map[s] for s in data_sources])
            cmd.append(f"--sources={sources_arg}")

            # 试运行模式
            if dry_run:
                cmd.append("--dry-run")

            # 显示命令
            st.code(" ".join(cmd), language="bash")

            # 执行
            with st.spinner("正在导入数据..."):
                try:
                    process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1,
                        universal_newlines=True,
                        encoding='utf-8',
                        errors='replace'  # 替换无法解码的字符，而不是报错
                    )

                    # 创建日志输出区域
                    log_container = st.empty()
                    log_lines = []

                    # 实时读取输出
                    for line in process.stdout:
                        log_lines.append(line.strip())
                        log_container.text_area(
                            "输出日志",
                            "\n".join(log_lines[-50:]),  # 只显示最后50行
                            height=400
                        )

                    process.wait()

                    if process.returncode == 0:
                        st.success("✅ Phase 1 导入完成！")
                        st.balloons()

                        # 显示更新后的统计
                        with PhraseRepository() as repo:
                            new_stats = repo.get_statistics()
                            st.metric("最终短语总数", f"{new_stats.get('total_count', 0):,}")
                    else:
                        st.error(f"❌ 导入失败，退出代码: {process.returncode}")

                except Exception as e:
                    st.error(f"❌ 执行出错: {str(e)}")

    # 使用说明
    with st.expander("📖 使用说明"):
        st.markdown("""
        ### 数据准备

        1. **SEMRUSH数据**:
           - 将CSV文件放到 `data/raw/semrush/` 目录
           - 文件应包含列: `Keyword`, `Search Volume`

        2. **下拉词数据**:
           - 将CSV文件放到 `data/raw/dropdown/` 目录
           - 文件应包含列: `keyword`

        3. **相关搜索数据**:
           - 将Excel文件放到 `data/raw/related_search/` 目录
           - 文件应包含列: `Related Search`

        ### 导入流程

        1. 系统会自动读取对应目录下的所有文件
        2. 对每个短语进行清理和去重
        3. 保存到 `phrases` 表（如非试运行模式）
        4. 标记 `first_seen_round` 和 `source_type`

        ### 注意事项

        - 重复导入会自动去重（基于短语文本）
        - **首次导入建议勾选"试运行模式"验证流程**
        - 大数据量导入可能需要几分钟时间
        - 试运行模式只检查数据格式，不写入数据库
        """)

    # 故障排查
    with st.expander("🔧 故障排查"):
        st.markdown("""
        ### 常见问题

        **Q: 找不到数据文件**
        - 确认文件已放到正确的目录
        - 检查文件扩展名（.csv 或 .xlsx）
        - 确保文件名不包含特殊字符

        **Q: 数据库连接失败**
        - 检查 `config/settings.py` 中的数据库配置
        - 确认MySQL服务正在运行
        - 验证用户名密码是否正确

        **Q: 导入速度很慢**
        - 大数据量导入是正常的（5万条约需2-3分钟）
        - 首次导入会建立索引，后续会更快
        - **可以先用"试运行模式"快速验证数据格式**

        **Q: 导入后数量不对**
        - 系统会自动去重，最终数量 < 原始文件总数是正常的
        - 检查日志中的"去重后记录数"统计

        **Q: 如何测试导入功能**
        - 勾选"试运行模式"，不会写入数据库
        - 查看日志确认数据格式正确后，取消勾选正式导入
        """)

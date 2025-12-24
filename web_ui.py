"""
词根聚类需求挖掘 - Web可视化界面
基于Streamlit的可视化操作平台，集成所有Phase操作

运行方式:
    streamlit run web_ui.py
"""
import streamlit as st
import sys
from pathlib import Path
import subprocess
import threading
import time
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from storage.repository import PhraseRepository, ClusterMetaRepository, DemandRepository, TokenRepository
from config.settings import LLM_PROVIDER, DATABASE_CONFIG


# ============================================================================
# 页面配置
# ============================================================================

st.set_page_config(
    page_title="词根聚类需求挖掘系统",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
        border-bottom: 3px solid #1f77b4;
        margin-bottom: 2rem;
    }
    .phase-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 5px solid #1f77b4;
    }
    .status-success {
        color: #28a745;
        font-weight: bold;
    }
    .status-running {
        color: #ffc107;
        font-weight: bold;
    }
    .status-error {
        color: #dc3545;
        font-weight: bold;
    }
    .metric-card {
        background-color: white;
        padding: 1rem;
        border-radius: 5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# 工具函数
# ============================================================================

def get_database_stats():
    """获取数据库统计信息"""
    try:
        from storage.models import Demand

        with PhraseRepository() as phrase_repo:
            phrase_stats = phrase_repo.get_statistics()

        with ClusterMetaRepository() as cluster_repo:
            clusters_A = cluster_repo.get_all_clusters('A')
            clusters_B = cluster_repo.get_all_clusters('B')
            selected_A = cluster_repo.get_selected_clusters('A')

        with DemandRepository() as demand_repo:
            all_demands = demand_repo.session.query(Demand).all()

        with TokenRepository() as token_repo:
            all_tokens = token_repo.get_all_tokens()

        return {
            'phrases_count': phrase_stats.get('total_count', 0),
            'clusters_A': len(clusters_A),
            'clusters_B': len(clusters_B),
            'selected_A': len(selected_A),
            'demands_count': len(all_demands),
            'tokens_count': len(all_tokens),
            'by_source': phrase_stats.get('by_source', {}),
            'by_status': phrase_stats.get('by_status', {}),
        }
    except Exception as e:
        st.error(f"获取数据库统计失败: {str(e)}")
        return None


def run_script_in_background(script_path, args=None):
    """在后台运行脚本"""
    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        universal_newlines=True
    )

    return process


# ============================================================================
# 侧边栏 - 导航和配置
# ============================================================================

with st.sidebar:
    st.markdown("## 🔍 系统导航")

    page = st.radio(
        "选择页面",
        ["🏠 首页概览",
         "📥 Phase 1: 数据导入",
         "📝 Phase 0: 关键词扩展",
         "📊 Phase 0: 基线测量",
         "🔄 Phase 2: 大组聚类",
         "✅ Phase 3: 聚类筛选",
         "🏷️ Phase 4: Token提取",
         "📊 Phase 5: 需求生成",
         "🌱 词根管理",
         "📋 数据查看与管理",
         "⚙️ 配置管理",
         "📖 使用说明"],
        key="navigation"
    )

    st.markdown("---")

    # 快速统计
    st.markdown("### 📊 快速统计")
    stats = get_database_stats()
    if stats:
        st.metric("短语总数", f"{stats['phrases_count']:,}")
        st.metric("大组数量", stats['clusters_A'])
        st.metric("选中大组", stats['selected_A'])
        st.metric("需求卡片", stats['demands_count'])
        st.metric("Token数量", stats['tokens_count'])

    st.markdown("---")

    # 系统信息
    st.markdown("### ℹ️ 系统信息")
    st.text(f"LLM: {LLM_PROVIDER}")
    st.text(f"数据库: {DATABASE_CONFIG.get('database', 'N/A')}")

    st.markdown("---")
    st.markdown("**版本**: MVP v1.0")
    st.markdown("**更新**: 2024-12-19")


# ============================================================================
# 页面路由
# ============================================================================

if page == "🏠 首页概览":
    st.markdown('<div class="main-header">🔍 词根聚类需求挖掘系统</div>', unsafe_allow_html=True)

    st.markdown("""
    ### 欢迎使用词根聚类需求挖掘系统！

    这是一个基于NLP和机器学习的需求挖掘系统，通过分析大量搜索关键词来发现用户需求模式。
    """)

    # 工作流程图
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
        <div class="phase-card">
            <h4>📥 Phase 1: 数据导入</h4>
            <p>导入原始CSV数据</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="phase-card">
            <h4>📝 Phase 0: 关键词扩展</h4>
            <p>关键词分词、停用词管理与扩展</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="phase-card">
            <h4>📊 Phase 0: 基线测量</h4>
            <p>系统能力测量与优化建议</p>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
        <div class="phase-card">
            <h4>🔄 Phase 2: 大组聚类</h4>
            <p>语义聚类生成大组</p>
        </div>
        """, unsafe_allow_html=True)

    col5, col6, col7 = st.columns(3)

    with col5:
        st.markdown("""
        <div class="phase-card">
            <h4>✅ Phase 3: 聚类筛选</h4>
            <p>人工筛选有价值聚类</p>
        </div>
        """, unsafe_allow_html=True)

    with col6:
        st.markdown("""
        <div class="phase-card">
            <h4>🏷️ Phase 4: Token提取</h4>
            <p>提取关键词并分类</p>
        </div>
        """, unsafe_allow_html=True)

    with col7:
        st.markdown("""
        <div class="phase-card">
            <h4>📊 Phase 5: 需求生成</h4>
            <p>小组聚类+需求卡片</p>
        </div>
        """, unsafe_allow_html=True)

    # 数据库统计
    st.markdown("---")
    st.markdown("### 📊 数据库统计")

    if stats:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("短语总数", f"{stats['phrases_count']:,}")
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("大组数量", stats['clusters_A'])
            st.markdown('</div>', unsafe_allow_html=True)

        with col3:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("需求卡片", stats['demands_count'])
            st.markdown('</div>', unsafe_allow_html=True)

        with col4:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Token数量", stats['tokens_count'])
            st.markdown('</div>', unsafe_allow_html=True)

        # 按来源分布
        if stats['by_source']:
            st.markdown("### 📁 数据来源分布")
            st.bar_chart(stats['by_source'])

    # 快速操作
    st.markdown("---")
    st.markdown("### ⚡ 快速操作")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🚀 开始新项目", use_container_width=True):
            st.info("请前往 Phase 1 开始数据导入")

    with col2:
        if st.button("📊 查看聚类", use_container_width=True):
            st.info("请前往 Phase 2 或 Phase 3")

    with col3:
        if st.button("📖 查看文档", use_container_width=True):
            st.info("请前往 使用说明 页面")


elif page == "📥 Phase 1: 数据导入":
    from ui.pages import phase1_import
    phase1_import.render()

elif page == "📝 Phase 0: 关键词扩展":
    from ui.pages import phase0_expansion
    phase0_expansion.main()

elif page == "📊 Phase 0: 基线测量":
    from ui.pages import phase0_baseline
    phase0_baseline.render()

elif page == "🔄 Phase 2: 大组聚类":
    from ui.pages import phase2_clustering
    phase2_clustering.render()

elif page == "✅ Phase 3: 聚类筛选":
    from ui.pages import phase3_selection
    phase3_selection.render()

elif page == "🏷️ Phase 4: Token提取":
    from ui.pages import phase4_tokens
    phase4_tokens.render()

elif page == "📊 Phase 5: 需求生成":
    from ui.pages import phase5_demands
    phase5_demands.render()

elif page == "🌱 词根管理":
    from ui.pages import seed_word_management
    seed_word_management.render()

elif page == "📋 数据查看与管理":
    from ui.pages import data_viewer
    data_viewer.render()

elif page == "⚙️ 配置管理":
    from ui.pages import config_page
    config_page.render()

elif page == "📖 使用说明":
    from ui.pages import documentation
    documentation.render()

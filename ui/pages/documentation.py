"""
文档查看页面
"""
import streamlit as st
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def render():
    st.markdown('<div class="main-header">📖 使用说明</div>', unsafe_allow_html=True)

    st.markdown("""
    ### 系统文档导航

    完整的文档体系帮助您快速上手和解决问题。
    """)

    st.markdown("---")

    # 文档导航
    st.markdown("## 📚 文档目录")

    # 快速开始文档
    with st.expander("🚀 快速开始 (QUICK_START.md)", expanded=True):
        quick_start_path = project_root / "docs" / "QUICK_START.md"

        if quick_start_path.exists():
            with open(quick_start_path, 'r', encoding='utf-8') as f:
                content = f.read()
            st.markdown(content)
        else:
            st.warning(f"⚠️ 文档不存在: {quick_start_path}")

    # 完整使用说明
    with st.expander("📖 完整使用说明 (USER_GUIDE.md)"):
        user_guide_path = project_root / "docs" / "USER_GUIDE.md"

        if user_guide_path.exists():
            st.info("文档较长，请滚动查看")

            with open(user_guide_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 分页显示（每5000字符一页）
            chunk_size = 5000
            chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]

            page = st.selectbox(f"选择页码（共{len(chunks)}页）", range(1, len(chunks)+1))

            st.markdown(chunks[page-1])

            if page < len(chunks):
                st.info(f"👉 还有内容，请选择下一页查看")
        else:
            st.warning(f"⚠️ 文档不存在: {user_guide_path}")

    # Phase 4 文档
    with st.expander("📊 Phase 4 实施摘要 (Phase4_Implementation_Summary.md)"):
        phase4_path = project_root / "docs" / "Phase4_Implementation_Summary.md"

        if phase4_path.exists():
            with open(phase4_path, 'r', encoding='utf-8') as f:
                content = f.read()
            st.markdown(content)
        else:
            st.warning(f"⚠️ 文档不存在: {phase4_path}")

    # Phase 5 文档
    with st.expander("🏷️ Phase 5 实施摘要 (Phase5_Implementation_Summary.md)"):
        phase5_path = project_root / "docs" / "Phase5_Implementation_Summary.md"

        if phase5_path.exists():
            with open(phase5_path, 'r', encoding='utf-8') as f:
                content = f.read()
            st.markdown(content)
        else:
            st.warning(f"⚠️ 文档不存在: {phase5_path}")

    # 文档导航索引
    with st.expander("🗺️ 文档导航索引 (DOCUMENTATION_INDEX.md)"):
        doc_index_path = project_root / "docs" / "DOCUMENTATION_INDEX.md"

        if doc_index_path.exists():
            with open(doc_index_path, 'r', encoding='utf-8') as f:
                content = f.read()
            st.markdown(content)
        else:
            st.warning(f"⚠️ 文档不存在: {doc_index_path}")

    st.markdown("---")

    # 快速参考
    st.markdown("## 🎯 快速参考")

    tab1, tab2, tab3, tab4 = st.tabs(["常用命令", "配置参数", "故障排查", "API成本"])

    with tab1:
        st.markdown("### 常用命令")

        st.markdown("#### Phase 1: 数据导入")
        st.code("""
# 完整导入
python scripts/run_phase1_import.py

# 测试导入（1000条）
python scripts/run_phase1_import.py --limit 1000
        """, language="bash")

        st.markdown("#### Phase 2: 大组聚类")
        st.code("""
# 默认参数
python scripts/run_phase2_clustering.py

# 自定义参数
python scripts/run_phase2_clustering.py --min-cluster-size=40 --min-samples=5

# 使用缓存
python scripts/run_phase2_clustering.py --use-cache
        """, language="bash")

        st.markdown("#### Phase 3: 聚类筛选")
        st.code("""
# 导出报告
python scripts/run_phase3_selection.py

# 跳过LLM
python scripts/run_phase3_selection.py --skip-llm

# 导入选择
python scripts/import_selection.py data/output/clusters_levelA.csv
        """, language="bash")

        st.markdown("#### Phase 4: 需求生成")
        st.code("""
# 完整运行
python scripts/run_phase4_demands.py

# 测试模式（跳过LLM）
python scripts/run_phase4_demands.py --skip-llm --test-limit 2

# 自定义参数
python scripts/run_phase4_demands.py --min-cluster-size=8 --min-samples=3
        """, language="bash")

        st.markdown("#### Phase 5: Token提取")
        st.code("""
# 完整运行
python scripts/run_phase5_tokens.py --sample-size 10000 --min-frequency 3

# 测试模式
python scripts/run_phase5_tokens.py --skip-llm --sample-size 1000 --min-frequency 5

# 全量运行
python scripts/run_phase5_tokens.py --sample-size 0 --min-frequency 2
        """, language="bash")

    with tab2:
        st.markdown("### 配置参数")

        st.markdown("#### 数据库配置")
        st.code("""
DATABASE_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'your_user',
    'password': 'your_password',
    'database': 'search_demand_mining',
}
        """, language="python")

        st.markdown("#### LLM配置")
        st.code("""
LLM_PROVIDER = "openai"  # openai, anthropic, deepseek

LLM_CONFIG = {
    "openai": {
        "api_key": "sk-your-api-key",
        "model": "gpt-4o-mini",
        "temperature": 0.7,
        "max_tokens": 2000
    }
}
        """, language="python")

        st.markdown("#### 聚类配置")
        st.code("""
# 大组聚类
LARGE_CLUSTER_CONFIG = {
    "min_cluster_size": 30,  # 簇太多增大，太少减小
    "min_samples": 3,        # 噪音太多减小
    "metric": "cosine",
}

# 小组聚类
SMALL_CLUSTER_CONFIG = {
    "min_cluster_size": 5,
    "min_samples": 2,
    "metric": "cosine",
}
        """, language="python")

    with tab3:
        st.markdown("### 故障排查")

        st.markdown("#### 数据库连接失败")
        st.code("""
# 1. 检查MySQL服务是否启动
# Windows: 服务管理器
# Linux: sudo systemctl status mysql

# 2. 测试连接
python -c "from storage.repository import PhraseRepository; repo = PhraseRepository(); print('连接成功')"

# 3. 检查配置
# 打开 config/settings.py 确认用户名密码正确
        """, language="bash")

        st.markdown("#### LLM API调用失败")
        st.code("""
# 1. 检查API密钥
# 打开 config/settings.py 确认 api_key 正确

# 2. 测试连接
python -c "from ai.client import LLMClient; client = LLMClient(); print(client.chat([{'role': 'user', 'content': 'test'}]))"

# 3. 检查配额
# 登录API提供商网站查看剩余配额
        """, language="bash")

        st.markdown("#### 内存不足")
        st.code("""
# 1. 使用采样模式
python scripts/run_phase5_tokens.py --sample-size 5000

# 2. 分批处理
python scripts/run_phase4_demands.py --test-limit 3

# 3. 关闭其他程序释放内存
        """, language="bash")

        st.markdown("#### 聚类结果不理想")
        st.markdown("""
        **簇太多（>100个）**:
        - 增大 `min_cluster_size` 到 40-50
        - 增大 `min_samples` 到 5

        **簇太少（<40个）**:
        - 减小 `min_cluster_size` 到 20-25
        - 减小 `min_samples` 到 2

        **噪音点太多（>50%）**:
        - 减小 `min_samples` 到 2
        """)

    with tab4:
        st.markdown("### API成本参考")

        st.markdown("#### 典型项目（55,275条短语）")

        cost_table = """
| 阶段 | API调用 | OpenAI | Anthropic | DeepSeek |
|------|---------|--------|-----------|----------|
| Phase 2 Embedding | 55,275短语 | $0.03 | N/A | N/A |
| Phase 4 需求卡片 | ~168次 | $0.50 | $10.00 | $0.07 |
| Phase 5 Token分类 | ~1000 tokens | $0.05 | $1.00 | $0.01 |
| **总计** | - | **$0.58** | **$11.00** | **$0.08** |
        """

        st.markdown(cost_table)

        st.markdown("#### 成本优化建议")
        st.markdown("""
        **测试阶段（免费）**:
        - 使用 `--skip-llm` 跳过所有LLM调用
        - 使用 `--test-limit` 限制处理数量
        - Phase 2 使用本地embedding（免费）

        **生产阶段**:
        - 推荐 OpenAI GPT-4o-mini（$0.58）
        - 或 DeepSeek（$0.08，质量略低）
        - Anthropic质量最高但成本高10倍
        """)

    st.markdown("---")

    # 视频教程（占位）
    st.markdown("## 🎥 视频教程")

    st.info("📹 视频教程开发中...")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 快速上手")
        st.markdown("- 环境配置")
        st.markdown("- 运行Phase 1-2")
        st.markdown("- 查看结果")

    with col2:
        st.markdown("### 进阶使用")
        st.markdown("- 参数调优")
        st.markdown("- 需求审核")
        st.markdown("- Token管理")

    with col3:
        st.markdown("### 故障排除")
        st.markdown("- 常见错误")
        st.markdown("- 配置问题")
        st.markdown("- 性能优化")

    st.markdown("---")

    # 外部资源
    st.markdown("## 🔗 外部资源")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 技术文档")
        st.markdown("""
        - [HDBSCAN算法文档](https://hdbscan.readthedocs.io/)
        - [Sentence Transformers文档](https://www.sbert.net/)
        - [SQLAlchemy文档](https://docs.sqlalchemy.org/)
        - [Streamlit文档](https://docs.streamlit.io/)
        """)

    with col2:
        st.markdown("### 项目资源")
        st.markdown("""
        - [GitHub仓库](https://github.com/shierbd/xuq)
        - [问题反馈](https://github.com/shierbd/xuq/issues)
        - README.md
        - 项目Wiki（开发中）
        """)

    st.markdown("---")

    # 获取帮助
    st.markdown("## 🆘 获取帮助")

    st.markdown("""
    ### 遇到问题？

    1. **查看文档**
       - 先查看本页面的快速参考
       - 阅读对应Phase的详细文档
       - 查看FAQ部分

    2. **检查配置**
       - 前往"⚙️ 配置管理"页面
       - 使用测试功能验证配置
       - 确认数据库和API连接正常

    3. **测试模式**
       - 使用 `--skip-llm` 跳过LLM
       - 使用 `--test-limit` 限制处理量
       - 使用小样本数据验证流程

    4. **查看日志**
       - 脚本会输出详细的错误信息
       - 检查 `data/output/` 目录下的报告
       - 查看数据库中的数据状态

    5. **寻求支持**
       - GitHub Issues: 报告bug或提问
       - 邮件联系: （待添加）
       - 社区讨论: （待建立）
    """)

    st.markdown("---")

    st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem;">
        <p>📚 完整文档请查看 docs/ 目录</p>
        <p>💡 建议新用户从 QUICK_START.md 开始</p>
        <p>🚀 祝你挖掘出好需求！</p>
    </div>
    """, unsafe_allow_html=True)

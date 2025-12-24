"""
配置管理页面
"""
import streamlit as st
import sys
from pathlib import Path
import json

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.settings import (
    DATABASE_CONFIG, LLM_PROVIDER, LLM_CONFIG,
    EMBEDDING_MODEL, EMBEDDING_MODEL_VERSION, EMBEDDING_DIM,
    LARGE_CLUSTER_CONFIG, SMALL_CLUSTER_CONFIG
)


def load_env_config():
    """从.env文件加载当前配置"""
    import os
    from dotenv import load_dotenv

    # 重新加载.env文件
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file, override=True)

    # 读取配置
    current_provider = os.getenv('LLM_PROVIDER', 'deepseek')
    current_api_key = os.getenv(f'{current_provider.upper()}_API_KEY', '')
    current_model = os.getenv(f'{current_provider.upper()}_MODEL', '')

    # 根据provider设置默认模型
    if not current_model:
        if current_provider == 'deepseek':
            current_model = 'deepseek-chat'
        elif current_provider == 'openai':
            current_model = 'gpt-4o-mini'
        elif current_provider == 'anthropic':
            current_model = 'claude-3-5-sonnet-20241022'

    return {
        'provider': current_provider,
        'api_key': current_api_key,
        'model': current_model
    }


def save_env_config(provider, api_key, model):
    """保存配置到.env文件"""
    env_file = project_root / ".env"

    # 读取现有.env内容
    env_lines = []
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            env_lines = f.readlines()

    # 更新配置
    updated = {
        'LLM_PROVIDER': False,
        f'{provider.upper()}_API_KEY': False,
        f'{provider.upper()}_MODEL': False
    }

    new_lines = []
    for line in env_lines:
        line_stripped = line.strip()
        if line_stripped.startswith('LLM_PROVIDER='):
            new_lines.append(f'LLM_PROVIDER={provider}\n')
            updated['LLM_PROVIDER'] = True
        elif line_stripped.startswith(f'{provider.upper()}_API_KEY='):
            new_lines.append(f'{provider.upper()}_API_KEY={api_key}\n')
            updated[f'{provider.upper()}_API_KEY'] = True
        elif line_stripped.startswith(f'{provider.upper()}_MODEL='):
            new_lines.append(f'{provider.upper()}_MODEL={model}\n')
            updated[f'{provider.upper()}_MODEL'] = True
        else:
            new_lines.append(line)

    # 添加未更新的配置
    if not updated['LLM_PROVIDER']:
        new_lines.append(f'LLM_PROVIDER={provider}\n')
    if not updated[f'{provider.upper()}_API_KEY']:
        new_lines.append(f'{provider.upper()}_API_KEY={api_key}\n')
    if not updated[f'{provider.upper()}_MODEL']:
        new_lines.append(f'{provider.upper()}_MODEL={model}\n')

    # 保存
    with open(env_file, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)


def render():
    st.markdown('<div class="main-header">⚙️ 配置管理</div>', unsafe_allow_html=True)

    st.markdown("""
    ### 系统配置

    快速配置LLM提供商和API密钥，或编辑详细配置文件。
    """)

    st.markdown("---")

    # ============ 新增：LLM配置表单 ============
    st.markdown("## 🚀 快速配置LLM")

    # 加载当前配置
    current_config = load_env_config()

    # 显示当前配置状态
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("当前提供商", current_config['provider'].upper())
    with col2:
        st.metric("当前模型", current_config['model'])
    with col3:
        api_key_display = current_config['api_key']
        if api_key_display:
            api_key_display = f"{api_key_display[:8]}...{api_key_display[-4:]}"
        else:
            api_key_display = "未配置"
        st.metric("API密钥", api_key_display)

    st.info("💡 修改下方配置后点击保存，配置会立即保存到 `.env` 文件。刷新页面后会显示最新配置。")

    with st.form("llm_config_form"):
        col1, col2 = st.columns(2)

        with col1:
            # 提供商选择 - 使用当前配置作为默认值
            provider_options = ["deepseek", "openai", "anthropic"]
            default_provider_index = provider_options.index(current_config['provider']) if current_config['provider'] in provider_options else 0

            provider = st.selectbox(
                "选择LLM提供商",
                options=provider_options,
                index=default_provider_index,
                help="推荐使用DeepSeek（成本最低）或OpenAI（性价比高）"
            )

            # 根据选择的提供商显示不同的模型选项
            if provider == "deepseek":
                model_options = ["deepseek-chat", "deepseek-coder"]
                default_model_index = model_options.index(current_config['model']) if current_config['model'] in model_options else 0

                model = st.selectbox(
                    "选择模型",
                    options=model_options,
                    index=default_model_index,
                    help="deepseek-chat: 通用模型\ndeeseek-coder: 代码专用"
                )
                api_url = st.text_input(
                    "API Base URL",
                    value="https://api.deepseek.com/v1",
                    help="通常使用默认值即可"
                )
            elif provider == "openai":
                model_options = ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"]
                default_model_index = model_options.index(current_config['model']) if current_config['model'] in model_options else 0

                model = st.selectbox(
                    "选择模型",
                    options=model_options,
                    index=default_model_index,
                    help="推荐使用gpt-4o-mini（性价比最高）"
                )
                api_url = st.text_input(
                    "API Base URL",
                    value="https://api.openai.com/v1",
                    help="如果使用OpenAI兼容接口，可修改此地址"
                )
            else:  # anthropic
                model_options = ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229"]
                default_model_index = model_options.index(current_config['model']) if current_config['model'] in model_options else 0

                model = st.selectbox(
                    "选择模型",
                    options=model_options,
                    index=default_model_index,
                    help="Claude Sonnet: 平衡性能\nClaude Opus: 最高性能"
                )
                api_url = None

        with col2:
            # API密钥输入 - 显示占位符提示当前有配置
            api_key_placeholder = f"当前已配置 {current_config['provider'].upper()} API Key" if current_config['api_key'] else f"请输入您的{provider.upper()} API Key"

            api_key = st.text_input(
                "API密钥",
                type="password",
                placeholder=api_key_placeholder,
                help="留空则保持当前密钥不变；输入新密钥则会覆盖"
            )

            # 参数配置
            temperature = st.slider(
                "Temperature（创造性）",
                min_value=0.0,
                max_value=1.0,
                value=0.3,
                step=0.1,
                help="0.0=确定性强，1.0=创造性强。推荐0.3"
            )

            max_tokens = st.number_input(
                "最大Token数",
                min_value=500,
                max_value=8000,
                value=2000,
                step=500,
                help="单次请求最多生成的token数"
            )

        # 提交按钮
        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            submit_button = st.form_submit_button(
                "💾 保存配置",
                type="primary",
                use_container_width=True
            )

        with col2:
            test_button = st.form_submit_button(
                "🧪 测试连接",
                use_container_width=True
            )

    # 处理表单提交
    if submit_button:
        # 如果API密钥为空，使用当前配置的密钥
        final_api_key = api_key if api_key else current_config['api_key']

        if not final_api_key:
            st.error("❌ 请输入API密钥")
        else:
            try:
                # 保存到.env
                save_env_config(provider, final_api_key, model)

                st.success(f"""
                ✅ 配置已保存！

                - **提供商**: {provider}
                - **模型**: {model}
                - **API密钥**: {final_api_key[:8]}...{final_api_key[-4:]}

                💡 **配置已立即生效**，刷新页面即可看到最新配置
                """)

                st.info("🔄 如果需要在Phase 3/4/5中使用新配置，请重启Web UI")

                # 提示用户刷新页面
                st.warning("⚠️ 点击下方按钮刷新页面查看最新配置")
                if st.button("🔄 刷新页面", type="secondary"):
                    st.rerun()

            except Exception as e:
                st.error(f"❌ 保存失败: {str(e)}")

    if test_button:
        # 如果API密钥为空，使用当前配置的密钥
        test_api_key = api_key if api_key else current_config['api_key']

        if not test_api_key:
            st.error("❌ 请先输入API密钥，或确保已保存过API密钥")
        else:
            with st.spinner(f"正在测试 {provider} 连接..."):
                try:
                    # 临时设置环境变量进行测试
                    import os
                    os.environ['LLM_PROVIDER'] = provider
                    os.environ[f'{provider.upper()}_API_KEY'] = test_api_key
                    os.environ[f'{provider.upper()}_MODEL'] = model
                    if api_url:
                        os.environ[f'{provider.upper()}_BASE_URL'] = api_url

                    # 重新加载配置模块
                    import importlib
                    import config.settings
                    importlib.reload(config.settings)

                    # 现在导入LLMClient，这样它会读取新的配置
                    from ai.client import LLMClient

                    # 创建客户端（会使用刚刚reload的配置）
                    client = LLMClient()

                    # 发送测试消息
                    response = client._call_llm([{
                        "role": "user",
                        "content": "请用中文回复：你好！"
                    }])

                    st.success(f"✅ {provider.upper()} 连接成功！")
                    st.info(f"**模型回复**: {response}")

                except Exception as e:
                    st.error(f"❌ 连接失败: {str(e)}")
                    st.warning("请检查：\n1. API密钥是否正确\n2. 网络连接是否正常\n3. API额度是否充足")

                    # 显示详细错误信息用于调试
                    with st.expander("🔍 查看详细错误"):
                        import traceback
                        st.code(traceback.format_exc())

    st.markdown("---")

    # 数据库配置
    st.markdown("## 🗄️ 数据库配置")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 当前配置")
        st.json(DATABASE_CONFIG)

    with col2:
        st.markdown("### 测试连接")

        if st.button("🔌 测试数据库连接", use_container_width=True):
            try:
                from storage.repository import PhraseRepository

                with PhraseRepository() as repo:
                    count = repo.get_phrase_count()

                st.success(f"✅ 连接成功！数据库有 {count:,} 条短语")

            except Exception as e:
                st.error(f"❌ 连接失败: {str(e)}")

        st.markdown("### 修改方法")
        st.info("""
        编辑 `config/settings.py` 文件：

        ```python
        DATABASE_CONFIG = {
            'host': 'localhost',
            'port': 3306,
            'user': 'your_user',
            'password': 'your_password',
            'database': 'search_demand_mining',
        }
        ```
        """)

    st.markdown("---")

    # LLM配置
    st.markdown("## 🤖 LLM配置")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 当前提供商")
        st.info(f"**Provider**: {LLM_PROVIDER}")

        st.markdown("### 配置详情")
        if LLM_PROVIDER in LLM_CONFIG:
            config = LLM_CONFIG[LLM_PROVIDER].copy()
            # 隐藏API密钥
            if 'api_key' in config:
                config['api_key'] = "***" + config['api_key'][-4:] if len(config['api_key']) > 4 else "****"
            st.json(config)
        else:
            st.warning(f"⚠️ 未找到 {LLM_PROVIDER} 的配置")

    with col2:
        st.markdown("### 测试LLM")

        if st.button("🧪 测试LLM连接", use_container_width=True):
            try:
                from ai.client import LLMClient

                client = LLMClient()
                response = client._call_llm([{
                    "role": "user",
                    "content": "请用中文回复：你好，测试连接！"
                }])

                st.success(f"✅ LLM响应: {response}")

            except Exception as e:
                st.error(f"❌ 测试失败: {str(e)}")

        st.markdown("### 可用提供商")
        st.markdown("""
        - **openai**: GPT-4o-mini（推荐，性价比高）
        - **anthropic**: Claude Sonnet（准确率高，成本较高）
        - **deepseek**: DeepSeek（最便宜）

        修改 `config/settings.py`:
        ```python
        LLM_PROVIDER = "openai"  # 或 anthropic, deepseek
        ```
        """)

    st.markdown("---")

    # Embedding配置
    st.markdown("## 🧮 Embedding配置")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 当前配置")
        embedding_config = {
            "model": EMBEDDING_MODEL,
            "version": EMBEDDING_MODEL_VERSION,
            "dimension": EMBEDDING_DIM
        }
        st.json(embedding_config)

    with col2:
        st.markdown("### 说明")
        st.info(f"""
        **Model**: {EMBEDDING_MODEL}
        **Version**: {EMBEDDING_MODEL_VERSION}
        **Dimension**: {EMBEDDING_DIM}

        使用本地Sentence Transformer模型进行embedding计算。
        成本: 免费（本地计算）
        """)

        if st.button("🧪 测试Embedding", use_container_width=True):
            try:
                from core.embedding import EmbeddingService

                service = EmbeddingService(use_cache=False)
                embeddings = service.embed_texts(["test phrase"], show_progress=False)

                st.success(f"✅ Embedding生成成功！维度: {embeddings.shape[1]}")

            except Exception as e:
                st.error(f"❌ 测试失败: {str(e)}")

    st.markdown("---")

    # 聚类配置
    st.markdown("## 🔄 聚类配置")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 大组聚类 (Level A)")
        st.json(LARGE_CLUSTER_CONFIG)

        st.markdown("**参数说明**:")
        st.markdown("""
        - `min_cluster_size`: 最小聚类大小（默认30）
          - 增大 → 更少、更大的簇
          - 减小 → 更多、更小的簇

        - `min_samples`: 最小样本数（默认3）
          - 增大 → 更紧密的簇（噪音点更多）
          - 减小 → 更松散的簇（噪音点更少）

        - `metric`: 距离度量（cosine推荐）
        """)

    with col2:
        st.markdown("### 小组聚类 (Level B)")
        st.json(SMALL_CLUSTER_CONFIG)

        st.markdown("**调整建议**:")
        st.markdown("""
        **大组聚类结果不理想**:
        - 簇太多（>100个）→ 增大 min_cluster_size 到 40-50
        - 簇太少（<40个）→ 减小 min_cluster_size 到 20-25
        - 噪音点太多（>50%）→ 减小 min_samples 到 2

        **小组聚类结果不理想**:
        - 小组太多（>15个/大组）→ 增大 min_cluster_size 到 8-10
        - 小组太少（<3个/大组）→ 减小 min_cluster_size 到 3-4
        """)

    st.markdown("---")

    # 文件路径配置
    st.markdown("## 📁 文件路径")

    paths_info = {
        "项目根目录": str(project_root),
        "数据目录": str(project_root / "data"),
        "原始数据": str(project_root / "data" / "raw"),
        "输出目录": str(project_root / "data" / "output"),
        "缓存目录": str(project_root / "data" / "cache"),
        "脚本目录": str(project_root / "scripts"),
        "配置文件": str(project_root / "config" / "settings.py")
    }

    for name, path in paths_info.items():
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown(f"**{name}**")
        with col2:
            st.code(path, language="text")

    st.markdown("---")

    # API成本估算
    st.markdown("## 💰 API成本估算")

    st.markdown("### 典型项目（55,275条短语，28个选中大组）")

    cost_data = {
        "阶段": ["Phase 2 Embedding", "Phase 4 需求卡片", "Phase 5 Token分类", "总计"],
        "OpenAI": ["$0.03", "$0.50", "$0.05", "$0.58"],
        "Anthropic": ["N/A", "$10.00", "$1.00", "$11.00"],
        "DeepSeek": ["N/A", "$0.07", "$0.01", "$0.08"]
    }

    import pandas as pd
    df = pd.DataFrame(cost_data)

    st.dataframe(df, use_container_width=True)

    st.markdown("### 成本优化建议")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**测试阶段**:")
        st.markdown("""
        - 使用 `--skip-llm` 跳过LLM调用
        - 使用 `--test-limit` 限制处理数量
        - 使用小样本数据验证流程
        - Phase 2 使用本地embedding（免费）
        """)

    with col2:
        st.markdown("**生产阶段**:")
        st.markdown("""
        - 推荐使用 OpenAI GPT-4o-mini（性价比最高）
        - DeepSeek最便宜但质量略低
        - 批量API调用节省成本
        - 使用缓存避免重复计算
        """)

    st.markdown("---")

    # 环境信息
    st.markdown("## 📊 环境信息")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### Python环境")
        st.text(f"版本: {sys.version.split()[0]}")
        st.text(f"路径: {sys.executable}")

    with col2:
        st.markdown("### 已安装包")
        try:
            import streamlit
            import pandas
            import sqlalchemy
            st.text(f"streamlit: {streamlit.__version__}")
            st.text(f"pandas: {pandas.__version__}")
            st.text(f"sqlalchemy: {sqlalchemy.__version__}")
        except Exception as e:
            st.error(f"检查失败: {str(e)}")

    with col3:
        st.markdown("### 系统信息")
        import platform
        st.text(f"系统: {platform.system()}")
        st.text(f"版本: {platform.release()}")

    st.markdown("---")

    # 配置文件编辑器
    st.markdown("## 📝 配置文件编辑器")

    st.warning("⚠️ 修改配置后需要重启应用才能生效")

    settings_file = project_root / "config" / "settings.py"

    if settings_file.exists():
        try:
            with open(settings_file, 'r', encoding='utf-8') as f:
                content = f.read()

            edited_content = st.text_area(
                "编辑 config/settings.py",
                value=content,
                height=400,
                help="修改后点击下方的保存按钮"
            )

            col1, col2, col3 = st.columns([1, 1, 2])

            with col1:
                if st.button("💾 保存配置", type="primary", use_container_width=True):
                    try:
                        with open(settings_file, 'w', encoding='utf-8') as f:
                            f.write(edited_content)
                        st.success("✅ 配置已保存！请重启应用使配置生效。")
                    except Exception as e:
                        st.error(f"❌ 保存失败: {str(e)}")

            with col2:
                if st.button("🔄 重置", use_container_width=True):
                    st.rerun()

        except Exception as e:
            st.error(f"❌ 无法读取配置文件: {str(e)}")
    else:
        st.error(f"❌ 配置文件不存在: {settings_file}")

    st.markdown("---")

    # 使用说明
    with st.expander("📖 使用说明"):
        st.markdown("""
        ### 配置管理

        本页面提供系统配置的查看和测试功能。

        ### 修改配置

        1. **方法1: 在线编辑**
           - 在页面底部的"配置文件编辑器"中修改
           - 点击"保存配置"
           - 重启应用

        2. **方法2: 直接编辑**
           - 使用文本编辑器打开 `config/settings.py`
           - 修改相应配置
           - 保存文件
           - 重启应用

        ### 测试功能

        使用各个"测试"按钮验证配置是否正确：
        - 🔌 测试数据库连接
        - 🧪 测试LLM连接
        - 🧮 测试Embedding

        ### 重要提示

        - 修改配置后必须重启Streamlit应用
        - 建议先备份配置文件
        - API密钥请妥善保管，不要泄露
        """)

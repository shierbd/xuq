"""
[REQ-2.7] Phase 7 商品筛选与AI标注系统 - Web UI页面

提供完整的商品管理界面：
1. 数据导入（CSV/Excel，字段映射）
2. 商品列表展示和筛选
3. AI标注配置和执行
4. 动态字段管理
5. 数据导出
"""
import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime
import json
from typing import Dict, Any, List, Optional

from core.product_management import (
    ProductImporter,
    ProductAIAnnotator,
    ProductFieldManager,
    ProductExporter
)
from storage.product_repository import (
    ProductRepository,
    ProductFieldDefinitionRepository,
    ProductImportLogRepository
)


def render_page():
    """渲染Phase 7主页面"""
    st.title("📦 Phase 7: 商品筛选与AI标注系统")

    # 侧边栏：功能选择
    with st.sidebar:
        st.header("功能菜单")
        page = st.radio(
            "选择功能",
            [
                "📊 数据概览",
                "📥 数据导入",
                "🔍 商品筛选",
                "🤖 AI标注",
                "⚙️ 字段管理",
                "📤 数据导出",
                "📋 导入历史"
            ]
        )

    # 根据选择渲染不同页面
    if page == "📊 数据概览":
        render_overview()
    elif page == "📥 数据导入":
        render_import()
    elif page == "🔍 商品筛选":
        render_filter()
    elif page == "🤖 AI标注":
        render_ai_annotation()
    elif page == "⚙️ 字段管理":
        render_field_management()
    elif page == "📤 数据导出":
        render_export()
    elif page == "📋 导入历史":
        render_import_history()


# ==================== 1. 数据概览 ====================
def render_overview():
    """渲染数据概览页面"""
    st.header("📊 数据概览")

    repo = ProductRepository()
    stats = repo.get_statistics()

    # 显示统计卡片
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("总商品数", stats["total"])

    with col2:
        etsy_count = stats["by_platform"].get("etsy", 0)
        st.metric("Etsy商品", etsy_count)

    with col3:
        gumroad_count = stats["by_platform"].get("gumroad", 0)
        st.metric("Gumroad商品", gumroad_count)

    st.divider()

    # AI分析状态
    st.subheader("AI分析状态")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        pending = stats["by_ai_status"].get("pending", 0)
        st.metric("待分析", pending, delta=None)

    with col2:
        processing = stats["by_ai_status"].get("processing", 0)
        st.metric("分析中", processing)

    with col3:
        completed = stats["by_ai_status"].get("completed", 0)
        st.metric("已完成", completed)

    with col4:
        failed = stats["by_ai_status"].get("failed", 0)
        st.metric("失败", failed, delta=None, delta_color="inverse")

    # 进度条
    if stats["total"] > 0:
        progress = completed / stats["total"]
        st.progress(progress, text=f"AI标注进度: {progress*100:.1f}%")

    st.divider()

    # 如果没有数据，显示友好提示
    if stats["total"] == 0:
        st.info("📭 暂无商品数据")

        st.markdown("""
        ### 🚀 开始使用Phase 7

        欢迎使用商品筛选与AI标注系统！这个系统可以帮助您：

        - 📥 **批量导入商品数据**：支持CSV和Excel文件
        - 🔍 **智能筛选商品**：多条件组合筛选
        - 🤖 **AI自动标注**：生成商品标签和需求分析
        - ⚙️ **灵活字段管理**：自定义商品属性
        - 📤 **便捷数据导出**：导出筛选结果

        ---

        ### 📝 使用步骤

        1. **导入数据**：点击左侧菜单「📥 数据导入」上传商品文件
        2. **查看商品**：在「🔍 商品筛选」中浏览和筛选商品
        3. **AI标注**：在「🤖 AI标注」中批量生成标签
        4. **导出结果**：在「📤 数据导出」中导出处理后的数据

        ---

        **💡 提示**：建议先导入少量数据进行测试，确认字段映射正确后再批量导入。
        """)

        # 快速操作按钮
        col1, col2 = st.columns(2)

        with col1:
            if st.button("📥 开始导入数据", type="primary", use_container_width=True):
                st.info("💡 请在左侧菜单中选择「📥 数据导入」")

        with col2:
            if st.button("📖 查看使用说明", use_container_width=True):
                st.info("💡 请在左侧菜单中选择「📖 使用说明」")
    else:
        # 有数据时显示快速操作
        st.subheader("⚡ 快速操作")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🔍 查看商品", use_container_width=True):
                st.info("💡 请在左侧菜单中选择「🔍 商品筛选」")

        with col2:
            if pending > 0:
                if st.button(f"🤖 标注 {pending} 个商品", use_container_width=True):
                    st.info("💡 请在左侧菜单中选择「🤖 AI标注」")
            else:
                st.button("✅ 全部已标注", disabled=True, use_container_width=True)

        with col3:
            if st.button("📤 导出数据", use_container_width=True):
                st.info("💡 请在左侧菜单中选择「📤 数据导出」")


# ==================== 2. 数据导入 ====================
def render_import():
    """渲染数据导入页面"""
    st.header("📥 数据导入")

    st.info("💡 支持CSV和Excel文件，可以无列名导入（按列顺序映射）")

    # 文件上传
    uploaded_file = st.file_uploader(
        "选择文件",
        type=["csv", "xlsx", "xls"],
        help="支持CSV和Excel格式"
    )

    if uploaded_file is not None:
        # 保存临时文件
        temp_path = Path("data/temp") / uploaded_file.name
        temp_path.parent.mkdir(parents=True, exist_ok=True)

        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.success(f"✅ 文件已上传: {uploaded_file.name}")

        # 预览数据
        st.subheader("数据预览")
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(temp_path, header=None, nrows=5)
            else:
                df = pd.read_excel(temp_path, header=None, nrows=5)

            st.dataframe(df, use_container_width=True)

            # 字段映射配置
            st.subheader("字段映射配置")

            col1, col2 = st.columns(2)

            with col1:
                platform = st.selectbox(
                    "选择平台",
                    ["etsy", "gumroad"],
                    help="商品来源平台"
                )

            with col2:
                skip_duplicates = st.checkbox(
                    "跳过重复数据",
                    value=True,
                    help="根据URL去重"
                )

            # 字段映射
            st.write("**字段映射** (将列索引映射到字段名)")

            field_mapping = {}

            # 核心字段映射
            core_fields = {
                "product_name": "商品名称 *",
                "description": "商品描述",
                "price": "价格",
                "sales": "销量",
                "rating": "评分",
                "review_count": "评价数",
                "url": "商品链接（可选）",
                "shop_name": "店铺名称"
            }

            st.write("**核心字段**")
            cols = st.columns(2)

            for idx, (field_key, field_label) in enumerate(core_fields.items()):
                with cols[idx % 2]:
                    col_idx = st.number_input(
                        field_label,
                        min_value=-1,
                        max_value=len(df.columns)-1,
                        value=-1,
                        key=f"field_{field_key}",
                        help=f"选择对应的列索引，-1表示不映射"
                    )

                    if col_idx >= 0:
                        field_mapping[f"col_{col_idx}"] = field_key

            # 导入按钮
            if st.button("🚀 开始导入", type="primary", use_container_width=True):
                if not field_mapping:
                    st.error("❌ 请至少映射一个字段")
                elif "product_name" not in field_mapping.values():
                    st.error("❌ 商品名称是必填字段")
                else:
                    # URL字段不再是必填，如果没有会自动生成占位符
                    if "url" not in field_mapping.values():
                        st.warning("⚠️ 未映射URL字段，将自动生成占位符URL")

                    # 执行导入
                    with st.spinner("正在导入数据..."):
                        importer = ProductImporter()
                        result = importer.import_from_file(
                            file_path=str(temp_path),
                            platform=platform,
                            field_mapping=field_mapping,
                            skip_duplicates=skip_duplicates
                        )

                    if result["success"]:
                        st.success(f"""
                        ✅ 导入完成！
                        - 总行数: {result['total_rows']}
                        - 成功导入: {result['imported_rows']}
                        - 跳过: {result['skipped_rows']}
                        - 耗时: {result['duration_seconds']}秒
                        """)
                    else:
                        st.error(f"❌ 导入失败: {result.get('error', '未知错误')}")

        except Exception as e:
            st.error(f"❌ 文件读取失败: {str(e)}")


# ==================== 3. 商品筛选 ====================
def render_filter():
    """渲染商品筛选页面"""
    st.header("🔍 商品筛选")

    repo = ProductRepository()

    # 筛选条件
    with st.expander("🔧 筛选条件", expanded=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            platform = st.selectbox(
                "平台",
                ["全部", "etsy", "gumroad"]
            )
            platform = None if platform == "全部" else platform

        with col2:
            ai_status = st.selectbox(
                "AI分析状态",
                ["全部", "pending", "processing", "completed", "failed"]
            )
            ai_status = None if ai_status == "全部" else ai_status

        with col3:
            limit = st.number_input(
                "显示数量",
                min_value=10,
                max_value=1000,
                value=50,
                step=10
            )

        # 高级筛选
        st.write("**高级筛选**")

        col1, col2 = st.columns(2)

        with col1:
            keyword = st.text_input("关键词搜索", placeholder="搜索商品名称或描述")

        with col2:
            min_review_count = st.number_input(
                "最低评价数",
                min_value=0,
                value=0
            )

        col1, col2 = st.columns(2)

        with col1:
            min_price = st.number_input("最低价格", min_value=0.0, value=0.0)

        with col2:
            max_price = st.number_input("最高价格", min_value=0.0, value=0.0)

    # 查询数据
    if keyword or min_review_count > 0 or min_price > 0 or max_price > 0:
        # 使用高级搜索
        products, total = repo.search(
            keyword=keyword if keyword else None,
            platform=platform,
            min_price=min_price if min_price > 0 else None,
            max_price=max_price if max_price > 0 else None,
            min_review_count=min_review_count if min_review_count > 0 else None,
            limit=limit
        )
        st.info(f"找到 {total} 个商品，显示前 {len(products)} 个")
    else:
        # 使用简单查询
        products = repo.get_all(
            platform=platform,
            ai_status=ai_status,
            limit=limit
        )
        st.info(f"显示 {len(products)} 个商品")

    # 显示商品列表
    if products:
        # 转换为DataFrame
        df = pd.DataFrame(products)

        # 选择显示列
        display_columns = [
            "product_id",
            "product_name",
            "price",
            "rating",
            "review_count",
            "platform",
            "ai_analysis_status",
            "shop_name"
        ]

        # 过滤存在的列
        display_columns = [col for col in display_columns if col in df.columns]

        st.dataframe(
            df[display_columns],
            use_container_width=True,
            hide_index=True
        )

        # 商品详情
        st.subheader("商品详情")

        selected_id = st.number_input(
            "输入商品ID查看详情",
            min_value=1,
            value=products[0]["product_id"] if products else 1
        )

        if st.button("查看详情"):
            product = repo.get_by_id(selected_id)

            if product:
                col1, col2 = st.columns(2)

                with col1:
                    st.write("**基本信息**")
                    st.write(f"- 商品名称: {product['product_name']}")
                    st.write(f"- 价格: ${product['price']}")
                    st.write(f"- 评分: {product['rating']}⭐")
                    st.write(f"- 评价数: {product['review_count']}")
                    st.write(f"- 平台: {product['platform']}")
                    st.write(f"- 店铺: {product['shop_name']}")

                with col2:
                    st.write("**AI分析结果**")
                    st.write(f"- 状态: {product['ai_analysis_status']}")

                    if product.get('tags'):
                        st.write(f"- 标签: {', '.join(product['tags'])}")

                    if product.get('demand_analysis'):
                        st.write(f"- 需求分析: {product['demand_analysis']}")

                if product.get('description'):
                    st.write("**商品描述**")
                    st.text_area("", product['description'], height=100, disabled=True)

                if product.get('url'):
                    st.write("**商品链接**")
                    st.write(product['url'])
            else:
                st.warning(f"未找到ID为 {selected_id} 的商品")
    else:
        # 友好的空状态提示
        st.info("📭 暂无商品数据")

        st.markdown("""
        ### 💡 快速开始

        您还没有导入任何商品数据。请按照以下步骤开始：

        1. **📥 导入数据**：点击左侧菜单的"📥 数据导入"
        2. **📤 上传文件**：选择CSV或Excel文件
        3. **🔧 配置映射**：设置字段映射关系
        4. **🚀 开始导入**：点击导入按钮
        5. **🔍 筛选查看**：返回此页面查看导入的商品

        ---

        **支持的文件格式**：CSV, XLSX, XLS
        **支持的平台**：Etsy, Gumroad
        """)

        # 添加快速导航按钮
        if st.button("📥 前往数据导入", type="primary", use_container_width=True):
            st.info("💡 请在左侧菜单中选择「📥 数据导入」")


# ==================== 4. AI标注 ====================
def render_ai_annotation():
    """渲染AI标注页面"""
    st.header("🤖 AI标注")

    repo = ProductRepository()
    stats = repo.get_statistics()

    pending_count = stats["by_ai_status"].get("pending", 0)

    st.info(f"当前有 {pending_count} 个商品待标注")

    # 标注配置
    with st.expander("⚙️ 标注配置", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            batch_size = st.number_input(
                "批次大小",
                min_value=1,
                max_value=100,
                value=10,
                help="每批处理的商品数量"
            )

        with col2:
            use_custom_prompt = st.checkbox(
                "使用自定义提示词",
                value=False
            )

        custom_prompt = None
        if use_custom_prompt:
            custom_prompt = st.text_area(
                "自定义提示词模板",
                value="""请分析以下商品信息，完成两个任务：

1. 生成3个中文标签，描述商品的类别、特点或用途
2. 判断这个商品解决了什么用户需求

商品信息：
- 名称：{product_name}
- 描述：{description}
- 价格：${price}
- 评分：{rating}星
- 评价数：{review_count}条

请以JSON格式返回结果：
{{
    "tags": ["标签1", "标签2", "标签3"],
    "demand_analysis": "需求分析文本"
}}""",
                height=300
            )

    # 开始标注
    if st.button("🚀 开始AI标注", type="primary", use_container_width=True):
        if pending_count == 0:
            st.warning("没有待标注的商品")
        else:
            with st.spinner(f"正在标注 {batch_size} 个商品..."):
                annotator = ProductAIAnnotator()
                result = annotator.annotate_batch(
                    batch_size=batch_size,
                    prompt_template=custom_prompt if use_custom_prompt else None
                )

            if result["success"]:
                st.success(f"""
                ✅ 标注完成！
                - 处理数量: {result['processed']}
                - 成功: {result['success_count']}
                - 失败: {result['failed_count']}
                """)

                # 刷新页面
                st.rerun()
            else:
                st.error(f"❌ 标注失败: {result.get('message', '未知错误')}")

    # 显示最近标注的商品
    st.subheader("最近标注的商品")

    recent_products = repo.get_all(
        ai_status="completed",
        limit=10,
        order_by="updated_at",
        order_dir="desc"
    )

    if recent_products:
        for product in recent_products:
            with st.expander(f"📦 {product['product_name'][:50]}..."):
                col1, col2 = st.columns(2)

                with col1:
                    st.write(f"**价格**: ${product['price']}")
                    st.write(f"**评分**: {product['rating']}⭐")
                    st.write(f"**平台**: {product['platform']}")

                with col2:
                    if product.get('tags'):
                        st.write(f"**标签**: {', '.join(product['tags'])}")

                if product.get('demand_analysis'):
                    st.write(f"**需求分析**: {product['demand_analysis']}")


# ==================== 5. 字段管理 ====================
def render_field_management():
    """渲染字段管理页面"""
    st.header("⚙️ 动态字段管理")

    st.info("💡 管理商品表的自定义字段，类似飞书多维表格")

    manager = ProductFieldManager()

    # 显示现有字段
    st.subheader("现有字段")

    fields = manager.get_all_fields()

    if fields:
        df = pd.DataFrame(fields)

        display_columns = [
            "field_id",
            "field_name",
            "field_key",
            "field_type",
            "is_required",
            "is_system_field",
            "field_order"
        ]

        st.dataframe(
            df[display_columns],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("暂无自定义字段")

    st.divider()

    # 添加新字段
    st.subheader("添加新字段")

    with st.form("add_field_form"):
        col1, col2 = st.columns(2)

        with col1:
            field_name = st.text_input(
                "字段名称",
                placeholder="例如：供应商名称"
            )

        with col2:
            field_key = st.text_input(
                "字段键名",
                placeholder="例如：supplier_name"
            )

        col1, col2 = st.columns(2)

        with col1:
            field_type = st.selectbox(
                "字段类型",
                ["text", "number", "date", "url", "tags", "select", "multi_select", "textarea"]
            )

        with col2:
            is_required = st.checkbox("必填字段", value=False)

        field_description = st.text_area(
            "字段描述",
            placeholder="描述这个字段的用途"
        )

        submitted = st.form_submit_button("➕ 添加字段", use_container_width=True)

        if submitted:
            if not field_name or not field_key:
                st.error("❌ 字段名称和键名不能为空")
            else:
                try:
                    field_id = manager.add_field(
                        field_name=field_name,
                        field_key=field_key,
                        field_type=field_type,
                        is_required=is_required,
                        field_description=field_description
                    )
                    st.success(f"✅ 字段添加成功！ID: {field_id}")
                    st.rerun()
                except ValueError as e:
                    st.error(f"❌ {str(e)}")

    st.divider()

    # 删除字段
    st.subheader("删除字段")

    if fields:
        # 只显示非系统字段
        custom_fields = [f for f in fields if not f['is_system_field']]

        if custom_fields:
            field_to_delete = st.selectbox(
                "选择要删除的字段",
                options=[f['field_id'] for f in custom_fields],
                format_func=lambda x: next(f['field_name'] for f in custom_fields if f['field_id'] == x)
            )

            if st.button("🗑️ 删除字段", type="secondary"):
                if manager.remove_field(field_to_delete):
                    st.success("✅ 字段删除成功")
                    st.rerun()
                else:
                    st.error("❌ 字段删除失败")
        else:
            st.info("暂无可删除的自定义字段")


# ==================== 6. 数据导出 ====================
def render_export():
    """渲染数据导出页面"""
    st.header("📤 数据导出")

    repo = ProductRepository()

    # 导出配置
    with st.expander("⚙️ 导出配置", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            export_format = st.selectbox(
                "导出格式",
                ["CSV", "Excel"]
            )

        with col2:
            platform = st.selectbox(
                "平台筛选",
                ["全部", "etsy", "gumroad"]
            )
            platform = None if platform == "全部" else platform

        # 字段选择
        st.write("**选择导出字段**")

        all_fields = [
            "product_id",
            "product_name",
            "description",
            "price",
            "sales",
            "rating",
            "review_count",
            "url",
            "shop_name",
            "platform",
            "tags",
            "demand_analysis",
            "ai_analysis_status"
        ]

        selected_fields = st.multiselect(
            "字段",
            options=all_fields,
            default=["product_name", "price", "rating", "review_count", "platform", "tags"]
        )

    # 导出按钮
    if st.button("📥 导出数据", type="primary", use_container_width=True):
        if not selected_fields:
            st.error("❌ 请至少选择一个字段")
        else:
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"products_export_{timestamp}"

            if export_format == "CSV":
                output_path = f"data/exports/{filename}.csv"
            else:
                output_path = f"data/exports/{filename}.xlsx"

            # 确保目录存在
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            # 执行导出
            with st.spinner("正在导出数据..."):
                exporter = ProductExporter()

                filters = {"platform": platform} if platform else None

                if export_format == "CSV":
                    result = exporter.export_to_csv(
                        output_path=output_path,
                        filters=filters,
                        selected_fields=selected_fields
                    )
                else:
                    result = exporter.export_to_excel(
                        output_path=output_path,
                        filters=filters,
                        selected_fields=selected_fields
                    )

            if result["success"]:
                st.success(f"""
                ✅ 导出成功！
                - 文件路径: {result['file_path']}
                - 行数: {result['row_count']}
                """)

                # 提供下载链接
                with open(result['file_path'], 'rb') as f:
                    st.download_button(
                        label="⬇️ 下载文件",
                        data=f,
                        file_name=Path(result['file_path']).name,
                        mime="text/csv" if export_format == "CSV" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            else:
                st.error(f"❌ 导出失败: {result.get('error', '未知错误')}")


# ==================== 7. 导入历史 ====================
def render_import_history():
    """渲染导入历史页面"""
    st.header("📋 导入历史")

    log_repo = ProductImportLogRepository()

    # 筛选条件
    col1, col2 = st.columns(2)

    with col1:
        platform = st.selectbox(
            "平台",
            ["全部", "etsy", "gumroad"]
        )
        platform = None if platform == "全部" else platform

    with col2:
        status = st.selectbox(
            "状态",
            ["全部", "in_progress", "completed", "failed"]
        )
        status = None if status == "全部" else status

    # 查询日志
    logs = log_repo.get_all(
        platform=platform,
        status=status,
        limit=50
    )

    if logs:
        # 显示日志列表
        for log in logs:
            status_emoji = {
                "in_progress": "⏳",
                "completed": "✅",
                "failed": "❌"
            }.get(log['import_status'], "❓")

            with st.expander(f"{status_emoji} {log['source_file']} - {log['imported_at'][:19]}"):
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.write(f"**平台**: {log['platform']}")
                    st.write(f"**状态**: {log['import_status']}")

                with col2:
                    st.write(f"**总行数**: {log['total_rows']}")
                    st.write(f"**成功导入**: {log['imported_rows']}")

                with col3:
                    st.write(f"**跳过**: {log['skipped_rows']}")
                    st.write(f"**耗时**: {log['duration_seconds']}秒")

                if log.get('error_message'):
                    st.error(f"错误信息: {log['error_message']}")

                if log.get('field_mapping'):
                    st.write("**字段映射**")
                    st.json(log['field_mapping'])
    else:
        st.info("暂无导入历史")


# ==================== 主入口 ====================
if __name__ == "__main__":
    render_page()

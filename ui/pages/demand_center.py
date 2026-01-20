"""
需求中心 - 需求溯源与管理

展示所有需求及其溯源信息，支持筛选、查看详情、验证等操作
"""
import streamlit as st
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime
import json

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.demand_provenance_service import DemandProvenanceService
from storage.models import get_session, Demand


def render():
    st.markdown('<div class="main-header">🎯 需求中心</div>', unsafe_allow_html=True)

    st.markdown("""
    ### 功能说明

    需求中心提供完整的需求溯源和管理功能：
    - 📊 查看所有需求及其来源
    - 🔍 按Phase、Method、验证状态筛选
    - 📈 查看置信度演化历史
    - ✅ 验证需求并提升置信度
    - 🔗 查看需求关联的商品、短语、Token
    """)

    st.markdown("---")

    # 初始化服务
    provenance_service = DemandProvenanceService()

    # 侧边栏：筛选选项
    with st.sidebar:
        st.markdown("### 🔍 筛选选项")

        # 按Phase筛选
        phase_filter = st.selectbox(
            "来源Phase",
            ["全部", "phase1", "phase2", "phase3", "phase4", "phase5", "phase6", "phase7", "manual"],
            index=0
        )

        # 按验证状态筛选
        validation_filter = st.selectbox(
            "验证状态",
            ["全部", "已验证", "未验证"],
            index=0
        )

        # 按置信度筛选
        confidence_filter = st.slider(
            "最低置信度",
            min_value=0.0,
            max_value=1.0,
            value=0.0,
            step=0.1
        )

    # 主内容区域
    tab1, tab2, tab3 = st.tabs(["📊 需求列表", "📈 统计分析", "🔍 需求详情"])

    with tab1:
        render_demand_list(provenance_service, phase_filter, validation_filter, confidence_filter)

    with tab2:
        render_statistics(provenance_service)

    with tab3:
        render_demand_detail(provenance_service)


def render_demand_list(service, phase_filter, validation_filter, confidence_filter):
    """渲染需求列表"""
    st.markdown("### 📋 需求列表")

    try:
        # 查询需求
        session = get_session()
        query = session.query(Demand)

        # 应用筛选
        if phase_filter != "全部":
            query = query.filter(Demand.source_phase == phase_filter)

        if validation_filter == "已验证":
            query = query.filter(Demand.is_validated == True)
        elif validation_filter == "未验证":
            query = query.filter(Demand.is_validated == False)

        if confidence_filter > 0:
            query = query.filter(Demand.confidence_score >= confidence_filter)

        demands = query.order_by(Demand.demand_id.desc()).limit(100).all()
        session.close()

        if not demands:
            st.info("没有找到符合条件的需求")
            return

        # 转换为DataFrame
        data = []
        for d in demands:
            data.append({
                "ID": d.demand_id,
                "标题": d.title[:50] + "..." if len(d.title) > 50 else d.title,
                "来源": f"{d.source_phase or 'unknown'} / {d.source_method or 'unknown'}",
                "置信度": f"{float(d.confidence_score or 0):.2f}",
                "验证状态": "✅ 已验证" if d.is_validated else "⏳ 未验证",
                "类型": d.demand_type or "other",
                "创建时间": d.discovered_at.strftime("%Y-%m-%d %H:%M") if d.discovered_at else "未知"
            })

        df = pd.DataFrame(data)

        # 显示统计
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("总需求数", len(demands))
        with col2:
            validated_count = sum(1 for d in demands if d.is_validated)
            st.metric("已验证", validated_count)
        with col3:
            avg_confidence = sum(float(d.confidence_score or 0) for d in demands) / len(demands)
            st.metric("平均置信度", f"{avg_confidence:.2f}")
        with col4:
            phase7_count = sum(1 for d in demands if d.source_phase == 'phase7')
            st.metric("Phase 7需求", phase7_count)

        st.markdown("---")

        # 显示表格
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        # 选择需求查看详情
        st.markdown("---")
        st.markdown("### 🔍 查看需求详情")

        demand_ids = [d.demand_id for d in demands]
        selected_id = st.selectbox(
            "选择需求ID",
            demand_ids,
            format_func=lambda x: f"需求 {x}: {next((d.title[:40] for d in demands if d.demand_id == x), 'Unknown')}"
        )

        if selected_id:
            st.session_state['selected_demand_id'] = selected_id

    except Exception as e:
        st.error(f"查询需求失败: {e}")
        import traceback
        st.code(traceback.format_exc())


def render_statistics(service):
    """渲染统计分析"""
    st.markdown("### 📊 需求来源统计")

    try:
        stats = service.get_demands_by_source()

        # 按Phase分布
        st.markdown("#### 按Phase分布")
        if stats['by_phase']:
            phase_data = []
            for phase, data in stats['by_phase'].items():
                phase_data.append({
                    "Phase": phase,
                    "需求数": data['count'],
                    "平均置信度": f"{data['avg_confidence']:.2f}"
                })

            df_phase = pd.DataFrame(phase_data)
            st.dataframe(df_phase, use_container_width=True, hide_index=True)

            # 可视化
            st.bar_chart(df_phase.set_index('Phase')['需求数'])
        else:
            st.info("暂无数据")

        st.markdown("---")

        # 按Method分布
        st.markdown("#### 按Method分布")
        if stats['by_method']:
            method_data = []
            for method, count in stats['by_method'].items():
                method_data.append({
                    "Method": method,
                    "需求数": count
                })

            df_method = pd.DataFrame(method_data)
            st.dataframe(df_method, use_container_width=True, hide_index=True)
        else:
            st.info("暂无数据")

        st.markdown("---")

        # 验证状态分布
        st.markdown("#### 验证状态分布")
        col1, col2 = st.columns(2)

        with col1:
            st.metric("已验证", stats['by_validation_status']['validated'])

        with col2:
            st.metric("未验证", stats['by_validation_status']['unvalidated'])

    except Exception as e:
        st.error(f"查询统计失败: {e}")


def render_demand_detail(service):
    """渲染需求详情"""
    st.markdown("### 🔍 需求详情")

    # 从session state获取选中的需求ID
    selected_id = st.session_state.get('selected_demand_id')

    if not selected_id:
        st.info("请先在「需求列表」标签页中选择一个需求")
        return

    try:
        # 获取完整溯源信息
        provenance = service.get_demand_provenance(selected_id)

        # 基本信息
        st.markdown("#### 📋 基本信息")
        col1, col2 = st.columns(2)

        with col1:
            st.write(f"**需求ID**: {provenance['demand']['demand_id']}")
            st.write(f"**标题**: {provenance['demand']['title']}")
            st.write(f"**类型**: {provenance['demand']['demand_type']}")
            st.write(f"**状态**: {provenance['demand']['status']}")

        with col2:
            st.write(f"**验证状态**: {'✅ 已验证' if provenance['demand']['is_validated'] else '⏳ 未验证'}")
            st.write(f"**验证次数**: {provenance['demand']['validation_count']}")
            st.write(f"**当前置信度**: {provenance['source']['confidence_score']:.2f}")

        if provenance['demand'].get('description'):
            st.markdown("**描述**:")
            st.write(provenance['demand']['description'])

        st.markdown("---")

        # 来源信息
        st.markdown("#### 📍 来源信息")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.write(f"**Phase**: {provenance['source']['phase']}")

        with col2:
            st.write(f"**Method**: {provenance['source']['method']}")

        with col3:
            discovered_at = provenance['source']['discovered_at']
            if discovered_at:
                st.write(f"**发现时间**: {discovered_at[:19]}")

        st.markdown("---")

        # 关联数据
        st.markdown("#### 🔗 关联数据")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("关联短语", len(provenance['related_phrases']))

        with col2:
            st.metric("关联商品", len(provenance['related_products']))

        with col3:
            st.metric("关联Token", len(provenance['related_tokens']))

        # 显示关联商品详情
        if provenance['related_products']:
            st.markdown("##### 关联商品")
            for prod in provenance['related_products']:
                with st.expander(f"商品 {prod['product_id']}: {prod['product_name'][:50]}"):
                    st.write(f"**适配度**: {prod['fit_level']} ({prod['fit_score']:.2f})")
                    st.write(f"**验证状态**: {'✅ 已验证' if prod['is_validated'] else '⏳ 未验证'}")
                    st.write(f"**创建时间**: {prod['created_at'][:19] if prod['created_at'] else '未知'}")

        st.markdown("---")

        # 置信度演化
        st.markdown("#### 📈 置信度演化")
        if provenance['confidence_history']:
            history_data = []
            for h in provenance['confidence_history']:
                history_data.append({
                    "时间": h['timestamp'][:19],
                    "置信度": h['score'],
                    "原因": h['reason']
                })

            df_history = pd.DataFrame(history_data)
            st.dataframe(df_history, use_container_width=True, hide_index=True)

            # 可视化
            st.line_chart(df_history.set_index('时间')['置信度'])
        else:
            st.info("暂无置信度历史")

        st.markdown("---")

        # 事件时间线
        st.markdown("#### ⏱️ 事件时间线")
        if provenance['event_timeline']:
            for i, event in enumerate(provenance['event_timeline'], 1):
                event_type_emoji = {
                    'created': '✨',
                    'updated': '📝',
                    'validated': '✅',
                    'linked_phrase': '🔗',
                    'linked_product': '🔗',
                    'linked_token': '🔗',
                    'confidence_changed': '📈',
                    'status_changed': '🔄'
                }.get(event['event_type'], '📌')

                st.write(f"{i}. {event_type_emoji} **[{event['event_type']}]** {event['description']}")
                st.caption(f"   时间: {event['timestamp'][:19]} | 触发者: {event['triggered_by']}")
        else:
            st.info("暂无事件记录")

        st.markdown("---")

        # 操作按钮
        st.markdown("#### ⚙️ 操作")

        col1, col2, col3 = st.columns(3)

        with col1:
            if not provenance['demand']['is_validated']:
                if st.button("✅ 验证需求", use_container_width=True):
                    try:
                        service.validate_demand(
                            demand_id=selected_id,
                            validated_by="user",
                            validation_notes="通过Web UI验证"
                        )
                        st.success("需求已验证！置信度已提升20%")
                        st.rerun()
                    except Exception as e:
                        st.error(f"验证失败: {e}")

        with col2:
            if st.button("🔄 刷新", use_container_width=True):
                st.rerun()

    except Exception as e:
        st.error(f"查询需求详情失败: {e}")
        import traceback
        st.code(traceback.format_exc())


if __name__ == "__main__":
    render()

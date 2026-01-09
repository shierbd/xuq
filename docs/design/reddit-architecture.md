# Reddit板块分析与标注系统 - 系统架构设计文档

**版本**: v1.0
**创建日期**: 2026-01-09
**作者**: Claude Code
**状态**: 设计完成

---

## 目录

1. [概述](#概述)
2. [系统架构图](#系统架构图)
3. [模块设计](#模块设计)
4. [数据流设计](#数据流设计)
5. [UI设计](#ui设计)
6. [集成方案](#集成方案)
7. [部署方案](#部署方案)

---

## 概述

### 系统定位

Reddit板块分析与标注系统是词根聚类需求挖掘系统的**独立功能模块**（Phase 6），用于分析Reddit板块数据，生成中文标签和重要性评分。

### 设计目标

- **独立性**: 与现有功能完全解耦，使用独立的数据表
- **复用性**: 复用现有的LLM集成和数据库连接
- **可扩展性**: 支持未来添加更多分析维度
- **易用性**: 提供友好的Web UI界面

---

## 系统架构图

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit Web UI                          │
│                  (ui/pages/phase6_reddit.py)                 │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐  │
│  │ 数据导入  │ AI配置   │ 板块列表  │ 标签管理  │ 数据导出  │  │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Business Logic Layer                        │
│                 (core/reddit_analyzer.py)                    │
│  ┌──────────────┬──────────────┬──────────────┐            │
│  │ 文件解析      │ AI分析引擎    │ 标签管理      │            │
│  │ import_data  │ analyze_*    │ tag_*        │            │
│  └──────────────┴──────────────┴──────────────┘            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Data Access Layer                           │
│              (storage/reddit_repository.py)                  │
│  ┌──────────────────────┬──────────────────────┐            │
│  │ RedditSubreddit      │ AIPromptConfig       │            │
│  │ Repository           │ Repository           │            │
│  └──────────────────────┴──────────────────────┘            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Database Layer                            │
│                  (MySQL / SQLite)                            │
│  ┌──────────────────────┬──────────────────────┐            │
│  │ reddit_subreddits    │ ai_prompt_configs    │            │
│  └──────────────────────┴──────────────────────┘            │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   External Services                          │
│                     (ai/client.py)                           │
│  ┌──────────────┬──────────────┬──────────────┐            │
│  │ OpenAI API   │ Anthropic    │ DeepSeek API │            │
│  └──────────────┴──────────────┴──────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

---

## 模块设计

### 1. 核心业务模块 (core/reddit_analyzer.py)

**职责**: Reddit板块分析的核心业务逻辑

**主要功能**:
```python
# 文件导入
- import_from_csv(file_path, batch_id) → 导入CSV文件
- import_from_excel(file_path, batch_id) → 导入Excel文件
- parse_file_without_headers(file_path) → 解析无列名文件
- validate_data(df) → 数据验证
- deduplicate_by_name(records) → 按名称去重

# AI分析
- analyze_subreddit(subreddit_data, config) → 分析单个板块
- batch_analyze(subreddit_list, config, batch_size=10) → 批量分析
- generate_tags(name, description, subscribers) → 生成标签
- calculate_importance(name, description, subscribers) → 计算重要性
- parse_ai_response(response) → 解析AI响应

# 标签管理
- get_all_tags() → 获取所有标签
- get_tag_statistics() → 获取标签统计
- group_by_tags(tags) → 按标签分组
- search_by_tags(tags) → 按标签搜索

# 数据导出
- export_to_csv(subreddit_ids, output_path) → 导出CSV
- export_to_excel(subreddit_ids, output_path) → 导出Excel
```

**模块结构**:
```python
# core/reddit_analyzer.py

from typing import Dict, Any, List, Optional
import pandas as pd
from datetime import datetime
from ai.client import LLMClient
from storage.reddit_repository import RedditSubredditRepository, AIPromptConfigRepository

class RedditAnalyzer:
    """Reddit板块分析器"""

    def __init__(self):
        self.llm_client = LLMClient()

    # 文件导入方法
    def import_from_csv(self, file_path: str, batch_id: Optional[str] = None) -> Dict[str, Any]:
        """从CSV导入数据"""
        pass

    def import_from_excel(self, file_path: str, batch_id: Optional[str] = None) -> Dict[str, Any]:
        """从Excel导入数据"""
        pass

    # AI分析方法
    def analyze_subreddit(self, subreddit_data: Dict, config: Dict) -> Dict[str, Any]:
        """分析单个板块"""
        pass

    def batch_analyze(self, subreddit_list: List[Dict], config: Dict, batch_size: int = 10) -> Dict[str, Any]:
        """批量分析板块"""
        pass

    # 标签管理方法
    def get_all_tags(self) -> List[str]:
        """获取所有标签"""
        pass

    def get_tag_statistics(self) -> Dict[str, int]:
        """获取标签统计"""
        pass

    # 导出方法
    def export_to_csv(self, subreddit_ids: List[int], output_path: str) -> str:
        """导出为CSV"""
        pass
```

---

### 2. 数据访问模块 (storage/reddit_repository.py)

**职责**: 封装数据库操作，提供CRUD接口

**主要类**:

#### RedditSubredditRepository

```python
class RedditSubredditRepository:
    """Reddit板块数据访问层"""

    def __init__(self, session=None):
        self.session = session or get_session()

    # 基础CRUD
    def create(self, data: Dict) -> int:
        """创建记录，返回ID"""

    def get_by_id(self, subreddit_id: int) -> Optional[Dict]:
        """按ID查询"""

    def get_by_name(self, name: str) -> Optional[Dict]:
        """按名称查询"""

    def update(self, subreddit_id: int, data: Dict) -> bool:
        """更新记录"""

    def delete(self, subreddit_id: int) -> bool:
        """删除记录"""

    # 批量操作
    def bulk_insert(self, records: List[Dict], batch_size: int = 1000) -> int:
        """批量插入"""

    def bulk_update(self, updates: List[Dict]) -> int:
        """批量更新"""

    # 查询方法
    def get_by_status(self, status: str, limit: int = 100) -> List[Dict]:
        """按状态查询"""

    def get_by_tags(self, tags: List[str]) -> List[Dict]:
        """按标签查询（OR查询）"""

    def get_by_batch(self, batch_id: str) -> List[Dict]:
        """按批次查询"""

    def query(self, filters: Dict, sort_by: str, sort_order: str, limit: int, offset: int) -> Dict:
        """通用查询方法"""

    # 统计方法
    def count_by_status(self) -> Dict[str, int]:
        """按状态统计"""

    def get_tag_statistics(self) -> Dict[str, int]:
        """获取标签统计"""

    # 状态更新
    def update_status(self, subreddit_id: int, status: str) -> bool:
        """更新分析状态"""
```

#### AIPromptConfigRepository

```python
class AIPromptConfigRepository:
    """AI提示词配置数据访问层"""

    def __init__(self, session=None):
        self.session = session or get_session()

    # 基础CRUD
    def create(self, data: Dict) -> int:
        """创建配置"""

    def get_by_id(self, config_id: int) -> Optional[Dict]:
        """按ID查询"""

    def update(self, config_id: int, data: Dict) -> bool:
        """更新配置"""

    def delete(self, config_id: int) -> bool:
        """删除配置"""

    # 查询方法
    def get_default_config(self, config_type: str = 'reddit_analysis') -> Optional[Dict]:
        """获取默认配置"""

    def get_active_configs(self, config_type: str = 'reddit_analysis') -> List[Dict]:
        """获取所有启用的配置"""

    def get_all_configs(self) -> List[Dict]:
        """获取所有配置"""

    # 配置管理
    def set_default(self, config_id: int) -> bool:
        """设置为默认配置"""

    def activate(self, config_id: int) -> bool:
        """启用配置"""

    def deactivate(self, config_id: int) -> bool:
        """禁用配置"""
```

---

### 3. 数据模型 (storage/models.py)

**新增模型**:

```python
# storage/models.py

from sqlalchemy import Column, Integer, String, Text, BigInteger, TIMESTAMP, Boolean, DECIMAL
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class RedditSubreddit(Base):
    """Reddit板块模型"""
    __tablename__ = 'reddit_subreddits'

    subreddit_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text)
    subscribers = Column(BigInteger, default=0)
    tag1 = Column(String(100))
    tag2 = Column(String(100))
    tag3 = Column(String(100))
    importance_score = Column(Integer)
    ai_analysis_status = Column(String(20), nullable=False, default='pending', index=True)
    ai_analysis_timestamp = Column(TIMESTAMP)
    ai_model_used = Column(String(100))
    ai_confidence = Column(Integer)
    notes = Column(Text)
    import_batch_id = Column(String(50), index=True)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<RedditSubreddit(id={self.subreddit_id}, name='{self.name}', status='{self.ai_analysis_status}')>"


class AIPromptConfig(Base):
    """AI提示词配置模型"""
    __tablename__ = 'ai_prompt_configs'

    config_id = Column(Integer, primary_key=True, autoincrement=True)
    config_name = Column(String(100), unique=True, nullable=False)
    config_type = Column(String(50), nullable=False, default='reddit_analysis', index=True)
    prompt_template = Column(Text, nullable=False)
    system_message = Column(Text)
    temperature = Column(DECIMAL(3, 2), default=0.7)
    max_tokens = Column(Integer, default=500)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    is_default = Column(Boolean, nullable=False, default=False, index=True)
    description = Column(Text)
    created_by = Column(String(100), default='system')
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<AIPromptConfig(id={self.config_id}, name='{self.config_name}', type='{self.config_type}')>"
```

---

## 数据流设计

### 1. 数据导入流程

```
用户上传文件 (CSV/Excel)
    ↓
Streamlit file_uploader
    ↓
保存临时文件
    ↓
RedditAnalyzer.import_from_csv/excel()
    ↓
pandas读取文件（无列名，按列顺序）
    ↓
数据验证
    - name非空
    - subscribers >= 0
    - description为空 → status='skipped'
    ↓
去重处理（按name，保留subscribers最大）
    ↓
生成batch_id
    ↓
RedditSubredditRepository.bulk_insert()
    ↓
批量插入数据库（每批1000条）
    ↓
返回导入统计
    ↓
UI显示结果
```

---

### 2. AI分析流程

```
用户点击"开始分析"
    ↓
选择AI配置（或使用默认配置）
    ↓
RedditAnalyzer.batch_analyze()
    ↓
查询待分析板块（status='pending'）
    ↓
获取AI配置
    ↓
批量处理（每批10条）
    ↓
对每个板块：
    ├─ 更新status='processing'
    ├─ 构建提示词（填充模板变量）
    ├─ 调用LLM API
    ├─ 解析JSON响应
    │   └─ {"tag1": "...", "tag2": "...", "tag3": "...", "importance_score": N, "confidence": N}
    ├─ 更新数据库
    │   ├─ tag1, tag2, tag3
    │   ├─ importance_score
    │   ├─ ai_confidence
    │   ├─ ai_analysis_status='completed'
    │   ├─ ai_analysis_timestamp
    │   └─ ai_model_used
    └─ 记录结果
    ↓
返回分析统计
    ↓
UI显示进度和结果
```

---

### 3. 标签筛选流程

```
用户选择标签（multiselect）
    ↓
构建筛选条件
    filters = {'tags': ['标签1', '标签2']}
    ↓
RedditSubredditRepository.query()
    ↓
构建SQL查询
    WHERE tag1 IN (...) OR tag2 IN (...) OR tag3 IN (...)
    ↓
执行查询
    ↓
返回匹配的板块列表
    ↓
UI显示结果（data_editor）
```

---

## UI设计

### 页面布局 (ui/pages/phase6_reddit.py)

```python
import streamlit as st
from core.reddit_analyzer import RedditAnalyzer

# 页面标题
st.title("🔍 Reddit板块分析与标注系统")

# 创建选项卡
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📥 数据导入",
    "⚙️ AI配置",
    "📊 板块列表",
    "🏷️ 标签管理",
    "📤 数据导出"
])

# Tab 1: 数据导入
with tab1:
    st.header("数据导入")

    # 文件上传
    uploaded_file = st.file_uploader(
        "上传CSV或Excel文件（无列名，3列：名称、描述、订阅数）",
        type=['csv', 'xlsx', 'xls']
    )

    # 批次ID
    batch_id = st.text_input(
        "导入批次ID（可选）",
        placeholder="留空自动生成"
    )

    # 导入按钮
    if st.button("开始导入", type="primary"):
        if uploaded_file:
            with st.spinner("正在导入..."):
                # 保存临时文件
                temp_path = f"/tmp/{uploaded_file.name}"
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                # 导入数据
                analyzer = RedditAnalyzer()
                file_type = 'csv' if uploaded_file.name.endswith('.csv') else 'excel'
                result = analyzer.import_from_csv(temp_path, batch_id) if file_type == 'csv' else analyzer.import_from_excel(temp_path, batch_id)

                # 显示结果
                if result['success']:
                    st.success(result['message'])
                    col1, col2, col3 = st.columns(3)
                    col1.metric("导入成功", result['data']['imported_count'])
                    col2.metric("跳过", result['data']['skipped_count'])
                    col3.metric("错误", result['data']['error_count'])
                else:
                    st.error(result['message'])
        else:
            st.warning("请先上传文件")

# Tab 2: AI配置
with tab2:
    st.header("AI配置管理")

    # 配置选择
    configs = get_prompt_configs()
    config_names = [c['config_name'] for c in configs['data']]
    selected_config = st.selectbox("选择配置", config_names)

    # 配置编辑
    if selected_config:
        config = next(c for c in configs['data'] if c['config_name'] == selected_config)

        config_name = st.text_input("配置名称", value=config['config_name'])
        prompt_template = st.text_area("提示词模板", value=config['prompt_template'], height=300)
        system_message = st.text_area("系统消息", value=config['system_message'], height=100)

        col1, col2 = st.columns(2)
        temperature = col1.slider("温度参数", 0.0, 2.0, float(config['temperature']), 0.1)
        max_tokens = col2.number_input("最大Token数", 100, 10000, config['max_tokens'])

        col3, col4 = st.columns(2)
        is_active = col3.checkbox("启用", value=config['is_active'])
        is_default = col4.checkbox("设为默认", value=config['is_default'])

        # 保存按钮
        if st.button("保存配置"):
            # 保存逻辑
            pass

# Tab 3: 板块列表
with tab3:
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
        all_tags = get_all_tags()
        tag_filter = st.multiselect("标签筛选", all_tags)

    with col3:
        score_range = st.slider("重要性评分", 1, 5, (1, 5))

    # 排序
    sort_by = st.selectbox(
        "排序方式",
        ['创建时间', '订阅人数', '重要性评分'],
        index=0
    )

    # 查询数据
    filters = {
        'status': status_filter,
        'tags': tag_filter,
        'importance_score_min': score_range[0],
        'importance_score_max': score_range[1]
    }

    result = query_subreddits(filters=filters, sort_by='created_at', limit=100)

    if result['success']:
        df = pd.DataFrame(result['data']['data'])

        # 数据表格（可编辑）
        edited_df = st.data_editor(
            df,
            column_config={
                "subreddit_id": st.column_config.NumberColumn("ID", disabled=True),
                "name": st.column_config.TextColumn("板块名称", disabled=True),
                "subscribers": st.column_config.NumberColumn("订阅数", disabled=True),
                "tag1": st.column_config.TextColumn("标签1"),
                "tag2": st.column_config.TextColumn("标签2"),
                "tag3": st.column_config.TextColumn("标签3"),
                "importance_score": st.column_config.NumberColumn("评分", min_value=1, max_value=5),
                "ai_analysis_status": st.column_config.SelectboxColumn("状态", options=['pending', 'completed', 'failed'])
            },
            hide_index=True,
            use_container_width=True
        )

        # 操作按钮
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("批量分析"):
                # 分析逻辑
                pass

        with col2:
            if st.button("保存修改"):
                # 保存逻辑
                pass

        with col3:
            if st.download_button(
                "导出CSV",
                data=df.to_csv(index=False).encode('utf-8'),
                file_name=f"reddit_subreddits_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            ):
                st.success("导出成功")

# Tab 4: 标签管理
with tab4:
    st.header("标签管理")

    # 标签统计
    tag_stats = get_tag_statistics()

    if tag_stats['success']:
        st.subheader("标签统计")

        # 标签云（使用columns显示）
        tags = tag_stats['data']['tag_counts']
        sorted_tags = sorted(tags.items(), key=lambda x: x[1], reverse=True)

        for i in range(0, len(sorted_tags), 4):
            cols = st.columns(4)
            for j, (tag, count) in enumerate(sorted_tags[i:i+4]):
                cols[j].metric(tag, count)

        # 按标签分组查看
        st.subheader("按标签查看板块")
        selected_tag = st.selectbox("选择标签", [t[0] for t in sorted_tags])

        if selected_tag:
            result = query_subreddits(filters={'tags': [selected_tag]})
            if result['success']:
                st.dataframe(result['data']['data'])

# Tab 5: 数据导出
with tab5:
    st.header("数据导出")

    # 导出选项
    export_format = st.radio("导出格式", ['CSV', 'Excel'])

    # 筛选条件
    st.subheader("筛选条件")
    export_status = st.multiselect("状态", ['pending', 'completed', 'failed'], default=['completed'])
    export_tags = st.multiselect("标签", get_all_tags())

    # 导出按钮
    if st.button("生成导出文件"):
        filters = {
            'status': export_status,
            'tags': export_tags
        }

        result = query_subreddits(filters=filters, limit=10000)

        if result['success']:
            df = pd.DataFrame(result['data']['data'])

            if export_format == 'CSV':
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "下载CSV文件",
                    data=csv,
                    file_name=f"reddit_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            else:
                # Excel导出逻辑
                pass
```

---

## 集成方案

### 与现有系统的集成

#### 1. 复用LLM客户端 (ai/client.py)

```python
# 在 core/reddit_analyzer.py 中
from ai.client import LLMClient

class RedditAnalyzer:
    def __init__(self):
        # 复用现有的LLM客户端
        self.llm_client = LLMClient()

    def analyze_subreddit(self, subreddit_data, config):
        # 调用LLM
        response = self.llm_client.chat(
            messages=[
                {"role": "system", "content": config['system_message']},
                {"role": "user", "content": prompt}
            ],
            temperature=config['temperature'],
            max_tokens=config['max_tokens']
        )
        return response
```

#### 2. 复用数据库连接 (storage/models.py)

```python
# 在 storage/models.py 中添加新模型
from storage.models import Base, get_engine, get_session

# 新增模型会自动使用现有的数据库连接
class RedditSubreddit(Base):
    __tablename__ = 'reddit_subreddits'
    # ...

class AIPromptConfig(Base):
    __tablename__ = 'ai_prompt_configs'
    # ...

# 创建表
def create_reddit_tables():
    engine = get_engine()
    Base.metadata.create_all(engine, tables=[
        RedditSubreddit.__table__,
        AIPromptConfig.__table__
    ])
```

#### 3. 集成到Web UI (web_ui.py)

```python
# 在 web_ui.py 中添加新页面
import streamlit as st

# 侧边栏导航
page = st.sidebar.selectbox(
    "选择功能",
    [
        "仪表盘",
        "Phase 0: 词根管理",
        "Phase 1: 数据导入",
        "Phase 2: 聚类执行",
        "Phase 3: 聚类筛选",
        "Phase 4: 需求卡片",
        "Phase 5: Token管理",
        "Phase 6: Reddit分析",  # 新增
        "配置页面",
        "文档页面"
    ]
)

# 路由
if page == "Phase 6: Reddit分析":
    from ui.pages import phase6_reddit
    phase6_reddit.render()
```

---

## 部署方案

### 开发环境

```bash
# 1. 创建数据库表
python
>>> from storage.models import create_reddit_tables
>>> create_reddit_tables()

# 2. 启动Streamlit
streamlit run web_ui.py
```

### 生产环境

```bash
# 使用Docker Compose
docker-compose up -d
```

---

**文档版本**: v1.0
**最后更新**: 2026-01-09

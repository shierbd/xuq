# MVP版本实施方案（基于GPT反馈调整）

**调整日期**: 2024-12-19
**调整原因**: 原方案过度设计，现聚焦MVP快速验证
**核心目标**: 2周内完成Phase 1-4，产出第一批需求卡片

---

## 🎯 核心变化总结

### 变化对比表

| 维度 | 原方案 | MVP方案 | 变化原因 |
|------|--------|---------|----------|
| **架构模块** | 10+模块 | 4个核心模块 | 降低维护复杂度 |
| **数据表字段** | demands 17字段 | demands 9字段 | 去除未使用的商业化字段 |
| **UI方案** | Web界面 | 导出+手工+回写 | 快速验证，避免前端开发 |
| **开发周期** | 3-4周 | 2周 | 聚焦核心流程 |
| **Phase范围** | Phase 1-6 | Phase 1-4 + 简化5/7 | 优先级重排 |

---

## 📦 一、简化后的架构

### 1.1 目录结构（从10+模块缩减到4个核心）

```
词根聚类需求挖掘/
│
├── config/
│   ├── __init__.py
│   └── settings.py              # 统一配置（数据库、聚类、LLM）
│
├── core/                         # 核心业务逻辑
│   ├── __init__.py
│   ├── data_integration.py       # 数据整合清洗
│   ├── clustering.py             # 大组+小组聚类引擎
│   ├── embedding.py              # Embedding服务（带缓存）
│   └── incremental.py            # 增量更新逻辑
│
├── storage/                      # 数据库访问层
│   ├── __init__.py
│   ├── models.py                 # SQLAlchemy模型（Phrase, Demand, Token, ClusterMeta）
│   └── repository.py             # 数据库CRUD封装
│
├── ai/                           # LLM集成
│   ├── __init__.py
│   ├── client.py                 # LLM API调用封装
│   └── prompts.py                # Prompt模板
│
├── scripts/                      # 入口脚本
│   ├── run_phase1_import.py      # 运行阶段1：数据导入
│   ├── run_phase2_clustering.py  # 运行阶段2：大组聚类
│   ├── run_phase3_selection.py   # 运行阶段3：导出大组报告
│   ├── run_phase4_demands.py     # 运行阶段4：小组+需求卡片
│   ├── import_selection.py       # 导入人工选择结果
│   └── run_incremental.py        # 增量更新
│
├── utils/                        # 工具函数
│   ├── __init__.py
│   └── helpers.py                # 文本处理、导出等
│
├── data/                         # 数据目录（.gitignore排除）
├── docs/                         # 文档
├── requirements.txt
└── README.md
```

**对比原方案**：
- ❌ 删除：services/（过度封装）
- ❌ 删除：pipelines/（用scripts/替代）
- ❌ 删除：ui/（Web界面暂不实现）
- ❌ 删除：tests/（MVP先跑通再补测试）
- ❌ 删除：migrations/（直接创建表，不需要迁移）

---

## 🗄️ 二、MVP版数据表设计

### 2.1 phrases表（短语总库）

**保留字段**（从17个缩减到13个）：

```sql
CREATE TABLE phrases (
    phrase_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    phrase VARCHAR(255) UNIQUE NOT NULL,

    -- 来源信息
    seed_word VARCHAR(100),
    source_type ENUM('semrush', 'dropdown', 'related_search'),
    first_seen_round INT NOT NULL,

    -- 统计数据
    frequency BIGINT DEFAULT 1,
    volume BIGINT DEFAULT 0,

    -- 聚类分配
    cluster_id_A INT,
    cluster_id_B INT,

    -- 需求关联
    mapped_demand_id INT,

    -- 处理状态
    processed_status ENUM('unseen', 'reviewed', 'assigned', 'archived') DEFAULT 'unseen',

    -- 元数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_cluster_A (cluster_id_A),
    INDEX idx_status (processed_status),
    INDEX idx_round (first_seen_round)
);
```

**删除字段**（暂不实现）：
- ❌ cpc, keyword_difficulty（商业化指标）
- ❌ word_count, phrase_length, query_type（特征工程暂不用）
- ❌ has_question_word（特征工程暂不用）

---

### 2.2 demands表（需求卡片库）

**MVP版字段**（从17个缩减到9个核心字段）：

```sql
CREATE TABLE demands (
    demand_id INT PRIMARY KEY AUTO_INCREMENT,

    -- 需求描述（核心）
    title VARCHAR(255) NOT NULL,
    description TEXT,
    user_scenario TEXT,

    -- 分类
    demand_type ENUM('tool', 'content', 'service', 'education', 'other'),

    -- 关联信息
    source_cluster_A INT,
    source_cluster_B INT,
    related_phrases_count INT DEFAULT 0,

    -- 商业评估（简化）
    business_value ENUM('high', 'medium', 'low', 'unknown') DEFAULT 'unknown',

    -- 状态追踪
    status ENUM('idea', 'validated', 'in_progress', 'archived') DEFAULT 'idea',

    -- 元数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_status (status),
    INDEX idx_type (demand_type),
    INDEX idx_cluster_A (source_cluster_A)
);
```

**删除字段**（Phase 6再加）：
- ❌ monetization_potential（暂无法评估）
- ❌ competition_level（暂无法评估）
- ❌ revenue, landing_url, product_id（还没产品）
- ❌ tags, main_tokens（JSON字段暂不用）
- ❌ priority（简化为business_value）

---

### 2.3 tokens表（需求框架词库）

**MVP版字段**（从13个缩减到7个）：

```sql
CREATE TABLE tokens (
    token_id INT PRIMARY KEY AUTO_INCREMENT,
    token_text VARCHAR(100) UNIQUE NOT NULL,

    -- 分类（核心）
    token_type ENUM('intent', 'action', 'object', 'attribute', 'condition', 'other') NOT NULL,

    -- 统计信息
    in_phrase_count INT DEFAULT 0,

    -- 来源追踪
    first_seen_round INT NOT NULL,

    -- 验证状态
    verified BOOLEAN DEFAULT FALSE,
    notes TEXT,

    -- 元数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_type (token_type),
    INDEX idx_frequency (in_phrase_count DESC)
);
```

**删除字段**（Phase 5完整版再加）：
- ❌ sub_category（暂不细分）
- ❌ in_demand_count, total_frequency（Phase 5再统计）
- ❌ synonyms, related_tokens（JSON关联暂不做）
- ❌ commercial_value, avg_cpc, avg_competition（商业化指标暂不用）

---

### 2.4 cluster_meta表（聚类元数据）

**MVP版字段**（简化为10个核心字段）：

```sql
CREATE TABLE cluster_meta (
    cluster_id INT PRIMARY KEY,
    cluster_level ENUM('A', 'B') NOT NULL,
    parent_cluster_id INT,

    -- 统计信息
    size INT,
    total_frequency BIGINT,

    -- 代表信息
    example_phrases TEXT,
    main_theme VARCHAR(255),

    -- 选择状态（关键！）
    is_selected BOOLEAN DEFAULT FALSE,
    selection_score INT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_level (cluster_level),
    INDEX idx_selected (is_selected)
);
```

**删除字段**：
- ❌ seed_words_in_cluster（暂不统计）
- ❌ cohesion_score, noise_ratio（质量指标Phase 2完整版再加）
- ❌ selection_reason（先用selection_score数字即可）

---

## 🔄 三、MVP版工作流程

### 3.1 Phase 1：数据导入（1天）

**脚本**: `scripts/run_phase1_import.py`

```python
# 伪代码示例
from core.data_integration import DataIntegrator
from storage.repository import PhraseRepository

def main():
    # 1. 读取三种数据源
    integrator = DataIntegrator()
    semrush_data = integrator.load_semrush("原始词/sm导出词")
    dropdown_data = integrator.load_dropdown("原始词/下拉词")
    related_data = integrator.load_related("原始词/相关搜索.xlsx")

    # 2. 合并、清洗、去重
    merged = integrator.merge_all([semrush_data, dropdown_data, related_data])
    cleaned = integrator.clean(merged)

    # 3. 写入数据库
    repo = PhraseRepository()
    repo.bulk_insert(cleaned, first_seen_round=1)

    print(f"✓ 导入完成：{len(cleaned)} 条短语")
```

**输出**：
- 数据库 phrases 表填充完毕
- 日志：data/logs/phase1_import.log

---

### 3.2 Phase 2：大组聚类（1天）

**脚本**: `scripts/run_phase2_clustering.py`

```python
from core.clustering import ClusteringEngine
from core.embedding import EmbeddingService
from storage.repository import PhraseRepository, ClusterMetaRepository

def main():
    # 1. 从数据库读取所有短语
    repo = PhraseRepository()
    phrases = repo.get_all()

    # 2. 聚类引擎
    embedding_service = EmbeddingService(model='all-MiniLM-L6-v2')
    clustering = ClusteringEngine(embedding_service)

    # 3. 大组聚类
    labels, cluster_meta = clustering.fit_large_clusters(
        phrases,
        min_cluster_size=30,
        min_samples=3
    )

    # 4. 更新数据库
    repo.update_cluster_A(phrases, labels)
    ClusterMetaRepository().save_batch(cluster_meta)

    print(f"✓ 大组聚类完成：{len(set(labels))} 个大组")
```

**输出**：
- phrases.cluster_id_A 更新
- cluster_meta 表填充（cluster_level='A'）
- 缓存：data/cache/embeddings_round1.npz

---

### 3.3 Phase 3：大组筛选（半天 + 人工时间）

**步骤A：脚本生成报告**

`scripts/run_phase3_selection.py`

```python
from ai.client import LLMClient
from storage.repository import ClusterMetaRepository
import pandas as pd

def main():
    # 1. 读取大组元数据
    clusters = ClusterMetaRepository().get_all_level_A()

    # 2. AI生成主题标签
    llm = LLMClient(provider='openai')
    for cluster in clusters:
        theme = llm.generate_cluster_theme(
            example_phrases=cluster.example_phrases.split('; '),
            cluster_size=cluster.size
        )
        cluster.main_theme = theme['theme']

    # 3. 生成HTML报告
    df = pd.DataFrame([{
        'cluster_id': c.cluster_id,
        'size': c.size,
        'total_frequency': c.total_frequency,
        'main_theme': c.main_theme,
        'example_phrases': c.example_phrases,
        'selection_score': '',  # 空白，供人工填写
    } for c in clusters])

    df.to_html('data/output/cluster_selection_report.html', index=False)
    df.to_csv('data/output/cluster_selection_report.csv', index=False)

    print("✓ 报告生成完成，请在CSV中填写 selection_score (1-5)")
    print("  选中的大组打分 4-5，其他打分 1-3")
```

**步骤B：人工操作**

1. 打开 `data/output/cluster_selection_report.html`（浏览器翻译）
2. 在 `cluster_selection_report.csv` 中：
   - 阅读 main_theme 和 example_phrases
   - 在 selection_score 列填写 1-5 分
   - 4-5分 = 选中，1-3分 = 不选中
3. 保存CSV

**步骤C：导入选择结果**

`scripts/import_selection.py`

```python
import pandas as pd
from storage.repository import ClusterMetaRepository

def main():
    # 读取人工打分
    df = pd.read_csv('data/output/cluster_selection_report.csv')

    # 更新数据库
    repo = ClusterMetaRepository()
    for _, row in df.iterrows():
        repo.update(
            cluster_id=row['cluster_id'],
            selection_score=row['selection_score'],
            is_selected=(row['selection_score'] >= 4)
        )

    selected_count = len(df[df['selection_score'] >= 4])
    print(f"✓ 选中 {selected_count} 个大组")
```

---

### 3.4 Phase 4：小组聚类 + 需求卡片（2-3天）

**步骤A：小组聚类 + AI生成需求初稿**

`scripts/run_phase4_demands.py`

```python
from core.clustering import ClusteringEngine
from ai.client import LLMClient
from storage.repository import (
    ClusterMetaRepository, PhraseRepository, DemandRepository
)

def main():
    # 1. 读取选中的大组
    selected_clusters = ClusterMetaRepository().get_selected()

    clustering = ClusteringEngine()
    llm = LLMClient()
    demands = []

    # 2. 对每个选中的大组
    for cluster_A in selected_clusters:
        # 2.1 获取该大组的短语
        phrases = PhraseRepository().get_by_cluster_A(cluster_A.cluster_id)

        # 2.2 小组聚类
        labels_B = clustering.fit_small_clusters(
            phrases,
            parent_cluster_id=cluster_A.cluster_id
        )
        PhraseRepository().update_cluster_B(phrases, labels_B)

        # 2.3 为每个小组生成需求卡片初稿
        for cluster_B_id in set(labels_B):
            if cluster_B_id == -1:  # 跳过噪音
                continue

            phrases_in_B = [p for p, label in zip(phrases, labels_B) if label == cluster_B_id]

            # AI生成需求卡片
            demand_draft = llm.generate_demand_card(
                phrases=[p.phrase for p in phrases_in_B],
                cluster_theme=cluster_A.main_theme
            )

            # 保存到数据库
            demand = DemandRepository().create(
                title=demand_draft['title'],
                description=demand_draft['description'],
                user_scenario=demand_draft.get('user_scenario', ''),
                demand_type=demand_draft.get('demand_type', 'other'),
                source_cluster_A=cluster_A.cluster_id,
                source_cluster_B=cluster_B_id,
                status='idea'
            )
            demands.append(demand)

    # 3. 导出需求卡片供审核
    df = pd.DataFrame([{
        'demand_id': d.demand_id,
        'title': d.title,
        'description': d.description,
        'user_scenario': d.user_scenario,
        'demand_type': d.demand_type,
        'related_phrases_count': d.related_phrases_count,
        'business_value': '',  # 供人工填写
        'status': 'idea',      # 供人工修改
    } for d in demands])

    df.to_csv('data/output/demands_draft.csv', index=False)
    print(f"✓ 生成 {len(demands)} 个需求卡片初稿")
    print("  请在 demands_draft.csv 中审核并修改")
```

**步骤B：人工审核**

1. 打开 `data/output/demands_draft.csv`
2. 对每个需求：
   - 阅读 title, description, user_scenario
   - 修改不准确的描述
   - 填写 business_value (high/medium/low)
   - 修改 status：
     - `validated` = 确认有效
     - `archived` = 删除/无效
3. 保存CSV

**步骤C：导入审核结果**

```python
# 在 run_phase4_demands.py 末尾添加
def import_reviewed_demands():
    df = pd.read_csv('data/output/demands_draft.csv')
    repo = DemandRepository()

    for _, row in df.iterrows():
        repo.update(
            demand_id=row['demand_id'],
            title=row['title'],
            description=row['description'],
            business_value=row['business_value'],
            status=row['status']
        )

        # 更新phrases的mapped_demand_id
        if row['status'] == 'validated':
            phrases = PhraseRepository().get_by_cluster_B(row['source_cluster_B'])
            PhraseRepository().map_to_demand(phrases, row['demand_id'])

    print("✓ 需求卡片审核完成")
```

---

### 3.5 Phase 5（简化版）：tokens提取（1天）

**仅提取核心tokens，不做复杂分类**

```python
from utils.helpers import extract_tokens
from ai.client import LLMClient
from storage.repository import TokenRepository

def main():
    # 1. 获取已验证需求的短语
    phrases = PhraseRepository().get_mapped_to_demands()

    # 2. 粗拆词
    candidate_tokens = extract_tokens([p.phrase for p in phrases])

    # 3. AI批量分类（简化版：只分intent/action/object/other）
    llm = LLMClient()
    classifications = llm.batch_classify_tokens(
        tokens=[t['text'] for t in candidate_tokens],
        batch_size=50
    )

    # 4. 保存
    repo = TokenRepository()
    for candidate, classification in zip(candidate_tokens, classifications):
        repo.create(
            token_text=candidate['text'],
            token_type=classification['token_type'],
            in_phrase_count=candidate['frequency'],
            first_seen_round=1,
            verified=False
        )

    print(f"✓ 提取 {len(candidate_tokens)} 个tokens")
```

---

### 3.6 Phase 7（简化版）：增量更新（1天）

**只实现核心：导入+去重+分配大组+标记状态**

```python
from core.incremental import IncrementalUpdater

def main():
    updater = IncrementalUpdater(round_id=2)

    # 1. 导入新数据
    new_phrases, updated_phrases = updater.import_new_data([
        "原始词/第二轮/sm导出词",
        "原始词/第二轮/下拉词"
    ])

    # 2. 分配到大组
    updater.assign_to_large_clusters(new_phrases)

    # 3. 过滤：只处理未处理的新短语
    actionable = updater.filter_actionable(new_phrases)

    print(f"✓ 新增 {len(new_phrases)} 条短语")
    print(f"  待处理: {len(actionable)} 条")
    print("  后续可运行 Phase 4 对这些新短语生成需求")
```

**小组重聚类**暂不自动做，等需要时手动运行Phase 4脚本

---

## ⏱️ 四、MVP开发时间表

### 4.1 第一周

| 天数 | 任务 | 产出 |
|------|------|------|
| Day 1 | 搭建架构、创建数据库表 | 目录结构、models.py |
| Day 2 | Phase 1 实现 | 数据导入脚本、phrases表有数据 |
| Day 3 | Phase 2 实现 | 大组聚类脚本、cluster_meta有数据 |
| Day 4 | Phase 3 实现 | 大组报告生成、AI主题标签 |
| Day 5 | 人工筛选大组 | 选出10-15个目标大组 |

### 4.2 第二周

| 天数 | 任务 | 产出 |
|------|------|------|
| Day 6-7 | Phase 4 实现（小组+需求） | 需求卡片初稿 |
| Day 8 | 人工审核需求卡片 | 确认10-20个有效需求 |
| Day 9 | Phase 5 简化实现（可选） | tokens基础词库 |
| Day 10 | Phase 7 简化实现 + 测试 | 增量更新脚本 |

**总计**: 10个工作日（2周）

---

## 🔐 五、关键实现细节（必须遵守）

### 5.1 严禁物理删除大组

```python
# ❌ 禁止这样做
def delete_cluster(cluster_id):
    db.execute("DELETE FROM cluster_meta WHERE cluster_id = ?", cluster_id)
    db.execute("UPDATE phrases SET cluster_id_A = NULL WHERE cluster_id_A = ?", cluster_id)

# ✅ 正确做法：只改标记
def unselect_cluster(cluster_id):
    ClusterMetaRepository().update(
        cluster_id=cluster_id,
        is_selected=False,
        selection_score=0
    )
```

### 5.2 增量过滤规则（写死不变）

```python
def filter_actionable_phrases(phrases):
    """只处理真正需要处理的新短语"""
    actionable = []

    for phrase in phrases:
        # 规则1: 必须是未处理的
        if phrase.processed_status != 'unseen':
            continue

        # 规则2: 如果已关联需求，检查需求状态
        if phrase.mapped_demand_id:
            demand = DemandRepository().get(phrase.mapped_demand_id)
            # 如果需求已稳定，不再处理
            if demand.status in ['validated', 'in_progress']:
                phrase.processed_status = 'archived'
                PhraseRepository().update(phrase)
                continue

        # 规则3: 噪音点且频次很低，直接归档
        if phrase.cluster_id_A == -1 and phrase.frequency < 10:
            phrase.processed_status = 'archived'
            PhraseRepository().update(phrase)
            continue

        actionable.append(phrase)

    return actionable
```

### 5.3 Embedding模型版本固定

```python
# config/settings.py
EMBEDDING_MODEL = 'all-MiniLM-L6-v2'
EMBEDDING_MODEL_VERSION = '2.2.0'  # 记录版本

# core/embedding.py
class EmbeddingService:
    def __init__(self):
        self.model_name = EMBEDDING_MODEL
        self.model_version = EMBEDDING_MODEL_VERSION

        # 检查缓存是否匹配版本
        if os.path.exists('data/cache/model_version.txt'):
            cached_version = open('data/cache/model_version.txt').read()
            if cached_version != self.model_version:
                raise ValueError(
                    f"Embedding模型版本不匹配！\n"
                    f"缓存版本: {cached_version}\n"
                    f"当前版本: {self.model_version}\n"
                    f"请删除缓存或重新生成embeddings"
                )
```

---

## 📊 六、MVP成功标准

完成以下标准，即认为MVP成功：

### 6.1 数据验证
- [x] phrases 表有 50,000+ 条数据
- [x] cluster_meta 表有 60-100 个大组
- [x] 选中 10-15 个目标大组
- [x] demands 表有 20-50 个需求卡片
- [x] 至少10个需求 status='validated'

### 6.2 流程验证
- [x] Phase 1-4 全部跑通
- [x] 人工筛选流程（导出→手工→导入）可用
- [x] AI生成的需求卡片准确率 >60%
- [x] 增量更新不会重复处理已有需求

### 6.3 可用性验证
- [x] 从5万词产出10-20个可落地的需求想法
- [x] 每个需求下有真实的搜索短语支撑
- [x] 能够快速定位"哪些词属于同一需求"

---

## 🚀 七、MVP之后的迭代路径

完成MVP后，按以下优先级迭代：

### 第二轮迭代（+2周）
1. **Phase 5 完整版**：tokens词库完善
2. **Phase 7 完整版**：增量小组重聚类
3. **数据表字段扩展**：添加 tags, main_tokens (JSON)

### 第三轮迭代（+2周）
4. **Web UI**：ClusterSelector, DemandEditor
5. **批量操作功能**：合并需求、批量标记
6. **导出工具**：SEO词表、Landing Page素材

### 第四轮迭代（有产品后）
7. **Phase 6**：商业化字段（revenue, landing_url）
8. **数据可视化**：需求地图、词云、趋势图
9. **自动化Pipeline**：定期扫描新词、自动推送报告

---

## 📝 八、总结

### 与原方案对比

| 维度 | 原方案 | MVP方案 | 收益 |
|------|--------|---------|------|
| 开发周期 | 3-4周 | 2周 | ⏱️ 节省50%时间 |
| 架构模块 | 10+模块 | 4个核心模块 | 🧩 降低70%复杂度 |
| 代码量 | ~5000行 | ~2000行 | 📉 减少60%代码 |
| 数据表字段 | 47个字段 | 29个字段 | 🗄️ 减少40%字段 |
| UI工作量 | Web界面 | 导出+手工 | 🎨 省去前端开发 |
| 首次产出 | Phase 1-6 | Phase 1-4 | 🎯 更快验证价值 |

### 核心保留

✅ **流程逻辑**：0-7阶段完全保留
✅ **三张表**：phrases/demands/tokens架构保留
✅ **关键策略**：
  - 大组不删除，用is_selected标记
  - 增量过滤避免重复处理
  - Embedding模型版本固定

### 核心简化

✅ **架构**：从10+模块减少到4个核心模块
✅ **字段**：删除40%暂不使用的字段
✅ **UI**：用导出+手工替代Web界面
✅ **优先级**：Phase 1-4 必做，5/7 简化，6 延后

---

**最后更新**: 2024-12-19
**版本**: MVP v1.0（基于GPT反馈调整）
**预计完成**: 2周内产出第一批需求卡片

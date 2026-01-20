# 需求溯源系统 - 快速开始指南

## 🚀 5分钟快速上手

本指南帮助你快速部署和使用需求溯源系统。

---

## 📋 前置条件

- ✅ Python 3.8+
- ✅ MySQL/MariaDB 或 SQLite
- ✅ 已有的词根聚类需求挖掘系统

---

## 🔧 步骤1: 数据库迁移 (2分钟)

### 1.1 备份数据库

```bash
# MySQL备份
mysqldump -u root -p keyword_clustering > backup_$(date +%Y%m%d).sql

# SQLite备份
cp keyword_clustering.db keyword_clustering_backup_$(date +%Y%m%d).db
```

### 1.2 运行迁移脚本

```bash
cd D:\xiangmu\词根聚类需求挖掘
python scripts/migrate_add_traceability.py
```

迁移脚本会:
1. 扩展demands表,添加11个溯源字段
2. 创建4个新表(关联表和审计表)
3. 为现有需求补充默认溯源信息
4. 验证迁移结果

**预期输出:**
```
================================================================================
数据库迁移: 添加需求溯源系统
================================================================================

⚠️  警告: 此操作将修改数据库结构
   建议先备份数据库!

是否继续? (yes/no): yes

================================================================================
步骤1: 扩展demands表,添加溯源字段
================================================================================
  [1/11] 执行: ALTER TABLE demands ADD COLUMN source_phase VARCHAR(20)...
      ✓ 成功
  ...

✓ 步骤1完成: demands表扩展成功

================================================================================
步骤2: 创建溯源系统表
================================================================================
  将创建以下表:
    - demand_phrase_mappings
    - demand_product_mappings
    - demand_token_mappings
    - demand_provenance

✓ 步骤2完成: 溯源系统表创建成功

================================================================================
步骤3: 为现有数据补充默认溯源信息
================================================================================
  找到 20 个需求需要补充溯源信息
    进度: 10/20
    进度: 20/20

✓ 步骤3完成: 已为 20 个需求补充溯源信息

================================================================================
步骤4: 验证迁移结果
================================================================================
  demands表检查:
    总需求数: 20
    有source_phase的: 20 (100.0%)
    有confidence_score的: 20 (100.0%)

  新表检查:
    需求-短语关联 (demand_phrase_mappings): 0 条记录
    需求-商品关联 (demand_product_mappings): 0 条记录
    需求-词根关联 (demand_token_mappings): 0 条记录
    溯源审计记录 (demand_provenance): 20 条记录

✓ 步骤4完成: 迁移验证通过

================================================================================
✓ 迁移完成!
================================================================================
```

---

## 🧪 步骤2: 测试功能 (2分钟)

运行测试脚本验证功能:

```bash
python scripts/test_traceability_system.py
```

**预期输出:**
```
================================================================================
需求溯源系统 - 功能测试
================================================================================

================================================================================
测试1: 创建需求并记录溯源
================================================================================

✓ 成功创建需求 ID: 21
  - 标题: 在线表格协作工具
  - 来源: phase7 / product_reverse_engineering
  - 初始置信度: 0.75

================================================================================
测试2: 建立需求与短语的关联
================================================================================

✓ 成功关联 3 个短语
  - 短语 100: 相关性 0.9
  - 短语 101: 相关性 0.85
  - 短语 102: 相关性 0.8

...

================================================================================
✓ 所有测试通过!
================================================================================

测试需求ID: 21
可以在数据库中查看完整的溯源记录
```

---

## 💻 步骤3: 开始使用 (1分钟)

### 3.1 基本使用示例

创建一个测试脚本 `test_my_demand.py`:

```python
from core.demand_provenance_service import DemandProvenanceService

# 创建需求
with DemandProvenanceService() as service:
    # 1. 创建需求
    demand_id = service.create_demand_with_provenance(
        title="我的第一个需求",
        description="这是一个测试需求",
        source_phase="manual",
        source_method="manual_creation",
        source_data_ids=[],
        confidence_score=0.8
    )

    print(f"✓ 创建需求成功! ID: {demand_id}")

    # 2. 查询溯源信息
    provenance = service.get_demand_provenance(demand_id)

    print(f"\n需求信息:")
    print(f"  标题: {provenance['demand']['title']}")
    print(f"  来源: {provenance['source']['phase']}")
    print(f"  置信度: {provenance['source']['confidence_score']}")
    print(f"  事件数: {len(provenance['event_timeline'])}")
```

运行:
```bash
python test_my_demand.py
```

---

## 📊 步骤4: 查看数据 (可选)

### 4.1 查询数据库

```sql
-- 查看所有需求的溯源信息
SELECT
    demand_id,
    title,
    source_phase,
    source_method,
    confidence_score,
    is_validated,
    discovered_at
FROM demands
ORDER BY discovered_at DESC
LIMIT 10;

-- 查看需求的事件时间线
SELECT
    event_type,
    event_description,
    triggered_by_user,
    created_at
FROM demand_provenance
WHERE demand_id = 21
ORDER BY created_at;

-- 统计各Phase的需求数量
SELECT
    source_phase,
    COUNT(*) as count,
    AVG(confidence_score) as avg_confidence
FROM demands
GROUP BY source_phase;
```

### 4.2 使用Python查询

```python
from core.demand_provenance_service import DemandProvenanceService

with DemandProvenanceService() as service:
    # 获取统计信息
    stats = service.get_demands_by_source()

    print("按Phase分布:")
    for phase, data in stats['by_phase'].items():
        print(f"  {phase}: {data['count']} 个, 平均置信度 {data['avg_confidence']:.2f}")

    print("\n验证状态:")
    print(f"  已验证: {stats['by_validation_status']['validated']}")
    print(f"  未验证: {stats['by_validation_status']['unvalidated']}")
```

---

## 🎯 常见使用场景

### 场景1: 从商品创建需求 (Phase 7)

```python
from core.demand_provenance_service import DemandProvenanceService

# 假设你已经有商品数据和AI标注结果
product_id = 1001
core_need = "在线表格编辑工具"
tags = ["表格工具", "在线协作", "数据管理"]
fit_level = "high"

with DemandProvenanceService() as service:
    # 创建需求
    demand_id = service.create_demand_with_provenance(
        title=core_need,
        description=f"从商品 {product_id} 提取的需求",
        source_phase="phase7",
        source_method="product_reverse_engineering",
        source_data_ids=[product_id],
        confidence_score=0.75
    )

    # 关联商品
    service.link_demand_to_products(
        demand_id=demand_id,
        product_ids=[product_id],
        fit_scores=[0.9],
        fit_levels=[fit_level],
        source="product_analysis",
        phase="phase7",
        method="ai_annotation"
    )

    print(f"✓ 需求创建成功! ID: {demand_id}")
```

### 场景2: 从关键词聚类创建需求 (Phase 4)

```python
with DemandProvenanceService() as service:
    # 创建需求
    demand_id = service.create_demand_with_provenance(
        title="免费PDF编辑工具",
        description="用户需要免费的PDF编辑软件",
        source_phase="phase4",
        source_method="keyword_clustering",
        source_data_ids=[],  # 稍后关联短语
        confidence_score=0.6
    )

    # 关联短语
    phrase_ids = [100, 101, 102, 103, 104]  # 聚类中的短语ID
    relevance_scores = [0.95, 0.9, 0.85, 0.8, 0.75]

    service.link_demand_to_phrases(
        demand_id=demand_id,
        phrase_ids=phrase_ids,
        relevance_scores=relevance_scores,
        source="clustering",
        phase="phase4",
        method="hdbscan_clustering"
    )

    print(f"✓ 需求创建并关联 {len(phrase_ids)} 个短语")
```

### 场景3: 验证需求

```python
with DemandProvenanceService() as service:
    # 人工验证
    service.validate_demand(
        demand_id=21,
        validated_by="user",
        validation_notes="经过市场调研,需求真实存在,有商业价值"
    )

    print("✓ 需求验证完成,置信度自动提升20%")
```

### 场景4: 更新置信度

```python
with DemandProvenanceService() as service:
    # AI验证后提升置信度
    service.update_confidence_score(
        demand_id=21,
        new_score=0.85,
        reason="AI分析发现多个相似商品,需求验证通过",
        triggered_by="ai"
    )

    print("✓ 置信度已更新")
```

---

## 🔍 查看溯源信息

### 完整溯源信息

```python
from core.demand_provenance_service import DemandProvenanceService

with DemandProvenanceService() as service:
    provenance = service.get_demand_provenance(21)

    # 基本信息
    print(f"需求: {provenance['demand']['title']}")
    print(f"类型: {provenance['demand']['demand_type']}")
    print(f"状态: {provenance['demand']['status']}")

    # 来源信息
    print(f"\n来源:")
    print(f"  Phase: {provenance['source']['phase']}")
    print(f"  Method: {provenance['source']['method']}")
    print(f"  发现时间: {provenance['source']['discovered_at']}")
    print(f"  置信度: {provenance['source']['confidence_score']:.2f}")

    # 关联数据
    print(f"\n关联:")
    print(f"  短语: {len(provenance['related_phrases'])} 个")
    print(f"  商品: {len(provenance['related_products'])} 个")
    print(f"  Token: {len(provenance['related_tokens'])} 个")

    # 置信度历史
    print(f"\n置信度演化:")
    for h in provenance['confidence_history']:
        print(f"  {h['timestamp'][:19]} - {h['score']:.2f} ({h['reason']})")

    # 事件时间线
    print(f"\n事件时间线:")
    for e in provenance['event_timeline']:
        print(f"  [{e['event_type']}] {e['description']}")
        print(f"    时间: {e['timestamp'][:19]}, 触发者: {e['triggered_by']}")
```

---

## 📈 下一步

### 集成到现有代码

1. **修改Phase 7的AI标注逻辑**
   - 编辑 `core/product_management.py`
   - 在AI标注后调用溯源服务创建需求

2. **创建需求中心UI**
   - 创建 `ui/pages/demand_center.py`
   - 展示需求列表、溯源信息、统计图表

3. **添加批量操作**
   - 批量验证需求
   - 批量更新置信度
   - 批量关联数据

---

## ❓ 常见问题

### Q1: 迁移失败怎么办?

**A:** 恢复备份并检查错误信息:
```bash
# MySQL恢复
mysql -u root -p keyword_clustering < backup_20260120.sql

# SQLite恢复
cp keyword_clustering_backup_20260120.db keyword_clustering.db
```

### Q2: 如何查看某个需求的完整历史?

**A:** 使用 `get_demand_provenance()` 方法:
```python
with DemandProvenanceService() as service:
    provenance = service.get_demand_provenance(demand_id)
    # 查看 provenance['event_timeline']
```

### Q3: 如何删除测试数据?

**A:** 直接删除需求即可,关联数据会自动删除(CASCADE):
```sql
DELETE FROM demands WHERE demand_id = 21;
```

### Q4: 置信度如何计算?

**A:** 置信度是手动设置的,建议规则:
- 初始创建: 0.5-0.7
- AI验证通过: +0.1-0.2
- 人工验证通过: +0.2
- 关联数据越多: 适当提升

### Q5: 如何批量导入历史需求?

**A:** 使用循环调用 `create_demand_with_provenance()`:
```python
with DemandProvenanceService() as service:
    for demand_data in historical_demands:
        demand_id = service.create_demand_with_provenance(
            title=demand_data['title'],
            description=demand_data['description'],
            source_phase="manual",
            source_method="historical_import",
            source_data_ids=[],
            confidence_score=0.5
        )
```

---

## 📚 更多资源

- [完整设计文档](design/demand-traceability-design.md)
- [实施总结](Traceability_System_Implementation_Summary.md)
- [API文档](../core/demand_provenance_service.py)
- [数据库模型](../storage/models_traceability.py)

---

## ✅ 检查清单

完成以下步骤确保系统正常运行:

- [ ] 备份数据库
- [ ] 运行迁移脚本
- [ ] 验证迁移结果
- [ ] 运行测试脚本
- [ ] 创建测试需求
- [ ] 查询溯源信息
- [ ] 查看数据库数据
- [ ] 集成到现有代码

---

**祝你使用愉快! 🎉**

如有问题,请查看完整文档或提交Issue。

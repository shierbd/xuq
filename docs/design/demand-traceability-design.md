# 需求溯源系统设计方案

## 1. 设计目标

为多维度需求分析工具建立完整的溯源体系,实现:

1. **来源追踪**: 记录每个需求从哪个Phase、哪个方法发现
2. **数据溯源**: 追踪需求关联的原始数据(短语、商品、Reddit板块等)
3. **演化历史**: 记录需求的置信度变化、验证过程
4. **关系追踪**: 追踪需求与词、产品的多对多关联
5. **审计日志**: 记录所有关键操作的历史

## 2. 核心概念

### 2.1 需求三角关系

```
       Demand (需求)
      /      |      \
     /       |       \
  Phrase   Token   Product
  (词组)   (词根)   (商品)
```

### 2.2 溯源维度

- **Phase维度**: phase1-7, manual (手动创建)
- **Method维度**:
  - keyword_clustering (关键词聚类)
  - reddit_analysis (Reddit板块分析)
  - product_reverse_engineering (商品反向工程)
  - manual_creation (人工创建)
  - ai_inference (AI推断)
- **Source维度**: 具体的数据源ID (phrase_id, product_id, subreddit_id等)
- **Time维度**: 发现时间、更新时间、验证时间

## 3. 数据库设计

### 3.1 扩展Demand表 (demands)

在现有Demand表基础上新增溯源字段:

```python
class Demand(Base):
    # ... 现有字段 ...

    # ========== 新增: 溯源字段 ==========

    # 来源追踪
    source_phase = Column(String(20), index=True)  # phase1-7, manual
    source_method = Column(String(50), index=True)  # 发现方法
    source_data_ids = Column(Text)  # JSON数组: 源数据ID列表

    # 置信度追踪
    confidence_score = Column(DECIMAL(3, 2), default=Decimal("0.5"))  # 0.00-1.00
    confidence_history = Column(Text)  # JSON数组: 置信度变化历史

    # 时间追踪
    discovered_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    last_validated_at = Column(TIMESTAMP)
    validation_count = Column(Integer, default=0)

    # 验证状态
    is_validated = Column(Boolean, default=False, index=True)
    validated_by = Column(String(100))  # user, ai, system
    validation_notes = Column(Text)
```

### 3.2 新建: DemandPhraseMapping (需求-短语关联表)

```python
class DemandPhraseMapping(Base):
    """需求与短语的多对多关联表"""

    __tablename__ = "demand_phrase_mappings"

    # 主键
    mapping_id = Column(Integer, primary_key=True, autoincrement=True)

    # 关联关系
    demand_id = Column(Integer, ForeignKey('demands.demand_id'), nullable=False, index=True)
    phrase_id = Column(BigInteger, ForeignKey('phrases.phrase_id'), nullable=False, index=True)

    # 关联强度
    relevance_score = Column(DECIMAL(3, 2))  # 0.00-1.00

    # 溯源信息
    mapping_source = Column(String(50), index=True)  # clustering, manual, ai_inference
    created_by_phase = Column(String(20))  # 哪个Phase创建的关联
    created_by_method = Column(String(50))  # 哪个方法创建的关联

    # 验证状态
    is_validated = Column(Boolean, default=False, index=True)
    validated_at = Column(TIMESTAMP)
    validated_by = Column(String(100))

    # 元数据
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    notes = Column(Text)

    # 复合索引
    __table_args__ = (
        Index('idx_demand_phrase', 'demand_id', 'phrase_id'),
        Index('idx_source_validated', 'mapping_source', 'is_validated'),
    )
```

### 3.3 新建: DemandProductMapping (需求-商品关联表)

```python
class DemandProductMapping(Base):
    """需求与商品的多对多关联表"""

    __tablename__ = "demand_product_mappings"

    # 主键
    mapping_id = Column(Integer, primary_key=True, autoincrement=True)

    # 关联关系
    demand_id = Column(Integer, ForeignKey('demands.demand_id'), nullable=False, index=True)
    product_id = Column(BigInteger, ForeignKey('products.product_id'), nullable=False, index=True)

    # 适配度评分
    fit_score = Column(DECIMAL(3, 2))  # 0.00-1.00
    fit_level = enum_column(
        "fit_level",
        ["high", "medium", "low"],
        enum_name="fit_level_enum",
        index=True
    )

    # 溯源信息
    mapping_source = Column(String(50), index=True)  # product_analysis, manual, ai_inference
    created_by_phase = Column(String(20))
    created_by_method = Column(String(50))

    # 验证状态
    is_validated = Column(Boolean, default=False, index=True)
    validated_at = Column(TIMESTAMP)
    validated_by = Column(String(100))
    validation_notes = Column(Text)

    # 元数据
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)

    # 复合索引
    __table_args__ = (
        Index('idx_demand_product', 'demand_id', 'product_id'),
        Index('idx_fit_validated', 'fit_level', 'is_validated'),
    )
```

### 3.4 新建: DemandTokenMapping (需求-词根关联表)

```python
class DemandTokenMapping(Base):
    """需求与Token的多对多关联表"""

    __tablename__ = "demand_token_mappings"

    # 主键
    mapping_id = Column(Integer, primary_key=True, autoincrement=True)

    # 关联关系
    demand_id = Column(Integer, ForeignKey('demands.demand_id'), nullable=False, index=True)
    token_id = Column(Integer, ForeignKey('tokens.token_id'), nullable=False, index=True)

    # 关联类型
    token_role = enum_column(
        "token_role",
        ["core", "supporting", "context"],
        enum_name="token_role_enum",
        index=True
    )  # core=核心词, supporting=支撑词, context=上下文词

    # 重要性评分
    importance_score = Column(DECIMAL(3, 2))  # 0.00-1.00

    # 溯源信息
    mapping_source = Column(String(50), index=True)
    created_by_phase = Column(String(20))
    created_by_method = Column(String(50))

    # 验证状态
    is_validated = Column(Boolean, default=False, index=True)
    validated_at = Column(TIMESTAMP)

    # 元数据
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)

    # 复合索引
    __table_args__ = (
        Index('idx_demand_token', 'demand_id', 'token_id'),
        Index('idx_role_validated', 'token_role', 'is_validated'),
    )
```

### 3.5 新建: DemandProvenance (需求溯源审计表)

```python
class DemandProvenance(Base):
    """需求溯源审计表 - 记录需求的所有变更历史"""

    __tablename__ = "demand_provenance"

    # 主键
    provenance_id = Column(Integer, primary_key=True, autoincrement=True)

    # 关联需求
    demand_id = Column(Integer, ForeignKey('demands.demand_id'), nullable=False, index=True)

    # 事件类型
    event_type = enum_column(
        "event_type",
        [
            "created",           # 创建
            "updated",           # 更新
            "validated",         # 验证
            "merged",            # 合并
            "split",             # 拆分
            "linked_phrase",     # 关联短语
            "linked_product",    # 关联商品
            "linked_token",      # 关联词根
            "confidence_changed", # 置信度变化
            "status_changed"     # 状态变化
        ],
        enum_name="event_type_enum",
        nullable=False,
        index=True
    )

    # 事件详情
    event_description = Column(Text)
    old_value = Column(Text)  # JSON格式: 变更前的值
    new_value = Column(Text)  # JSON格式: 变更后的值

    # 溯源信息
    triggered_by_phase = Column(String(20))
    triggered_by_method = Column(String(50))
    triggered_by_user = Column(String(100))  # user, ai, system

    # 关联数据
    related_data_type = Column(String(50))  # phrase, product, token, cluster
    related_data_id = Column(Integer)

    # 元数据
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow, index=True)

    # 索引
    __table_args__ = (
        Index('idx_demand_event', 'demand_id', 'event_type'),
        Index('idx_demand_time', 'demand_id', 'created_at'),
    )
```

## 4. 核心功能实现

### 4.1 需求创建时的溯源记录

```python
class DemandProvenanceService:
    """需求溯源服务"""

    def create_demand_with_provenance(
        self,
        title: str,
        description: str,
        source_phase: str,
        source_method: str,
        source_data_ids: List[int],
        confidence_score: float = 0.5
    ) -> int:
        """
        创建需求并记录溯源信息

        Args:
            title: 需求标题
            description: 需求描述
            source_phase: 来源Phase (phase1-7, manual)
            source_method: 发现方法
            source_data_ids: 源数据ID列表
            confidence_score: 初始置信度

        Returns:
            demand_id: 创建的需求ID
        """
        # 1. 创建需求
        demand = Demand(
            title=title,
            description=description,
            source_phase=source_phase,
            source_method=source_method,
            source_data_ids=json.dumps(source_data_ids),
            confidence_score=Decimal(str(confidence_score)),
            confidence_history=json.dumps([{
                'score': confidence_score,
                'timestamp': datetime.utcnow().isoformat(),
                'reason': 'initial_creation'
            }]),
            discovered_at=datetime.utcnow()
        )

        session.add(demand)
        session.flush()

        # 2. 记录溯源事件
        provenance = DemandProvenance(
            demand_id=demand.demand_id,
            event_type='created',
            event_description=f'需求由{source_method}方法发现',
            new_value=json.dumps({
                'title': title,
                'source_phase': source_phase,
                'source_method': source_method,
                'confidence_score': confidence_score
            }),
            triggered_by_phase=source_phase,
            triggered_by_method=source_method,
            triggered_by_user='system'
        )

        session.add(provenance)
        session.commit()

        return demand.demand_id
```

### 4.2 建立需求-短语关联

```python
def link_demand_to_phrases(
    self,
    demand_id: int,
    phrase_ids: List[int],
    relevance_scores: List[float],
    source: str,
    phase: str,
    method: str
) -> List[int]:
    """
    建立需求与短语的关联

    Args:
        demand_id: 需求ID
        phrase_ids: 短语ID列表
        relevance_scores: 相关性评分列表
        source: 关联来源 (clustering, manual, ai_inference)
        phase: 创建关联的Phase
        method: 创建关联的方法

    Returns:
        mapping_ids: 创建的关联ID列表
    """
    mapping_ids = []

    for phrase_id, score in zip(phrase_ids, relevance_scores):
        # 检查是否已存在
        existing = session.query(DemandPhraseMapping).filter_by(
            demand_id=demand_id,
            phrase_id=phrase_id
        ).first()

        if existing:
            # 更新评分
            existing.relevance_score = Decimal(str(score))
            mapping_id = existing.mapping_id
        else:
            # 创建新关联
            mapping = DemandPhraseMapping(
                demand_id=demand_id,
                phrase_id=phrase_id,
                relevance_score=Decimal(str(score)),
                mapping_source=source,
                created_by_phase=phase,
                created_by_method=method
            )
            session.add(mapping)
            session.flush()
            mapping_id = mapping.mapping_id

        mapping_ids.append(mapping_id)

        # 记录溯源事件
        provenance = DemandProvenance(
            demand_id=demand_id,
            event_type='linked_phrase',
            event_description=f'关联短语 (ID: {phrase_id})',
            new_value=json.dumps({
                'phrase_id': phrase_id,
                'relevance_score': score,
                'source': source
            }),
            triggered_by_phase=phase,
            triggered_by_method=method,
            triggered_by_user='system',
            related_data_type='phrase',
            related_data_id=phrase_id
        )
        session.add(provenance)

    session.commit()
    return mapping_ids
```

### 4.3 置信度更新与历史追踪

```python
def update_confidence_score(
    self,
    demand_id: int,
    new_score: float,
    reason: str,
    triggered_by: str = 'system'
) -> None:
    """
    更新需求置信度并记录历史

    Args:
        demand_id: 需求ID
        new_score: 新置信度 (0.0-1.0)
        reason: 变更原因
        triggered_by: 触发者 (user, ai, system)
    """
    demand = session.query(Demand).get(demand_id)

    if not demand:
        raise ValueError(f"Demand {demand_id} not found")

    # 记录旧值
    old_score = float(demand.confidence_score)

    # 更新置信度
    demand.confidence_score = Decimal(str(new_score))

    # 更新历史
    history = json.loads(demand.confidence_history or '[]')
    history.append({
        'score': new_score,
        'timestamp': datetime.utcnow().isoformat(),
        'reason': reason,
        'triggered_by': triggered_by
    })
    demand.confidence_history = json.dumps(history)

    # 记录溯源事件
    provenance = DemandProvenance(
        demand_id=demand_id,
        event_type='confidence_changed',
        event_description=f'置信度从 {old_score:.2f} 变更为 {new_score:.2f}',
        old_value=json.dumps({'confidence_score': old_score}),
        new_value=json.dumps({'confidence_score': new_score, 'reason': reason}),
        triggered_by_user=triggered_by
    )

    session.add(provenance)
    session.commit()
```

### 4.4 需求验证

```python
def validate_demand(
    self,
    demand_id: int,
    validated_by: str,
    validation_notes: str = None
) -> None:
    """
    验证需求

    Args:
        demand_id: 需求ID
        validated_by: 验证者 (user, ai)
        validation_notes: 验证备注
    """
    demand = session.query(Demand).get(demand_id)

    if not demand:
        raise ValueError(f"Demand {demand_id} not found")

    # 更新验证状态
    demand.is_validated = True
    demand.validated_by = validated_by
    demand.last_validated_at = datetime.utcnow()
    demand.validation_count += 1
    demand.validation_notes = validation_notes

    # 提升置信度
    old_confidence = float(demand.confidence_score)
    new_confidence = min(1.0, old_confidence + 0.2)  # 验证后提升20%
    demand.confidence_score = Decimal(str(new_confidence))

    # 记录溯源事件
    provenance = DemandProvenance(
        demand_id=demand_id,
        event_type='validated',
        event_description=f'需求已被{validated_by}验证',
        old_value=json.dumps({
            'is_validated': False,
            'confidence_score': old_confidence
        }),
        new_value=json.dumps({
            'is_validated': True,
            'confidence_score': new_confidence,
            'validated_by': validated_by,
            'notes': validation_notes
        }),
        triggered_by_user=validated_by
    )

    session.add(provenance)
    session.commit()
```

## 5. 查询接口

### 5.1 获取需求的完整溯源信息

```python
def get_demand_provenance(self, demand_id: int) -> Dict:
    """
    获取需求的完整溯源信息

    Returns:
        {
            'demand': {...},  # 需求基本信息
            'source': {...},  # 来源信息
            'related_phrases': [...],  # 关联的短语
            'related_products': [...],  # 关联的商品
            'related_tokens': [...],  # 关联的词根
            'confidence_history': [...],  # 置信度历史
            'event_timeline': [...]  # 事件时间线
        }
    """
    demand = session.query(Demand).get(demand_id)

    if not demand:
        raise ValueError(f"Demand {demand_id} not found")

    # 1. 基本信息
    result = {
        'demand': {
            'demand_id': demand.demand_id,
            'title': demand.title,
            'description': demand.description,
            'status': demand.status,
            'is_validated': demand.is_validated
        },
        'source': {
            'phase': demand.source_phase,
            'method': demand.source_method,
            'discovered_at': demand.discovered_at.isoformat(),
            'confidence_score': float(demand.confidence_score)
        }
    }

    # 2. 关联的短语
    phrase_mappings = session.query(DemandPhraseMapping).filter_by(
        demand_id=demand_id
    ).all()

    result['related_phrases'] = [{
        'phrase_id': m.phrase_id,
        'phrase': session.query(Phrase).get(m.phrase_id).phrase,
        'relevance_score': float(m.relevance_score),
        'mapping_source': m.mapping_source,
        'is_validated': m.is_validated
    } for m in phrase_mappings]

    # 3. 关联的商品
    product_mappings = session.query(DemandProductMapping).filter_by(
        demand_id=demand_id
    ).all()

    result['related_products'] = [{
        'product_id': m.product_id,
        'product_name': session.query(Product).get(m.product_id).product_name,
        'fit_score': float(m.fit_score),
        'fit_level': m.fit_level,
        'is_validated': m.is_validated
    } for m in product_mappings]

    # 4. 关联的词根
    token_mappings = session.query(DemandTokenMapping).filter_by(
        demand_id=demand_id
    ).all()

    result['related_tokens'] = [{
        'token_id': m.token_id,
        'token_text': session.query(Token).get(m.token_id).token_text,
        'token_role': m.token_role,
        'importance_score': float(m.importance_score)
    } for m in token_mappings]

    # 5. 置信度历史
    result['confidence_history'] = json.loads(demand.confidence_history or '[]')

    # 6. 事件时间线
    events = session.query(DemandProvenance).filter_by(
        demand_id=demand_id
    ).order_by(DemandProvenance.created_at).all()

    result['event_timeline'] = [{
        'event_type': e.event_type,
        'description': e.event_description,
        'timestamp': e.created_at.isoformat(),
        'triggered_by': e.triggered_by_user
    } for e in events]

    return result
```

### 5.2 按来源统计需求

```python
def get_demands_by_source(self) -> Dict:
    """
    按来源统计需求分布

    Returns:
        {
            'by_phase': {...},
            'by_method': {...},
            'by_validation_status': {...}
        }
    """
    # 按Phase统计
    by_phase = {}
    phase_stats = session.query(
        Demand.source_phase,
        func.count(Demand.demand_id).label('count'),
        func.avg(Demand.confidence_score).label('avg_confidence')
    ).group_by(Demand.source_phase).all()

    for phase, count, avg_conf in phase_stats:
        by_phase[phase] = {
            'count': count,
            'avg_confidence': float(avg_conf) if avg_conf else 0
        }

    # 按Method统计
    by_method = {}
    method_stats = session.query(
        Demand.source_method,
        func.count(Demand.demand_id).label('count')
    ).group_by(Demand.source_method).all()

    for method, count in method_stats:
        by_method[method] = count

    # 按验证状态统计
    validation_stats = session.query(
        Demand.is_validated,
        func.count(Demand.demand_id).label('count')
    ).group_by(Demand.is_validated).all()

    by_validation = {
        'validated': 0,
        'unvalidated': 0
    }

    for is_validated, count in validation_stats:
        if is_validated:
            by_validation['validated'] = count
        else:
            by_validation['unvalidated'] = count

    return {
        'by_phase': by_phase,
        'by_method': by_method,
        'by_validation_status': by_validation
    }
```

## 6. UI展示设计

### 6.1 需求详情页 - 溯源信息展示

```
┌─────────────────────────────────────────────────────────┐
│ 需求详情: [需求标题]                                      │
├─────────────────────────────────────────────────────────┤
│                                                           │
│ 📍 来源信息                                               │
│   • 发现阶段: Phase 7 - 商品反向工程                      │
│   • 发现方法: product_reverse_engineering                 │
│   • 发现时间: 2026-01-17 10:30:25                        │
│   • 置信度: ████████░░ 80%                               │
│                                                           │
│ 🔗 关联数据                                               │
│   • 关联短语: 15个 (查看详情)                            │
│   • 关联商品: 8个 (查看详情)                             │
│   • 关联词根: 5个 (查看详情)                             │
│                                                           │
│ 📊 置信度演化                                             │
│   [折线图显示置信度随时间变化]                            │
│                                                           │
│ 📜 事件时间线                                             │
│   2026-01-17 10:30  ✨ 需求创建 (初始置信度: 50%)        │
│   2026-01-17 11:15  🔗 关联8个商品                       │
│   2026-01-17 14:20  📈 置信度提升至 65% (AI验证)         │
│   2026-01-18 09:00  ✅ 人工验证通过 (置信度: 80%)        │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

### 6.2 需求中心 - 来源分布视图

```
┌─────────────────────────────────────────────────────────┐
│ 需求中心 - 来源分布                                       │
├─────────────────────────────────────────────────────────┤
│                                                           │
│ 按Phase分布:                                              │
│   Phase 1-5 (关键词聚类)  ████████████░░░░  45个 (60%)   │
│   Phase 6 (Reddit分析)    ████░░░░░░░░░░░  12个 (16%)   │
│   Phase 7 (商品分析)      ██████░░░░░░░░░  18个 (24%)   │
│                                                           │
│ 按验证状态:                                               │
│   已验证   ████████░░░░░░  30个 (40%)                    │
│   未验证   ████████████░░  45个 (60%)                    │
│                                                           │
│ 平均置信度: 67%                                           │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

## 7. 实施计划

### Phase 1: 数据库迁移 (1-2天)
- [ ] 创建4个新表的migration脚本
- [ ] 扩展Demand表字段
- [ ] 测试MySQL和SQLite兼容性
- [ ] 执行数据库迁移

### Phase 2: 核心服务实现 (2-3天)
- [ ] 实现DemandProvenanceService类
- [ ] 实现需求创建时的溯源记录
- [ ] 实现关联关系建立
- [ ] 实现置信度更新机制
- [ ] 实现验证功能

### Phase 3: 查询接口 (1-2天)
- [ ] 实现溯源信息查询
- [ ] 实现统计分析接口
- [ ] 实现时间线查询
- [ ] 添加单元测试

### Phase 4: UI集成 (2-3天)
- [ ] 创建需求详情页溯源展示
- [ ] 创建需求中心来源分布视图
- [ ] 添加置信度演化图表
- [ ] 添加事件时间线组件

### Phase 5: 数据迁移 (1天)
- [ ] 为现有需求补充溯源信息
- [ ] 为现有关联关系补充元数据
- [ ] 数据一致性检查

## 8. 注意事项

1. **性能考虑**:
   - DemandProvenance表会快速增长,需要定期归档
   - 复合索引优化查询性能
   - 考虑使用缓存减少数据库查询

2. **数据一致性**:
   - 使用事务确保需求创建和溯源记录的原子性
   - 定期检查关联关系的有效性

3. **扩展性**:
   - 预留字段支持未来新的Phase和Method
   - JSON字段支持灵活的元数据存储

4. **隐私和安全**:
   - 审计日志不可删除,只能归档
   - 敏感操作需要记录操作者信息

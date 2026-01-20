"""
需求溯源服务 - DemandProvenanceService

提供需求溯源的核心功能:
1. 创建需求并记录溯源信息
2. 建立需求与短语/商品/词根的关联
3. 更新置信度并记录历史
4. 验证需求
5. 查询溯源信息
6. 统计分析

使用示例:
    service = DemandProvenanceService()

    # 创建需求
    demand_id = service.create_demand_with_provenance(
        title="需要一个在线表格工具",
        description="用户需要在线编辑和分享表格",
        source_phase="phase7",
        source_method="product_reverse_engineering",
        source_data_ids=[1001, 1002, 1003],
        confidence_score=0.75
    )

    # 关联短语
    service.link_demand_to_phrases(
        demand_id=demand_id,
        phrase_ids=[100, 101, 102],
        relevance_scores=[0.9, 0.8, 0.7],
        source="ai_inference",
        phase="phase7",
        method="semantic_matching"
    )

    # 验证需求
    service.validate_demand(
        demand_id=demand_id,
        validated_by="user",
        validation_notes="经过人工审核,需求准确"
    )
"""
import json
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from decimal import Decimal
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session

from storage.models import get_session, Demand, Phrase, Product, Token
from storage.models_traceability import (
    DemandPhraseMapping,
    DemandProductMapping,
    DemandTokenMapping,
    DemandProvenance
)


class DemandProvenanceService:
    """需求溯源服务"""

    def __init__(self, session: Optional[Session] = None):
        """
        初始化服务

        Args:
            session: 数据库会话,如果不提供则自动创建
        """
        self.session = session or get_session()
        self._auto_session = session is None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._auto_session:
            self.session.close()

    # ==================== 1. 需求创建 ====================

    def create_demand_with_provenance(
        self,
        title: str,
        description: str,
        source_phase: str,
        source_method: str,
        source_data_ids: List[int],
        confidence_score: float = 0.5,
        demand_type: str = "other",
        user_scenario: str = None
    ) -> int:
        """
        创建需求并记录溯源信息

        Args:
            title: 需求标题
            description: 需求描述
            source_phase: 来源Phase (phase1-7, manual)
            source_method: 发现方法
            source_data_ids: 源数据ID列表
            confidence_score: 初始置信度 (0.0-1.0)
            demand_type: 需求类型
            user_scenario: 用户场景

        Returns:
            demand_id: 创建的需求ID
        """
        # 1. 创建需求
        demand = Demand(
            title=title,
            description=description,
            user_scenario=user_scenario,
            demand_type=demand_type,
            source_phase=source_phase,
            source_method=source_method,
            source_data_ids=json.dumps(source_data_ids),
            confidence_score=Decimal(str(confidence_score)),
            confidence_history=json.dumps([{
                'score': confidence_score,
                'timestamp': datetime.utcnow().isoformat(),
                'reason': 'initial_creation'
            }]),
            discovered_at=datetime.utcnow(),
            validation_count=0,
            is_validated=False
        )

        self.session.add(demand)
        self.session.flush()

        # 2. 记录溯源事件
        provenance = DemandProvenance(
            demand_id=demand.demand_id,
            event_type='created',
            event_description=f'需求由{source_method}方法发现',
            new_value=json.dumps({
                'title': title,
                'source_phase': source_phase,
                'source_method': source_method,
                'confidence_score': confidence_score,
                'source_data_ids': source_data_ids
            }),
            triggered_by_phase=source_phase,
            triggered_by_method=source_method,
            triggered_by_user='system'
        )

        self.session.add(provenance)
        self.session.commit()

        return demand.demand_id

    # ==================== 2. 关联管理 ====================

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
            relevance_scores: 相关性评分列表 (0.0-1.0)
            source: 关联来源 (clustering, manual, ai_inference)
            phase: 创建关联的Phase
            method: 创建关联的方法

        Returns:
            mapping_ids: 创建的关联ID列表
        """
        if len(phrase_ids) != len(relevance_scores):
            raise ValueError("phrase_ids和relevance_scores长度必须相同")

        mapping_ids = []

        for phrase_id, score in zip(phrase_ids, relevance_scores):
            # 检查是否已存在
            existing = self.session.query(DemandPhraseMapping).filter_by(
                demand_id=demand_id,
                phrase_id=phrase_id
            ).first()

            if existing:
                # 更新评分
                old_score = float(existing.relevance_score)
                existing.relevance_score = Decimal(str(score))
                mapping_id = existing.mapping_id

                # 记录更新事件
                provenance = DemandProvenance(
                    demand_id=demand_id,
                    event_type='updated',
                    event_description=f'更新短语关联评分 (ID: {phrase_id})',
                    old_value=json.dumps({'relevance_score': old_score}),
                    new_value=json.dumps({'relevance_score': score}),
                    triggered_by_phase=phase,
                    triggered_by_method=method,
                    triggered_by_user='system',
                    related_data_type='phrase',
                    related_data_id=phrase_id
                )
                self.session.add(provenance)
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
                self.session.add(mapping)
                self.session.flush()
                mapping_id = mapping.mapping_id

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
                self.session.add(provenance)

            mapping_ids.append(mapping_id)

        self.session.commit()
        return mapping_ids

    def link_demand_to_products(
        self,
        demand_id: int,
        product_ids: List[int],
        fit_scores: List[float],
        fit_levels: List[str],
        source: str,
        phase: str,
        method: str
    ) -> List[int]:
        """
        建立需求与商品的关联

        Args:
            demand_id: 需求ID
            product_ids: 商品ID列表
            fit_scores: 适配度评分列表 (0.0-1.0)
            fit_levels: 适配度等级列表 (high/medium/low)
            source: 关联来源 (product_analysis, manual, ai_inference)
            phase: 创建关联的Phase
            method: 创建关联的方法

        Returns:
            mapping_ids: 创建的关联ID列表
        """
        if not (len(product_ids) == len(fit_scores) == len(fit_levels)):
            raise ValueError("product_ids, fit_scores和fit_levels长度必须相同")

        mapping_ids = []

        for product_id, score, level in zip(product_ids, fit_scores, fit_levels):
            # 检查是否已存在
            existing = self.session.query(DemandProductMapping).filter_by(
                demand_id=demand_id,
                product_id=product_id
            ).first()

            if existing:
                # 更新评分
                existing.fit_score = Decimal(str(score))
                existing.fit_level = level
                mapping_id = existing.mapping_id
            else:
                # 创建新关联
                mapping = DemandProductMapping(
                    demand_id=demand_id,
                    product_id=product_id,
                    fit_score=Decimal(str(score)),
                    fit_level=level,
                    mapping_source=source,
                    created_by_phase=phase,
                    created_by_method=method
                )
                self.session.add(mapping)
                self.session.flush()
                mapping_id = mapping.mapping_id

                # 记录溯源事件
                provenance = DemandProvenance(
                    demand_id=demand_id,
                    event_type='linked_product',
                    event_description=f'关联商品 (ID: {product_id})',
                    new_value=json.dumps({
                        'product_id': product_id,
                        'fit_score': score,
                        'fit_level': level,
                        'source': source
                    }),
                    triggered_by_phase=phase,
                    triggered_by_method=method,
                    triggered_by_user='system',
                    related_data_type='product',
                    related_data_id=product_id
                )
                self.session.add(provenance)

            mapping_ids.append(mapping_id)

        self.session.commit()
        return mapping_ids

    def link_demand_to_tokens(
        self,
        demand_id: int,
        token_ids: List[int],
        token_roles: List[str],
        importance_scores: List[float],
        source: str,
        phase: str,
        method: str
    ) -> List[int]:
        """
        建立需求与Token的关联

        Args:
            demand_id: 需求ID
            token_ids: Token ID列表
            token_roles: Token角色列表 (core/supporting/context)
            importance_scores: 重要性评分列表 (0.0-1.0)
            source: 关联来源 (token_extraction, manual, ai_inference)
            phase: 创建关联的Phase
            method: 创建关联的方法

        Returns:
            mapping_ids: 创建的关联ID列表
        """
        if not (len(token_ids) == len(token_roles) == len(importance_scores)):
            raise ValueError("token_ids, token_roles和importance_scores长度必须相同")

        mapping_ids = []

        for token_id, role, score in zip(token_ids, token_roles, importance_scores):
            # 检查是否已存在
            existing = self.session.query(DemandTokenMapping).filter_by(
                demand_id=demand_id,
                token_id=token_id
            ).first()

            if existing:
                # 更新
                existing.token_role = role
                existing.importance_score = Decimal(str(score))
                mapping_id = existing.mapping_id
            else:
                # 创建新关联
                mapping = DemandTokenMapping(
                    demand_id=demand_id,
                    token_id=token_id,
                    token_role=role,
                    importance_score=Decimal(str(score)),
                    mapping_source=source,
                    created_by_phase=phase,
                    created_by_method=method
                )
                self.session.add(mapping)
                self.session.flush()
                mapping_id = mapping.mapping_id

                # 记录溯源事件
                provenance = DemandProvenance(
                    demand_id=demand_id,
                    event_type='linked_token',
                    event_description=f'关联Token (ID: {token_id})',
                    new_value=json.dumps({
                        'token_id': token_id,
                        'token_role': role,
                        'importance_score': score,
                        'source': source
                    }),
                    triggered_by_phase=phase,
                    triggered_by_method=method,
                    triggered_by_user='system',
                    related_data_type='token',
                    related_data_id=token_id
                )
                self.session.add(provenance)

            mapping_ids.append(mapping_id)

        self.session.commit()
        return mapping_ids

    # ==================== 3. 置信度管理 ====================

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
        demand = self.session.query(Demand).get(demand_id)

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

        self.session.add(provenance)
        self.session.commit()

    # ==================== 4. 需求验证 ====================

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
        demand = self.session.query(Demand).get(demand_id)

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

        # 更新置信度历史
        history = json.loads(demand.confidence_history or '[]')
        history.append({
            'score': new_confidence,
            'timestamp': datetime.utcnow().isoformat(),
            'reason': f'validated_by_{validated_by}',
            'triggered_by': validated_by
        })
        demand.confidence_history = json.dumps(history)

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

        self.session.add(provenance)
        self.session.commit()

    # ==================== 5. 查询接口 ====================

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
        demand = self.session.query(Demand).get(demand_id)

        if not demand:
            raise ValueError(f"Demand {demand_id} not found")

        # 1. 基本信息
        result = {
            'demand': {
                'demand_id': demand.demand_id,
                'title': demand.title,
                'description': demand.description,
                'demand_type': demand.demand_type,
                'status': demand.status,
                'is_validated': demand.is_validated,
                'validation_count': demand.validation_count
            },
            'source': {
                'phase': demand.source_phase,
                'method': demand.source_method,
                'data_ids': json.loads(demand.source_data_ids or '[]'),
                'discovered_at': demand.discovered_at.isoformat() if demand.discovered_at else None,
                'confidence_score': float(demand.confidence_score) if demand.confidence_score else 0.5
            }
        }

        # 2. 关联的短语
        phrase_mappings = self.session.query(
            DemandPhraseMapping, Phrase
        ).join(
            Phrase, DemandPhraseMapping.phrase_id == Phrase.phrase_id
        ).filter(
            DemandPhraseMapping.demand_id == demand_id
        ).all()

        result['related_phrases'] = [{
            'phrase_id': m.phrase_id,
            'phrase': p.phrase,
            'relevance_score': float(m.relevance_score) if m.relevance_score else 0,
            'mapping_source': m.mapping_source,
            'is_validated': m.is_validated,
            'created_at': m.created_at.isoformat() if m.created_at else None
        } for m, p in phrase_mappings]

        # 3. 关联的商品
        product_mappings = self.session.query(
            DemandProductMapping, Product
        ).join(
            Product, DemandProductMapping.product_id == Product.product_id
        ).filter(
            DemandProductMapping.demand_id == demand_id
        ).all()

        result['related_products'] = [{
            'product_id': m.product_id,
            'product_name': p.product_name,
            'fit_score': float(m.fit_score) if m.fit_score else 0,
            'fit_level': m.fit_level,
            'is_validated': m.is_validated,
            'created_at': m.created_at.isoformat() if m.created_at else None
        } for m, p in product_mappings]

        # 4. 关联的词根
        token_mappings = self.session.query(
            DemandTokenMapping, Token
        ).join(
            Token, DemandTokenMapping.token_id == Token.token_id
        ).filter(
            DemandTokenMapping.demand_id == demand_id
        ).all()

        result['related_tokens'] = [{
            'token_id': m.token_id,
            'token_text': t.token_text,
            'token_type': t.token_type,
            'token_role': m.token_role,
            'importance_score': float(m.importance_score) if m.importance_score else 0
        } for m, t in token_mappings]

        # 5. 置信度历史
        result['confidence_history'] = json.loads(demand.confidence_history or '[]')

        # 6. 事件时间线
        events = self.session.query(DemandProvenance).filter_by(
            demand_id=demand_id
        ).order_by(DemandProvenance.created_at).all()

        result['event_timeline'] = [{
            'event_type': e.event_type,
            'description': e.event_description,
            'timestamp': e.created_at.isoformat() if e.created_at else None,
            'triggered_by': e.triggered_by_user,
            'related_data_type': e.related_data_type,
            'related_data_id': e.related_data_id
        } for e in events]

        return result

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
        phase_stats = self.session.query(
            Demand.source_phase,
            func.count(Demand.demand_id).label('count'),
            func.avg(Demand.confidence_score).label('avg_confidence')
        ).group_by(Demand.source_phase).all()

        for phase, count, avg_conf in phase_stats:
            by_phase[phase or 'unknown'] = {
                'count': count,
                'avg_confidence': float(avg_conf) if avg_conf else 0
            }

        # 按Method统计
        by_method = {}
        method_stats = self.session.query(
            Demand.source_method,
            func.count(Demand.demand_id).label('count')
        ).group_by(Demand.source_method).all()

        for method, count in method_stats:
            by_method[method or 'unknown'] = count

        # 按验证状态统计
        validation_stats = self.session.query(
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


# ==================== 便捷函数 ====================

def create_demand_from_product(
    product_id: int,
    core_need: str,
    tags: List[str],
    fit_level: str = "high"
) -> int:
    """
    从商品创建需求的便捷函数

    Args:
        product_id: 商品ID
        core_need: 核心需求描述
        tags: 标签列表
        fit_level: 适配度等级

    Returns:
        demand_id: 创建的需求ID
    """
    with DemandProvenanceService() as service:
        # 创建需求
        demand_id = service.create_demand_with_provenance(
            title=core_need,
            description=f"从商品 {product_id} 提取的需求",
            source_phase="phase7",
            source_method="product_reverse_engineering",
            source_data_ids=[product_id],
            confidence_score=0.7 if fit_level == "high" else 0.5
        )

        # 关联商品
        fit_score = 0.9 if fit_level == "high" else (0.6 if fit_level == "medium" else 0.3)
        service.link_demand_to_products(
            demand_id=demand_id,
            product_ids=[product_id],
            fit_scores=[fit_score],
            fit_levels=[fit_level],
            source="product_analysis",
            phase="phase7",
            method="ai_annotation"
        )

        return demand_id

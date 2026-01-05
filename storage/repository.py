"""
数据库操作封装（Repository层）
提供CRUD操作接口，隔离业务逻辑和数据库细节
"""
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from tqdm import tqdm

from storage.models import Phrase, Demand, Token, ClusterMeta, SeedWord, get_session


class PhraseRepository:
    """短语表操作封装"""

    def __init__(self, session: Session = None):
        """
        初始化Repository

        Args:
            session: SQLAlchemy会话，如果为None则自动创建
        """
        self.session = session or get_session()
        self._should_close = session is None  # 记录是否需要关闭会话

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._should_close:
            self.session.close()

    def bulk_insert_phrases(self, records: List[Dict], batch_size: int = 1000) -> int:
        """
        批量插入短语记录（使用bulk_insert_mappings提高性能）

        Args:
            records: 字典列表，每个字典包含phrase的所有字段
            batch_size: 批次大小

        Returns:
            成功插入的记录数
        """
        print(f"\n📥 批量插入短语数据（batch_size={batch_size}）...")

        total_inserted = 0
        failed_records = []

        # 分批插入
        for i in tqdm(range(0, len(records), batch_size), desc="插入进度"):
            batch = records[i:i + batch_size]
            try:
                self.session.bulk_insert_mappings(Phrase, batch)
                self.session.commit()
                total_inserted += len(batch)
            except Exception as e:
                self.session.rollback()
                print(f"\n⚠️  批次 {i//batch_size + 1} 插入失败: {str(e)}")
                failed_records.extend(batch)

        # 如果有失败记录，尝试逐条插入
        if failed_records:
            print(f"\n🔄 尝试逐条插入 {len(failed_records)} 条失败记录...")
            for record in tqdm(failed_records, desc="逐条插入"):
                try:
                    phrase_obj = Phrase(**record)
                    self.session.add(phrase_obj)
                    self.session.commit()
                    total_inserted += 1
                except Exception as e:
                    self.session.rollback()
                    # 忽略重复记录错误
                    if 'Duplicate entry' in str(e) or 'UNIQUE constraint' in str(e):
                        continue
                    else:
                        print(f"⚠️  记录插入失败: {record.get('phrase', 'unknown')} - {str(e)}")

        print(f"✓ 成功插入 {total_inserted} 条记录")
        return total_inserted

    def get_phrase_count(self) -> int:
        """获取短语总数"""
        return self.session.query(func.count(Phrase.phrase_id)).scalar()

    def get_phrase_by_text(self, phrase_text: str) -> Optional[Phrase]:
        """根据短语文本查询记录"""
        return self.session.query(Phrase).filter(Phrase.phrase == phrase_text).first()

    def get_phrases_by_cluster(self, cluster_id: int, cluster_level: str = 'A') -> List[Phrase]:
        """
        获取指定聚类的所有短语

        Args:
            cluster_id: 聚类ID
            cluster_level: 聚类级别（'A'或'B'）

        Returns:
            短语列表
        """
        if cluster_level == 'A':
            return self.session.query(Phrase).filter(Phrase.cluster_id_A == cluster_id).all()
        else:
            return self.session.query(Phrase).filter(Phrase.cluster_id_B == cluster_id).all()

    def get_phrases_by_round(self, round_id: int) -> List[Phrase]:
        """获取指定轮次的短语"""
        return self.session.query(Phrase).filter(Phrase.first_seen_round == round_id).all()

    def get_phrases_paginated(self, page: int = 1, page_size: int = 1000,
                              filters: Dict = None) -> Tuple[List[Phrase], int]:
        """
        分页获取短语

        Args:
            page: 页码（从1开始）
            page_size: 每页大小
            filters: 过滤条件字典
                - cluster_id_A: 大组ID
                - cluster_id_B: 小组ID
                - source_type: 数据源类型
                - processed_status: 处理状态
                - first_seen_round: 首次出现轮次

        Returns:
            (phrases_list, total_count)
        """
        query = self.session.query(Phrase)

        # 应用过滤器
        if filters:
            if 'cluster_id_A' in filters:
                query = query.filter(Phrase.cluster_id_A == filters['cluster_id_A'])
            if 'cluster_id_B' in filters:
                query = query.filter(Phrase.cluster_id_B == filters['cluster_id_B'])
            if 'source_type' in filters:
                query = query.filter(Phrase.source_type == filters['source_type'])
            if 'processed_status' in filters:
                query = query.filter(Phrase.processed_status == filters['processed_status'])
            if 'first_seen_round' in filters:
                query = query.filter(Phrase.first_seen_round == filters['first_seen_round'])

        # 获取总数
        total = query.count()

        # 分页
        offset = (page - 1) * page_size
        phrases = query.offset(offset).limit(page_size).all()

        return phrases, total

    def get_unseen_phrases(self, limit: Optional[int] = None) -> List[Phrase]:
        """
        获取未处理的短语（processed_status='unseen'）

        Args:
            limit: 限制返回数量

        Returns:
            短语列表
        """
        query = self.session.query(Phrase).filter(Phrase.processed_status == 'unseen')
        if limit:
            query = query.limit(limit)
        return query.all()

    def update_cluster_assignment(self, phrase_id: int, cluster_id_A: Optional[int] = None,
                                   cluster_id_B: Optional[int] = None) -> bool:
        """
        更新短语的聚类分配

        Args:
            phrase_id: 短语ID
            cluster_id_A: 大组ID
            cluster_id_B: 小组ID

        Returns:
            是否更新成功
        """
        try:
            phrase = self.session.query(Phrase).filter(Phrase.phrase_id == phrase_id).first()
            if phrase:
                if cluster_id_A is not None:
                    phrase.cluster_id_A = cluster_id_A
                if cluster_id_B is not None:
                    phrase.cluster_id_B = cluster_id_B
                phrase.processed_status = 'assigned'
                self.session.commit()
                return True
            return False
        except Exception as e:
            self.session.rollback()
            print(f"⚠️  更新失败: {str(e)}")
            return False

    def get_statistics(self) -> Dict:
        """
        获取短语表统计信息

        Returns:
            统计信息字典
        """
        stats = {
            'total_count': self.get_phrase_count(),
            'by_source': {},
            'by_status': {},
            'by_round': {},
            'clustered_A': 0,
            'clustered_B': 0,
            'mapped_to_demand': 0,
        }

        # 按source_type统计
        source_counts = self.session.query(
            Phrase.source_type, func.count(Phrase.phrase_id)
        ).group_by(Phrase.source_type).all()
        stats['by_source'] = {src: cnt for src, cnt in source_counts}

        # 按processed_status统计
        status_counts = self.session.query(
            Phrase.processed_status, func.count(Phrase.phrase_id)
        ).group_by(Phrase.processed_status).all()
        stats['by_status'] = {status: cnt for status, cnt in status_counts}

        # 按first_seen_round统计
        round_counts = self.session.query(
            Phrase.first_seen_round, func.count(Phrase.phrase_id)
        ).group_by(Phrase.first_seen_round).all()
        stats['by_round'] = {rnd: cnt for rnd, cnt in round_counts}

        # 聚类统计
        stats['clustered_A'] = self.session.query(func.count(Phrase.phrase_id)).filter(
            Phrase.cluster_id_A.isnot(None)
        ).scalar()
        stats['clustered_B'] = self.session.query(func.count(Phrase.phrase_id)).filter(
            Phrase.cluster_id_B.isnot(None)
        ).scalar()

        # 需求关联统计
        stats['mapped_to_demand'] = self.session.query(func.count(Phrase.phrase_id)).filter(
            Phrase.mapped_demand_id.isnot(None)
        ).scalar()

        return stats

    def get_seed_word_expansion(self) -> Dict[str, Dict]:
        """
        获取词根扩展统计

        Returns:
            {
                seed_word: {
                    'count': 扩展词数量,
                    'by_round': {round: count},
                    'by_source': {source_type: count}
                }
            }
        """
        # 获取所有seed_word及其统计
        seed_stats = self.session.query(
            Phrase.seed_word,
            Phrase.first_seen_round,
            Phrase.source_type,
            func.count(Phrase.phrase_id).label('count')
        ).filter(
            Phrase.seed_word.isnot(None)
        ).group_by(
            Phrase.seed_word,
            Phrase.first_seen_round,
            Phrase.source_type
        ).all()

        # 组织数据
        result = {}
        for seed, round_num, source, count in seed_stats:
            if seed not in result:
                result[seed] = {
                    'count': 0,
                    'by_round': {},
                    'by_source': {}
                }

            result[seed]['count'] += count
            result[seed]['by_round'][round_num] = result[seed]['by_round'].get(round_num, 0) + count
            result[seed]['by_source'][source or 'unknown'] = result[seed]['by_source'].get(source or 'unknown', 0) + count

        return result

    def get_phrases_by_seed_word(
        self,
        seed_word: str,
        round_num: Optional[int] = None,
        limit: int = 100
    ) -> List[Phrase]:
        """
        获取指定词根扩展出的关键词

        Args:
            seed_word: 词根
            round_num: 筛选特定轮次（None=所有）
            limit: 限制返回数量

        Returns:
            Phrase对象列表
        """
        query = self.session.query(Phrase).filter(
            Phrase.seed_word == seed_word
        )

        if round_num is not None:
            query = query.filter(Phrase.first_seen_round == round_num)

        query = query.order_by(Phrase.frequency.desc()).limit(limit)

        return query.all()

    def get_all_seed_words(self) -> List[str]:
        """获取所有唯一的词根"""
        seeds = self.session.query(Phrase.seed_word).filter(
            Phrase.seed_word.isnot(None)
        ).distinct().all()

        return [s[0] for s in seeds if s[0]]

    def get_words_seed_status(self, words: List[str]) -> Dict[str, int]:
        """
        批量查询词汇的词根状态

        Args:
            words: 词汇列表

        Returns:
            {word: expansion_count}，expansion_count表示该词作为seed_word扩展了多少个phrase
            如果expansion_count=0，表示该词不是词根
        """
        # 查询每个词作为seed_word的扩展数量
        seed_counts = self.session.query(
            Phrase.seed_word,
            func.count(Phrase.phrase_id).label('count')
        ).filter(
            Phrase.seed_word.in_(words)
        ).group_by(Phrase.seed_word).all()

        # 构建结果字典
        result = {word: 0 for word in words}
        for seed_word, count in seed_counts:
            result[seed_word] = count

        return result


class ClusterMetaRepository:
    """聚类元数据表操作封装"""

    def __init__(self, session: Session = None):
        self.session = session or get_session()
        self._should_close = session is None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._should_close:
            self.session.close()

    def create_or_update_cluster(self, cluster_id: int, cluster_level: str,
                                  size: int, example_phrases: str,
                                  main_theme: str = None,
                                  parent_cluster_id: int = None,
                                  total_frequency: int = 0) -> ClusterMeta:
        """
        创建或更新聚类元数据

        Args:
            cluster_id: 聚类ID
            cluster_level: 聚类级别（'A'或'B'）
            size: 聚类大小
            example_phrases: 示例短语（分号分隔）
            main_theme: AI生成的主题标签
            parent_cluster_id: 父聚类ID（仅对B级别有效）
            total_frequency: 总频次

        Returns:
            ClusterMeta对象
        """
        cluster = self.session.query(ClusterMeta).filter(
            and_(ClusterMeta.cluster_id == cluster_id,
                 ClusterMeta.cluster_level == cluster_level)
        ).first()

        if cluster:
            # 更新现有记录
            cluster.size = size
            cluster.example_phrases = example_phrases
            cluster.main_theme = main_theme
            cluster.parent_cluster_id = parent_cluster_id
            cluster.total_frequency = total_frequency
        else:
            # 创建新记录
            cluster = ClusterMeta(
                cluster_id=cluster_id,
                cluster_level=cluster_level,
                size=size,
                example_phrases=example_phrases,
                main_theme=main_theme,
                parent_cluster_id=parent_cluster_id,
                total_frequency=total_frequency,
                is_selected=False,
                selection_score=None
            )
            self.session.add(cluster)

        self.session.commit()
        return cluster

    def get_selected_clusters(self, cluster_level: str = 'A') -> List[ClusterMeta]:
        """获取已选中的聚类"""
        return self.session.query(ClusterMeta).filter(
            and_(ClusterMeta.cluster_level == cluster_level,
                 ClusterMeta.is_selected == True)
        ).all()

    def get_all_clusters(self, cluster_level: str = 'A') -> List[ClusterMeta]:
        """获取所有聚类"""
        return self.session.query(ClusterMeta).filter(
            ClusterMeta.cluster_level == cluster_level
        ).order_by(ClusterMeta.size.desc()).all()

    def update_selection(self, cluster_id: int, cluster_level: str,
                        is_selected: bool, selection_score: int = None) -> bool:
        """更新聚类选择状态"""
        try:
            cluster = self.session.query(ClusterMeta).filter(
                and_(ClusterMeta.cluster_id == cluster_id,
                     ClusterMeta.cluster_level == cluster_level)
            ).first()
            if cluster:
                cluster.is_selected = is_selected
                cluster.selection_score = selection_score
                self.session.commit()
                return True
            return False
        except Exception as e:
            self.session.rollback()
            # 抛出异常而不是打印，让调用方处理
            raise e

    def update_cluster_labeling(
        self,
        cluster_id: int,
        llm_label: str,
        llm_summary: str,
        primary_demand_type: str,
        secondary_demand_types: str,
        labeling_confidence: int,
        cluster_level: str = 'A'
    ) -> bool:
        """
        更新聚类的DeepSeek语义标注

        Args:
            cluster_id: 聚类ID
            llm_label: 简短语义标签
            llm_summary: 详细描述
            primary_demand_type: 主需求类型
            secondary_demand_types: 次要需求类型（JSON字符串）
            labeling_confidence: 标注置信度
            cluster_level: 聚类级别（默认'A'）

        Returns:
            是否成功
        """
        try:
            from datetime import datetime

            cluster = self.session.query(ClusterMeta).filter(
                and_(ClusterMeta.cluster_id == cluster_id,
                     ClusterMeta.cluster_level == cluster_level)
            ).first()

            if cluster:
                cluster.llm_label = llm_label
                cluster.llm_summary = llm_summary
                cluster.primary_demand_type = primary_demand_type
                cluster.secondary_demand_types = secondary_demand_types
                cluster.labeling_confidence = labeling_confidence
                cluster.labeling_timestamp = datetime.utcnow()
                self.session.commit()
                return True
            return False
        except Exception as e:
            self.session.rollback()
            raise e


class DemandRepository:
    """需求卡片表操作封装"""

    def __init__(self, session: Session = None):
        self.session = session or get_session()
        self._should_close = session is None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._should_close:
            self.session.close()

    def create_demand(self, title: str, description: str, user_scenario: str,
                     demand_type: str, source_cluster_A: int, source_cluster_B: int,
                     related_phrases_count: int = 0, business_value: str = 'unknown',
                     status: str = 'idea') -> Demand:
        """创建需求卡片"""
        demand = Demand(
            title=title,
            description=description,
            user_scenario=user_scenario,
            demand_type=demand_type,
            source_cluster_A=source_cluster_A,
            source_cluster_B=source_cluster_B,
            related_phrases_count=related_phrases_count,
            business_value=business_value,
            status=status
        )
        self.session.add(demand)
        self.session.commit()
        self.session.refresh(demand)  # 刷新对象，确保所有属性都已加载
        return demand

    def get_validated_demands(self) -> List[Demand]:
        """获取已验证的需求"""
        return self.session.query(Demand).filter(Demand.status == 'validated').all()

    def get_demands_by_cluster(self, cluster_id: int, cluster_level: str = 'A') -> List[Demand]:
        """获取指定聚类的需求"""
        if cluster_level == 'A':
            return self.session.query(Demand).filter(Demand.source_cluster_A == cluster_id).all()
        else:
            return self.session.query(Demand).filter(Demand.source_cluster_B == cluster_id).all()


class TokenRepository:
    """Token词库表操作封装"""

    def __init__(self, session: Session = None):
        self.session = session or get_session()
        self._should_close = session is None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._should_close:
            self.session.close()

    def create_token(self, token_text: str, token_type: str,
                     in_phrase_count: int = 0, first_seen_round: int = 1,
                     verified: bool = False, notes: str = None) -> Token:
        """创建token记录"""
        # 检查是否已存在
        existing = self.session.query(Token).filter(
            Token.token_text == token_text
        ).first()

        if existing:
            # 更新统计信息
            existing.in_phrase_count = max(existing.in_phrase_count, in_phrase_count)
            if notes:
                existing.notes = notes
            self.session.commit()
            return existing

        # 创建新token
        token = Token(
            token_text=token_text,
            token_type=token_type,
            in_phrase_count=in_phrase_count,
            first_seen_round=first_seen_round,
            verified=verified,
            notes=notes
        )
        self.session.add(token)
        self.session.commit()
        return token

    def get_all_tokens(self, token_type: str = None, verified_only: bool = False) -> List[Token]:
        """获取所有tokens"""
        query = self.session.query(Token)

        if token_type:
            query = query.filter(Token.token_type == token_type)

        if verified_only:
            query = query.filter(Token.verified == True)

        return query.order_by(Token.in_phrase_count.desc()).all()

    def get_token_by_text(self, token_text: str) -> Optional[Token]:
        """根据文本获取token"""
        return self.session.query(Token).filter(Token.token_text == token_text).first()

    def update_verification(self, token_text: str, verified: bool, notes: str = None) -> bool:
        """更新token验证状态"""
        token = self.get_token_by_text(token_text)
        if token:
            token.verified = verified
            if notes:
                token.notes = notes
            self.session.commit()
            return True
        return False

    def bulk_insert_tokens(self, tokens: List[Dict]) -> int:
        """批量插入tokens"""
        inserted = 0
        for token_data in tokens:
            try:
                self.create_token(**token_data)
                inserted += 1
            except Exception:
                continue
        return inserted


# 便捷函数


class SeedWordRepository:
    """词根管理表操作封装"""

    def __init__(self, session: Session = None):
        """初始化Repository"""
        self.session = session or get_session()
        self._should_close = session is None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._should_close:
            self.session.close()

    def create_or_update_seed_word(
        self,
        seed_word: str,
        token_types: list = None,  # 改为列表，支持多分类
        primary_token_type: str = None,  # 主要类别
        definition: str = None,
        business_value: str = None,
        user_scenario: str = None,
        parent_seed_word: str = None,
        level: int = 1,
        status: str = "active",
        priority: str = "medium",
        source: str = "user_created",
        first_seen_round: int = None,
        verified: bool = False,
        confidence: str = "medium",
        tags: str = None,
        notes: str = None
    ) -> SeedWord:
        """
        创建或更新词根记录

        Args:
            seed_word: 词根文本
            token_types: Token类型列表（可多选）如 ["intent", "action"]
            primary_token_type: 主要Token类型（用于排序和筛选）
            definition: 词根定义
            business_value: 商业价值说明
            user_scenario: 用户场景
            parent_seed_word: 父词根
            level: 层级
            status: 状态
            priority: 优先级
            source: 来源
            first_seen_round: 首次出现轮次
            verified: 是否已审核
            confidence: 置信度
            tags: 标签（JSON格式）
            notes: 备注

        Returns:
            SeedWord对象
        """
        import json

        existing = self.get_seed_word(seed_word)

        if existing:
            # 更新现有记录（仅更新非None的字段）
            if token_types is not None:
                existing.token_types = json.dumps(token_types)
            if primary_token_type is not None:
                existing.primary_token_type = primary_token_type
            if definition is not None:
                existing.definition = definition
            if business_value is not None:
                existing.business_value = business_value
            if user_scenario is not None:
                existing.user_scenario = user_scenario
            if parent_seed_word is not None:
                existing.parent_seed_word = parent_seed_word
            if level is not None:
                existing.level = level
            if status is not None:
                existing.status = status
            if priority is not None:
                existing.priority = priority
            if verified is not None:
                existing.verified = verified
            if confidence is not None:
                existing.confidence = confidence
            if tags is not None:
                existing.tags = tags
            if notes is not None:
                existing.notes = notes

            self.session.commit()
            return existing
        else:
            # 创建新记录
            new_seed = SeedWord(
                seed_word=seed_word,
                token_types=json.dumps(token_types) if token_types else None,
                primary_token_type=primary_token_type,
                definition=definition,
                business_value=business_value,
                user_scenario=user_scenario,
                parent_seed_word=parent_seed_word,
                level=level,
                status=status,
                priority=priority,
                source=source,
                first_seen_round=first_seen_round,
                verified=verified,
                confidence=confidence,
                tags=tags,
                notes=notes
            )
            self.session.add(new_seed)
            self.session.commit()
            return new_seed

    def get_seed_word(self, seed_word: str) -> Optional[SeedWord]:
        """根据词根文本查询记录"""
        return self.session.query(SeedWord).filter(
            SeedWord.seed_word == seed_word
        ).first()

    def get_all_seed_words(
        self,
        primary_token_type: str = None,  # 改为按主要类别筛选
        status: str = None,
        verified_only: bool = False,
        priority: str = None
    ) -> List[SeedWord]:
        """
        获取所有词根记录（支持筛选）

        Args:
            primary_token_type: 按主要Token类型筛选
            status: 按状态筛选
            verified_only: 仅返回已审核的
            priority: 按优先级筛选

        Returns:
            词根列表
        """
        query = self.session.query(SeedWord)

        if primary_token_type:
            query = query.filter(SeedWord.primary_token_type == primary_token_type)
        if status:
            query = query.filter(SeedWord.status == status)
        if verified_only:
            query = query.filter(SeedWord.verified == True)
        if priority:
            query = query.filter(SeedWord.priority == priority)

        return query.order_by(SeedWord.expansion_count.desc()).all()

    def get_seeds_by_type(self, token_type: str, include_secondary: bool = True) -> List[SeedWord]:
        """
        获取指定类型的所有词根

        Args:
            token_type: 类型（intent/action/object/other）
            include_secondary: 是否包含次要类别匹配的词根

        Returns:
            词根列表
        """
        import json

        if not include_secondary:
            # 仅匹配主要类别
            return self.session.query(SeedWord).filter(
                SeedWord.primary_token_type == token_type
            ).order_by(SeedWord.expansion_count.desc()).all()
        else:
            # 匹配主要类别或包含在多分类中
            all_seeds = self.session.query(SeedWord).all()
            matched_seeds = []

            for seed in all_seeds:
                # 检查主要类别
                if seed.primary_token_type == token_type:
                    matched_seeds.append(seed)
                    continue

                # 检查多分类
                if seed.token_types:
                    try:
                        types = json.loads(seed.token_types)
                        if token_type in types:
                            matched_seeds.append(seed)
                    except:
                        continue

            # 按expansion_count排序
            matched_seeds.sort(key=lambda x: x.expansion_count or 0, reverse=True)
            return matched_seeds

    def update_expansion_stats(self, seed_word: str) -> bool:
        """
        更新词根的扩展统计信息（从phrases表聚合）

        Args:
            seed_word: 词根文本

        Returns:
            是否成功
        """
        try:
            seed_obj = self.get_seed_word(seed_word)
            if not seed_obj:
                return False

            # 统计该词根扩展的phrase数量
            expansion_count = self.session.query(func.count(Phrase.phrase_id)).filter(
                Phrase.seed_word == seed_word
            ).scalar() or 0

            # 统计总搜索量
            total_volume = self.session.query(func.sum(Phrase.volume)).filter(
                Phrase.seed_word == seed_word
            ).scalar() or 0

            # 统计平均频次
            avg_frequency = self.session.query(func.avg(Phrase.frequency)).filter(
                Phrase.seed_word == seed_word
            ).scalar() or 0

            # 更新
            seed_obj.expansion_count = expansion_count
            seed_obj.total_volume = total_volume
            seed_obj.avg_frequency = int(avg_frequency)

            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            print(f"❌ 更新词根统计失败: {str(e)}")
            return False

    def batch_update_all_stats(self) -> int:
        """
        批量更新所有词根的统计信息

        Returns:
            更新成功的数量
        """
        all_seeds = self.get_all_seed_words()
        success_count = 0

        print(f"\n📊 批量更新 {len(all_seeds)} 个词根的统计信息...")
        for seed in tqdm(all_seeds, desc="更新进度"):
            if self.update_expansion_stats(seed.seed_word):
                success_count += 1

        print(f"✓ 成功更新 {success_count} 个词根")
        return success_count

    def link_demand(self, seed_word: str, demand_id: int, is_primary: bool = False) -> bool:
        """
        关联词根与需求

        Args:
            seed_word: 词根文本
            demand_id: 需求ID
            is_primary: 是否为主要关联

        Returns:
            是否成功
        """
        try:
            seed_obj = self.get_seed_word(seed_word)
            if not seed_obj:
                return False

            # 更新主要需求ID
            if is_primary:
                seed_obj.primary_demand_id = demand_id

            # 更新关联需求列表（JSON格式）
            import json
            if seed_obj.related_demand_ids:
                demand_ids = json.loads(seed_obj.related_demand_ids)
            else:
                demand_ids = []

            if demand_id not in demand_ids:
                demand_ids.append(demand_id)

            seed_obj.related_demand_ids = json.dumps(demand_ids)
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            print(f"❌ 关联需求失败: {str(e)}")
            return False

    def get_seeds_by_demand(self, demand_id: int) -> List[SeedWord]:
        """获取与指定需求关联的所有词根"""
        # 查询primary_demand_id匹配的
        primary_seeds = self.session.query(SeedWord).filter(
            SeedWord.primary_demand_id == demand_id
        ).all()

        # 查询related_demand_ids中包含的（需要JSON搜索）
        # 注意：这需要数据库支持JSON搜索，SQLite可能需要特殊处理
        all_seeds = self.session.query(SeedWord).all()
        related_seeds = []

        import json
        for seed in all_seeds:
            if seed.related_demand_ids:
                try:
                    demand_ids = json.loads(seed.related_demand_ids)
                    if demand_id in demand_ids:
                        related_seeds.append(seed)
                except:
                    continue

        # 合并并去重
        result_dict = {s.seed_id: s for s in primary_seeds + related_seeds}
        return list(result_dict.values())

    def get_statistics(self) -> Dict:
        """获取词根统计信息"""
        total = self.session.query(func.count(SeedWord.seed_id)).scalar() or 0

        # 按主要类别统计
        by_primary_type = {}
        for token_type in ['intent', 'action', 'object', 'other']:
            count = self.session.query(func.count(SeedWord.seed_id)).filter(
                SeedWord.primary_token_type == token_type
            ).scalar() or 0
            by_primary_type[token_type] = count

        by_status = {}
        for status in ['active', 'paused', 'archived']:
            count = self.session.query(func.count(SeedWord.seed_id)).filter(
                SeedWord.status == status
            ).scalar() or 0
            by_status[status] = count

        verified_count = self.session.query(func.count(SeedWord.seed_id)).filter(
            SeedWord.verified == True
        ).scalar() or 0

        return {
            'total': total,
            'by_primary_type': by_primary_type,
            'by_status': by_status,
            'verified_count': verified_count,
            'verified_rate': round(verified_count / total * 100, 1) if total > 0 else 0
        }


# ==================== 测试工具函数 ====================
def test_database_connection():
    """测试数据库连接"""
    try:
        with PhraseRepository() as repo:
            count = repo.get_phrase_count()
            print(f"✅ 数据库连接成功！当前phrases表记录数: {count}")
            return True
    except Exception as e:
        print(f"❌ 数据库连接失败: {str(e)}")
        return False


if __name__ == "__main__":
    test_database_connection()

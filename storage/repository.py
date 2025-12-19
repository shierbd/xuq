"""
数据库操作封装（Repository层）
提供CRUD操作接口，隔离业务逻辑和数据库细节
"""
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from tqdm import tqdm

from storage.models import Phrase, Demand, Token, ClusterMeta, get_session


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
            print(f"⚠️  更新失败: {str(e)}")
            return False


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


# 便捷函数
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

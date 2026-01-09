"""
Reddit板块分析功能 - 数据访问层

提供两个Repository类：
1. RedditSubredditRepository - Reddit板块数据访问
2. AIPromptConfigRepository - AI提示词配置数据访问
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy import or_, and_, func
from sqlalchemy.orm import Session
from storage.models import (
    get_session,
    RedditSubreddit,
    AIPromptConfig
)


# ==================== RedditSubredditRepository ====================
class RedditSubredditRepository:
    """Reddit板块数据访问层"""

    def __init__(self, session: Optional[Session] = None):
        """
        初始化Repository

        Args:
            session: SQLAlchemy会话对象（可选，默认创建新会话）
        """
        self.session = session or get_session()
        self._should_close = session is None  # 如果是自己创建的session，需要关闭

    def __enter__(self):
        """支持with语句"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出with语句时关闭session"""
        if self._should_close:
            self.session.close()

    # ==================== 基础CRUD ====================

    def create(self, data: Dict[str, Any]) -> int:
        """
        创建记录

        Args:
            data: 记录数据字典

        Returns:
            创建的记录ID
        """
        subreddit = RedditSubreddit(**data)
        self.session.add(subreddit)
        self.session.commit()
        return subreddit.subreddit_id

    def get_by_id(self, subreddit_id: int) -> Optional[Dict[str, Any]]:
        """
        按ID查询

        Args:
            subreddit_id: 板块ID

        Returns:
            记录字典，不存在返回None
        """
        subreddit = self.session.query(RedditSubreddit).filter_by(
            subreddit_id=subreddit_id
        ).first()

        if not subreddit:
            return None

        return self._to_dict(subreddit)

    def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        按名称查询

        Args:
            name: 板块名称

        Returns:
            记录字典，不存在返回None
        """
        subreddit = self.session.query(RedditSubreddit).filter_by(
            name=name
        ).first()

        if not subreddit:
            return None

        return self._to_dict(subreddit)

    def update(self, subreddit_id: int, data: Dict[str, Any]) -> bool:
        """
        更新记录

        Args:
            subreddit_id: 板块ID
            data: 更新数据字典

        Returns:
            是否更新成功
        """
        result = self.session.query(RedditSubreddit).filter_by(
            subreddit_id=subreddit_id
        ).update(data)

        self.session.commit()
        return result > 0

    def delete(self, subreddit_id: int) -> bool:
        """
        删除记录

        Args:
            subreddit_id: 板块ID

        Returns:
            是否删除成功
        """
        result = self.session.query(RedditSubreddit).filter_by(
            subreddit_id=subreddit_id
        ).delete()

        self.session.commit()
        return result > 0

    # ==================== 批量操作 ====================

    def bulk_insert(self, records: List[Dict[str, Any]], batch_size: int = 1000) -> int:
        """
        批量插入记录

        Args:
            records: 记录列表
            batch_size: 批次大小

        Returns:
            插入的记录数量
        """
        total_inserted = 0

        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            self.session.bulk_insert_mappings(RedditSubreddit, batch)
            self.session.commit()
            total_inserted += len(batch)

        return total_inserted

    def bulk_update(self, updates: List[Dict[str, Any]]) -> int:
        """
        批量更新记录

        Args:
            updates: 更新列表，每个元素必须包含subreddit_id

        Returns:
            更新的记录数量
        """
        if not updates:
            return 0

        self.session.bulk_update_mappings(RedditSubreddit, updates)
        self.session.commit()
        return len(updates)

    # ==================== 查询方法 ====================

    def get_by_status(self, status: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        按状态查询

        Args:
            status: 分析状态
            limit: 返回数量限制

        Returns:
            记录列表
        """
        subreddits = self.session.query(RedditSubreddit).filter_by(
            ai_analysis_status=status
        ).limit(limit).all()

        return [self._to_dict(s) for s in subreddits]

    def get_by_tags(self, tags: List[str]) -> List[Dict[str, Any]]:
        """
        按标签查询（OR查询）

        Args:
            tags: 标签列表

        Returns:
            记录列表
        """
        if not tags:
            return []

        # 构建OR查询条件
        conditions = []
        for tag in tags:
            conditions.append(RedditSubreddit.tag1 == tag)
            conditions.append(RedditSubreddit.tag2 == tag)
            conditions.append(RedditSubreddit.tag3 == tag)

        subreddits = self.session.query(RedditSubreddit).filter(
            or_(*conditions)
        ).all()

        return [self._to_dict(s) for s in subreddits]

    def get_by_batch(self, batch_id: str) -> List[Dict[str, Any]]:
        """
        按批次查询

        Args:
            batch_id: 批次ID

        Returns:
            记录列表
        """
        subreddits = self.session.query(RedditSubreddit).filter_by(
            import_batch_id=batch_id
        ).all()

        return [self._to_dict(s) for s in subreddits]

    def query(
        self,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        通用查询方法

        Args:
            filters: 筛选条件字典
                - status: List[str] - 状态列表
                - tags: List[str] - 标签列表（OR查询）
                - importance_score_min: int - 最小评分
                - importance_score_max: int - 最大评分
                - subscribers_min: int - 最小订阅数
                - subscribers_max: int - 最大订阅数
                - batch_id: str - 批次ID
                - search_text: str - 搜索文本（名称或描述）
            sort_by: 排序字段
            sort_order: 排序方向（asc/desc）
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            {
                'total': int,
                'data': List[Dict]
            }
        """
        query = self.session.query(RedditSubreddit)

        # 应用筛选条件
        if filters:
            # 状态筛选
            if 'status' in filters and filters['status']:
                query = query.filter(RedditSubreddit.ai_analysis_status.in_(filters['status']))

            # 标签筛选
            if 'tags' in filters and filters['tags']:
                tag_conditions = []
                for tag in filters['tags']:
                    tag_conditions.append(RedditSubreddit.tag1 == tag)
                    tag_conditions.append(RedditSubreddit.tag2 == tag)
                    tag_conditions.append(RedditSubreddit.tag3 == tag)
                query = query.filter(or_(*tag_conditions))

            # 评分范围筛选
            if 'importance_score_min' in filters:
                query = query.filter(RedditSubreddit.importance_score >= filters['importance_score_min'])
            if 'importance_score_max' in filters:
                query = query.filter(RedditSubreddit.importance_score <= filters['importance_score_max'])

            # 订阅数范围筛选
            if 'subscribers_min' in filters:
                query = query.filter(RedditSubreddit.subscribers >= filters['subscribers_min'])
            if 'subscribers_max' in filters:
                query = query.filter(RedditSubreddit.subscribers <= filters['subscribers_max'])

            # 批次筛选
            if 'batch_id' in filters:
                query = query.filter(RedditSubreddit.import_batch_id == filters['batch_id'])

            # 文本搜索
            if 'search_text' in filters and filters['search_text']:
                search_pattern = f"%{filters['search_text']}%"
                query = query.filter(
                    or_(
                        RedditSubreddit.name.like(search_pattern),
                        RedditSubreddit.description.like(search_pattern)
                    )
                )

        # 获取总数
        total = query.count()

        # 排序
        if sort_order.lower() == 'desc':
            query = query.order_by(getattr(RedditSubreddit, sort_by).desc())
        else:
            query = query.order_by(getattr(RedditSubreddit, sort_by).asc())

        # 分页
        query = query.limit(limit).offset(offset)

        # 执行查询
        subreddits = query.all()

        return {
            'total': total,
            'data': [self._to_dict(s) for s in subreddits]
        }

    # ==================== 统计方法 ====================

    def count_by_status(self) -> Dict[str, int]:
        """
        按状态统计

        Returns:
            状态计数字典
        """
        results = self.session.query(
            RedditSubreddit.ai_analysis_status,
            func.count(RedditSubreddit.subreddit_id)
        ).group_by(RedditSubreddit.ai_analysis_status).all()

        return {status: count for status, count in results}

    def get_tag_statistics(self) -> Dict[str, int]:
        """
        获取标签统计

        Returns:
            标签计数字典
        """
        tag_counts = {}

        # 统计tag1
        results1 = self.session.query(
            RedditSubreddit.tag1,
            func.count(RedditSubreddit.subreddit_id)
        ).filter(RedditSubreddit.tag1.isnot(None)).group_by(RedditSubreddit.tag1).all()

        for tag, count in results1:
            tag_counts[tag] = tag_counts.get(tag, 0) + count

        # 统计tag2
        results2 = self.session.query(
            RedditSubreddit.tag2,
            func.count(RedditSubreddit.subreddit_id)
        ).filter(RedditSubreddit.tag2.isnot(None)).group_by(RedditSubreddit.tag2).all()

        for tag, count in results2:
            tag_counts[tag] = tag_counts.get(tag, 0) + count

        # 统计tag3
        results3 = self.session.query(
            RedditSubreddit.tag3,
            func.count(RedditSubreddit.subreddit_id)
        ).filter(RedditSubreddit.tag3.isnot(None)).group_by(RedditSubreddit.tag3).all()

        for tag, count in results3:
            tag_counts[tag] = tag_counts.get(tag, 0) + count

        return tag_counts

    # ==================== 状态更新 ====================

    def update_status(self, subreddit_id: int, status: str) -> bool:
        """
        更新分析状态

        Args:
            subreddit_id: 板块ID
            status: 新状态

        Returns:
            是否更新成功
        """
        return self.update(subreddit_id, {'ai_analysis_status': status})

    # ==================== 辅助方法 ====================

    def _to_dict(self, subreddit: RedditSubreddit) -> Dict[str, Any]:
        """
        将ORM对象转换为字典

        Args:
            subreddit: RedditSubreddit对象

        Returns:
            字典
        """
        return {
            'subreddit_id': subreddit.subreddit_id,
            'name': subreddit.name,
            'description': subreddit.description,
            'subscribers': subreddit.subscribers,
            'tag1': subreddit.tag1,
            'tag2': subreddit.tag2,
            'tag3': subreddit.tag3,
            'importance_score': subreddit.importance_score,
            'ai_analysis_status': subreddit.ai_analysis_status,
            'ai_analysis_timestamp': subreddit.ai_analysis_timestamp,
            'ai_model_used': subreddit.ai_model_used,
            'ai_confidence': subreddit.ai_confidence,
            'notes': subreddit.notes,
            'import_batch_id': subreddit.import_batch_id,
            'created_at': subreddit.created_at,
            'updated_at': subreddit.updated_at
        }


# ==================== AIPromptConfigRepository ====================
class AIPromptConfigRepository:
    """AI提示词配置数据访问层"""

    def __init__(self, session: Optional[Session] = None):
        """
        初始化Repository

        Args:
            session: SQLAlchemy会话对象（可选，默认创建新会话）
        """
        self.session = session or get_session()
        self._should_close = session is None

    def __enter__(self):
        """支持with语句"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出with语句时关闭session"""
        if self._should_close:
            self.session.close()

    # ==================== 基础CRUD ====================

    def create(self, data: Dict[str, Any]) -> int:
        """
        创建配置

        Args:
            data: 配置数据字典

        Returns:
            创建的配置ID
        """
        config = AIPromptConfig(**data)
        self.session.add(config)
        self.session.commit()
        return config.config_id

    def get_by_id(self, config_id: int) -> Optional[Dict[str, Any]]:
        """
        按ID查询

        Args:
            config_id: 配置ID

        Returns:
            配置字典，不存在返回None
        """
        config = self.session.query(AIPromptConfig).filter_by(
            config_id=config_id
        ).first()

        if not config:
            return None

        return self._to_dict(config)

    def update(self, config_id: int, data: Dict[str, Any]) -> bool:
        """
        更新配置

        Args:
            config_id: 配置ID
            data: 更新数据字典

        Returns:
            是否更新成功
        """
        result = self.session.query(AIPromptConfig).filter_by(
            config_id=config_id
        ).update(data)

        self.session.commit()
        return result > 0

    def delete(self, config_id: int) -> bool:
        """
        删除配置

        Args:
            config_id: 配置ID

        Returns:
            是否删除成功
        """
        result = self.session.query(AIPromptConfig).filter_by(
            config_id=config_id
        ).delete()

        self.session.commit()
        return result > 0

    # ==================== 查询方法 ====================

    def get_default_config(self, config_type: str = 'reddit_analysis') -> Optional[Dict[str, Any]]:
        """
        获取默认配置

        Args:
            config_type: 配置类型

        Returns:
            配置字典，不存在返回None
        """
        config = self.session.query(AIPromptConfig).filter_by(
            config_type=config_type,
            is_default=True,
            is_active=True
        ).first()

        if not config:
            return None

        return self._to_dict(config)

    def get_active_configs(self, config_type: str = 'reddit_analysis') -> List[Dict[str, Any]]:
        """
        获取所有启用的配置

        Args:
            config_type: 配置类型

        Returns:
            配置列表
        """
        configs = self.session.query(AIPromptConfig).filter_by(
            config_type=config_type,
            is_active=True
        ).all()

        return [self._to_dict(c) for c in configs]

    def get_all_configs(self) -> List[Dict[str, Any]]:
        """
        获取所有配置

        Returns:
            配置列表
        """
        configs = self.session.query(AIPromptConfig).all()
        return [self._to_dict(c) for c in configs]

    # ==================== 配置管理 ====================

    def set_default(self, config_id: int) -> bool:
        """
        设置为默认配置

        Args:
            config_id: 配置ID

        Returns:
            是否设置成功
        """
        # 先获取配置的类型
        config = self.session.query(AIPromptConfig).filter_by(
            config_id=config_id
        ).first()

        if not config:
            return False

        # 取消同类型的其他默认配置
        self.session.query(AIPromptConfig).filter_by(
            config_type=config.config_type,
            is_default=True
        ).update({'is_default': False})

        # 设置当前配置为默认
        config.is_default = True
        self.session.commit()

        return True

    def activate(self, config_id: int) -> bool:
        """
        启用配置

        Args:
            config_id: 配置ID

        Returns:
            是否启用成功
        """
        return self.update(config_id, {'is_active': True})

    def deactivate(self, config_id: int) -> bool:
        """
        禁用配置

        Args:
            config_id: 配置ID

        Returns:
            是否禁用成功
        """
        return self.update(config_id, {'is_active': False})

    # ==================== 辅助方法 ====================

    def _to_dict(self, config: AIPromptConfig) -> Dict[str, Any]:
        """
        将ORM对象转换为字典

        Args:
            config: AIPromptConfig对象

        Returns:
            字典
        """
        return {
            'config_id': config.config_id,
            'config_name': config.config_name,
            'config_type': config.config_type,
            'prompt_template': config.prompt_template,
            'system_message': config.system_message,
            'temperature': float(config.temperature) if config.temperature else 0.7,
            'max_tokens': config.max_tokens,
            'is_active': config.is_active,
            'is_default': config.is_default,
            'description': config.description,
            'created_by': config.created_by,
            'created_at': config.created_at,
            'updated_at': config.updated_at
        }


# ==================== 便捷导入 ====================
__all__ = [
    'RedditSubredditRepository',
    'AIPromptConfigRepository'
]

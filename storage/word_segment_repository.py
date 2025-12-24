# -*- coding: utf-8 -*-
"""
分词结果Repository
管理word_segments和segmentation_batches表的CRUD操作
"""
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from collections import Counter

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from storage.models import WordSegment, SegmentationBatch, get_session


class WordSegmentRepository:
    """分词结果Repository"""

    def __init__(self):
        """初始化"""
        self.session: Optional[Session] = None

    def __enter__(self):
        """进入上下文管理器"""
        self.session = get_session()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文管理器"""
        if self.session:
            if exc_type is None:
                self.session.commit()
            else:
                self.session.rollback()
            self.session.close()

    # ==================== 分词结果管理 ====================

    def get_word_segments(self, min_frequency: int = 1) -> Dict[str, int]:
        """
        获取所有分词结果（返回Counter格式）

        Args:
            min_frequency: 最小频次过滤

        Returns:
            {word: frequency}字典
        """
        words = self.session.query(
            WordSegment.word,
            WordSegment.frequency
        ).filter(
            WordSegment.frequency >= min_frequency
        ).all()

        return {word: freq for word, freq in words}

    def save_word_segments(
        self,
        word_counter: Counter,
        pos_tags: Optional[Dict[str, Tuple[str, str, str]]] = None,
        translations: Optional[Dict[str, str]] = None,
        batch_id: Optional[int] = None
    ) -> int:
        """
        保存或更新分词结果

        Args:
            word_counter: {word: frequency} Counter对象
            pos_tags: {word: (pos_tag, pos_category, pos_chinese)}
            translations: {word: translation}
            batch_id: 所属批次ID

        Returns:
            新增的单词数量
        """
        new_words_count = 0

        for word, frequency in word_counter.items():
            # 检查是否已存在
            existing = self.session.query(WordSegment).filter(
                WordSegment.word == word
            ).first()

            if existing:
                # 更新频次（累加）
                existing.frequency += frequency
                existing.updated_at = datetime.utcnow()

                # 更新词性和翻译（如果提供）
                if pos_tags and word in pos_tags:
                    pos_tag, pos_category, pos_chinese = pos_tags[word]
                    existing.pos_tag = pos_tag
                    existing.pos_category = pos_category
                    existing.pos_chinese = pos_chinese

                if translations and word in translations:
                    existing.translation = translations[word]
            else:
                # 创建新记录
                new_word = WordSegment(
                    word=word,
                    frequency=frequency,
                    pos_tag=pos_tags[word][0] if pos_tags and word in pos_tags else None,
                    pos_category=pos_tags[word][1] if pos_tags and word in pos_tags else None,
                    pos_chinese=pos_tags[word][2] if pos_tags and word in pos_tags else None,
                    translation=translations.get(word) if translations else None,
                )
                self.session.add(new_word)
                new_words_count += 1

        self.session.commit()
        return new_words_count

    def get_word_segment(self, word: str) -> Optional[WordSegment]:
        """获取单个单词的分词记录"""
        return self.session.query(WordSegment).filter(
            WordSegment.word == word
        ).first()

    def get_all_words(self) -> List[str]:
        """获取所有已分词的单词列表"""
        words = self.session.query(WordSegment.word).all()
        return [w[0] for w in words]

    def get_statistics(self) -> Dict:
        """
        获取分词结果统计

        Returns:
            统计信息字典
        """
        total_words = self.session.query(func.count(WordSegment.word_id)).scalar() or 0
        total_frequency = self.session.query(func.sum(WordSegment.frequency)).scalar() or 0
        root_words_count = self.session.query(func.count(WordSegment.word_id)).filter(
            WordSegment.is_root == True
        ).scalar() or 0

        # 按词性分类统计
        pos_stats = self.session.query(
            WordSegment.pos_category,
            func.count(WordSegment.word_id)
        ).group_by(WordSegment.pos_category).all()

        return {
            'total_words': total_words,
            'total_frequency': total_frequency,
            'root_words_count': root_words_count,
            'by_pos_category': {pos: count for pos, count in pos_stats if pos}
        }

    # ==================== 词根管理 ====================

    def mark_as_root(
        self,
        words: List[str],
        round_num: int,
        source: str = 'user_selected'
    ) -> int:
        """
        标记词为词根

        Args:
            words: 要标记的词列表
            round_num: 轮次
            source: 来源（initial_import, user_selected）

        Returns:
            成功标记的数量
        """
        marked_count = 0

        for word in words:
            word_segment = self.get_word_segment(word)
            if word_segment:
                word_segment.is_root = True
                word_segment.root_round = round_num
                word_segment.root_source = source
                word_segment.updated_at = datetime.utcnow()
                marked_count += 1

        self.session.commit()
        return marked_count

    def unmark_as_root(self, words: List[str]) -> int:
        """
        取消词根标记

        Args:
            words: 要取消标记的词列表

        Returns:
            取消标记的数量
        """
        unmarked_count = 0

        for word in words:
            word_segment = self.get_word_segment(word)
            if word_segment and word_segment.is_root:
                word_segment.is_root = False
                word_segment.root_round = None
                word_segment.root_source = None
                word_segment.updated_at = datetime.utcnow()
                unmarked_count += 1

        self.session.commit()
        return unmarked_count

    def get_root_words(self, round_num: Optional[int] = None) -> List[Dict]:
        """
        获取词根列表

        Args:
            round_num: 筛选特定轮次（None=所有）

        Returns:
            词根信息列表
        """
        query = self.session.query(WordSegment).filter(
            WordSegment.is_root == True
        )

        if round_num is not None:
            query = query.filter(WordSegment.root_round == round_num)

        roots = query.order_by(WordSegment.root_round, WordSegment.frequency.desc()).all()

        return [{
            'word': r.word,
            'frequency': r.frequency,
            'round': r.root_round,
            'source': r.root_source,
            'translation': r.translation,
            'pos_category': r.pos_category
        } for r in roots]

    # ==================== 批次管理 ====================

    def create_batch(self, phrase_count: int, notes: Optional[str] = None) -> int:
        """
        创建分词批次记录

        Args:
            phrase_count: 要处理的短语数
            notes: 备注

        Returns:
            批次ID
        """
        batch = SegmentationBatch(
            phrase_count=phrase_count,
            status='in_progress',
            notes=notes
        )
        self.session.add(batch)
        self.session.commit()
        return batch.batch_id

    def complete_batch(
        self,
        batch_id: int,
        word_count: int,
        new_word_count: int,
        duration_seconds: int
    ):
        """
        完成批次记录

        Args:
            batch_id: 批次ID
            word_count: 总单词数
            new_word_count: 新增单词数
            duration_seconds: 耗时（秒）
        """
        batch = self.session.query(SegmentationBatch).get(batch_id)
        if batch:
            batch.word_count = word_count
            batch.new_word_count = new_word_count
            batch.duration_seconds = duration_seconds
            batch.status = 'completed'
            self.session.commit()

    def fail_batch(self, batch_id: int, error_message: str):
        """标记批次失败"""
        batch = self.session.query(SegmentationBatch).get(batch_id)
        if batch:
            batch.status = 'failed'
            batch.notes = error_message
            self.session.commit()

    def get_latest_batch(self) -> Optional[SegmentationBatch]:
        """获取最新的批次记录"""
        return self.session.query(SegmentationBatch).order_by(
            SegmentationBatch.batch_date.desc()
        ).first()

    def get_batch_history(self, limit: int = 10) -> List[SegmentationBatch]:
        """获取批次历史记录"""
        return self.session.query(SegmentationBatch).order_by(
            SegmentationBatch.batch_date.desc()
        ).limit(limit).all()

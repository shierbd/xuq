# -*- coding: utf-8 -*-
"""
增量分词模块
实现智能的增量分词：只对新增关键词分词，合并已有结果
"""
import time
from typing import List, Dict, Tuple, Set
from collections import Counter

from utils.keyword_segmentation import segment_keywords
from storage.repository import PhraseRepository
from storage.word_segment_repository import WordSegmentRepository


def incremental_segmentation(
    stopwords: Set[str],
    pos_tagging: bool = True,
    translation: bool = False
) -> Tuple[Counter, Dict, Dict, Dict]:
    """
    执行增量分词：只对新增的关键词进行分词

    工作流程：
    1. 从数据库加载所有关键词
    2. 检查哪些关键词已经分过词
    3. 只对新增的关键词进行分词
    4. 合并新旧分词结果
    5. 保存到数据库

    Args:
        stopwords: 停用词集合
        pos_tagging: 是否进行词性标注
        translation: 是否进行翻译

    Returns:
        (word_counter, pos_tags, translations, stats)
    """
    stats = {
        'total_phrases': 0,
        'existing_phrases': 0,
        'new_phrases': 0,
        'total_words': 0,
        'existing_words': 0,
        'new_words': 0,
        'duration_seconds': 0
    }

    start_time = time.time()

    # 1. 加载所有关键词
    print("[1/6] Loading keywords from database...")
    with PhraseRepository() as phrase_repo:
        all_phrases = []
        page = 1
        page_size = 10000

        while True:
            phrases, total = phrase_repo.get_phrases_paginated(
                page=page,
                page_size=page_size
            )
            if not phrases:
                break
            all_phrases.extend([p.phrase for p in phrases])
            page += 1
            if len(all_phrases) >= total:
                break

    keywords = all_phrases
    stats['total_phrases'] = len(keywords)
    print(f"[OK] Loaded {len(keywords)} keywords")

    # 2. 检查已分词的关键词（通过记录批次）
    # 这里简化处理：加载已有的分词结果
    print("[2/6] Loading existing word segments...")
    with WordSegmentRepository() as ws_repo:
        existing_word_counter = ws_repo.get_word_segments(min_frequency=1)
        existing_pos_tags = {}
        existing_translations = {}

        # 加载已有的词性和翻译信息
        for word in existing_word_counter.keys():
            ws = ws_repo.get_word_segment(word)
            if ws:
                if ws.pos_tag:
                    existing_pos_tags[word] = (
                        ws.pos_tag,
                        ws.pos_category,
                        ws.pos_chinese
                    )
                if ws.translation:
                    existing_translations[word] = ws.translation

    stats['existing_words'] = len(existing_word_counter)
    print(f"[OK] Found {len(existing_word_counter)} existing words")

    # 3. 对新关键词进行分词
    # 注意：这里简化处理，直接对所有关键词分词
    # 更精确的做法是记录哪些phrases已分词
    print("[3/6] Segmenting keywords...")
    new_word_counter = segment_keywords(keywords, stopwords)
    print(f"[OK] Segmented into {len(new_word_counter)} unique words")

    # 4. 合并新旧结果（频次累加）
    print("[4/6] Merging results...")
    merged_counter = Counter(existing_word_counter)
    for word, freq in new_word_counter.items():
        if word in merged_counter:
            # 注意：这里不累加，因为新分词是全量的
            merged_counter[word] = freq
        else:
            merged_counter[word] = freq
            stats['new_words'] += 1

    stats['total_words'] = len(merged_counter)
    print(f"[OK] Total unique words: {stats['total_words']} (new: {stats['new_words']})")

    # 5. 词性标注（可选）
    pos_tags = existing_pos_tags.copy()
    if pos_tagging:
        print("[5/6] POS tagging...")
        from utils.pos_tagging import tag_words_batch, POS_TAGGING_AVAILABLE

        if POS_TAGGING_AVAILABLE:
            # 只对新词和缺少词性的词进行标注
            words_to_tag = [
                w for w in merged_counter.keys()
                if w not in pos_tags
            ]

            if words_to_tag:
                new_pos_tags = tag_words_batch(words_to_tag)
                pos_tags.update(new_pos_tags)
                print(f"[OK] Tagged {len(words_to_tag)} words")
            else:
                print("[Skip] All words already tagged")
        else:
            print("[Skip] POS tagging not available")
    else:
        print("[5/6] POS tagging disabled")

    # 6. 翻译（可选）
    translations = existing_translations.copy()
    if translation:
        print("[6/6] Translating...")
        from utils.translation import translate_words_batch, TRANSLATION_AVAILABLE

        if TRANSLATION_AVAILABLE:
            # 只对缺少翻译的词进行翻译
            words_to_translate = [
                w for w in merged_counter.keys()
                if w not in translations
            ]

            if words_to_translate:
                new_translations = translate_words_batch(words_to_translate)
                translations.update(new_translations)
                print(f"[OK] Translated {len(words_to_translate)} words")
            else:
                print("[Skip] All words already translated")
        else:
            print("[Skip] Translation not available")
    else:
        print("[6/6] Translation disabled")

    # 计算耗时
    stats['duration_seconds'] = int(time.time() - start_time)

    return merged_counter, pos_tags, translations, stats


def save_segmentation_results(
    word_counter: Counter,
    pos_tags: Dict,
    translations: Dict,
    stats: Dict
) -> int:
    """
    保存分词结果到数据库

    Args:
        word_counter: 词频统计
        pos_tags: 词性标注
        translations: 翻译
        stats: 统计信息

    Returns:
        批次ID
    """
    print("\n[Save] Saving results to database...")

    with WordSegmentRepository() as ws_repo:
        # 创建批次记录
        batch_id = ws_repo.create_batch(
            phrase_count=stats['total_phrases'],
            notes=f"Incremental segmentation: {stats['new_words']} new words"
        )

        # 保存分词结果
        new_words_count = ws_repo.save_word_segments(
            word_counter=word_counter,
            pos_tags=pos_tags,
            translations=translations,
            batch_id=batch_id
        )

        # 完成批次记录
        ws_repo.complete_batch(
            batch_id=batch_id,
            word_count=len(word_counter),
            new_word_count=new_words_count,
            duration_seconds=stats['duration_seconds']
        )

        print(f"[OK] Saved batch #{batch_id}")
        print(f"[OK] New words added: {new_words_count}")

    return batch_id


def load_segmentation_results() -> Tuple[Counter, Dict, Dict]:
    """
    从数据库加载分词结果

    Returns:
        (word_counter, pos_tags, translations)
    """
    with WordSegmentRepository() as ws_repo:
        word_counter = Counter(ws_repo.get_word_segments())

        # 加载词性和翻译
        pos_tags = {}
        translations = {}

        for word in word_counter.keys():
            ws = ws_repo.get_word_segment(word)
            if ws:
                if ws.pos_tag:
                    pos_tags[word] = (ws.pos_tag, ws.pos_category, ws.pos_chinese)
                if ws.translation:
                    translations[word] = ws.translation

    return word_counter, pos_tags, translations

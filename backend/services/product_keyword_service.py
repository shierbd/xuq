"""
商品管理模块 - 簇关键词/词根提取服务
"""
import re
import math
from typing import Dict, List, Optional, Iterable, Callable
from collections import Counter
from sqlalchemy.orm import Session
from backend.models.product import Product
from backend.models.product_cluster_keyword import ProductClusterKeyword


class ProductClusterKeywordService:
    """商品簇关键词提取服务"""

    STOP_WORDS = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
        'template', 'digital', 'download', 'instant', 'editable', 'customizable',
        'printable', 'pdf', 'file', 'files', 'bundle', 'pack', 'set',
    }

    def __init__(self, db: Session):
        self.db = db

    def _normalize_token(self, token: str) -> str:
        word = token.lower()
        if len(word) <= 3:
            return word

        # basic plural normalization
        if word.endswith("ies") and len(word) > 4:
            word = word[:-3] + "y"
        elif word.endswith("sses"):
            word = word[:-2]
        elif word.endswith("es") and len(word) > 4:
            word = word[:-2]
        elif word.endswith("s") and len(word) > 3 and not word.endswith("ss"):
            word = word[:-1]

        # light stemming for common verb forms
        if word.endswith("ing") and len(word) > 5:
            base = word[:-3]
            if len(base) >= 2 and base[-1] == base[-2]:
                base = base[:-1]
            word = base
        elif word.endswith("ed") and len(word) > 4:
            word = word[:-2]

        return word

    def _iter_cluster_names(self, cluster_id: int) -> Iterable[str]:
        query = self.db.query(Product.product_name).filter(
            Product.is_deleted == False,
            Product.cluster_id == cluster_id
        ).yield_per(1000)
        for (name,) in query:
            if name:
                yield name

    def _tokenize(self, text: str, min_word_len: int = 3) -> List[str]:
        if not text:
            return []
        words = re.findall(r'\b[a-z]{3,}\b', text.lower())
        tokens: List[str] = []
        for word in words:
            normalized = self._normalize_token(word)
            if len(normalized) < min_word_len:
                continue
            if normalized in self.STOP_WORDS:
                continue
            tokens.append(normalized)
        return tokens

    def extract_keywords_for_cluster(
        self,
        cluster_id: int,
        top_n: int = 10,
        min_word_len: int = 3
    ) -> List[Dict]:
        counter = Counter()
        for name in self._iter_cluster_names(cluster_id):
            counter.update(self._tokenize(name, min_word_len=min_word_len))

        total_terms = sum(counter.values())
        keywords = []
        for word, count in counter.most_common(top_n):
            score = count / total_terms if total_terms > 0 else 0.0
            keywords.append({
                "keyword": word,
                "count": int(count),
                "score": float(score)
            })
        return keywords

    def generate_cluster_keywords(
        self,
        cluster_ids: Optional[List[int]] = None,
        top_n: int = 10,
        min_word_len: int = 3,
        overwrite: bool = True,
        method: str = "tfidf",
        progress_callback: Optional[Callable[[float, Optional[str]], None]] = None
    ) -> Dict:
        if cluster_ids is None:
            cluster_ids = [
                row[0] for row in self.db.query(Product.cluster_id).filter(
                    Product.cluster_id.isnot(None),
                    Product.cluster_id != -1,
                    Product.is_deleted == False
                ).distinct().all()
            ]

        total_clusters = len(cluster_ids)
        processed = 0
        inserted = 0
        method_normalized = (method or "tfidf").lower()
        use_tfidf = method_normalized in {"tfidf", "tf-idf"}

        df_counter = Counter()
        if use_tfidf and total_clusters > 0:
            for idx, cluster_id in enumerate(cluster_ids, start=1):
                cluster_counter = Counter()
                for name in self._iter_cluster_names(cluster_id):
                    cluster_counter.update(self._tokenize(name, min_word_len=min_word_len))
                for token in cluster_counter.keys():
                    df_counter[token] += 1
                if progress_callback:
                    progress = 5 + 35 * (idx / total_clusters)
                    progress_callback(progress, f"df pass {idx}/{total_clusters}")

        for idx, cluster_id in enumerate(cluster_ids, start=1):
            if overwrite:
                self.db.query(ProductClusterKeyword).filter(
                    ProductClusterKeyword.cluster_id == cluster_id
                ).delete()

            counter = Counter()
            for name in self._iter_cluster_names(cluster_id):
                counter.update(self._tokenize(name, min_word_len=min_word_len))

            total_terms = sum(counter.values())
            keywords: List[Dict] = []
            if total_terms > 0:
                if use_tfidf:
                    for word, count in counter.items():
                        df = df_counter.get(word, 0)
                        idf = math.log((1 + total_clusters) / (1 + df)) + 1.0
                        score = (count / total_terms) * idf
                        keywords.append({
                            "keyword": word,
                            "count": int(count),
                            "score": float(score)
                        })
                    keywords.sort(key=lambda item: item["score"], reverse=True)
                    keywords = keywords[:top_n]
                else:
                    for word, count in counter.most_common(top_n):
                        score = count / total_terms if total_terms > 0 else 0.0
                        keywords.append({
                            "keyword": word,
                            "count": int(count),
                            "score": float(score)
                        })

            for item in keywords:
                self.db.add(ProductClusterKeyword(
                    cluster_id=cluster_id,
                    keyword=item["keyword"],
                    count=item["count"],
                    score=item["score"],
                    method="tfidf" if use_tfidf else "tf"
                ))

            processed += 1
            inserted += len(keywords)

            if processed % 50 == 0:
                self.db.commit()
            if progress_callback and total_clusters > 0:
                progress = 40 + 60 * (idx / total_clusters)
                progress_callback(progress, f"keywords {idx}/{total_clusters}")

        self.db.commit()

        return {
            "total_clusters": total_clusters,
            "processed_clusters": processed,
            "inserted_keywords": inserted,
            "top_n": top_n,
            "method": "tfidf" if use_tfidf else "tf"
        }

    def get_cluster_keywords(self, cluster_id: int, limit: int = 20) -> List[Dict]:
        rows = self.db.query(ProductClusterKeyword).filter(
            ProductClusterKeyword.cluster_id == cluster_id
        ).order_by(ProductClusterKeyword.count.desc()).limit(limit).all()

        return [{
            "keyword": row.keyword,
            "count": row.count,
            "score": row.score,
            "method": row.method
        } for row in rows]

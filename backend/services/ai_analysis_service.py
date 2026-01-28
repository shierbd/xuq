"""
[REQ-011] P5.2: Top商品AI深度分析服务
对每个簇的Top商品进行AI深度分析
"""
import os
import json
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from backend.models.product import Product


class AIAnalysisService:
    """[REQ-011] Top商品AI深度分析服务"""

    def __init__(self, db: Session):
        self.db = db
        self.api_key = os.getenv('CLAUDE_API_KEY') or os.getenv('DEEPSEEK_API_KEY')
        self.use_claude = bool(os.getenv('CLAUDE_API_KEY'))

    def generate_analysis_prompt(self, products: List[Product]) -> str:
        """
        生成AI分析提示词

        Args:
            products: 商品列表

        Returns:
            str: 提示词
        """
        product_names = "\n".join([f"{i+1}. {p.product_name}" for i, p in enumerate(products)])

        prompt = f"""请分析以下数字产品，这些是同一类别中评价数最高的商品：

{product_names}

请提供以下分析（用JSON格式返回）：

1. user_need: 这些商品满足的核心用户需求（1-2句话，中文）
2. delivery_type_verified: 验证交付形式是否正确（如果当前提取的不准确，请提供正确的）
3. key_keywords: 补充关键词（提取商品名中的核心关键词，英文，最多5个）

返回格式示例：
{{
  "user_need": "帮助用户规划和管理预算，提供可视化的财务追踪工具",
  "delivery_type_verified": "Template",
  "key_keywords": ["Budget", "Finance", "Planner", "Tracker", "Money"]
}}

请只返回JSON，不要包含其他文字。"""

        return prompt

    def call_ai_api(self, prompt: str) -> Optional[Dict]:
        """
        调用AI API进行分析

        Args:
            prompt: 提示词

        Returns:
            Optional[Dict]: AI返回的分析结果
        """
        if not self.api_key:
            return None

        try:
            if self.use_claude:
                # 调用Claude API
                import anthropic
                client = anthropic.Anthropic(api_key=self.api_key)

                message = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1024,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )

                response_text = message.content[0].text
            else:
                # 调用DeepSeek API
                import requests

                response = requests.post(
                    "https://api.deepseek.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "deepseek-chat",
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": 1024
                    }
                )

                response_text = response.json()['choices'][0]['message']['content']

            # 解析JSON响应
            # 尝试提取JSON部分
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return result
            else:
                return None

        except Exception as e:
            print(f"AI API调用失败: {e}")
            return None

    def analyze_cluster_top_products(self, cluster_id: int, top_n: int = 3) -> Tuple[bool, str, Optional[Dict]]:
        """
        分析单个簇的Top商品

        Args:
            cluster_id: 簇ID
            top_n: Top商品数量

        Returns:
            Tuple[bool, str, Optional[Dict]]: (是否成功, 消息, 分析结果)
        """
        # 获取Top商品
        top_products = self.db.query(Product).filter(
            Product.cluster_id == cluster_id,
            Product.is_deleted == False
        ).order_by(desc(Product.review_count)).limit(top_n).all()

        if not top_products:
            return False, "簇中没有商品", None

        # 生成提示词
        prompt = self.generate_analysis_prompt(top_products)

        # 调用AI API
        analysis_result = self.call_ai_api(prompt)

        if not analysis_result:
            return False, "AI分析失败", None

        # 更新簇中所有商品的user_need
        if 'user_need' in analysis_result:
            self.db.query(Product).filter(
                Product.cluster_id == cluster_id
            ).update({"user_need": analysis_result['user_need']})
            self.db.commit()

        return True, "分析成功", analysis_result

    def analyze_all_clusters(self, top_n: int = 3) -> Dict[str, any]:
        """
        分析所有簇的Top商品

        Args:
            top_n: 每个簇的Top商品数量

        Returns:
            Dict: 分析结果统计
        """
        # 获取所有簇
        clusters = self.db.query(Product.cluster_id).filter(
            Product.cluster_id.isnot(None),
            Product.cluster_id != -1,  # 排除噪音点
            Product.is_deleted == False
        ).group_by(Product.cluster_id).all()

        cluster_ids = [row[0] for row in clusters]

        processed = 0
        failed = 0
        results = []

        for cluster_id in cluster_ids:
            success, message, analysis = self.analyze_cluster_top_products(cluster_id, top_n)

            if success:
                processed += 1
                results.append({
                    "cluster_id": cluster_id,
                    "analysis": analysis
                })
            else:
                failed += 1

        return {
            "total_clusters": len(cluster_ids),
            "processed": processed,
            "failed": failed,
            "results": results
        }

    def get_analysis_statistics(self) -> Dict[str, any]:
        """
        获取AI分析统计信息

        Returns:
            Dict: 统计信息
        """
        total = self.db.query(Product).filter(Product.is_deleted == False).count()

        # 统计user_need字段的填充情况
        user_need_count = self.db.query(Product).filter(
            Product.is_deleted == False,
            Product.user_need.isnot(None)
        ).count()

        # 统计各簇的分析情况
        clusters_with_analysis = self.db.query(Product.cluster_id).filter(
            Product.is_deleted == False,
            Product.cluster_id.isnot(None),
            Product.cluster_id != -1,
            Product.user_need.isnot(None)
        ).group_by(Product.cluster_id).count()

        total_clusters = self.db.query(Product.cluster_id).filter(
            Product.is_deleted == False,
            Product.cluster_id.isnot(None),
            Product.cluster_id != -1
        ).group_by(Product.cluster_id).count()

        return {
            "total_products": total,
            "user_need_filled": user_need_count,
            "user_need_rate": round(user_need_count / total * 100, 2) if total > 0 else 0,
            "clusters_analyzed": clusters_with_analysis,
            "total_clusters": total_clusters,
            "cluster_analysis_rate": round(clusters_with_analysis / total_clusters * 100, 2) if total_clusters > 0 else 0
        }

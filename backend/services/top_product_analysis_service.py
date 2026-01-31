"""
[REQ-011] P5.2: Top商品AI深度分析服务
对每个簇的Top商品进行AI深度分析
"""
import os
import json
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from backend.models.product import Product
import anthropic
import httpx

class TopProductAnalysisService:
    """[REQ-011] P5.2: Top商品AI深度分析服务"""

    def __init__(self, db: Session, ai_provider: Optional[str] = None):
        """
        初始化服务

        Args:
            db: 数据库会话
            ai_provider: AI提供商 ('claude' 或 'deepseek')，可选
        """
        self.db = db
        self.ai_provider = ai_provider

        # 只在需要AI功能时检查API密钥
        if ai_provider:
            if ai_provider == 'claude':
                self.api_key = os.getenv('CLAUDE_API_KEY')
                if not self.api_key:
                    raise ValueError("未找到 CLAUDE_API_KEY 环境变量")
            elif ai_provider == 'deepseek':
                self.api_key = os.getenv('DEEPSEEK_API_KEY') or "sk-fb8318ee2b3c45a39ba642843ed8a287"
            else:
                raise ValueError(f"不支持的AI提供商: {ai_provider}")

    def get_top_products_by_cluster(self, top_n: int = 3) -> Dict[int, List[Product]]:
        """
        获取每个簇的Top N商品（按评价数排序）

        Args:
            top_n: 每个簇取Top N个商品，默认3

        Returns:
            Dict[int, List[Product]]: {cluster_id: [top_products]}
        """
        # 获取所有有效的cluster_id（排除噪音点-1和None）
        cluster_ids = self.db.query(Product.cluster_id).filter(
            and_(
                Product.is_deleted == False,
                Product.cluster_id != None,
                Product.cluster_id != -1
            )
        ).distinct().all()

        cluster_ids = [cid[0] for cid in cluster_ids]

        result = {}
        for cluster_id in cluster_ids:
            # 获取该簇的Top N商品（按评价数降序）
            top_products = self.db.query(Product).filter(
                and_(
                    Product.cluster_id == cluster_id,
                    Product.is_deleted == False,
                    Product.review_count != None
                )
            ).order_by(Product.review_count.desc()).limit(top_n).all()

            if top_products:
                result[cluster_id] = top_products

        return result

    def analyze_product_with_ai(self, product: Product) -> Dict[str, any]:
        """
        使用AI分析单个商品

        Args:
            product: 商品对象

        Returns:
            Dict: 分析结果
                {
                    "user_need": "用户需求描述",
                    "delivery_type_verified": "验证后的交付形式",
                    "additional_keywords": ["补充关键词1", "补充关键词2"]
                }
        """
        if not self.ai_provider:
            raise ValueError("未指定AI提供商")

        # 构建分析提示词
        prompt = self._build_analysis_prompt(product)

        # 调用AI
        if self.ai_provider == 'claude':
            response = self._call_claude_api(prompt)
        elif self.ai_provider == 'deepseek':
            response = self._call_deepseek_api(prompt)
        else:
            raise ValueError(f"不支持的AI提供商: {self.ai_provider}")

        # 解析响应
        try:
            result = json.loads(response)
            return result
        except json.JSONDecodeError:
            # 如果无法解析JSON，返回原始文本
            return {
                "user_need": response,
                "delivery_type_verified": product.delivery_type,
                "additional_keywords": []
            }

    def _build_analysis_prompt(self, product: Product) -> str:
        """
        构建AI分析提示词

        Args:
            product: 商品对象

        Returns:
            str: 提示词
        """
        prompt = f"""请分析以下Etsy商品，提供深度分析：

商品名称: {product.product_name}
评分: {product.rating}
评价数: {product.review_count}
价格: ${product.price}
类别: {product.cluster_name or product.cluster_name_cn or '未知'}
当前识别的交付形式: {product.delivery_type or '未识别'}

请提供以下分析（以JSON格式返回）：

1. user_need: 这个商品满足的用户需求是什么？（用1-2句话描述）
2. delivery_type_verified: 验证交付形式是否正确（如果不正确，请提供正确的）
3. additional_keywords: 补充关键词（提取商品名称中的核心关键词，最多5个）

返回格式：
{{
    "user_need": "用户需求描述",
    "delivery_type_verified": "交付形式",
    "additional_keywords": ["关键词1", "关键词2", "关键词3"]
}}

只返回JSON，不要其他内容。"""

        return prompt

    def _call_claude_api(self, prompt: str) -> str:
        """
        调用Claude API

        Args:
            prompt: 提示词

        Returns:
            str: API响应
        """
        client = anthropic.Anthropic(api_key=self.api_key)

        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return message.content[0].text

    def _call_deepseek_api(self, prompt: str) -> str:
        """
        调用DeepSeek API

        Args:
            prompt: 提示词

        Returns:
            str: API响应
        """
        url = "https://api.deepseek.com/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1024,
            "temperature": 0.7
        }

        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']

    def analyze_top_products(
        self,
        top_n: int = 3,
        ai_provider: str = 'deepseek'
    ) -> Dict[str, any]:
        """
        批量分析所有簇的Top商品

        Args:
            top_n: 每个簇取Top N个商品
            ai_provider: AI提供商

        Returns:
            Dict: 分析结果统计
        """
        # 设置AI提供商
        self.ai_provider = ai_provider

        # 获取Top商品
        top_products_by_cluster = self.get_top_products_by_cluster(top_n)

        total_clusters = len(top_products_by_cluster)
        total_products = sum(len(products) for products in top_products_by_cluster.values())
        analyzed_count = 0
        error_count = 0

        print(f"开始分析Top商品...")
        print(f"总簇数: {total_clusters}")
        print(f"总商品数: {total_products}")
        print(f"AI提供商: {ai_provider}")
        print()

        # 逐个分析
        for cluster_id, products in top_products_by_cluster.items():
            print(f"处理簇 {cluster_id} ({len(products)}个商品)...")

            # 分析该簇的Top商品
            cluster_analysis = None
            for product in products:
                try:
                    # 调用AI分析
                    analysis = self.analyze_product_with_ai(product)

                    # 更新商品的user_need
                    product.user_need = analysis.get('user_need', '')

                    # 验证交付形式
                    verified_delivery = analysis.get('delivery_type_verified')
                    if verified_delivery and verified_delivery != product.delivery_type:
                        product.delivery_type = verified_delivery

                    # 保存第一个成功分析的结果，用于继承
                    if not cluster_analysis:
                        cluster_analysis = analysis.get('user_need', '')

                    analyzed_count += 1
                    print(f"  [OK] 商品 {product.product_id}: {product.product_name[:50]}...")

                except Exception as e:
                    error_count += 1
                    print(f"  [FAIL] 商品 {product.product_id} 分析失败: {str(e)}")

            # 让该簇的其他商品继承分析结果
            if cluster_analysis:
                self._inherit_cluster_analysis(cluster_id, cluster_analysis)

            # 提交当前簇的更改
            self.db.commit()

        return {
            "total_clusters": total_clusters,
            "total_top_products": total_products,
            "analyzed_count": analyzed_count,
            "error_count": error_count,
            "success_rate": f"{analyzed_count / total_products * 100:.2f}%" if total_products > 0 else "0%"
        }

    def _inherit_cluster_analysis(self, cluster_id: int, user_need: str):
        """
        让簇内其他商品继承Top商品的分析结果

        Args:
            cluster_id: 簇ID
            user_need: 用户需求描述
        """
        # 更新该簇中所有没有user_need的商品
        self.db.query(Product).filter(
            and_(
                Product.cluster_id == cluster_id,
                Product.is_deleted == False,
                Product.user_need == None
            )
        ).update({"user_need": user_need}, synchronize_session=False)

    def get_analysis_statistics(self) -> Dict[str, any]:
        """
        获取分析统计信息

        Returns:
            Dict: 统计信息
        """
        # 总商品数
        total_products = self.db.query(func.count(Product.product_id)).filter(
            Product.is_deleted == False
        ).scalar()

        # 已分析商品数（有user_need的）
        analyzed_products = self.db.query(func.count(Product.product_id)).filter(
            and_(
                Product.is_deleted == False,
                Product.user_need != None,
                Product.user_need != ''
            )
        ).scalar()

        # 未分析商品数
        unanalyzed_products = total_products - analyzed_products

        # 分析覆盖率
        coverage_rate = (analyzed_products / total_products * 100) if total_products > 0 else 0

        return {
            "total_products": total_products,
            "analyzed_products": analyzed_products,
            "unanalyzed_products": unanalyzed_products,
            "coverage_rate": f"{coverage_rate:.2f}%"
        }

    def analyze_single_cluster(
        self,
        cluster_id: int,
        top_n: int = 3,
        ai_provider: str = 'deepseek'
    ) -> Dict[str, any]:
        """
        分析单个簇的Top商品

        Args:
            cluster_id: 簇ID
            top_n: Top N个商品
            ai_provider: AI提供商

        Returns:
            Dict: 分析结果
        """
        # 设置AI提供商
        self.ai_provider = ai_provider

        # 获取该簇的Top商品
        top_products = self.db.query(Product).filter(
            and_(
                Product.cluster_id == cluster_id,
                Product.is_deleted == False,
                Product.review_count != None
            )
        ).order_by(Product.review_count.desc()).limit(top_n).all()

        if not top_products:
            return {
                "cluster_id": cluster_id,
                "message": "该簇没有商品或商品没有评价数",
                "analyzed_count": 0
            }

        analyzed_count = 0
        error_count = 0
        cluster_analysis = None

        print(f"分析簇 {cluster_id} 的Top {top_n}商品...")

        for product in top_products:
            try:
                # 调用AI分析
                analysis = self.analyze_product_with_ai(product)

                # 更新商品的user_need
                product.user_need = analysis.get('user_need', '')

                # 验证交付形式
                verified_delivery = analysis.get('delivery_type_verified')
                if verified_delivery and verified_delivery != product.delivery_type:
                    product.delivery_type = verified_delivery

                # 保存第一个成功分析的结果
                if not cluster_analysis:
                    cluster_analysis = analysis.get('user_need', '')

                analyzed_count += 1
                print(f"  [OK] 商品 {product.product_id}: {product.product_name[:50]}...")

            except Exception as e:
                error_count += 1
                print(f"  [FAIL] 商品 {product.product_id} 分析失败: {str(e)}")

        # 让该簇的其他商品继承分析结果
        if cluster_analysis:
            self._inherit_cluster_analysis(cluster_id, cluster_analysis)

        # 提交更改
        self.db.commit()

        return {
            "cluster_id": cluster_id,
            "total_top_products": len(top_products),
            "analyzed_count": analyzed_count,
            "error_count": error_count,
            "cluster_analysis": cluster_analysis
        }

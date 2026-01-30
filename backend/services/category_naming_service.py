"""
[REQ-008] P4.1: 类别名称生成服务
使用 AI 为聚类簇生成可读的类别名称
"""
import os
import json
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.models.product import Product
import httpx


class CategoryNamingService:
    """类别名称生成服务"""

    def __init__(self, db: Session, ai_provider: str = "deepseek", use_unified_api: bool = False):
        """
        初始化服务

        Args:
            db: 数据库会话
            ai_provider: AI 提供商 ("deepseek" 或 "claude")，仅在use_unified_api=False时使用
            use_unified_api: 是否使用统一AI调用接口（推荐）
        """
        self.db = db
        self.use_unified_api = use_unified_api

        if use_unified_api:
            # 使用统一AI调用接口
            from backend.services.ai_call_service import AICallService
            self.ai_call_service = AICallService(db)
        else:
            # 使用旧的直接调用方式（向后兼容）
            self.ai_provider = ai_provider.lower()

            # 获取 API 密钥
            if self.ai_provider == "deepseek":
                self.api_key = os.getenv("DEEPSEEK_API_KEY")
                self.api_url = "https://api.deepseek.com/v1/chat/completions"
                self.model = "deepseek-chat"
            elif self.ai_provider == "claude":
                self.api_key = os.getenv("CLAUDE_API_KEY")
                self.api_url = "https://api.anthropic.com/v1/messages"
                self.model = "claude-3-haiku-20240307"
            else:
                raise ValueError(f"不支持的 AI 提供商: {ai_provider}")

            if not self.api_key:
                raise ValueError(f"未找到 {ai_provider.upper()}_API_KEY 环境变量")

    def get_top_products_by_cluster(
        self,
        cluster_id: int,
        limit: int = 5
    ) -> List[str]:
        """
        获取簇内 Top N 商品名称

        Args:
            cluster_id: 簇ID
            limit: 返回商品数量

        Returns:
            商品名称列表
        """
        products = self.db.query(Product).filter(
            Product.cluster_id == cluster_id,
            Product.is_deleted == False
        ).order_by(
            Product.review_count.desc()
        ).limit(limit).all()

        return [p.product_name for p in products]

    def build_prompt(self, product_names: List[str]) -> str:
        """
        构建 AI Prompt

        Args:
            product_names: 商品名称列表

        Returns:
            Prompt 字符串
        """
        products_text = "\n".join([f"{i+1}. {name}" for i, name in enumerate(product_names)])

        prompt = f"""分析以下 Etsy 商品名称，生成一个简洁的类别名称。

商品列表：
{products_text}

要求：
1. 类别名称使用英文
2. 2-4个单词
3. 使用 Title Case（每个单词首字母大写）
4. 准确反映商品的共同特征
5. 只返回类别名称，不要任何解释

示例格式：
- Budget Planning Template
- Wedding Checklist Printable
- Meal Prep Tracker

类别名称："""

        return prompt

    async def call_deepseek_api(self, prompt: str) -> str:
        """
        调用 DeepSeek API

        Args:
            prompt: 提示词

        Returns:
            生成的类别名称
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": 50
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.api_url,
                headers=headers,
                json=payload
            )

            if response.status_code != 200:
                raise Exception(f"DeepSeek API 调用失败: {response.status_code} - {response.text}")

            result = response.json()
            category_name = result["choices"][0]["message"]["content"].strip()

            # 清理可能的多余文本
            category_name = category_name.replace("类别名称：", "").strip()
            category_name = category_name.replace("Category Name:", "").strip()

            return category_name

    async def call_claude_api(self, prompt: str) -> str:
        """
        调用 Claude API

        Args:
            prompt: 提示词

        Returns:
            生成的类别名称
        """
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        payload = {
            "model": self.model,
            "max_tokens": 50,
            "temperature": 0.3,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.api_url,
                headers=headers,
                json=payload
            )

            if response.status_code != 200:
                raise Exception(f"Claude API 调用失败: {response.status_code} - {response.text}")

            result = response.json()
            category_name = result["content"][0]["text"].strip()

            # 清理可能的多余文本
            category_name = category_name.replace("类别名称：", "").strip()
            category_name = category_name.replace("Category Name:", "").strip()

            return category_name

    async def generate_category_name(
        self,
        cluster_id: int,
        top_n: int = 5
    ) -> Dict:
        """
        为单个簇生成类别名称

        Args:
            cluster_id: 簇ID
            top_n: 使用 Top N 商品

        Returns:
            生成结果
        """
        # 1. 获取 Top N 商品
        product_names = self.get_top_products_by_cluster(cluster_id, top_n)

        if not product_names:
            return {
                "success": False,
                "cluster_id": cluster_id,
                "error": "簇内没有商品"
            }

        # 2. 构建 Prompt
        prompt = self.build_prompt(product_names)

        # 3. 调用 AI API
        try:
            if self.use_unified_api:
                # 使用统一AI调用接口
                result = await self.ai_call_service.call_by_scenario(
                    scenario_name="类别名称生成",
                    prompt=prompt,
                    temperature=0.3,
                    max_tokens=50
                )
                category_name = result["content"].strip()

                # 清理可能的多余文本
                category_name = category_name.replace("类别名称：", "").strip()
                category_name = category_name.replace("Category Name:", "").strip()
            else:
                # 使用旧的直接调用方式（向后兼容）
                if self.ai_provider == "deepseek":
                    category_name = await self.call_deepseek_api(prompt)
                else:
                    category_name = await self.call_claude_api(prompt)

            # 4. 更新数据库
            self.db.query(Product).filter(
                Product.cluster_id == cluster_id
            ).update({
                "cluster_name": category_name
            })
            self.db.commit()

            return {
                "success": True,
                "cluster_id": cluster_id,
                "category_name": category_name,
                "top_products": product_names
            }

        except Exception as e:
            return {
                "success": False,
                "cluster_id": cluster_id,
                "error": str(e)
            }

    async def generate_all_category_names(
        self,
        cluster_ids: Optional[List[int]] = None,
        top_n: int = 5,
        batch_size: int = 10
    ) -> Dict:
        """
        批量生成类别名称

        Args:
            cluster_ids: 簇ID列表（None 表示处理所有簇）
            top_n: 使用 Top N 商品
            batch_size: 批次大小（用于进度显示）

        Returns:
            批量生成结果
        """
        # 1. 获取所有簇ID
        if cluster_ids is None:
            cluster_ids = [
                row[0] for row in self.db.query(Product.cluster_id).filter(
                    Product.cluster_id != -1,
                    Product.is_deleted == False
                ).distinct().all()
            ]

        total_clusters = len(cluster_ids)
        results = []
        success_count = 0
        failed_count = 0

        print(f"开始生成类别名称...")
        print(f"总簇数: {total_clusters}")
        print(f"AI 提供商: {self.ai_provider}")
        print()

        # 2. 逐个处理
        for i, cluster_id in enumerate(cluster_ids, 1):
            print(f"进度: {i}/{total_clusters} ({i/total_clusters*100:.1f}%) - 簇ID: {cluster_id}")

            result = await self.generate_category_name(cluster_id, top_n)
            results.append(result)

            if result["success"]:
                success_count += 1
                print(f"  [OK] Success: {result['category_name']}")
            else:
                failed_count += 1
                print(f"  [FAIL] Failed: {result['error']}")

            print()

        # 3. 返回汇总结果
        return {
            "success": True,
            "total_clusters": total_clusters,
            "processed": len(results),
            "success_count": success_count,
            "failed_count": failed_count,
            "results": results
        }

    def get_cluster_statistics(self) -> Dict:
        """
        获取簇统计信息

        Returns:
            统计信息
        """
        # 总簇数（不包括噪音点）
        total_clusters = self.db.query(func.count(func.distinct(Product.cluster_id))).filter(
            Product.cluster_id != -1,
            Product.is_deleted == False
        ).scalar()

        # 已命名簇数
        named_clusters = self.db.query(func.count(func.distinct(Product.cluster_id))).filter(
            Product.cluster_id != -1,
            Product.cluster_name.isnot(None),
            Product.cluster_name != "",
            Product.is_deleted == False
        ).scalar()

        # 未命名簇数
        unnamed_clusters = total_clusters - named_clusters

        return {
            "total_clusters": total_clusters,
            "named_clusters": named_clusters,
            "unnamed_clusters": unnamed_clusters,
            "naming_rate": named_clusters / total_clusters * 100 if total_clusters > 0 else 0
        }

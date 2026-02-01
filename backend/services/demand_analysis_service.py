"""
[REQ-004] P3.1: 需求分析服务
使用 AI 分析每个簇的商品，识别满足的用户需求
"""
import os
import json
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.models.product import Product
import httpx


class DemandAnalysisService:
    """需求分析服务"""

    def __init__(self, db: Session, ai_provider: Optional[str] = None):
        """
        初始化服务

        Args:
            db: 数据库会话
            ai_provider: AI 提供商 ("deepseek" 或 "claude")，如果不使用 AI 功能可以不传
        """
        self.db = db
        self.ai_provider = ai_provider.lower() if ai_provider else None

        # 获取 API 密钥（可选，只在使用 AI 时需要）
        self.api_key = None
        self.api_url = None
        self.model = None

        # 只有指定了 AI provider 才初始化 API 配置
        if self.ai_provider == "deepseek":
            self.api_key = os.getenv("DEEPSEEK_API_KEY") or "sk-fb8318ee2b3c45a39ba642843ed8a287"
            self.api_url = "https://api.deepseek.com/v1/chat/completions"
            self.model = "deepseek-chat"
        elif self.ai_provider == "claude":
            self.api_key = os.getenv("CLAUDE_API_KEY")
            self.api_url = "https://api.anthropic.com/v1/messages"
            self.model = "claude-3-haiku-20240307"
        elif self.ai_provider is not None:
            raise ValueError(f"不支持的 AI 提供商: {ai_provider}")

    def get_cluster_products(
        self,
        cluster_id: int,
        limit: int = 10
    ) -> List[Dict]:
        """
        获取簇内商品信息

        Args:
            cluster_id: 簇ID
            limit: 返回商品数量

        Returns:
            商品信息列表
        """
        products = self.db.query(Product).filter(
            Product.cluster_id == cluster_id,
            Product.is_deleted == False
        ).order_by(
            Product.review_count.desc()
        ).limit(limit).all()

        return [{
            "product_id": p.product_id,
            "product_name": p.product_name,
            "review_count": p.review_count,
            "rating": p.rating,
            "price": p.price
        } for p in products]

    def build_demand_analysis_prompt(
        self,
        products: List[Dict],
        cluster_name: str = None
    ) -> str:
        """
        构建需求分析 Prompt

        Args:
            products: 商品信息列表
            cluster_name: 类别名称（可选）

        Returns:
            Prompt 字符串
        """
        products_text = "\n".join([
            f"{i+1}. {p['product_name']} (评价数: {p['review_count']}, 评分: {p['rating']})"
            for i, p in enumerate(products)
        ])

        cluster_info = f"类别: {cluster_name}\n" if cluster_name else ""

        prompt = f"""分析以下 Etsy 商品，识别这些商品满足的用户需求。

{cluster_info}商品列表：
{products_text}

请从以下维度分析用户需求：

1. **核心需求** (Core Need)
   - 用户想要解决什么问题？
   - 用户的主要痛点是什么？

2. **目标用户** (Target Users)
   - 谁会购买这些商品？
   - 用户的特征是什么？

3. **使用场景** (Use Cases)
   - 在什么情况下使用？
   - 典型的使用场景有哪些？

4. **价值主张** (Value Proposition)
   - 这些商品提供什么价值？
   - 为什么用户愿意付费？

请以 JSON 格式返回分析结果：
{{
  "core_need": "核心需求描述（英文，1-2句话）",
  "target_users": "目标用户描述（英文，1-2句话）",
  "use_cases": ["使用场景1", "使用场景2", "使用场景3"],
  "value_proposition": "价值主张描述（英文，1-2句话）",
  "summary": "需求总结（英文，1句话）"
}}

只返回 JSON，不要任何其他文本。"""

        return prompt

    async def call_deepseek_api(self, prompt: str) -> Dict:
        """
        调用 DeepSeek API

        Args:
            prompt: 提示词

        Returns:
            分析结果（JSON）
        """
        # 检查 API key
        if not self.api_key:
            raise ValueError(f"未找到 {self.ai_provider.upper()}_API_KEY 环境变量，无法使用 AI 分析功能")

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
            "temperature": 0.5,
            "max_tokens": 500
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self.api_url,
                headers=headers,
                json=payload
            )

            if response.status_code != 200:
                raise Exception(f"DeepSeek API 调用失败: {response.status_code} - {response.text}")

            result = response.json()
            content = result["choices"][0]["message"]["content"].strip()

            # 尝试解析 JSON
            try:
                # 移除可能的 markdown 代码块标记
                if content.startswith("```json"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()

                analysis_result = json.loads(content)
                return analysis_result
            except json.JSONDecodeError as e:
                raise Exception(f"无法解析 AI 返回的 JSON: {e}\n原始内容: {content}")

    async def call_claude_api(self, prompt: str) -> Dict:
        """
        调用 Claude API

        Args:
            prompt: 提示词

        Returns:
            分析结果（JSON）
        """
        # 检查 API key
        if not self.api_key:
            raise ValueError(f"未找到 {self.ai_provider.upper()}_API_KEY 环境变量，无法使用 AI 分析功能")

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        payload = {
            "model": self.model,
            "max_tokens": 500,
            "temperature": 0.5,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self.api_url,
                headers=headers,
                json=payload
            )

            if response.status_code != 200:
                raise Exception(f"Claude API 调用失败: {response.status_code} - {response.text}")

            result = response.json()
            content = result["content"][0]["text"].strip()

            # 尝试解析 JSON
            try:
                # 移除可能的 markdown 代码块标记
                if content.startswith("```json"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()

                analysis_result = json.loads(content)
                return analysis_result
            except json.JSONDecodeError as e:
                raise Exception(f"无法解析 AI 返回的 JSON: {e}\n原始内容: {content}")

    async def analyze_cluster_demand(
        self,
        cluster_id: int,
        top_n: int = 10
    ) -> Dict:
        """
        分析单个簇的用户需求

        Args:
            cluster_id: 簇ID
            top_n: 使用 Top N 商品

        Returns:
            分析结果
        """
        # 1. 获取簇内商品
        products = self.get_cluster_products(cluster_id, top_n)

        if not products:
            return {
                "success": False,
                "cluster_id": cluster_id,
                "error": "簇内没有商品"
            }

        # 2. 获取类别名称
        cluster_name = self.db.query(Product.cluster_name).filter(
            Product.cluster_id == cluster_id,
            Product.cluster_name.isnot(None)
        ).first()
        cluster_name = cluster_name[0] if cluster_name else None

        # 3. 构建 Prompt
        prompt = self.build_demand_analysis_prompt(products, cluster_name)

        # 4. 调用 AI API
        try:
            if self.ai_provider == "deepseek":
                analysis = await self.call_deepseek_api(prompt)
            else:
                analysis = await self.call_claude_api(prompt)

            # 5. 更新数据库（将需求总结保存到 user_need 字段）
            user_need = analysis.get("summary", "")
            if user_need:
                self.db.query(Product).filter(
                    Product.cluster_id == cluster_id
                ).update({
                    "user_need": user_need
                })
                self.db.commit()

            return {
                "success": True,
                "cluster_id": cluster_id,
                "cluster_name": cluster_name,
                "analysis": analysis,
                "product_count": len(products)
            }

        except Exception as e:
            return {
                "success": False,
                "cluster_id": cluster_id,
                "error": str(e)
            }

    async def analyze_all_clusters(
        self,
        cluster_ids: Optional[List[int]] = None,
        top_n: int = 10,
        batch_size: int = 5,
        max_clusters: Optional[int] = None,
        skip_analyzed: bool = True,
        force_reanalyze: bool = False
    ) -> Dict:
        """
        批量分析所有簇的用户需求

        Args:
            cluster_ids: 簇ID列表（None 表示处理所有簇）
            top_n: 使用 Top N 商品
            batch_size: 批次大小（用于进度显示）
            max_clusters: 最多分析的簇数量（None 表示不限制）
            skip_analyzed: 是否跳过已分析的簇（默认 True）
            force_reanalyze: 是否强制重新分析已分析的簇（默认 False）

        Returns:
            批量分析结果
        """
        # 调试日志：打印接收到的参数
        print(f"[DEBUG] Service received parameters:")
        print(f"  - max_clusters: {max_clusters} (type: {type(max_clusters)})")
        print(f"  - skip_analyzed: {skip_analyzed}")
        print(f"  - force_reanalyze: {force_reanalyze}")

        # 1. 获取所有簇ID（排除噪音点和未聚类商品）
        if cluster_ids is None:
            # 构建基础查询
            query = self.db.query(Product.cluster_id).filter(
                Product.cluster_id > 0,  # 只处理有效簇（cluster_id > 0）
                Product.is_deleted == False
            )

            # 根据参数决定是否过滤已分析的簇
            if force_reanalyze:
                # 强制重新分析：只选择已分析的簇
                query = query.filter(
                    Product.user_need.isnot(None),
                    Product.user_need != ""
                )
            elif skip_analyzed:
                # 跳过已分析：只选择未分析的簇
                query = query.filter(
                    (Product.user_need.is_(None)) | (Product.user_need == "")
                )
            # 如果两个参数都是 False，则不过滤，处理所有簇

            cluster_ids = [row[0] for row in query.distinct().all()]
            print(f"[DEBUG] Before limiting: {len(cluster_ids)} clusters")

            # 限制分析数量
            if max_clusters is not None and max_clusters > 0:
                print(f"[DEBUG] Limiting to {max_clusters} clusters")
                cluster_ids = cluster_ids[:max_clusters]
                print(f"[DEBUG] After limiting: {len(cluster_ids)} clusters")
            else:
                print(f"[DEBUG] No limit applied (max_clusters={max_clusters})")

        total_clusters = len(cluster_ids)
        results = []
        success_count = 0
        failed_count = 0

        print(f"Starting demand analysis...")
        print(f"Total clusters: {total_clusters}")
        print(f"AI provider: {self.ai_provider}")
        print()

        # 2. 逐个处理
        for i, cluster_id in enumerate(cluster_ids, 1):
            print(f"Progress: {i}/{total_clusters} ({i/total_clusters*100:.1f}%) - Cluster ID: {cluster_id}")

            result = await self.analyze_cluster_demand(cluster_id, top_n)
            results.append(result)

            if result["success"]:
                success_count += 1
                summary = result["analysis"].get("summary", "N/A")
                print(f"  [OK] Success: {summary}")
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

    def get_analysis_statistics(self) -> Dict:
        """
        获取需求分析统计信息

        Returns:
            统计信息
        """
        # 总簇数（只统计有效簇，cluster_id > 0）
        total_clusters = self.db.query(func.count(func.distinct(Product.cluster_id))).filter(
            Product.cluster_id > 0,  # 只统计有效簇
            Product.is_deleted == False
        ).scalar()

        # 已分析簇数
        analyzed_clusters = self.db.query(func.count(func.distinct(Product.cluster_id))).filter(
            Product.cluster_id > 0,  # 只统计有效簇
            Product.user_need.isnot(None),
            Product.user_need != "",
            Product.is_deleted == False
        ).scalar()

        # 未分析簇数
        unanalyzed_clusters = total_clusters - analyzed_clusters

        return {
            "total_clusters": total_clusters,
            "analyzed_clusters": analyzed_clusters,
            "unanalyzed_clusters": unanalyzed_clusters,
            "analysis_rate": analyzed_clusters / total_clusters * 100 if total_clusters > 0 else 0
        }

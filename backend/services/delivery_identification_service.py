"""
[REQ-005] P3.2: 交付产品识别服务
从商品名称中自动识别交付产品的类型、格式和平台
"""
import os
import json
import re
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.models.product import Product
import httpx


class DeliveryIdentificationService:
    """交付产品识别服务"""

    # 关键词规则库
    DELIVERY_KEYWORDS = {
        "template": "Template",
        "planner": "Planner",
        "tracker": "Tracker",
        "worksheet": "Worksheet",
        "printable": "Printable",
        "bundle": "Bundle",
        "kit": "Kit",
        "guide": "Guide",
        "checklist": "Checklist",
        "calendar": "Calendar",
        "organizer": "Organizer",
        "journal": "Journal",
        "notebook": "Notebook",
        "workbook": "Workbook",
        "spreadsheet": "Spreadsheet",
    }

    # 平台规则
    PLATFORM_KEYWORDS = {
        "notion": "Notion Template",
        "canva": "Canva Template",
        "excel": "Excel Template",
        "google sheets": "Google Sheets Template",
        "google sheet": "Google Sheets Template",
        "airtable": "Airtable Template",
        "trello": "Trello Template",
        "asana": "Asana Template",
        "clickup": "ClickUp Template",
        "monday": "Monday.com Template",
    }

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
            self.api_key = os.getenv("DEEPSEEK_API_KEY")
            self.api_url = "https://api.deepseek.com/v1/chat/completions"
            self.model = "deepseek-chat"
        elif self.ai_provider == "claude":
            self.api_key = os.getenv("CLAUDE_API_KEY")
            self.api_url = "https://api.anthropic.com/v1/messages"
            self.model = "claude-3-haiku-20240307"
        elif self.ai_provider is not None:
            raise ValueError(f"不支持的 AI 提供商: {ai_provider}")

    def identify_by_rules(self, product_name: str) -> Optional[str]:
        """
        使用关键词规则识别交付形式

        Args:
            product_name: 商品名称

        Returns:
            交付形式，如果无法识别则返回 None
        """
        product_name_lower = product_name.lower()

        # 1. 优先检查平台关键词
        for keyword, delivery_type in self.PLATFORM_KEYWORDS.items():
            if keyword in product_name_lower:
                return delivery_type

        # 2. 检查交付类型关键词
        for keyword, delivery_type in self.DELIVERY_KEYWORDS.items():
            if keyword in product_name_lower:
                return delivery_type

        return None

    def build_identification_prompt(self, product_name: str) -> str:
        """
        构建交付产品识别 Prompt

        Args:
            product_name: 商品名称

        Returns:
            Prompt 字符串
        """
        prompt = f"""分析以下 Etsy 商品名称，识别交付产品的类型。

商品名称: {product_name}

请识别以下信息：
1. **交付类型** (Delivery Type): 这是什么类型的产品？
   - 例如: Template, Planner, Tracker, Worksheet, Printable, Bundle, Kit, Guide, Checklist, Calendar 等

2. **平台** (Platform): 如果是特定平台的模板，是哪个平台？
   - 例如: Notion, Canva, Excel, Google Sheets, Airtable 等
   - 如果不是特定平台的模板，返回 "General"

3. **完整描述** (Full Description): 用简短的英文描述交付形式
   - 例如: "Notion Template", "Excel Planner", "Printable Checklist"

请以 JSON 格式返回结果：
{{
  "delivery_type": "交付类型（英文）",
  "platform": "平台名称（英文，如果没有则为 General）",
  "full_description": "完整描述（英文）"
}}

只返回 JSON，不要任何其他文本。"""

        return prompt

    async def call_deepseek_api(self, prompt: str) -> Dict:
        """
        调用 DeepSeek API

        Args:
            prompt: 提示词

        Returns:
            识别结果（JSON）
        """
        # 检查 API key
        if not self.api_key:
            raise ValueError(f"未找到 {self.ai_provider.upper()}_API_KEY 环境变量，无法使用 AI 识别功能")

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
            "max_tokens": 200
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

                identification_result = json.loads(content)
                return identification_result
            except json.JSONDecodeError as e:
                raise Exception(f"无法解析 AI 返回的 JSON: {e}\n原始内容: {content}")

    async def call_claude_api(self, prompt: str) -> Dict:
        """
        调用 Claude API

        Args:
            prompt: 提示词

        Returns:
            识别结果（JSON）
        """
        # 检查 API key
        if not self.api_key:
            raise ValueError(f"未找到 {self.ai_provider.upper()}_API_KEY 环境变量，无法使用 AI 识别功能")

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        payload = {
            "model": self.model,
            "max_tokens": 200,
            "temperature": 0.3,
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

                identification_result = json.loads(content)
                return identification_result
            except json.JSONDecodeError as e:
                raise Exception(f"无法解析 AI 返回的 JSON: {e}\n原始内容: {content}")

    async def identify_product(
        self,
        product_id: int,
        use_ai: bool = False
    ) -> Dict:
        """
        识别单个商品的交付形式

        Args:
            product_id: 商品ID
            use_ai: 是否使用 AI（如果规则无法识别）

        Returns:
            识别结果
        """
        # 1. 获取商品信息
        product = self.db.query(Product).filter(
            Product.product_id == product_id,
            Product.is_deleted == False
        ).first()

        if not product:
            return {
                "success": False,
                "product_id": product_id,
                "error": "商品不存在"
            }

        # 2. 先尝试使用规则识别
        delivery_type = self.identify_by_rules(product.product_name)

        if delivery_type:
            # 规则识别成功
            product.delivery_type = delivery_type
            self.db.commit()

            return {
                "success": True,
                "product_id": product_id,
                "product_name": product.product_name,
                "delivery_type": delivery_type,
                "method": "rule"
            }

        # 3. 如果规则无法识别且允许使用 AI
        if use_ai:
            try:
                # 构建 Prompt
                prompt = self.build_identification_prompt(product.product_name)

                # 调用 AI API
                if self.ai_provider == "deepseek":
                    identification = await self.call_deepseek_api(prompt)
                else:
                    identification = await self.call_claude_api(prompt)

                # 更新数据库
                delivery_type = identification.get("full_description", identification.get("delivery_type", "Unknown"))
                product.delivery_type = delivery_type
                self.db.commit()

                return {
                    "success": True,
                    "product_id": product_id,
                    "product_name": product.product_name,
                    "delivery_type": delivery_type,
                    "method": "ai",
                    "details": identification
                }

            except Exception as e:
                return {
                    "success": False,
                    "product_id": product_id,
                    "error": str(e),
                    "method": "ai"
                }

        # 4. 规则无法识别且不使用 AI
        return {
            "success": False,
            "product_id": product_id,
            "product_name": product.product_name,
            "error": "无法识别交付形式",
            "method": "rule"
        }

    async def identify_all_products(
        self,
        product_ids: Optional[List[int]] = None,
        use_ai_for_unmatched: bool = False,
        batch_size: int = 100
    ) -> Dict:
        """
        批量识别所有商品的交付形式

        Args:
            product_ids: 商品ID列表（None 表示处理所有商品）
            use_ai_for_unmatched: 对规则无法识别的商品使用 AI
            batch_size: 批次大小（用于进度显示）

        Returns:
            批量识别结果
        """
        # 1. 获取所有商品ID
        if product_ids is None:
            product_ids = [
                row[0] for row in self.db.query(Product.product_id).filter(
                    Product.is_deleted == False
                ).all()
            ]

        total_products = len(product_ids)
        results = []
        rule_matched = 0
        ai_matched = 0
        unmatched = 0

        print(f"开始交付产品识别...")
        print(f"总商品数: {total_products}")
        print(f"使用 AI 兜底: {'是' if use_ai_for_unmatched else '否'}")
        print()

        # 2. 逐个处理
        for i, product_id in enumerate(product_ids, 1):
            if i % batch_size == 0 or i == total_products:
                print(f"进度: {i}/{total_products} ({i/total_products*100:.1f}%)")

            result = await self.identify_product(product_id, use_ai=use_ai_for_unmatched)
            results.append(result)

            if result["success"]:
                if result.get("method") == "rule":
                    rule_matched += 1
                elif result.get("method") == "ai":
                    ai_matched += 1
            else:
                unmatched += 1

        # 3. 返回汇总结果
        return {
            "success": True,
            "total_products": total_products,
            "processed": len(results),
            "rule_matched": rule_matched,
            "ai_matched": ai_matched,
            "unmatched": unmatched,
            "match_rate": (rule_matched + ai_matched) / total_products * 100 if total_products > 0 else 0,
            "results": results
        }

    def get_identification_statistics(self) -> Dict:
        """
        获取交付产品识别统计信息

        Returns:
            统计信息
        """
        # 总商品数
        total_products = self.db.query(func.count(Product.product_id)).filter(
            Product.is_deleted == False
        ).scalar()

        # 已识别商品数
        identified_products = self.db.query(func.count(Product.product_id)).filter(
            Product.delivery_type.isnot(None),
            Product.delivery_type != "",
            Product.is_deleted == False
        ).scalar()

        # 未识别商品数
        unidentified_products = total_products - identified_products

        # 交付类型分布
        delivery_type_distribution = self.db.query(
            Product.delivery_type,
            func.count(Product.product_id).label('count')
        ).filter(
            Product.delivery_type.isnot(None),
            Product.delivery_type != "",
            Product.is_deleted == False
        ).group_by(Product.delivery_type).all()

        return {
            "total_products": total_products,
            "identified_products": identified_products,
            "unidentified_products": unidentified_products,
            "identification_rate": identified_products / total_products * 100 if total_products > 0 else 0,
            "delivery_type_distribution": [
                {"delivery_type": dt, "count": count}
                for dt, count in delivery_type_distribution
            ]
        }

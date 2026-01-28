"""
[REQ-010] P5.1: 商品属性提取服务
使用代码规则从商品名称中提取交付形式和关键词
[REQ-012] P5.3: AI辅助兜底
对代码规则无法提取的商品使用AI补充
"""
import os
import re
import json
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from backend.models.product import Product


class AttributeExtractionService:
    """[REQ-010] 商品属性提取服务"""

    # 交付形式关键词规则库
    DELIVERY_TYPE_RULES = {
        'template': 'Template',
        'planner': 'Planner',
        'tracker': 'Tracker',
        'worksheet': 'Worksheet',
        'printable': 'Printable',
        'bundle': 'Bundle',
        'kit': 'Kit',
        'guide': 'Guide',
        'checklist': 'Checklist',
        'calendar': 'Calendar',
        'ebook': 'Ebook',
        'workbook': 'Workbook',
        'journal': 'Journal',
        'organizer': 'Organizer',
        'spreadsheet': 'Spreadsheet',
    }

    # 平台规则
    PLATFORM_RULES = {
        'notion': 'Notion Template',
        'canva': 'Canva Template',
        'excel': 'Excel Template',
        'google sheets': 'Google Sheets Template',
        'google sheet': 'Google Sheets Template',
        'powerpoint': 'PowerPoint Template',
        'word': 'Word Template',
        'pdf': 'PDF',
        'figma': 'Figma Template',
        'trello': 'Trello Template',
        'airtable': 'Airtable Template',
    }

    # 停用词列表（用于关键词提取）
    STOP_WORDS = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
        'template', 'digital', 'download', 'instant', 'editable', 'customizable',
        'printable', 'pdf', 'file', 'files', 'bundle', 'pack', 'set',
    }

    def __init__(self, db: Session):
        self.db = db
        # [REQ-012] P5.3: AI API配置
        self.api_key = os.getenv('CLAUDE_API_KEY') or os.getenv('DEEPSEEK_API_KEY')
        self.use_claude = bool(os.getenv('CLAUDE_API_KEY'))

    def extract_delivery_type(self, product_name: str) -> Optional[str]:
        """
        从商品名称中提取交付形式

        Args:
            product_name: 商品名称

        Returns:
            Optional[str]: 交付形式，如果未找到则返回None
        """
        if not product_name:
            return None

        product_name_lower = product_name.lower()

        # 优先检查平台规则（更具体）
        for keyword, delivery_type in self.PLATFORM_RULES.items():
            if keyword in product_name_lower:
                return delivery_type

        # 检查交付形式规则
        for keyword, delivery_type in self.DELIVERY_TYPE_RULES.items():
            # 使用单词边界匹配，避免部分匹配
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, product_name_lower):
                return delivery_type

        return None

    def extract_delivery_format(self, product_name: str) -> Optional[str]:
        """
        从商品名称中提取交付格式

        Args:
            product_name: 商品名称

        Returns:
            Optional[str]: 交付格式（如PDF, Excel等）
        """
        if not product_name:
            return None

        product_name_lower = product_name.lower()

        # 格式关键词
        format_keywords = {
            'pdf': 'PDF',
            'excel': 'Excel',
            'word': 'Word',
            'powerpoint': 'PowerPoint',
            'ppt': 'PowerPoint',
            'google sheets': 'Google Sheets',
            'google docs': 'Google Docs',
            'canva': 'Canva',
            'notion': 'Notion',
            'figma': 'Figma',
            'jpg': 'JPG',
            'png': 'PNG',
            'svg': 'SVG',
        }

        for keyword, format_name in format_keywords.items():
            if keyword in product_name_lower:
                return format_name

        return None

    def extract_delivery_platform(self, product_name: str) -> Optional[str]:
        """
        从商品名称中提取交付平台

        Args:
            product_name: 商品名称

        Returns:
            Optional[str]: 交付平台
        """
        if not product_name:
            return None

        product_name_lower = product_name.lower()

        # 平台关键词
        platform_keywords = {
            'notion': 'Notion',
            'canva': 'Canva',
            'excel': 'Excel',
            'google sheets': 'Google Sheets',
            'google sheet': 'Google Sheets',
            'trello': 'Trello',
            'airtable': 'Airtable',
            'figma': 'Figma',
            'etsy': 'Etsy',
            'gumroad': 'Gumroad',
        }

        for keyword, platform_name in platform_keywords.items():
            if keyword in product_name_lower:
                return platform_name

        return None

    def extract_keywords(self, product_name: str, max_keywords: int = 5) -> List[str]:
        """
        从商品名称中提取关键词

        Args:
            product_name: 商品名称
            max_keywords: 最大关键词数量

        Returns:
            List[str]: 关键词列表
        """
        if not product_name:
            return []

        # 转小写
        text = product_name.lower()

        # 提取所有单词（3个字符以上）
        words = re.findall(r'\b[a-z]{3,}\b', text)

        # 过滤停用词
        keywords = [w for w in words if w not in self.STOP_WORDS]

        # 统计词频
        from collections import Counter
        word_counts = Counter(keywords)

        # 获取最常见的关键词
        top_keywords = [word for word, count in word_counts.most_common(max_keywords)]

        # 首字母大写
        return [w.capitalize() for w in top_keywords]

    def extract_all_attributes(self, product_name: str) -> Dict[str, any]:
        """
        提取商品的所有属性

        Args:
            product_name: 商品名称

        Returns:
            Dict: 包含所有提取属性的字典
        """
        return {
            'delivery_type': self.extract_delivery_type(product_name),
            'delivery_format': self.extract_delivery_format(product_name),
            'delivery_platform': self.extract_delivery_platform(product_name),
            'keywords': self.extract_keywords(product_name),
        }

    def process_product(self, product_id: int) -> Tuple[bool, str]:
        """
        处理单个商品的属性提取

        Args:
            product_id: 商品ID

        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        product = self.db.query(Product).filter(
            Product.product_id == product_id,
            Product.is_deleted == False
        ).first()

        if not product:
            return False, "商品不存在"

        # 提取属性
        attributes = self.extract_all_attributes(product.product_name)

        # 更新商品
        product.delivery_type = attributes['delivery_type']
        product.delivery_format = attributes['delivery_format']
        product.delivery_platform = attributes['delivery_platform']

        self.db.commit()

        return True, "属性提取成功"

    def process_all_products(self, batch_size: int = 100) -> Dict[str, any]:
        """
        批量处理所有商品的属性提取

        Args:
            batch_size: 批处理大小

        Returns:
            Dict: 处理结果统计
        """
        # 获取所有未删除的商品
        total_products = self.db.query(Product).filter(
            Product.is_deleted == False
        ).count()

        processed = 0
        failed = 0

        # 分批处理
        offset = 0
        while offset < total_products:
            products = self.db.query(Product).filter(
                Product.is_deleted == False
            ).offset(offset).limit(batch_size).all()

            for product in products:
                try:
                    # 提取属性
                    attributes = self.extract_all_attributes(product.product_name)

                    # 更新商品
                    product.delivery_type = attributes['delivery_type']
                    product.delivery_format = attributes['delivery_format']
                    product.delivery_platform = attributes['delivery_platform']

                    processed += 1
                except Exception as e:
                    failed += 1
                    print(f"处理商品 {product.product_id} 失败: {e}")

            # 提交批次
            self.db.commit()
            offset += batch_size

        return {
            'total': total_products,
            'processed': processed,
            'failed': failed,
            'success_rate': round(processed / total_products * 100, 2) if total_products > 0 else 0
        }

    def get_extraction_statistics(self) -> Dict[str, any]:
        """
        获取属性提取统计信息

        Returns:
            Dict: 统计信息
        """
        from sqlalchemy import func

        total = self.db.query(Product).filter(Product.is_deleted == False).count()

        # 统计各字段的填充情况
        delivery_type_count = self.db.query(Product).filter(
            Product.is_deleted == False,
            Product.delivery_type.isnot(None)
        ).count()

        delivery_format_count = self.db.query(Product).filter(
            Product.is_deleted == False,
            Product.delivery_format.isnot(None)
        ).count()

        delivery_platform_count = self.db.query(Product).filter(
            Product.is_deleted == False,
            Product.delivery_platform.isnot(None)
        ).count()

        # 统计各类型的分布
        delivery_type_dist = self.db.query(
            Product.delivery_type,
            func.count(Product.product_id).label('count')
        ).filter(
            Product.is_deleted == False,
            Product.delivery_type.isnot(None)
        ).group_by(Product.delivery_type).all()

        return {
            'total_products': total,
            'delivery_type_filled': delivery_type_count,
            'delivery_type_rate': round(delivery_type_count / total * 100, 2) if total > 0 else 0,
            'delivery_format_filled': delivery_format_count,
            'delivery_format_rate': round(delivery_format_count / total * 100, 2) if total > 0 else 0,
            'delivery_platform_filled': delivery_platform_count,
            'delivery_platform_rate': round(delivery_platform_count / total * 100, 2) if total > 0 else 0,
            'delivery_type_distribution': [
                {'type': dt, 'count': count} for dt, count in delivery_type_dist
            ]
        }

    # [REQ-012] P5.3: AI辅助兜底方法

    def extract_delivery_type_with_ai(self, product_name: str) -> Optional[str]:
        """
        使用AI提取交付形式（用于代码规则无法识别的情况）

        Args:
            product_name: 商品名称

        Returns:
            Optional[str]: 交付形式，如果AI无法识别则返回None
        """
        if not self.api_key:
            return None

        try:
            # 构建提示词
            prompt = f"""请分析以下商品名称，识别其交付形式（Delivery Type）。

商品名称: {product_name}

可能的交付形式包括：
- Template（模板）
- Planner（计划表）
- Tracker（追踪器）
- Worksheet（工作表）
- Printable（可打印文件）
- Bundle（捆绑包）
- Kit（工具包）
- Guide（指南）
- Checklist（清单）
- Calendar（日历）
- Ebook（电子书）
- Workbook（练习册）
- Journal（日记本）
- Organizer（整理器）
- Spreadsheet（电子表格）
- Notion Template（Notion模板）
- Canva Template（Canva模板）
- Excel Template（Excel模板）
- Google Sheets Template（Google Sheets模板）
- PowerPoint Template（PowerPoint模板）
- Word Template（Word模板）
- PDF（PDF文件）
- Figma Template（Figma模板）
- Trello Template（Trello模板）

请只返回最合适的一个交付形式，不要包含其他文字。如果无法确定，返回"Unknown"。"""

            if self.use_claude:
                # 调用Claude API
                import anthropic
                client = anthropic.Anthropic(api_key=self.api_key)

                message = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=100,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )

                response_text = message.content[0].text.strip()
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
                        "max_tokens": 100
                    }
                )

                response_text = response.json()['choices'][0]['message']['content'].strip()

            # 验证返回结果
            if response_text and response_text != "Unknown":
                return response_text
            else:
                return None

        except Exception as e:
            print(f"AI提取失败: {e}")
            return None

    def process_missing_delivery_types(self, max_products: Optional[int] = None, batch_size: int = 10) -> Dict[str, any]:
        """
        批量处理缺失delivery_type的商品（使用AI辅助）

        Args:
            max_products: 最大处理数量（None表示处理所有）
            batch_size: 批处理大小（默认10，避免API调用过快）

        Returns:
            Dict: 处理结果统计
        """
        if not self.api_key:
            return {
                'success': False,
                'message': 'API密钥未配置',
                'total': 0,
                'processed': 0,
                'filled': 0,
                'failed': 0
            }

        # 获取所有delivery_type为NULL的商品
        query = self.db.query(Product).filter(
            Product.is_deleted == False,
            Product.delivery_type.is_(None)
        )

        total_missing = query.count()

        if max_products:
            products = query.limit(max_products).all()
        else:
            products = query.all()

        processed = 0
        filled = 0
        failed = 0

        # 分批处理
        for i in range(0, len(products), batch_size):
            batch = products[i:i+batch_size]

            for product in batch:
                try:
                    # 使用AI提取delivery_type
                    delivery_type = self.extract_delivery_type_with_ai(product.product_name)

                    if delivery_type:
                        product.delivery_type = delivery_type
                        filled += 1

                    processed += 1

                except Exception as e:
                    failed += 1
                    print(f"处理商品 {product.product_id} 失败: {e}")

            # 提交批次
            self.db.commit()

        return {
            'success': True,
            'message': f'成功处理 {processed} 个商品，填充 {filled} 个',
            'total_missing': total_missing,
            'processed': processed,
            'filled': filled,
            'failed': failed,
            'fill_rate': round(filled / processed * 100, 2) if processed > 0 else 0
        }

"""
[REQ-2.7] Phase 7 商品筛选与AI标注系统 - 业务逻辑层

提供商品管理的核心业务逻辑：
1. 数据导入和清理
2. 字段映射配置
3. AI标注调度
4. 动态字段管理
"""
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import json
from datetime import datetime
from pathlib import Path
from storage.product_repository import (
    ProductRepository,
    ProductFieldDefinitionRepository,
    ProductImportLogRepository
)
from ai.client import LLMClient


class ProductImporter:
    """[REQ-2.7] 商品数据导入器"""

    def __init__(self):
        self.product_repo = ProductRepository()
        self.log_repo = ProductImportLogRepository()

    def import_from_file(
        self,
        file_path: str,
        platform: str,
        field_mapping: Dict[str, str],
        skip_duplicates: bool = True
    ) -> Dict[str, Any]:
        """
        [REQ-2.7] 从文件导入商品数据

        Args:
            file_path: 文件路径（CSV或Excel）
            platform: 平台名称（etsy/gumroad）
            field_mapping: 字段映射配置 {"col_0": "product_name", "col_1": "description", ...}
            skip_duplicates: 是否跳过重复数据

        Returns:
            导入结果统计
        """
        start_time = datetime.utcnow()
        source_file = Path(file_path).name

        # 创建导入日志
        log_id = self.log_repo.create({
            "source_file": source_file,
            "platform": platform,
            "total_rows": 0,
            "imported_rows": 0,
            "skipped_rows": 0,
            "duplicate_rows": 0,
            "field_mapping": json.dumps(field_mapping, ensure_ascii=False),
            "import_status": "in_progress"
        })

        try:
            # 读取文件
            df = self._read_file(file_path)
            total_rows = len(df)

            # 更新总行数
            self.log_repo.update(log_id, {"total_rows": total_rows})

            # 数据清理和转换
            products, skipped_rows = self._clean_and_transform(
                df, field_mapping, platform, source_file, skip_duplicates
            )

            # 批量插入
            imported_rows = len(products)
            if products:
                self.product_repo.bulk_insert(products)

            # 计算耗时
            duration = int((datetime.utcnow() - start_time).total_seconds())

            # 更新导入日志
            self.log_repo.update(log_id, {
                "imported_rows": imported_rows,
                "skipped_rows": skipped_rows,
                "import_status": "completed",
                "duration_seconds": duration
            })

            return {
                "success": True,
                "log_id": log_id,
                "total_rows": total_rows,
                "imported_rows": imported_rows,
                "skipped_rows": skipped_rows,
                "duration_seconds": duration
            }

        except Exception as e:
            # 记录错误
            self.log_repo.update(log_id, {
                "import_status": "failed",
                "error_message": str(e)
            })

            return {
                "success": False,
                "log_id": log_id,
                "error": str(e)
            }

    def _read_file(self, file_path: str) -> pd.DataFrame:
        """
        读取CSV或Excel文件

        Args:
            file_path: 文件路径

        Returns:
            DataFrame
        """
        file_ext = Path(file_path).suffix.lower()

        if file_ext == '.csv':
            # 尝试多种编码
            for encoding in ['utf-8', 'gbk', 'gb2312', 'latin1']:
                try:
                    return pd.read_csv(file_path, encoding=encoding, header=None)
                except:
                    continue
            raise ValueError("无法读取CSV文件，请检查文件编码")

        elif file_ext in ['.xlsx', '.xls']:
            return pd.read_excel(file_path, header=None)

        else:
            raise ValueError(f"不支持的文件格式: {file_ext}")

    def _clean_and_transform(
        self,
        df: pd.DataFrame,
        field_mapping: Dict[str, str],
        platform: str,
        source_file: str,
        skip_duplicates: bool
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        [REQ-2.7] 数据清理和转换

        Args:
            df: 原始DataFrame
            field_mapping: 字段映射
            platform: 平台名称
            source_file: 源文件名
            skip_duplicates: 是否跳过重复

        Returns:
            (清理后的商品列表, 跳过的行数)
        """
        products = []
        skipped_rows = 0

        for idx, row in df.iterrows():
            try:
                # 映射字段
                product = self._map_fields(row, field_mapping)

                # 数据验证
                if not self._validate_product(product):
                    skipped_rows += 1
                    continue

                # 去重检查
                if skip_duplicates and product.get('url'):
                    existing = self.product_repo.get_by_url(product['url'])
                    if existing:
                        skipped_rows += 1
                        continue

                # 添加元数据
                product['platform'] = platform
                product['source_file'] = source_file
                product['ai_analysis_status'] = 'pending'
                product['imported_at'] = datetime.utcnow()
                product['updated_at'] = datetime.utcnow()

                products.append(product)

            except Exception as e:
                skipped_rows += 1
                continue

        return products, skipped_rows

    def _map_fields(
        self,
        row: pd.Series,
        field_mapping: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        [REQ-2.7] 字段映射

        Args:
            row: DataFrame行
            field_mapping: 字段映射配置

        Returns:
            映射后的商品字典
        """
        product = {}

        for col_key, field_name in field_mapping.items():
            # 提取列索引
            col_idx = int(col_key.replace('col_', ''))

            if col_idx < len(row):
                value = row.iloc[col_idx]

                # 处理空值
                if pd.isna(value):
                    value = None
                else:
                    value = str(value).strip()

                # 类型转换
                if field_name == 'price' and value:
                    try:
                        # 移除货币符号和逗号
                        value = float(str(value).replace('$', '').replace(',', ''))
                    except:
                        value = None

                elif field_name in ['sales', 'review_count'] and value:
                    try:
                        value = int(float(str(value).replace(',', '')))
                    except:
                        value = 0

                elif field_name == 'rating' and value:
                    try:
                        value = float(value)
                    except:
                        value = None

                product[field_name] = value

        return product

    def _validate_product(self, product: Dict[str, Any]) -> bool:
        """
        [REQ-2.7] 数据验证

        Args:
            product: 商品数据

        Returns:
            是否有效
        """
        # 必填字段检查
        if not product.get('product_name'):
            return False

        if not product.get('url'):
            return False

        # 价格验证
        price = product.get('price')
        if price is not None and (price < 0 or price > 999999):
            return False

        # 评分验证
        rating = product.get('rating')
        if rating is not None and (rating < 0 or rating > 5):
            return False

        return True


class ProductAIAnnotator:
    """[REQ-2.7] 商品AI标注器"""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.product_repo = ProductRepository()
        self.llm_client = llm_client or LLMClient()

    def annotate_batch(
        self,
        batch_size: int = 10,
        prompt_template: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        [REQ-2.7] 批量AI标注

        Args:
            batch_size: 批次大小
            prompt_template: 自定义提示词模板

        Returns:
            标注结果统计
        """
        # 获取待标注商品
        products = self.product_repo.get_pending_ai_analysis(limit=batch_size)

        if not products:
            return {
                "success": True,
                "processed": 0,
                "message": "没有待标注的商品"
            }

        success_count = 0
        failed_count = 0

        for product in products:
            try:
                # 调用AI生成标签和需求分析
                result = self._annotate_single(product, prompt_template)

                # 更新数据库
                self.product_repo.update_ai_analysis(
                    product['product_id'],
                    result['tags'],
                    result['demand_analysis'],
                    'completed'
                )

                success_count += 1

            except Exception as e:
                # 标记为失败
                self.product_repo.update(
                    product['product_id'],
                    {'ai_analysis_status': 'failed'}
                )
                failed_count += 1

        return {
            "success": True,
            "processed": len(products),
            "success_count": success_count,
            "failed_count": failed_count
        }

    def _annotate_single(
        self,
        product: Dict[str, Any],
        prompt_template: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        [REQ-2.7] 单个商品AI标注

        Args:
            product: 商品数据
            prompt_template: 自定义提示词模板

        Returns:
            标注结果 {"tags": [...], "demand_analysis": "..."}
        """
        # 构建提示词
        if not prompt_template:
            prompt_template = """
请分析以下商品信息，完成两个任务：

1. 生成3个中文标签，描述商品的类别、特点或用途
2. 判断这个商品解决了什么用户需求

商品信息：
- 名称：{product_name}
- 描述：{description}
- 价格：${price}
- 评分：{rating}星
- 评价数：{review_count}条

请以JSON格式返回结果：
{{
    "tags": ["标签1", "标签2", "标签3"],
    "demand_analysis": "需求分析文本"
}}
"""

        prompt = prompt_template.format(
            product_name=product.get('product_name', ''),
            description=product.get('description', '')[:500],  # 限制长度
            price=product.get('price', 0),
            rating=product.get('rating', 0),
            review_count=product.get('review_count', 0)
        )

        # 调用LLM
        response = self.llm_client.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500
        )

        # 解析响应
        try:
            result = json.loads(response)
            return {
                "tags": result.get('tags', [])[:3],  # 确保只有3个标签
                "demand_analysis": result.get('demand_analysis', '')
            }
        except:
            # 如果解析失败，返回默认值
            return {
                "tags": ["未分类", "待标注", "其他"],
                "demand_analysis": "AI分析失败，需要人工标注"
            }


class ProductFieldManager:
    """[REQ-2.7] 动态字段管理器"""

    def __init__(self):
        self.field_repo = ProductFieldDefinitionRepository()

    def add_field(
        self,
        field_name: str,
        field_key: str,
        field_type: str,
        **kwargs
    ) -> int:
        """
        [REQ-2.7] 添加自定义字段

        Args:
            field_name: 字段显示名称
            field_key: 字段键名（用于JSON存储）
            field_type: 字段类型
            **kwargs: 其他字段配置

        Returns:
            字段ID
        """
        # 检查键名是否已存在
        existing = self.field_repo.get_by_key(field_key)
        if existing:
            raise ValueError(f"字段键名 '{field_key}' 已存在")

        # 获取当前最大order
        all_fields = self.field_repo.get_all()
        max_order = max([f['field_order'] for f in all_fields], default=0)

        field_data = {
            'field_name': field_name,
            'field_key': field_key,
            'field_type': field_type,
            'field_order': max_order + 1,
            'is_system_field': False,
            **kwargs
        }

        return self.field_repo.create(field_data)

    def remove_field(self, field_id: int) -> bool:
        """
        [REQ-2.7] 删除自定义字段（系统字段不可删除）

        Args:
            field_id: 字段ID

        Returns:
            是否删除成功
        """
        return self.field_repo.delete(field_id)

    def update_field(self, field_id: int, updates: Dict[str, Any]) -> bool:
        """
        [REQ-2.7] 更新字段配置

        Args:
            field_id: 字段ID
            updates: 更新数据

        Returns:
            是否更新成功
        """
        return self.field_repo.update(field_id, updates)

    def get_all_fields(self) -> List[Dict[str, Any]]:
        """
        [REQ-2.7] 获取所有字段定义

        Returns:
            字段定义列表
        """
        return self.field_repo.get_all(order_by_order=True)

    def reorder_fields(self, field_orders: Dict[int, int]) -> bool:
        """
        [REQ-2.7] 重新排序字段

        Args:
            field_orders: {field_id: new_order}

        Returns:
            是否成功
        """
        try:
            for field_id, new_order in field_orders.items():
                self.field_repo.update(field_id, {'field_order': new_order})
            return True
        except:
            return False


class ProductExporter:
    """[REQ-2.7] 商品数据导出器"""

    def __init__(self):
        self.product_repo = ProductRepository()

    def export_to_csv(
        self,
        output_path: str,
        filters: Optional[Dict[str, Any]] = None,
        selected_fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        [REQ-2.7] 导出商品数据为CSV

        Args:
            output_path: 输出文件路径
            filters: 筛选条件
            selected_fields: 要导出的字段列表

        Returns:
            导出结果
        """
        try:
            # 获取数据
            if filters:
                products, total = self.product_repo.search(**filters, limit=100000)
            else:
                products = self.product_repo.get_all(limit=100000)

            if not products:
                return {
                    "success": False,
                    "error": "没有数据可导出"
                }

            # 转换为DataFrame
            df = pd.DataFrame(products)

            # 选择字段
            if selected_fields:
                df = df[selected_fields]

            # 导出
            df.to_csv(output_path, index=False, encoding='utf-8-sig')

            return {
                "success": True,
                "file_path": output_path,
                "row_count": len(products)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def export_to_excel(
        self,
        output_path: str,
        filters: Optional[Dict[str, Any]] = None,
        selected_fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        [REQ-2.7] 导出商品数据为Excel

        Args:
            output_path: 输出文件路径
            filters: 筛选条件
            selected_fields: 要导出的字段列表

        Returns:
            导出结果
        """
        try:
            # 获取数据
            if filters:
                products, total = self.product_repo.search(**filters, limit=100000)
            else:
                products = self.product_repo.get_all(limit=100000)

            if not products:
                return {
                    "success": False,
                    "error": "没有数据可导出"
                }

            # 转换为DataFrame
            df = pd.DataFrame(products)

            # 选择字段
            if selected_fields:
                df = df[selected_fields]

            # 导出
            df.to_excel(output_path, index=False, engine='openpyxl')

            return {
                "success": True,
                "file_path": output_path,
                "row_count": len(products)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

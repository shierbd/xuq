"""
Product Entity Identifier - 产品实体识别器
核心原则：从交叉验证的变量中识别真实产品/工具/服务
"""
import sys
from pathlib import Path
from typing import List, Dict
import json
import time

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ai.client import LLMClient


class ProductIdentifier:
    """产品实体识别器：用DeepSeek AI识别真实产品"""

    def __init__(self):
        self.llm = LLMClient(provider="deepseek")

    def identify_products_from_variables(
        self,
        valid_variables: List[Dict],
        batch_size: int = 10
    ) -> List[Dict]:
        """
        从变量中识别产品实体

        Args:
            valid_variables: 通过交叉验证的高质量变量
            batch_size: 批量处理大小

        Returns:
            识别出的产品实体列表
        """
        print("\n" + "="*70)
        print("Phase 7: Product Entity Identification with DeepSeek AI".center(70))
        print("="*70)

        products = []
        total_batches = (len(valid_variables) + batch_size - 1) // batch_size

        print(f"\n[Processing] {len(valid_variables)} variables in {total_batches} batches...")

        for i in range(0, len(valid_variables), batch_size):
            batch = valid_variables[i:i+batch_size]
            batch_num = i // batch_size + 1

            print(f"\n  Batch {batch_num}/{total_batches}: Processing {len(batch)} variables...")

            # 批量识别
            batch_products = self._identify_batch(batch)
            products.extend(batch_products)

            print(f"    Identified {len(batch_products)} products from this batch")

            # 避免API限流
            if batch_num < total_batches:
                time.sleep(1)

        print(f"\n[Result] Total products identified: {len(products)}")

        return products

    def _identify_batch(self, variables: List[Dict]) -> List[Dict]:
        """批量识别产品"""

        # 构建批量识别的prompt
        variable_list = []
        for idx, var in enumerate(variables, 1):
            variable_list.append(
                f"{idx}. \"{var['variable_text']}\" (frequency: {var['frequency']}, templates: {var['template_match_count']})"
            )

        prompt = f"""You are a product/tool/service identifier. Analyze the following variables extracted from search queries and identify which ones are real products, tools, or services.

Variables extracted from search templates:
{chr(10).join(variable_list)}

For each variable, determine:
1. Is it a real product/tool/service name? (yes/no)
2. If yes, what category? (electronics, software, service, content, other)
3. Brief description (1 sentence)
4. Commercial value score (0-100, based on search demand)

Return ONLY a JSON array with this exact structure:
[
  {{
    "variable_text": "android",
    "is_product": true,
    "category": "software",
    "description": "Mobile operating system by Google",
    "commercial_value": 95
  }},
  {{
    "variable_text": "what",
    "is_product": false,
    "category": null,
    "description": "Query word, not a product",
    "commercial_value": 0
  }}
]

Return ONLY valid JSON, no markdown formatting, no explanation."""

        try:
            response = self.llm._call_llm(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=2000
            )

            # 清理响应（移除可能的markdown格式）
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()

            # 解析JSON
            results = json.loads(response)

            # 只保留识别为产品的结果
            products = []
            for result in results:
                if result.get('is_product', False):
                    # 找到原始变量数据
                    original_var = next(
                        (v for v in variables if v['variable_text'] == result['variable_text']),
                        None
                    )

                    if original_var:
                        products.append({
                            'product_name': result['variable_text'],
                            'category': result['category'],
                            'description': result['description'],
                            'commercial_value': result['commercial_value'],
                            'frequency': original_var['frequency'],
                            'template_match_count': original_var['template_match_count'],
                            'total_volume': original_var['total_volume'],
                            'cross_validation_score': original_var['cross_validation_score']
                        })

            return products

        except Exception as e:
            print(f"    [ERROR] Failed to process batch: {str(e)}")
            return []


def run_product_identification_pipeline():
    """运行产品识别流程"""

    print("="*70)
    print("Product Identification Pipeline with DeepSeek AI".center(70))
    print("="*70)
    print("\nPrinciple: AI identifies real products from cross-validated variables")

    # 1. 加载变量提取结果
    print("\n[Step 1] Loading variable extraction results...")
    results_file = project_root / 'outputs' / 'variable_extraction_results.json'

    if not results_file.exists():
        print(f"  [ERROR] Results file not found: {results_file}")
        print("  Please run core/variable_extractor.py first!")
        return

    with open(results_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    valid_variables = data['top_variables']
    print(f"  Loaded {len(valid_variables)} cross-validated variables")

    # 2. 使用DeepSeek识别产品
    print("\n[Step 2] Identifying products with DeepSeek AI...")
    identifier = ProductIdentifier()
    products = identifier.identify_products_from_variables(
        valid_variables=valid_variables,
        batch_size=10
    )

    # 3. 按商业价值排序
    products.sort(key=lambda x: x['commercial_value'], reverse=True)

    # 4. 保存结果
    print("\n[Step 3] Saving results...")
    output_dir = project_root / 'outputs'
    output_file = output_dir / 'product_entities.json'

    output_data = {
        'total_products': len(products),
        'products': products,
        'statistics': {
            'avg_commercial_value': sum(p['commercial_value'] for p in products) / len(products) if products else 0,
            'high_value_products': len([p for p in products if p['commercial_value'] >= 70]),
            'categories': {}
        }
    }

    # 统计类别分布
    for product in products:
        category = product['category']
        if category not in output_data['statistics']['categories']:
            output_data['statistics']['categories'][category] = 0
        output_data['statistics']['categories'][category] += 1

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    # 5. 生成报告
    print("\n" + "="*70)
    print("Product Identification Report".center(70))
    print("="*70)

    print(f"\n[Summary]")
    print(f"  Total products identified: {len(products)}")
    print(f"  Average commercial value: {output_data['statistics']['avg_commercial_value']:.1f}")
    print(f"  High-value products (≥70): {output_data['statistics']['high_value_products']}")

    print(f"\n[Category Distribution]")
    for category, count in sorted(output_data['statistics']['categories'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {category}: {count}")

    print(f"\n[Top 20 Products by Commercial Value]")
    for i, product in enumerate(products[:20], 1):
        print(f"\n  {i}. {product['product_name']}")
        print(f"     Category: {product['category']}")
        print(f"     Description: {product['description']}")
        print(f"     Commercial Value: {product['commercial_value']}/100")
        print(f"     Frequency: {product['frequency']}, Templates: {product['template_match_count']}")
        if product['total_volume'] > 0:
            print(f"     Total Search Volume: {product['total_volume']:,}")

    print("\n" + "="*70)
    print("Product identification completed successfully!".center(70))
    print("="*70)

    print(f"\nResults saved to:")
    print(f"  - {output_file}")

    return products


if __name__ == "__main__":
    run_product_identification_pipeline()

"""
[REQ-001] 数据导入功能 - 测试脚本
测试数据预处理和导入功能
"""
import sys
sys.path.insert(0, '.')

from backend.utils.data_preprocessor import parse_review_count, clean_product_name

def test_parse_review_count():
    """测试评价数量转换"""
    print("测试评价数量转换...")
    
    test_cases = [
        ("(1.1k)", 1100),
        ("(19.1k)", 19100),
        ("(9.8k)", 9800),
        ("(15)", 15),
        ("(2.5m)", 2500000),
        ("(abc)", None),
        ("", None),
    ]
    
    for input_val, expected in test_cases:
        result = parse_review_count(input_val)
        status = "PASS" if result == expected else "FAIL"
        print(f"  [{status}] {input_val} -> {result} (expected: {expected})")

def test_clean_product_name():
    """测试商品名称清洗"""
    print("\n测试商品名称清洗...")
    
    test_cases = [
        ("  Product Name  ", "Product Name"),
        ("Product   With   Spaces", "Product With Spaces"),
        ("Product (with brackets)", "Product (with brackets)"),
    ]
    
    for input_val, expected in test_cases:
        result = clean_product_name(input_val)
        status = "PASS" if result == expected else "FAIL"
        print(f"  [{status}] '{input_val}' -> '{result}'")

if __name__ == "__main__":
    print("=" * 60)
    print("[REQ-001] Data Import Function - Unit Tests")
    print("=" * 60)
    
    test_parse_review_count()
    test_clean_product_name()
    
    print("\n" + "=" * 60)
    print("Tests completed!")
    print("=" * 60)

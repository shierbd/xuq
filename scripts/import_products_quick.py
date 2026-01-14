"""
快速导入商品数据脚本

用法：
    python scripts/import_products_quick.py <文件路径>

示例：
    python scripts/import_products_quick.py "C:\\Users\\32941\\Downloads\\合并表格_20260114_150935.xlsx"
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.product_management import ProductImporter


def main():
    if len(sys.argv) < 2:
        print("Error: Please provide file path")
        print("\nUsage:")
        print("    python scripts/import_products_quick.py <file_path>")
        print("\nExample:")
        print('    python scripts/import_products_quick.py "C:\\Users\\32941\\Downloads\\file.xlsx"')
        sys.exit(1)

    file_path = sys.argv[1]

    if not Path(file_path).exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    print("=" * 60)
    print("Phase 7 Product Import")
    print("=" * 60)
    print(f"\nFile: {file_path}")
    print(f"Platform: etsy")
    print(f"Field Mapping:")
    print("   - Column 0 -> product_name")
    print("   - Column 1 -> rating")
    print("   - Column 2 -> review_count")
    print("   - Column 3 -> shop_name")
    print("   - Column 4 -> price")
    print("\nNote: URL field will use placeholder (no URL in data)")
    print("\n" + "=" * 60)

    # 配置字段映射
    field_mapping = {
        "col_0": "product_name",  # 商品名称
        "col_1": "rating",         # 评分
        "col_2": "review_count",   # 评价数（使用销量作为评价数）
        "col_3": "shop_name",      # 店铺名称
        "col_4": "price",          # 价格
    }

    print("\nStarting import...")

    # 创建导入器
    importer = ProductImporter()

    # 执行导入
    result = importer.import_from_file(
        file_path=file_path,
        platform="etsy",
        field_mapping=field_mapping,
        skip_duplicates=True
    )

    print("\n" + "=" * 60)

    if result["success"]:
        print("Import Success!")
        print(f"\nStatistics:")
        print(f"   - Total rows: {result['total_rows']}")
        print(f"   - Imported: {result['imported_rows']}")
        print(f"   - Skipped: {result['skipped_rows']}")
        print(f"   - Duration: {result['duration_seconds']}s")
        print(f"\nTip: You can now view products in Web UI")
        print(f"   URL: http://localhost:8501")
        print(f"   Navigate: Phase 7 -> Product Filter")
    else:
        print("Import Failed!")
        print(f"\nError: {result.get('error', 'Unknown error')}")

    print("=" * 60)


if __name__ == "__main__":
    main()

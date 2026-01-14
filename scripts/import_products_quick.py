"""
快速导入商品数据脚本

用法：
    python scripts/import_products_quick.py <文件路径>

示例：
    python scripts/import_products_quick.py "C:\Users\32941\Downloads\合并表格_20260114_150935.xlsx"
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.product_management import ProductImporter


def main():
    if len(sys.argv) < 2:
        print("❌ 错误：请提供文件路径")
        print("\n用法：")
        print("    python scripts/import_products_quick.py <文件路径>")
        print("\n示例：")
        print('    python scripts/import_products_quick.py "C:\\Users\\32941\\Downloads\\合并表格_20260114_150935.xlsx"')
        sys.exit(1)

    file_path = sys.argv[1]

    if not Path(file_path).exists():
        print(f"❌ 错误：文件不存在: {file_path}")
        sys.exit(1)

    print("=" * 60)
    print("📦 Phase 7 商品数据快速导入")
    print("=" * 60)
    print(f"\n📁 文件路径: {file_path}")
    print(f"📊 平台: etsy")
    print(f"🔧 字段映射:")
    print("   - 列0 → 商品名称")
    print("   - 列1 → 评分")
    print("   - 列2 → 销量")
    print("   - 列3 → 店铺名称")
    print("   - 列4 → 价格")
    print("\n⚠️  注意：URL字段将使用占位符（因为数据中没有URL）")
    print("\n" + "=" * 60)

    # 配置字段映射
    field_mapping = {
        "col_0": "product_name",  # 商品名称
        "col_1": "rating",         # 评分
        "col_2": "review_count",   # 评价数（使用销量作为评价数）
        "col_3": "shop_name",      # 店铺名称
        "col_4": "price",          # 价格
    }

    print("\n🚀 开始导入...")

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
        print("✅ 导入成功！")
        print(f"\n📊 导入统计:")
        print(f"   - 总行数: {result['total_rows']}")
        print(f"   - 成功导入: {result['imported_rows']}")
        print(f"   - 跳过: {result['skipped_rows']}")
        print(f"   - 耗时: {result['duration_seconds']}秒")
        print(f"\n💡 提示: 现在可以在Web UI中查看导入的商品了")
        print(f"   访问: http://localhost:8501")
        print(f"   导航: Phase 7 → 商品筛选")
    else:
        print("❌ 导入失败！")
        print(f"\n错误信息: {result.get('error', '未知错误')}")

    print("=" * 60)


if __name__ == "__main__":
    main()

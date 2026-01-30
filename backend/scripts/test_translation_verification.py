"""
翻译功能测试与验证脚本
测试内容：
1. 数据库翻译完成情况
2. 翻译质量抽样检查
3. 数据完整性验证
4. 边界情况测试
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy import func, distinct
from backend.database import SessionLocal
from backend.models.product import Product
import random

def test_translation_completion():
    """测试1：检查翻译完成情况"""
    print("=" * 60)
    print("测试1：翻译完成情况检查")
    print("=" * 60)

    db = SessionLocal()
    try:
        # 统计总商品数
        total_products = db.query(Product).filter(
            Product.is_deleted == False
        ).count()

        # 统计有类别名称的商品数
        products_with_cluster = db.query(Product).filter(
            Product.is_deleted == False,
            Product.cluster_name.isnot(None),
            Product.cluster_name != ""
        ).count()

        # 统计有中文翻译的商品数
        products_with_cn = db.query(Product).filter(
            Product.is_deleted == False,
            Product.cluster_name_cn.isnot(None),
            Product.cluster_name_cn != ""
        ).count()

        # 统计不同的英文类别数
        unique_en_categories = db.query(distinct(Product.cluster_name)).filter(
            Product.cluster_name.isnot(None),
            Product.cluster_name != ""
        ).count()

        # 统计不同的中文类别数
        unique_cn_categories = db.query(distinct(Product.cluster_name_cn)).filter(
            Product.cluster_name_cn.isnot(None),
            Product.cluster_name_cn != ""
        ).count()

        # 统计未翻译的类别
        untranslated = db.query(distinct(Product.cluster_name)).filter(
            Product.cluster_name.isnot(None),
            Product.cluster_name != "",
            Product.cluster_name_cn.is_(None)
        ).count()

        print(f"\n总商品数: {total_products}")
        print(f"有类别名称的商品数: {products_with_cluster}")
        print(f"有中文翻译的商品数: {products_with_cn}")
        print(f"不同的英文类别数: {unique_en_categories}")
        print(f"不同的中文类别数: {unique_cn_categories}")
        print(f"未翻译的类别数: {untranslated}")

        # 计算翻译完成率
        if unique_en_categories > 0:
            completion_rate = (unique_cn_categories / unique_en_categories) * 100
            print(f"\n翻译完成率: {completion_rate:.2f}%")

            if completion_rate == 100:
                print("[OK] 所有类别都已翻译完成！")
                return True
            else:
                print(f"[WARNING] 还有 {untranslated} 个类别未翻译")
                return False
        else:
            print("[WARNING] 没有找到任何类别名称")
            return False

    finally:
        db.close()

def test_translation_quality():
    """测试2：翻译质量抽样检查"""
    print("\n" + "=" * 60)
    print("测试2：翻译质量抽样检查（随机抽取20个）")
    print("=" * 60)

    db = SessionLocal()
    try:
        # 获取所有不同的类别名称对
        categories = db.query(
            Product.cluster_name,
            Product.cluster_name_cn
        ).filter(
            Product.cluster_name.isnot(None),
            Product.cluster_name != "",
            Product.cluster_name_cn.isnot(None),
            Product.cluster_name_cn != ""
        ).distinct().all()

        # 随机抽取20个
        sample_size = min(20, len(categories))
        samples = random.sample(categories, sample_size)

        print(f"\n随机抽取 {sample_size} 个类别进行质量检查：\n")

        for i, (en_name, cn_name) in enumerate(samples, 1):
            print(f"{i:2d}. {en_name}")
            print(f"    -> {cn_name}")
            print()

        print("✅ 翻译质量检查完成，请人工审核以上翻译是否准确")
        return True

    finally:
        db.close()

def test_data_integrity():
    """测试3：数据完整性验证"""
    print("\n" + "=" * 60)
    print("测试3：数据完整性验证")
    print("=" * 60)

    db = SessionLocal()
    try:
        # 检查是否有英文名称但没有中文名称的情况
        missing_cn = db.query(Product).filter(
            Product.cluster_name.isnot(None),
            Product.cluster_name != "",
            Product.cluster_name_cn.is_(None)
        ).count()

        # 检查是否有中文名称但没有英文名称的情况（异常情况）
        missing_en = db.query(Product).filter(
            Product.cluster_name.is_(None),
            Product.cluster_name_cn.isnot(None)
        ).count()

        # 检查中文名称长度是否合理（应该在1-50个字符之间）
        too_long = db.query(Product).filter(
            Product.cluster_name_cn.isnot(None),
            func.length(Product.cluster_name_cn) > 50
        ).count()

        too_short = db.query(Product).filter(
            Product.cluster_name_cn.isnot(None),
            func.length(Product.cluster_name_cn) < 2
        ).count()

        print(f"\n有英文名称但缺少中文翻译: {missing_cn}")
        print(f"有中文名称但缺少英文名称（异常）: {missing_en}")
        print(f"中文名称过长（>50字符）: {too_long}")
        print(f"中文名称过短（<2字符）: {too_short}")

        # 显示一些异常数据
        if too_long > 0:
            print("\n过长的中文名称示例：")
            long_names = db.query(
                Product.cluster_name,
                Product.cluster_name_cn
            ).filter(
                Product.cluster_name_cn.isnot(None),
                func.length(Product.cluster_name_cn) > 50
            ).limit(5).all()

            for en, cn in long_names:
                print(f"  {en} -> {cn} (长度: {len(cn)})")

        if missing_cn == 0 and missing_en == 0 and too_long == 0:
            print("\n✅ 数据完整性验证通过！")
            return True
        else:
            print("\n⚠️ 发现数据完整性问题")
            return False

    finally:
        db.close()

def test_category_distribution():
    """测试4：类别分布统计"""
    print("\n" + "=" * 60)
    print("测试4：类别分布统计")
    print("=" * 60)

    db = SessionLocal()
    try:
        # 统计每个类别的商品数量（Top 10）
        top_categories = db.query(
            Product.cluster_name,
            Product.cluster_name_cn,
            func.count(Product.product_id).label('count')
        ).filter(
            Product.cluster_name.isnot(None),
            Product.cluster_name != ""
        ).group_by(
            Product.cluster_name,
            Product.cluster_name_cn
        ).order_by(
            func.count(Product.product_id).desc()
        ).limit(10).all()

        print("\nTop 10 类别（按商品数量排序）：\n")
        for i, (en_name, cn_name, count) in enumerate(top_categories, 1):
            print(f"{i:2d}. {cn_name or en_name} ({en_name})")
            print(f"    商品数: {count}")
            print()

        print("✅ 类别分布统计完成")
        return True

    finally:
        db.close()

def test_edge_cases():
    """测试5：边界情况测试"""
    print("\n" + "=" * 60)
    print("测试5：边界情况测试")
    print("=" * 60)

    db = SessionLocal()
    try:
        # 检查是否有特殊字符
        special_chars = db.query(
            Product.cluster_name,
            Product.cluster_name_cn
        ).filter(
            Product.cluster_name_cn.isnot(None),
            Product.cluster_name_cn.like('%&%')
        ).limit(5).all()

        if special_chars:
            print("\n包含特殊字符的翻译：")
            for en, cn in special_chars:
                print(f"  {en} -> {cn}")
        else:
            print("\n✅ 未发现包含特殊字符的翻译")

        # 检查是否有重复的中文名称（不同英文名称翻译成相同中文）
        duplicate_cn = db.query(
            Product.cluster_name_cn,
            func.count(distinct(Product.cluster_name)).label('count')
        ).filter(
            Product.cluster_name_cn.isnot(None),
            Product.cluster_name_cn != ""
        ).group_by(
            Product.cluster_name_cn
        ).having(
            func.count(distinct(Product.cluster_name)) > 1
        ).all()

        if duplicate_cn:
            print(f"\n发现 {len(duplicate_cn)} 个重复的中文名称：")
            for cn_name, count in duplicate_cn[:5]:
                print(f"  {cn_name} (对应 {count} 个不同的英文名称)")

                # 显示对应的英文名称
                en_names = db.query(distinct(Product.cluster_name)).filter(
                    Product.cluster_name_cn == cn_name
                ).all()
                for (en,) in en_names:
                    print(f"    - {en}")
        else:
            print("\n✅ 未发现重复的中文名称")

        return True

    finally:
        db.close()

def generate_test_report():
    """生成测试报告"""
    print("\n" + "=" * 60)
    print("翻译功能测试报告")
    print("=" * 60)

    results = {
        "翻译完成情况": test_translation_completion(),
        "翻译质量检查": test_translation_quality(),
        "数据完整性验证": test_data_integrity(),
        "类别分布统计": test_category_distribution(),
        "边界情况测试": test_edge_cases()
    }

    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")

    all_passed = all(results.values())

    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有测试通过！翻译功能运行正常。")
    else:
        print("⚠️ 部分测试未通过，请检查上述问题。")
    print("=" * 60)

    return all_passed

if __name__ == "__main__":
    generate_test_report()

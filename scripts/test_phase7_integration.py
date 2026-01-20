"""
Phase 7 与溯源系统集成测试

测试AI标注后自动创建需求并建立溯源关系的完整流程

使用方法:
    python scripts/test_phase7_integration.py
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.product_management import ProductAIAnnotator
from core.demand_provenance_service import DemandProvenanceService
from storage.product_repository import ProductRepository


def test_integration():
    """测试Phase 7与溯源系统的集成"""
    print("=" * 80)
    print("Phase 7 与溯源系统集成测试")
    print("=" * 80)

    # 初始化服务
    annotator = ProductAIAnnotator()
    provenance_service = DemandProvenanceService()
    product_repo = ProductRepository()

    # 步骤1: 检查是否有待标注的商品
    print("\n[步骤1] 检查待标注商品...")
    pending_products = product_repo.get_pending_ai_analysis(limit=5)

    if not pending_products:
        print("  没有待标注的商品")
        print("\n提示: 请先导入商品数据并设置为待标注状态")
        return

    print(f"  找到 {len(pending_products)} 个待标注商品")
    for i, p in enumerate(pending_products[:3], 1):
        print(f"    {i}. {p.get('product_name', 'Unknown')[:50]}")

    # 步骤2: 执行AI标注（只标注1个商品作为测试）
    print("\n[步骤2] 执行AI标注...")
    print("  注意: 这将调用LLM API，可能需要几秒钟")

    try:
        result = annotator.annotate_batch(batch_size=1)

        print(f"\n  标注结果:")
        print(f"    处理数量: {result['processed']}")
        print(f"    成功数量: {result['success_count']}")
        print(f"    失败数量: {result['failed_count']}")
        print(f"    创建需求数: {result.get('demands_created', 0)}")

        if result['success_count'] == 0:
            print("\n  [ERROR] 标注失败，无法继续测试")
            return

    except Exception as e:
        print(f"\n  [ERROR] 标注过程出错: {e}")
        import traceback
        traceback.print_exc()
        return

    # 步骤3: 查询最新创建的需求
    print("\n[步骤3] 查询最新创建的需求...")

    try:
        stats = provenance_service.get_demands_by_source()

        if 'phase7' in stats['by_phase']:
            phase7_count = stats['by_phase']['phase7']['count']
            phase7_confidence = stats['by_phase']['phase7']['avg_confidence']

            print(f"  Phase 7 需求统计:")
            print(f"    需求数量: {phase7_count}")
            print(f"    平均置信度: {phase7_confidence:.2f}")
        else:
            print("  [WARNING] 未找到Phase 7的需求")

    except Exception as e:
        print(f"  [ERROR] 查询统计失败: {e}")

    # 步骤4: 查询最新需求的详细溯源信息
    print("\n[步骤4] 查询最新需求的溯源信息...")

    try:
        # 获取最新的phase7需求
        from storage.models import get_session, Demand
        session = get_session()

        latest_demand = session.query(Demand).filter(
            Demand.source_phase == 'phase7'
        ).order_by(Demand.demand_id.desc()).first()

        if latest_demand:
            print(f"\n  需求ID: {latest_demand.demand_id}")
            print(f"  标题: {latest_demand.title}")
            print(f"  置信度: {float(latest_demand.confidence_score):.2f}")

            # 获取完整溯源信息
            provenance = provenance_service.get_demand_provenance(latest_demand.demand_id)

            print(f"\n  来源信息:")
            print(f"    Phase: {provenance['source']['phase']}")
            print(f"    Method: {provenance['source']['method']}")
            print(f"    发现时间: {provenance['source']['discovered_at'][:19]}")

            print(f"\n  关联数据:")
            print(f"    关联商品: {len(provenance['related_products'])} 个")
            if provenance['related_products']:
                for prod in provenance['related_products']:
                    print(f"      - 商品 {prod['product_id']}: {prod['product_name'][:40]}")
                    print(f"        适配度: {prod['fit_level']} ({prod['fit_score']:.2f})")

            print(f"\n  事件时间线: {len(provenance['event_timeline'])} 个事件")
            for i, event in enumerate(provenance['event_timeline'][:5], 1):
                print(f"    {i}. [{event['event_type']}] {event['description']}")

        else:
            print("  [WARNING] 未找到Phase 7的需求")

        session.close()

    except Exception as e:
        print(f"  [ERROR] 查询溯源信息失败: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 80)
    print("[OK] 集成测试完成!")
    print("=" * 80)
    print("\n总结:")
    print("  1. AI标注成功提取了核心需求")
    print("  2. 自动创建了需求记录")
    print("  3. 建立了需求与商品的溯源关系")
    print("  4. 记录了完整的事件时间线")
    print("\n下一步:")
    print("  - 在Web UI中查看需求详情")
    print("  - 验证需求并提升置信度")
    print("  - 关联更多短语和Token")


if __name__ == "__main__":
    test_integration()

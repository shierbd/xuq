"""
溯源系统测试脚本

测试需求溯源系统的各项功能:
1. 创建需求并记录溯源
2. 建立关联关系
3. 更新置信度
4. 验证需求
5. 查询溯源信息
6. 统计分析

使用方法:
    python scripts/test_traceability_system.py
"""
import sys
from pathlib import Path
from pprint import pprint

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.demand_provenance_service import DemandProvenanceService


def test_create_demand():
    """测试1: 创建需求"""
    print("\n" + "=" * 80)
    print("测试1: 创建需求并记录溯源")
    print("=" * 80)

    with DemandProvenanceService() as service:
        demand_id = service.create_demand_with_provenance(
            title="在线表格协作工具",
            description="用户需要一个可以在线编辑、实时协作的表格工具",
            source_phase="phase7",
            source_method="product_reverse_engineering",
            source_data_ids=[1001, 1002, 1003],
            confidence_score=0.75,
            demand_type="tool",
            user_scenario="团队协作场景下需要共同编辑数据表格"
        )

        print(f"\n[OK] 成功创建需求 ID: {demand_id}")
        print(f"  - 标题: 在线表格协作工具")
        print(f"  - 来源: phase7 / product_reverse_engineering")
        print(f"  - 初始置信度: 0.75")

        return demand_id


def test_link_phrases(demand_id):
    """测试2: 关联短语"""
    print("\n" + "=" * 80)
    print("测试2: 建立需求与短语的关联")
    print("=" * 80)

    with DemandProvenanceService() as service:
        # 假设这些短语ID存在
        phrase_ids = [100, 101, 102]
        relevance_scores = [0.9, 0.85, 0.8]

        mapping_ids = service.link_demand_to_phrases(
            demand_id=demand_id,
            phrase_ids=phrase_ids,
            relevance_scores=relevance_scores,
            source="ai_inference",
            phase="phase7",
            method="semantic_matching"
        )

        print(f"\n[OK] 成功关联 {len(mapping_ids)} 个短语")
        for pid, score in zip(phrase_ids, relevance_scores):
            print(f"  - 短语 {pid}: 相关性 {score}")


def test_link_products(demand_id):
    """测试3: 关联商品"""
    print("\n" + "=" * 80)
    print("测试3: 建立需求与商品的关联")
    print("=" * 80)

    with DemandProvenanceService() as service:
        # 假设这些商品ID存在
        product_ids = [1001, 1002]
        fit_scores = [0.9, 0.85]
        fit_levels = ["high", "high"]

        mapping_ids = service.link_demand_to_products(
            demand_id=demand_id,
            product_ids=product_ids,
            fit_scores=fit_scores,
            fit_levels=fit_levels,
            source="product_analysis",
            phase="phase7",
            method="ai_annotation"
        )

        print(f"\n[OK] 成功关联 {len(mapping_ids)} 个商品")
        for pid, score, level in zip(product_ids, fit_scores, fit_levels):
            print(f"  - 商品 {pid}: 适配度 {level} ({score})")


def test_link_tokens(demand_id):
    """测试4: 关联Token"""
    print("\n" + "=" * 80)
    print("测试4: 建立需求与Token的关联")
    print("=" * 80)

    with DemandProvenanceService() as service:
        # 假设这些Token ID存在
        token_ids = [10, 11, 12]
        token_roles = ["core", "supporting", "context"]
        importance_scores = [0.95, 0.8, 0.6]

        mapping_ids = service.link_demand_to_tokens(
            demand_id=demand_id,
            token_ids=token_ids,
            token_roles=token_roles,
            importance_scores=importance_scores,
            source="token_extraction",
            phase="phase5",
            method="ngram_extraction"
        )

        print(f"\n[OK] 成功关联 {len(mapping_ids)} 个Token")
        for tid, role, score in zip(token_ids, token_roles, importance_scores):
            print(f"  - Token {tid}: 角色 {role}, 重要性 {score}")


def test_update_confidence(demand_id):
    """测试5: 更新置信度"""
    print("\n" + "=" * 80)
    print("测试5: 更新需求置信度")
    print("=" * 80)

    with DemandProvenanceService() as service:
        service.update_confidence_score(
            demand_id=demand_id,
            new_score=0.85,
            reason="AI验证通过,提升置信度",
            triggered_by="ai"
        )

        print(f"\n[OK] 成功更新置信度")
        print(f"  - 新置信度: 0.85")
        print(f"  - 原因: AI验证通过")


def test_validate_demand(demand_id):
    """测试6: 验证需求"""
    print("\n" + "=" * 80)
    print("测试6: 验证需求")
    print("=" * 80)

    with DemandProvenanceService() as service:
        service.validate_demand(
            demand_id=demand_id,
            validated_by="user",
            validation_notes="经过人工审核,需求描述准确,市场价值高"
        )

        print(f"\n[OK] 成功验证需求")
        print(f"  - 验证者: user")
        print(f"  - 备注: 经过人工审核,需求描述准确,市场价值高")


def test_get_provenance(demand_id):
    """测试7: 查询溯源信息"""
    print("\n" + "=" * 80)
    print("测试7: 查询需求的完整溯源信息")
    print("=" * 80)

    with DemandProvenanceService() as service:
        provenance = service.get_demand_provenance(demand_id)

        print(f"\n需求基本信息:")
        print(f"  ID: {provenance['demand']['demand_id']}")
        print(f"  标题: {provenance['demand']['title']}")
        print(f"  类型: {provenance['demand']['demand_type']}")
        print(f"  状态: {provenance['demand']['status']}")
        print(f"  已验证: {provenance['demand']['is_validated']}")

        print(f"\n来源信息:")
        print(f"  Phase: {provenance['source']['phase']}")
        print(f"  Method: {provenance['source']['method']}")
        print(f"  发现时间: {provenance['source']['discovered_at']}")
        print(f"  置信度: {provenance['source']['confidence_score']:.2f}")

        print(f"\n关联数据:")
        print(f"  短语: {len(provenance['related_phrases'])} 个")
        print(f"  商品: {len(provenance['related_products'])} 个")
        print(f"  Token: {len(provenance['related_tokens'])} 个")

        print(f"\n置信度演化:")
        for i, h in enumerate(provenance['confidence_history'], 1):
            print(f"  {i}. {h['timestamp'][:19]} - {h['score']:.2f} ({h['reason']})")

        print(f"\n事件时间线:")
        for i, e in enumerate(provenance['event_timeline'], 1):
            print(f"  {i}. [{e['event_type']}] {e['description']}")
            print(f"     时间: {e['timestamp'][:19]}, 触发者: {e['triggered_by']}")


def test_get_statistics():
    """测试8: 统计分析"""
    print("\n" + "=" * 80)
    print("测试8: 需求来源统计分析")
    print("=" * 80)

    with DemandProvenanceService() as service:
        stats = service.get_demands_by_source()

        print(f"\n按Phase分布:")
        for phase, data in stats['by_phase'].items():
            print(f"  {phase}: {data['count']} 个需求, 平均置信度 {data['avg_confidence']:.2f}")

        print(f"\n按Method分布:")
        for method, count in stats['by_method'].items():
            print(f"  {method}: {count} 个需求")

        print(f"\n按验证状态分布:")
        print(f"  已验证: {stats['by_validation_status']['validated']} 个")
        print(f"  未验证: {stats['by_validation_status']['unvalidated']} 个")


def main():
    """主函数"""
    print("=" * 80)
    print("需求溯源系统 - 功能测试")
    print("=" * 80)

    try:
        # 测试1: 创建需求
        demand_id = test_create_demand()

        # 测试2-4: 建立关联
        test_link_phrases(demand_id)
        test_link_products(demand_id)
        test_link_tokens(demand_id)

        # 测试5: 更新置信度
        test_update_confidence(demand_id)

        # 测试6: 验证需求
        test_validate_demand(demand_id)

        # 测试7: 查询溯源信息
        test_get_provenance(demand_id)

        # 测试8: 统计分析
        test_get_statistics()

        print("\n" + "=" * 80)
        print("[OK] 所有测试通过!")
        print("=" * 80)
        print(f"\n测试需求ID: {demand_id}")
        print("可以在数据库中查看完整的溯源记录")

    except Exception as e:
        print("\n" + "=" * 80)
        print("[ERROR] 测试失败!")
        print("=" * 80)
        print(f"\n错误信息: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

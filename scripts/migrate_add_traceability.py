"""
数据库迁移脚本 - 添加溯源系统

执行步骤:
1. 扩展demands表,添加溯源字段
2. 创建4个新表: demand_phrase_mappings, demand_product_mappings,
   demand_token_mappings, demand_provenance
3. 为现有数据补充默认溯源信息

使用方法:
    python scripts/migrate_add_traceability.py
    python scripts/migrate_add_traceability.py --yes  # 跳过确认
"""
import sys
import argparse
from pathlib import Path
from datetime import datetime
from decimal import Decimal

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from storage.models import get_engine, get_session
from storage.models_traceability import (
    DemandPhraseMapping,
    DemandProductMapping,
    DemandTokenMapping,
    DemandProvenance,
    Base
)
from sqlalchemy import text


def migrate_add_traceability_fields():
    """步骤1: 扩展demands表,添加溯源字段"""
    print("\n" + "=" * 80)
    print("步骤1: 扩展demands表,添加溯源字段")
    print("=" * 80)

    engine = get_engine()

    # 检查数据库类型
    is_sqlite = 'sqlite' in str(engine.url)

    alter_statements = [
        # 来源追踪字段
        "ALTER TABLE demands ADD COLUMN source_phase VARCHAR(20)",
        "ALTER TABLE demands ADD COLUMN source_method VARCHAR(50)",
        "ALTER TABLE demands ADD COLUMN source_data_ids TEXT",

        # 置信度追踪字段
        "ALTER TABLE demands ADD COLUMN confidence_score DECIMAL(3,2) DEFAULT 0.50",
        "ALTER TABLE demands ADD COLUMN confidence_history TEXT",

        # 时间追踪字段
        "ALTER TABLE demands ADD COLUMN discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP" if not is_sqlite else "ALTER TABLE demands ADD COLUMN discovered_at TIMESTAMP",
        "ALTER TABLE demands ADD COLUMN last_validated_at TIMESTAMP",
        "ALTER TABLE demands ADD COLUMN validation_count INTEGER DEFAULT 0",

        # 验证状态字段
        "ALTER TABLE demands ADD COLUMN is_validated BOOLEAN DEFAULT FALSE" if not is_sqlite else "ALTER TABLE demands ADD COLUMN is_validated INTEGER DEFAULT 0",
        "ALTER TABLE demands ADD COLUMN validated_by VARCHAR(100)",
        "ALTER TABLE demands ADD COLUMN validation_notes TEXT",
    ]

    index_statements = [
        "CREATE INDEX idx_demand_source_phase ON demands(source_phase)",
        "CREATE INDEX idx_demand_source_method ON demands(source_method)",
        "CREATE INDEX idx_demand_is_validated ON demands(is_validated)",
    ]

    with engine.connect() as conn:
        # 添加字段
        for i, stmt in enumerate(alter_statements, 1):
            try:
                print(f"  [{i}/{len(alter_statements)}] 执行: {stmt[:60]}...")
                conn.execute(text(stmt))
                conn.commit()
                print(f"      [OK] 成功")
            except Exception as e:
                if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                    print(f"      [SKIP] 字段已存在,跳过")
                else:
                    print(f"      [ERROR] 失败: {e}")
                    raise

        # 创建索引
        print(f"\n  创建索引...")
        for i, stmt in enumerate(index_statements, 1):
            try:
                print(f"  [{i}/{len(index_statements)}] 执行: {stmt[:60]}...")
                conn.execute(text(stmt))
                conn.commit()
                print(f"      [OK] 成功")
            except Exception as e:
                if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                    print(f"      [SKIP] 索引已存在,跳过")
                else:
                    print(f"      [ERROR] 失败: {e}")

    print("\n[OK] 步骤1完成: demands表扩展成功")


def create_traceability_tables():
    """步骤2: 创建4个新表"""
    print("\n" + "=" * 80)
    print("步骤2: 创建溯源系统表")
    print("=" * 80)

    engine = get_engine()

    tables = [
        "demand_phrase_mappings",
        "demand_product_mappings",
        "demand_token_mappings",
        "demand_provenance"
    ]

    print(f"\n  将创建以下表:")
    for table in tables:
        print(f"    - {table}")

    # 创建表
    Base.metadata.create_all(engine, tables=[
        DemandPhraseMapping.__table__,
        DemandProductMapping.__table__,
        DemandTokenMapping.__table__,
        DemandProvenance.__table__,
    ])

    print("\n[OK] 步骤2完成: 溯源系统表创建成功")


def backfill_existing_data():
    """步骤3: 为现有数据补充默认溯源信息"""
    print("\n" + "=" * 80)
    print("步骤3: 为现有数据补充默认溯源信息")
    print("=" * 80)

    session = get_session()

    try:
        # 查询需要补充溯源信息的需求
        result = session.execute(text("""
            SELECT demand_id, source_cluster_A, source_cluster_B, created_at
            FROM demands
            WHERE source_phase IS NULL
        """))

        demands_to_update = result.fetchall()

        if not demands_to_update:
            print("\n  没有需要更新的需求记录")
            return

        print(f"\n  找到 {len(demands_to_update)} 个需求需要补充溯源信息")

        # 批量更新
        for i, (demand_id, cluster_a, cluster_b, created_at) in enumerate(demands_to_update, 1):
            # 根据cluster信息推断来源
            if cluster_a is not None:
                source_phase = "phase4"  # 有聚类信息,来自Phase 4
                source_method = "keyword_clustering"
            else:
                source_phase = "manual"
                source_method = "manual_creation"

            # 更新需求
            session.execute(text("""
                UPDATE demands
                SET
                    source_phase = :phase,
                    source_method = :method,
                    confidence_score = 0.50,
                    confidence_history = :history,
                    discovered_at = :discovered_at,
                    validation_count = 0,
                    is_validated = 0
                WHERE demand_id = :demand_id
            """), {
                'phase': source_phase,
                'method': source_method,
                'history': f'[{{"score": 0.5, "timestamp": "{created_at.isoformat()}", "reason": "backfill_migration"}}]',
                'discovered_at': created_at,
                'demand_id': demand_id
            })

            # 创建溯源记录
            session.execute(text("""
                INSERT INTO demand_provenance
                (demand_id, event_type, event_description, new_value,
                 triggered_by_phase, triggered_by_method, triggered_by_user, created_at)
                VALUES
                (:demand_id, 'created', :description, :new_value,
                 :phase, :method, 'system', :created_at)
            """), {
                'demand_id': demand_id,
                'description': f'需求由{source_method}方法发现 (数据迁移补充)',
                'new_value': f'{{"source_phase": "{source_phase}", "source_method": "{source_method}"}}',
                'phase': source_phase,
                'method': source_method,
                'created_at': created_at
            })

            if i % 10 == 0:
                print(f"    进度: {i}/{len(demands_to_update)}")

        session.commit()
        print(f"\n[OK] 步骤3完成: 已为 {len(demands_to_update)} 个需求补充溯源信息")

    except Exception as e:
        session.rollback()
        print(f"\n[ERROR] 步骤3失败: {e}")
        raise
    finally:
        session.close()


def verify_migration():
    """步骤4: 验证迁移结果"""
    print("\n" + "=" * 80)
    print("步骤4: 验证迁移结果")
    print("=" * 80)

    session = get_session()

    try:
        # 检查demands表字段
        result = session.execute(text("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN source_phase IS NOT NULL THEN 1 ELSE 0 END) as with_phase,
                   SUM(CASE WHEN confidence_score IS NOT NULL THEN 1 ELSE 0 END) as with_confidence
            FROM demands
        """))

        row = result.fetchone()
        total, with_phase, with_confidence = row

        print(f"\n  demands表检查:")
        print(f"    总需求数: {total}")
        print(f"    有source_phase的: {with_phase} ({with_phase/total*100:.1f}%)")
        print(f"    有confidence_score的: {with_confidence} ({with_confidence/total*100:.1f}%)")

        # 检查新表
        tables_check = [
            ("demand_phrase_mappings", "需求-短语关联"),
            ("demand_product_mappings", "需求-商品关联"),
            ("demand_token_mappings", "需求-词根关联"),
            ("demand_provenance", "溯源审计记录")
        ]

        print(f"\n  新表检查:")
        for table_name, desc in tables_check:
            try:
                result = session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                count = result.fetchone()[0]
                print(f"    {desc} ({table_name}): {count} 条记录")
            except Exception as e:
                print(f"    {desc} ({table_name}): [ERROR] 表不存在或查询失败")

        print("\n[OK] 步骤4完成: 迁移验证通过")

    except Exception as e:
        print(f"\n[ERROR] 步骤4失败: {e}")
        raise
    finally:
        session.close()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='数据库迁移: 添加需求溯源系统')
    parser.add_argument('--yes', '-y', action='store_true', help='跳过确认提示')
    args = parser.parse_args()

    print("=" * 80)
    print("数据库迁移: 添加需求溯源系统")
    print("=" * 80)
    print("\n[警告] 此操作将修改数据库结构")
    print("   建议先备份数据库!")
    print()

    if not args.yes:
        response = input("是否继续? (yes/no): ").strip().lower()
        if response != 'yes':
            print("\n已取消迁移")
            return

    try:
        # 步骤1: 扩展demands表
        migrate_add_traceability_fields()

        # 步骤2: 创建新表
        create_traceability_tables()

        # 步骤3: 补充现有数据
        backfill_existing_data()

        # 步骤4: 验证迁移
        verify_migration()

        print("\n" + "=" * 80)
        print("[成功] 迁移完成!")
        print("=" * 80)
        print("\n下一步:")
        print("  1. 检查数据库中的新表和字段")
        print("  2. 运行测试确保功能正常")
        print("  3. 开始使用溯源功能")

    except Exception as e:
        print("\n" + "=" * 80)
        print("[失败] 迁移失败!")
        print("=" * 80)
        print(f"\n错误信息: {e}")
        print("\n建议:")
        print("  1. 检查错误信息")
        print("  2. 恢复数据库备份")
        print("  3. 修复问题后重新运行")
        sys.exit(1)


if __name__ == "__main__":
    main()

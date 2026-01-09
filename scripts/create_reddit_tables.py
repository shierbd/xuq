"""
创建Reddit板块分析功能的数据库表

运行方式：
    python scripts/create_reddit_tables.py
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from storage.models import (
    get_engine,
    get_session,
    Base,
    RedditSubreddit,
    AIPromptConfig
)
from decimal import Decimal


def create_reddit_tables():
    """创建Reddit相关的数据库表"""
    print("开始创建Reddit相关数据表...")

    engine = get_engine()

    # 只创建Reddit相关的表
    RedditSubreddit.__table__.create(engine, checkfirst=True)
    AIPromptConfig.__table__.create(engine, checkfirst=True)

    print("[OK] 数据表创建成功:")
    print("  - reddit_subreddits")
    print("  - ai_prompt_configs")


def insert_default_config():
    """插入默认的AI提示词配置"""
    print("\n开始插入默认配置...")

    session = get_session()

    try:
        # 检查是否已存在默认配置
        existing = session.query(AIPromptConfig).filter_by(
            config_name="Reddit板块分析默认配置"
        ).first()

        if existing:
            print("[WARN] 默认配置已存在，跳过插入")
            return

        # 创建默认配置
        default_config = AIPromptConfig(
            config_name="Reddit板块分析默认配置",
            config_type="reddit_analysis",
            prompt_template="""请分析以下Reddit板块信息，生成3个中文标签和重要性评分(1-5)：

板块名称：{name}
板块描述：{description}
订阅人数：{subscribers}

要求：
1. 生成3个简洁的中文标签（每个2-4个字）
2. 评估重要性评分（1=不重要，5=非常重要）
3. 返回JSON格式：{{"tag1": "标签1", "tag2": "标签2", "tag3": "标签3", "importance_score": 评分, "confidence": 置信度}}""",
            system_message="你是一个专业的Reddit社区分析专家，擅长理解社区主题和评估其重要性。",
            temperature=Decimal("0.7"),
            max_tokens=500,
            is_active=True,
            is_default=True,
            description="默认的Reddit板块分析配置，用于生成标签和重要性评分",
            created_by="system"
        )

        session.add(default_config)
        session.commit()

        print("[OK] 默认配置插入成功:")
        print(f"  - 配置ID: {default_config.config_id}")
        print(f"  - 配置名称: {default_config.config_name}")

    except Exception as e:
        session.rollback()
        print(f"[ERROR] 插入默认配置失败: {str(e)}")
        raise
    finally:
        session.close()


def main():
    """主函数"""
    print("=" * 60)
    print("Reddit板块分析功能 - 数据库初始化")
    print("=" * 60)

    try:
        # 1. 创建表
        create_reddit_tables()

        # 2. 插入默认配置
        insert_default_config()

        print("\n" + "=" * 60)
        print("[OK] 数据库初始化完成！")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] 初始化失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())

"""
导入审核后的需求卡片
从CSV文件读取人工审核后的需求状态和评分，更新数据库

运行方式:
    python scripts/import_demand_reviews.py [--file demands_reviewed.csv]

CSV格式要求:
    demand_id,title,status,business_value,notes
"""
import sys
import argparse
import pandas as pd
from pathlib import Path

# 设置UTF-8编码输出（Windows兼容）
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import OUTPUT_DIR
from storage.repository import DemandRepository
from utils.logger import get_logger
from utils.exceptions import DataValidationException

logger = get_logger(__name__)


def validate_csv(df: pd.DataFrame) -> bool:
    """验证CSV格式"""
    required_columns = ['demand_id']

    for col in required_columns:
        if col not in df.columns:
            raise DataValidationException(f"CSV缺少必需列: {col}")

    # 验证demand_id是否为整数
    if not pd.api.types.is_integer_dtype(df['demand_id']):
        try:
            df['demand_id'] = df['demand_id'].astype(int)
        except:
            raise DataValidationException("demand_id列必须是整数")

    logger.info(f"CSV验证通过: {len(df)} 条记录")
    return True


def import_reviews(csv_file: Path):
    """导入审核结果"""
    logger.info("="*70)
    logger.info("Phase 4: 导入需求审核结果")
    logger.info("="*70)

    # 读取CSV
    if not csv_file.exists():
        raise FileNotFoundError(f"文件不存在: {csv_file}")

    logger.info(f"读取CSV文件: {csv_file}")
    df = pd.read_csv(csv_file, encoding='utf-8')
    logger.info(f"共读取 {len(df)} 条记录")

    # 验证
    validate_csv(df)

    # 连接数据库
    with DemandRepository() as repo:
        updated_count = 0
        skipped_count = 0

        for idx, row in df.iterrows():
            demand_id = int(row['demand_id'])

            # 检查需求是否存在
            demand = repo.session.query(repo.model).filter_by(demand_id=demand_id).first()
            if not demand:
                logger.warning(f"需求ID {demand_id} 不存在，跳过")
                skipped_count += 1
                continue

            # 更新字段
            updated = False

            if 'status' in row and pd.notna(row['status']):
                status = str(row['status']).strip()
                if status in ['idea', 'validated', 'in_progress', 'archived']:
                    demand.status = status
                    updated = True

            if 'business_value' in row and pd.notna(row['business_value']):
                value = str(row['business_value']).strip()
                if value in ['high', 'medium', 'low', 'unknown']:
                    demand.business_value = value
                    updated = True

            if 'notes' in row and pd.notna(row['notes']):
                demand.notes = str(row['notes'])
                updated = True

            if updated:
                repo.session.commit()
                updated_count += 1
                logger.info(f"更新需求 {demand_id}: {demand.title}")

        logger.info("="*70)
        logger.info(f"导入完成: 更新 {updated_count} 条，跳过 {skipped_count} 条")
        logger.info("="*70)


def main():
    parser = argparse.ArgumentParser(description='导入需求审核结果')
    parser.add_argument(
        '--file',
        type=str,
        default='demands_reviewed.csv',
        help='审核后的CSV文件名（默认: demands_reviewed.csv）'
    )

    args = parser.parse_args()

    csv_file = OUTPUT_DIR / args.file

    try:
        import_reviews(csv_file)
    except Exception as e:
        logger.error(f"导入失败: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

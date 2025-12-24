"""
导入审核后的Token分类
从CSV文件读取人工审核后的Token验证结果，更新数据库

运行方式:
    python scripts/import_token_reviews.py [--file tokens_reviewed.csv]

CSV格式要求:
    token_text,token_type,verified,notes
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

from config.settings import OUTPUT_DIR, TOKEN_TYPES
from storage.repository import TokenRepository
from utils.logger import get_logger
from utils.exceptions import DataValidationException

logger = get_logger(__name__)


def validate_csv(df: pd.DataFrame) -> bool:
    """验证CSV格式"""
    required_columns = ['token_text']

    for col in required_columns:
        if col not in df.columns:
            raise DataValidationException(f"CSV缺少必需列: {col}")

    # 验证token_type是否有效
    if 'token_type' in df.columns:
        invalid_types = df[~df['token_type'].isin(TOKEN_TYPES + [''])]['token_type'].unique()
        if len(invalid_types) > 0:
            logger.warning(f"发现无效的token_type: {invalid_types}，将被忽略")

    # 验证verified是否为布尔值
    if 'verified' in df.columns:
        # 转换为布尔值
        df['verified'] = df['verified'].map({
            'True': True, 'true': True, 'TRUE': True, '1': True, 1: True,
            'False': False, 'false': False, 'FALSE': False, '0': False, 0: False,
            True: True, False: False
        })

    logger.info(f"CSV验证通过: {len(df)} 条记录")
    return True


def import_reviews(csv_file: Path):
    """导入审核结果"""
    logger.info("="*70)
    logger.info("Phase 5: 导入Token审核结果")
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
    with TokenRepository() as repo:
        updated_count = 0
        created_count = 0
        skipped_count = 0

        for idx, row in df.iterrows():
            token_text = str(row['token_text']).strip().lower()

            if not token_text:
                skipped_count += 1
                continue

            # 检查Token是否存在
            token = repo.session.query(repo.model).filter_by(token_text=token_text).first()

            # 准备更新数据
            update_data = {}

            if 'token_type' in row and pd.notna(row['token_type']):
                token_type = str(row['token_type']).strip()
                if token_type in TOKEN_TYPES:
                    update_data['token_type'] = token_type

            if 'verified' in row and pd.notna(row['verified']):
                update_data['verified'] = bool(row['verified'])

            if 'notes' in row and pd.notna(row['notes']):
                update_data['notes'] = str(row['notes'])

            if token:
                # 更新现有Token
                if update_data:
                    for key, value in update_data.items():
                        setattr(token, key, value)
                    repo.session.commit()
                    updated_count += 1
                    logger.info(f"更新Token: {token_text} -> {token.token_type}")
            else:
                # 创建新Token（如果提供了token_type）
                if 'token_type' in update_data:
                    repo.create_token(
                        token_text=token_text,
                        token_type=update_data['token_type'],
                        in_phrase_count=0,
                        first_seen_round=1,
                        verified=update_data.get('verified', False),
                        notes=update_data.get('notes', '')
                    )
                    created_count += 1
                    logger.info(f"创建新Token: {token_text} -> {update_data['token_type']}")
                else:
                    logger.warning(f"Token {token_text} 不存在且未提供token_type，跳过")
                    skipped_count += 1

        logger.info("="*70)
        logger.info(f"导入完成: 更新 {updated_count} 条，创建 {created_count} 条，跳过 {skipped_count} 条")
        logger.info("="*70)


def main():
    parser = argparse.ArgumentParser(description='导入Token审核结果')
    parser.add_argument(
        '--file',
        type=str,
        default='tokens_reviewed.csv',
        help='审核后的CSV文件名（默认: tokens_reviewed.csv）'
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

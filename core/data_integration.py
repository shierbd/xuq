"""
Phase 1: 数据整合与清洗模块
功能：从原始CSV/Excel文件读取数据，清洗后准备导入数据库
"""
import pandas as pd
import re
from pathlib import Path
from typing import List, Dict, Optional
from tqdm import tqdm
import chardet


def detect_file_encoding(file_path: Path) -> str:
    """
    自动检测文件编码

    Args:
        file_path: 文件路径

    Returns:
        检测到的编码名称
    """
    with open(file_path, 'rb') as f:
        raw_data = f.read(10000)  # 读取前10000字节
        result = chardet.detect(raw_data)
        encoding = result['encoding']

        # 处理常见的编码映射
        if encoding and encoding.lower() in ['gb2312', 'gbk', 'gb18030']:
            return 'gbk'
        elif encoding and 'utf' in encoding.lower():
            return 'utf-8-sig'
        else:
            return encoding or 'utf-8-sig'


class DataIntegration:
    """数据整合与清洗类"""

    def __init__(self, raw_data_dir: Path):
        """
        初始化数据整合器

        Args:
            raw_data_dir: 原始数据目录路径
        """
        self.raw_data_dir = raw_data_dir

        # 自动发现数据文件（支持灵活的文件名）
        self.source_files = self._discover_data_files()

    def _discover_data_files(self) -> Dict[str, any]:
        """
        自动发现原始数据文件

        Returns:
            数据源文件路径字典，值可以是单个Path或Path列表
        """
        discovered = {}

        # SEMRUSH数据：在 raw/semrush/ 目录下查找CSV文件
        # 优先使用 *_converted.csv，如果没有则使用 *_processed.csv
        semrush_dir = self.raw_data_dir / 'semrush'
        if semrush_dir.exists():
            # 优先查找converted文件
            converted_files = list(semrush_dir.glob('*_converted.csv'))
            if converted_files:
                discovered['semrush'] = converted_files[0]  # 使用转换后的文件
            else:
                # 否则查找processed文件
                processed_files = list(semrush_dir.glob('*_processed.csv'))
                if processed_files:
                    discovered['semrush'] = processed_files[0]

        # 下拉词数据：在 raw/dropdown/ 目录下查找CSV文件
        # 优先使用 *_converted.csv
        dropdown_dir = self.raw_data_dir / 'dropdown'
        if dropdown_dir.exists():
            converted_files = list(dropdown_dir.glob('*_converted.csv'))
            if converted_files:
                discovered['dropdown'] = converted_files[0]
            else:
                processed_files = list(dropdown_dir.glob('*_processed.csv'))
                if processed_files:
                    discovered['dropdown'] = processed_files[0]

        # 相关搜索数据：在 raw/related_search/ 目录下查找CSV/Excel文件
        # 优先使用 *_converted.csv
        related_dir = self.raw_data_dir / 'related_search'
        if related_dir.exists():
            converted_files = list(related_dir.glob('*_converted.csv'))
            if converted_files:
                discovered['related_search'] = converted_files[0]
            else:
                processed_files = list(related_dir.glob('*_processed.csv'))
                if processed_files:
                    discovered['related_search'] = processed_files[0]

        # 如果没有子目录，尝试在raw目录直接查找
        if not discovered:
            for pattern in ['*semrush*.csv', '*dropdown*.csv', '*related*.csv']:
                files = list(self.raw_data_dir.glob(pattern))
                if files:
                    source_type = pattern.replace('*', '').replace('.csv', '')
                    discovered[source_type] = files if len(files) > 1 else files[0]

        return discovered

    def load_semrush_data(self) -> pd.DataFrame:
        """
        加载SEMRUSH数据（支持单文件或多文件合并）

        Returns:
            DataFrame with columns: phrase, seed_word, source_type, frequency, volume
        """
        if 'semrush' not in self.source_files:
            logger.warning("SEMRUSH文件不存在，跳过")
            return pd.DataFrame()

        file_paths = self.source_files['semrush']

        # 支持单文件或多文件
        if not isinstance(file_paths, list):
            file_paths = [file_paths]

        all_dfs = []

        for file_path in file_paths:
            if not file_path.exists():
                logger.warning(f"文件不存在，跳过: {file_path.name}")
                continue

            logger.info(f"加载SEMRUSH数据: {file_path.name}")

            # 自动检测编码
            encoding = detect_file_encoding(file_path)
            logger.info(f"   检测到文件编码: {encoding}")

            try:
                df = pd.read_csv(file_path, encoding=encoding)
            except Exception as e:
                logger.warning(f"   使用 {encoding} 编码失败，尝试 utf-8-sig...")
                try:
                    df = pd.read_csv(file_path, encoding='utf-8-sig')
                except:
                    logger.warning(f"   使用 utf-8-sig 失败，尝试 gbk...")
                    try:
                        df = pd.read_csv(file_path, encoding='gbk')
                    except Exception as e2:
                        logger.error(f"   加载失败，跳过文件: {file_path.name}, 错误: {e2}")
                        continue

            # 选择需要的列
            required_cols = ['phrase', 'seed_word', 'source_type', 'frequency', 'volume']
            available_cols = [col for col in required_cols if col in df.columns]
            df = df[available_cols].copy()

            # 填充缺失的volume（如果没有volume列，使用frequency）
            if 'volume' not in df.columns:
                df['volume'] = df.get('frequency', 0)

            # 确保source_type正确
            df['source_type'] = 'semrush'

            logger.info(f"   成功加载 {len(df)} 条记录")
            all_dfs.append(df)

        if not all_dfs:
            logger.warning("没有成功加载任何SEMRUSH数据")
            return pd.DataFrame()

        # 合并所有数据
        combined_df = pd.concat(all_dfs, ignore_index=True)
        logger.info(f"SEMRUSH数据合并完成，总计 {len(combined_df)} 条记录（来自 {len(all_dfs)} 个文件）")

        return combined_df

    def load_dropdown_data(self) -> pd.DataFrame:
        """
        加载下拉词数据（支持单文件或多文件合并）

        Returns:
            DataFrame with columns: phrase, seed_word, source_type, frequency
        """
        if 'dropdown' not in self.source_files:
            logger.warning("下拉词文件不存在，跳过")
            return pd.DataFrame()

        file_paths = self.source_files['dropdown']

        # 支持单文件或多文件
        if not isinstance(file_paths, list):
            file_paths = [file_paths]

        all_dfs = []

        for file_path in file_paths:
            if not file_path.exists():
                logger.warning(f"文件不存在，跳过: {file_path.name}")
                continue

            logger.info(f"加载下拉词数据: {file_path.name}")

            # 自动检测编码
            encoding = detect_file_encoding(file_path)
            logger.info(f"   检测到文件编码: {encoding}")

            try:
                df = pd.read_csv(file_path, encoding=encoding)
            except Exception as e:
                logger.warning(f"   使用 {encoding} 编码失败，尝试其他编码...")
                try:
                    df = pd.read_csv(file_path, encoding='utf-8-sig')
                except:
                    try:
                        df = pd.read_csv(file_path, encoding='gbk')
                    except Exception as e2:
                        logger.error(f"   加载失败，跳过文件: {file_path.name}, 错误: {e2}")
                        continue

            # 选择需要的列
            required_cols = ['phrase', 'seed_word', 'source_type', 'frequency']
            available_cols = [col for col in required_cols if col in df.columns]
            df = df[available_cols].copy()

            # 添加volume列（下拉词没有volume，设为0）
            df['volume'] = 0

            # 确保source_type正确
            df['source_type'] = 'dropdown'

            logger.info(f"   成功加载 {len(df)} 条记录")
            all_dfs.append(df)

        if not all_dfs:
            logger.warning("没有成功加载任何下拉词数据")
            return pd.DataFrame()

        # 合并所有数据（如果有多个文件）
        if len(all_dfs) > 1:
            combined_df = pd.concat(all_dfs, ignore_index=True)
            logger.info(f"下拉词数据合并完成，总计 {len(combined_df)} 条记录（来自 {len(all_dfs)} 个文件）")
            return combined_df
        else:
            logger.info(f"成功加载 {len(all_dfs[0])} 条下拉词记录")
            return all_dfs[0]

    def load_related_search_data(self) -> pd.DataFrame:
        """
        加载相关搜索数据（支持单文件或多文件合并）

        Returns:
            DataFrame with columns: phrase, seed_word, source_type, frequency
        """
        if 'related_search' not in self.source_files:
            logger.warning("相关搜索文件不存在，跳过")
            return pd.DataFrame()

        file_paths = self.source_files['related_search']

        # 支持单文件或多文件
        if not isinstance(file_paths, list):
            file_paths = [file_paths]

        all_dfs = []

        for file_path in file_paths:
            if not file_path.exists():
                logger.warning(f"文件不存在，跳过: {file_path.name}")
                continue

            logger.info(f"加载相关搜索数据: {file_path.name}")

            # 支持Excel和CSV格式
            if file_path.suffix.lower() in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            else:
                # 自动检测编码
                encoding = detect_file_encoding(file_path)
                logger.info(f"   检测到文件编码: {encoding}")

                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                except Exception as e:
                    logger.warning(f"   使用 {encoding} 编码失败，尝试其他编码...")
                    try:
                        df = pd.read_csv(file_path, encoding='utf-8-sig')
                    except:
                        try:
                            df = pd.read_csv(file_path, encoding='gbk')
                        except Exception as e2:
                            logger.error(f"   加载失败，跳过文件: {file_path.name}, 错误: {e2}")
                            continue

            # 选择需要的列
            required_cols = ['phrase', 'seed_word', 'source_type', 'frequency']
            available_cols = [col for col in required_cols if col in df.columns]
            df = df[available_cols].copy()

            # 添加volume列（相关搜索没有volume，设为0）
            df['volume'] = 0

            # 确保source_type正确
            df['source_type'] = 'related_search'

            logger.info(f"   成功加载 {len(df)} 条记录")
            all_dfs.append(df)

        if not all_dfs:
            logger.warning("没有成功加载任何相关搜索数据")
            return pd.DataFrame()

        # 合并所有数据（如果有多个文件）
        if len(all_dfs) > 1:
            combined_df = pd.concat(all_dfs, ignore_index=True)
            logger.info(f"相关搜索数据合并完成，总计 {len(combined_df)} 条记录（来自 {len(all_dfs)} 个文件）")
            return combined_df
        else:
            logger.info(f"成功加载 {len(all_dfs[0])} 条相关搜索记录")
            return all_dfs[0]

    def clean_phrase(self, phrase: str) -> Optional[str]:
        """
        清洗单个短语

        Args:
            phrase: 原始短语

        Returns:
            清洗后的短语，如果无效则返回None
        """
        if pd.isna(phrase) or not isinstance(phrase, str):
            return None

        # 转小写
        phrase = phrase.lower().strip()

        # 移除多余空格
        phrase = re.sub(r'\s+', ' ', phrase)

        # 长度检查（1-255字符）
        if len(phrase) < 1 or len(phrase) > 255:
            return None

        # 移除纯数字短语
        if phrase.isdigit():
            return None

        # 移除特殊字符过多的短语（保留字母、数字、空格、连字符）
        valid_chars = re.findall(r'[a-z0-9\s\-]', phrase)
        if len(valid_chars) / len(phrase) < 0.5:  # 有效字符少于50%
            return None

        return phrase

    def clean_seed_word(self, seed_word: str) -> str:
        """
        清洗种子词

        Args:
            seed_word: 原始种子词

        Returns:
            清洗后的种子词
        """
        if pd.isna(seed_word) or not isinstance(seed_word, str):
            return 'unknown'

        seed_word = seed_word.lower().strip()
        if len(seed_word) == 0 or len(seed_word) > 100:
            return 'unknown'

        return seed_word

    def merge_and_clean(self, round_id: int = 1, sources: list = None) -> pd.DataFrame:
        """
        合并所有数据源并清洗

        Args:
            round_id: 数据轮次ID（默认为1）
            sources: 要导入的数据源列表，如 ['semrush', 'dropdown']，None表示全部导入

        Returns:
            清洗后的DataFrame，包含以下列：
            - phrase: 短语（唯一）
            - seed_word: 种子词
            - source_type: 数据源类型
            - frequency: 频次
            - volume: 搜索量
            - first_seen_round: 首次出现轮次
        """
        logger.info("\n" + "="*60)
        logger.info("开始数据整合与清洗")
        logger.info("="*60)

        # 1. 根据sources参数决定加载哪些数据源
        all_data = []

        # 如果未指定sources，加载所有可用数据源
        if sources is None:
            sources = ['semrush', 'dropdown', 'related_search']

        # 加载指定的数据源
        if 'semrush' in sources:
            semrush_df = self.load_semrush_data()
            if not semrush_df.empty:
                all_data.append(semrush_df)

        if 'dropdown' in sources:
            dropdown_df = self.load_dropdown_data()
            if not dropdown_df.empty:
                all_data.append(dropdown_df)

        if 'related_search' in sources:
            related_df = self.load_related_search_data()
            if not related_df.empty:
                all_data.append(related_df)

        # 2. 合并数据
        logger.info("\n合并数据源...")
        logger.info(f"   准备合并的数据源: {', '.join(sources)}")

        if not all_data:
            logger.error("❌ 没有可用的数据源！")
            return pd.DataFrame()

        df = pd.concat(all_data, ignore_index=True)
        logger.info(f"合并后总记录数: {len(df)}")
        logger.info("\n清洗数据...")
        logger.info("  - 清洗短语...")
        df['phrase_cleaned'] = df['phrase'].apply(self.clean_phrase)
        df = df[df['phrase_cleaned'].notna()].copy()
        df['phrase'] = df['phrase_cleaned']
        df.drop('phrase_cleaned', axis=1, inplace=True)
        logger.info(f"    剩余 {len(df)} 条有效记录")
        logger.info("  - 清洗种子词...")
        df['seed_word'] = df['seed_word'].apply(self.clean_seed_word)

        # 确保数值列正确
        df['frequency'] = pd.to_numeric(df['frequency'], errors='coerce').fillna(1).astype(int)
        df['volume'] = pd.to_numeric(df['volume'], errors='coerce').fillna(0).astype(int)

        # 4. 去重并聚合
        logger.info("\n去重并聚合...")
        df_grouped = df.groupby('phrase').agg({
            'seed_word': 'first',  # 取第一个种子词
            'source_type': 'first',  # 取第一个数据源
            'frequency': 'sum',  # 频次求和
            'volume': 'max',  # 搜索量取最大值
        }).reset_index()

        logger.info(f"去重后记录数: {len(df_grouped)}")
        df_grouped['first_seen_round'] = round_id

        # 6. 最终排序
        df_grouped = df_grouped.sort_values('frequency', ascending=False).reset_index(drop=True)

        # 7. 统计信息
        logger.info("\n" + "="*60)
        logger.info("数据统计")
        logger.info("="*60)
        logger.info(f"总记录数: {len(df_grouped)}")
        logger.info(f"\n按数据源分布:")
        logger.info(df_grouped['source_type'].value_counts())
        logger.info(f"\n频次统计:")
        logger.info(f"  最大值: {df_grouped['frequency'].max()}")
        logger.info(f"  最小值: {df_grouped['frequency'].min()}")
        logger.info(f"  平均值: {df_grouped['frequency'].mean():.2f}")
        logger.info(f"  中位数: {df_grouped['frequency'].median():.2f}")
        logger.info(f"\n搜索量统计:")
        logger.info(f"  有搜索量的记录: {(df_grouped['volume'] > 0).sum()}")
        logger.info(f"  最大搜索量: {df_grouped['volume'].max()}")
        logger.info("="*60)

        return df_grouped

    def prepare_for_database(self, df: pd.DataFrame) -> List[Dict]:
        """
        将DataFrame转换为适合数据库插入的字典列表

        Args:
            df: 清洗后的DataFrame

        Returns:
            字典列表，每个字典对应一条数据库记录
        """
        logger.info("\n准备数据库插入格式...")

        records = []
        for _, row in tqdm(df.iterrows(), total=len(df), desc="转换记录"):
            record = {
                'phrase': row['phrase'],
                'seed_word': row['seed_word'],
                'source_type': row['source_type'],
                'frequency': int(row['frequency']),
                'volume': int(row['volume']),
                'first_seen_round': int(row['first_seen_round']),
                # 以下字段使用默认值
                'cluster_id_A': None,
                'cluster_id_B': None,
                'mapped_demand_id': None,
                'processed_status': 'unseen',
            }
            records.append(record)

        logger.info(f"准备完成，共 {len(records)} 条记录")
        return records


from utils.logger import get_logger

logger = get_logger(__name__)


def test_data_integration():
    """测试数据整合功能"""
    from config.settings import RAW_DATA_DIR

    integrator = DataIntegration(RAW_DATA_DIR)
    df = integrator.merge_and_clean(round_id=1)

    if not df.empty:
        logger.info("\n✅ 数据整合测试成功！")
        logger.info(f"\n前5条记录:")
        logger.info(df.head())
        output_path = RAW_DATA_DIR.parent / 'processed' / 'integrated_data.csv'
        output_path.parent.mkdir(exist_ok=True)
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        logger.info(f"\n💾 测试数据已保存到: {output_path}")
    else:
        logger.error("\n❌ 数据整合失败！")


if __name__ == "__main__":
    test_data_integration()

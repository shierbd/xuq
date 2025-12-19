"""
整合三种数据源的脚本
将SEMRUSH、下拉词、相关搜索整合为统一格式
"""
import pandas as pd
from pathlib import Path
import glob

def process_semrush_data(folder_path, output_file):
    """
    处理SEMRUSH导出的数据

    输出格式：
    - phrase: 关键词短语
    - seed_word: 种子词
    - source_type: 'semrush'
    - frequency: Volume (搜索量)
    - intent: Intent
    - volume: Volume
    - keyword_difficulty: Keyword Difficulty
    - cpc: CPC (USD)
    """
    print("Processing SEMRUSH data...")

    all_data = []
    csv_files = list(Path(folder_path).glob("*.csv"))

    for i, file_path in enumerate(csv_files, 1):
        print(f"  [{i}/{len(csv_files)}] {file_path.name}")

        try:
            # 从文件名提取种子词
            seed_word = file_path.stem.split('_')[0]

            # 读取CSV
            df = pd.read_csv(file_path)

            # 标准化字段
            df_processed = pd.DataFrame({
                'phrase': df['Keyword'],
                'seed_word': seed_word,
                'source_type': 'semrush',
                'frequency': df['Volume'],
                'intent': df.get('Intent', ''),
                'volume': df['Volume'],
                'keyword_difficulty': df.get('Keyword Difficulty', 0),
                'cpc': df.get('CPC (USD)', 0.0)
            })

            all_data.append(df_processed)

        except Exception as e:
            print(f"    Error: {e}")
            continue

    # 合并所有数据
    if all_data:
        df_merged = pd.concat(all_data, ignore_index=True)

        # 保存
        df_merged.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\nSEMRUSH data saved: {output_file}")
        print(f"  Total rows: {len(df_merged):,}")
        print(f"  Seed words: {df_merged['seed_word'].nunique()}")

        return df_merged

    return None

def process_dropdown_data(folder_path, output_file):
    """
    处理Google下拉词数据

    输出格式：
    - phrase: 下拉词建议
    - seed_word: 种子关键词
    - source_type: 'dropdown'
    - frequency: 1 (默认)
    - expand_type: 扩展类型
    - expand_word: 扩展词
    - rank: 排名
    """
    print("\nProcessing Dropdown data...")

    all_data = []
    csv_files = list(Path(folder_path).glob("*.csv"))

    for i, file_path in enumerate(csv_files, 1):
        print(f"  [{i}/{len(csv_files)}] {file_path.name}")

        try:
            # 读取CSV
            df = pd.read_csv(file_path, encoding='utf-8-sig')

            # 标准化字段
            df_processed = pd.DataFrame({
                'phrase': df['下拉词建议'],
                'seed_word': df['种子关键词'],
                'source_type': 'dropdown',
                'frequency': 1,  # 下拉词没有搜索量，默认为1
                'expand_type': df.get('扩展类型', 'none'),
                'expand_word': df.get('扩展词', ''),
                'rank': df.get('排名', 0)
            })

            all_data.append(df_processed)

        except Exception as e:
            print(f"    Error: {e}")
            continue

    # 合并所有数据
    if all_data:
        df_merged = pd.concat(all_data, ignore_index=True)

        # 保存
        df_merged.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\nDropdown data saved: {output_file}")
        print(f"  Total rows: {len(df_merged):,}")
        print(f"  Seed words: {df_merged['seed_word'].nunique()}")

        return df_merged

    return None

def process_related_search(file_path, output_file):
    """
    处理Google相关搜索数据

    输出格式：
    - phrase: 相关搜索词
    - seed_word: 'unknown' (无法确定)
    - source_type: 'related_search'
    - frequency: 1 (默认)
    """
    print("\nProcessing Related Search data...")

    try:
        # 读取Excel
        df = pd.read_excel(file_path)

        # 获取第一列（相关搜索词）
        col_name = df.columns[0]

        # 标准化字段
        df_processed = pd.DataFrame({
            'phrase': df[col_name],
            'seed_word': 'unknown',  # 无法从数据中确定种子词
            'source_type': 'related_search',
            'frequency': 1  # 没有搜索量，默认为1
        })

        # 保存
        df_processed.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\nRelated Search data saved: {output_file}")
        print(f"  Total rows: {len(df_processed):,}")

        return df_processed

    except Exception as e:
        print(f"  Error: {e}")
        return None

def merge_all_sources(semrush_file, dropdown_file, related_file, output_file):
    """合并三种数据源"""
    print("\n" + "=" * 80)
    print("Merging all sources...")
    print("=" * 80)

    all_dfs = []

    # 读取SEMRUSH数据
    if Path(semrush_file).exists():
        df_semrush = pd.read_csv(semrush_file, encoding='utf-8-sig')
        print(f"SEMRUSH: {len(df_semrush):,} rows")
        all_dfs.append(df_semrush)

    # 读取下拉词数据
    if Path(dropdown_file).exists():
        df_dropdown = pd.read_csv(dropdown_file, encoding='utf-8-sig')
        print(f"Dropdown: {len(df_dropdown):,} rows")
        all_dfs.append(df_dropdown)

    # 读取相关搜索数据
    if Path(related_file).exists():
        df_related = pd.read_csv(related_file, encoding='utf-8-sig')
        print(f"Related Search: {len(df_related):,} rows")
        all_dfs.append(df_related)

    if not all_dfs:
        print("No data to merge!")
        return None

    # 合并
    df_merged = pd.concat(all_dfs, ignore_index=True)

    # 统一字段顺序
    core_columns = ['phrase', 'seed_word', 'source_type', 'frequency']
    other_columns = [col for col in df_merged.columns if col not in core_columns]
    df_merged = df_merged[core_columns + other_columns]

    # 去重（保留频次最高的）
    print(f"\nBefore dedup: {len(df_merged):,} rows")
    df_merged = df_merged.sort_values('frequency', ascending=False)
    df_merged = df_merged.drop_duplicates(subset=['phrase'], keep='first')
    print(f"After dedup: {len(df_merged):,} rows")

    # 保存
    df_merged.to_csv(output_file, index=False, encoding='utf-8-sig')

    print(f"\n[SUCCESS] Merged file saved: {output_file}")
    print(f"  Total phrases: {len(df_merged):,}")
    print(f"  Unique seed words: {df_merged['seed_word'].nunique()}")
    print(f"\nSource distribution:")
    print(df_merged['source_type'].value_counts().to_string())

    return df_merged

def main():
    """主函数"""
    print("=" * 80)
    print("Data Integration Script")
    print("=" * 80)

    # 路径配置
    base_path = Path(r"D:\xiangmu\词根聚类需求挖掘")
    raw_path = base_path / "原始词"
    output_path = base_path / "data" / "raw"

    # 确保输出目录存在
    output_path.mkdir(parents=True, exist_ok=True)

    # 处理三种数据源
    df_semrush = process_semrush_data(
        raw_path / "sm导出词",
        output_path / "semrush_processed.csv"
    )

    df_dropdown = process_dropdown_data(
        raw_path / "下拉词",
        output_path / "dropdown_processed.csv"
    )

    df_related = process_related_search(
        raw_path / "相关搜索.xlsx",
        output_path / "related_search_processed.csv"
    )

    # 合并所有数据
    df_merged = merge_all_sources(
        output_path / "semrush_processed.csv",
        output_path / "dropdown_processed.csv",
        output_path / "related_search_processed.csv",
        output_path / "merged_keywords_all.csv"
    )

    print("\n" + "=" * 80)
    print("[COMPLETED] Data integration finished!")
    print("=" * 80)
    print(f"\nNext steps:")
    print(f"  1. Check: {output_path / 'merged_keywords_all.csv'}")
    print(f"  2. Run clustering:")
    print(f"     cd scripts")
    print(f"     python -m core.step_A3_clustering")

if __name__ == "__main__":
    main()

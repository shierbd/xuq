"""
转换原始数据文件为标准格式
处理SEMRUSH、下拉词、相关搜索的原始导出文件
"""
import pandas as pd
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import RAW_DATA_DIR


def convert_semrush_files():
    """转换SEMRUSH导出的CSV文件"""
    semrush_dir = RAW_DATA_DIR / 'semrush'

    # 排除已处理的文件
    csv_files = [f for f in semrush_dir.glob('*_broad-match_*.csv')]

    if not csv_files:
        print("没有找到SEMRUSH原始文件")
        return None

    all_data = []

    for file_path in csv_files:
        print(f"处理SEMRUSH文件: {file_path.name}")

        df = pd.read_csv(file_path, encoding='utf-8-sig')

        # 提取种子词（从文件名）
        seed_word = file_path.stem.split('_')[0]  # 例如: agents_broad-match_us -> agents

        # 映射列名
        df_converted = pd.DataFrame({
            'phrase': df['Keyword'].str.lower().str.strip(),
            'seed_word': seed_word,
            'source_type': 'semrush',
            'frequency': 1,  # SEMRUSH数据默认频次为1
            'volume': df['Volume'].fillna(0).astype(int)
        })

        all_data.append(df_converted)
        print(f"  转换了 {len(df_converted)} 条记录")

    # 合并所有数据
    result = pd.concat(all_data, ignore_index=True)

    # 保存
    output_file = semrush_dir / 'semrush_converted.csv'
    result.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n[OK] SEMRUSH data saved to: {output_file}")
    print(f"  Total: {len(result)} records")

    return result


def convert_dropdown_excel():
    """转换下拉词Excel文件"""
    dropdown_dir = RAW_DATA_DIR / 'dropdown'

    # 查找Excel文件
    excel_files = list(dropdown_dir.glob('*.xlsx'))

    if not excel_files:
        print("没有找到下拉词Excel文件")
        return None

    excel_file = excel_files[0]
    print(f"\n处理下拉词文件: {excel_file.name}")

    df = pd.read_excel(excel_file)

    # 检查列名
    print(f"  Excel列名: {df.columns.tolist()}")

    # 假设第一列是短语，需要根据实际情况调整
    if len(df.columns) == 0:
        print("  ⚠️ Excel文件为空或格式错误")
        return None

    # 使用第一列作为短语
    df_converted = pd.DataFrame({
        'phrase': df.iloc[:, 0].astype(str).str.lower().str.strip(),
        'seed_word': 'unknown',  # 下拉词没有明确的种子词
        'source_type': 'dropdown',
        'frequency': 1,
        'volume': 0
    })

    # 清理无效数据
    df_converted = df_converted[df_converted['phrase'].notna()]
    df_converted = df_converted[df_converted['phrase'] != 'nan']

    # 保存
    output_file = dropdown_dir / 'dropdown_converted.csv'
    df_converted.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n[OK] Dropdown data saved to: {output_file}")
    print(f"  Total: {len(df_converted)} records")

    return df_converted


def convert_related_search_files():
    """转换相关搜索CSV文件"""
    related_dir = RAW_DATA_DIR / 'related_search'

    # 查找所有相关搜索文件（排除processed）
    csv_files = [f for f in related_dir.glob('*_2025-12-26.csv')]

    if not csv_files:
        print("\n没有找到相关搜索原始文件")
        return None

    print(f"\n处理相关搜索文件: 找到 {len(csv_files)} 个文件")

    all_data = []

    for file_path in csv_files:
        df = pd.read_csv(file_path, encoding='utf-8-sig')

        # 检查是否有中文列名
        if '种子关键词' in df.columns and '下拉词建议' in df.columns:
            df_converted = pd.DataFrame({
                'phrase': df['下拉词建议'].str.lower().str.strip(),
                'seed_word': df['种子关键词'].str.lower().str.strip(),
                'source_type': 'related_search',
                'frequency': 1,
                'volume': 0
            })
        else:
            print(f"  ⚠️ 跳过格式不匹配的文件: {file_path.name}")
            continue

        all_data.append(df_converted)

    if not all_data:
        print("  没有成功转换的文件")
        return None

    # 合并所有数据
    result = pd.concat(all_data, ignore_index=True)

    # 保存
    output_file = related_dir / 'related_search_converted.csv'
    result.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n[OK] Related search data saved to: {output_file}")
    print(f"  Total: {len(result)} records")

    return result


def main():
    """Main function"""
    print("="*70)
    print("Data Format Conversion Tool".center(70))
    print("="*70)

    # 转换各类数据
    semrush_df = convert_semrush_files()
    dropdown_df = convert_dropdown_excel()
    related_df = convert_related_search_files()

    print("\n" + "="*70)
    print("Conversion Summary".center(70))
    print("="*70)

    if semrush_df is not None:
        print(f"SEMRUSH: {len(semrush_df):,} records")
    if dropdown_df is not None:
        print(f"Dropdown: {len(dropdown_df):,} records")
    if related_df is not None:
        print(f"Related Search: {len(related_df):,} records")

    print("\n[OK] All converted files saved!")
    print("You can now import using:")
    print("  python scripts/run_phase1_import.py --round-id=2 --sources=semrush,dropdown,related")


if __name__ == "__main__":
    main()

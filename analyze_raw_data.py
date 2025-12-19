"""
分析原始数据的结构
分析三种数据源：SEMRUSH导出、下拉词、相关搜索
"""
import pandas as pd
import sys
from pathlib import Path
import glob

def analyze_semrush_data(folder_path):
    """分析SEMRUSH导出的CSV数据"""
    print("=" * 80)
    print("【数据源1：SEMRUSH导出词】")
    print("=" * 80)

    csv_files = list(Path(folder_path).glob("*.csv"))
    print(f"\n文件数量: {len(csv_files)}")

    if csv_files:
        # 读取第一个文件作为样例
        sample_file = csv_files[0]
        print(f"\n样例文件: {sample_file.name}")

        df = pd.read_csv(sample_file)
        print(f"\n字段名称: {list(df.columns)}")
        print(f"数据行数: {len(df)}")

        print("\n前3行数据:")
        print(df.head(3).to_string())

        print("\n字段说明:")
        print("  - Keyword: 关键词短语")
        print("  - Intent: 搜索意图 (Informational/Commercial/Transactional)")
        print("  - Volume: 月搜索量")
        print("  - Trend: 12个月搜索趋势")
        print("  - Keyword Difficulty: 关键词难度 (0-100)")
        print("  - CPC (USD): 每次点击成本")
        print("  - Competitive Density: 竞争密度 (0-1)")
        print("  - SERP Features: SERP特征")
        print("  - Number of Results: 搜索结果数")

        # 统计所有文件
        total_rows = 0
        seed_words = []
        for f in csv_files[:10]:  # 只统计前10个文件避免太慢
            try:
                df_temp = pd.read_csv(f)
                total_rows += len(df_temp)
                # 从文件名提取种子词
                seed = f.stem.split('_')[0]
                seed_words.append(seed)
            except:
                pass

        print(f"\n前10个文件总行数: {total_rows:,}")
        print(f"种子词示例: {', '.join(seed_words[:10])}")

    return csv_files

def analyze_dropdown_data(folder_path):
    """分析Google下拉词CSV数据"""
    print("\n\n" + "=" * 80)
    print("【数据源2：Google下拉词】")
    print("=" * 80)

    csv_files = list(Path(folder_path).glob("*.csv"))
    print(f"\n文件数量: {len(csv_files)}")

    if csv_files:
        # 读取第一个文件作为样例
        sample_file = csv_files[0]
        print(f"\n样例文件: {sample_file.name}")

        df = pd.read_csv(sample_file, encoding='utf-8-sig')
        print(f"\n字段名称: {list(df.columns)}")
        print(f"数据行数: {len(df)}")

        print("\n前5行数据:")
        print(df.head(5).to_string())

        print("\n字段说明:")
        print("  - 种子关键词: 原始种子词")
        print("  - 下拉词建议: Google下拉建议的关键词")
        print("  - 排名: 在下拉列表中的排名")
        print("  - 扩展类型: 扩展方式 (none/prefix/suffix)")
        print("  - 扩展词: 添加的前缀/后缀词")
        print("  - 语言: 语言 (en)")
        print("  - 地区: 地区 (US)")
        print("  - 状态: 抓取状态 (success)")

        # 统计扩展类型
        if '扩展类型' in df.columns:
            print("\n扩展类型分布:")
            print(df['扩展类型'].value_counts().to_string())

        # 统计所有文件
        total_rows = 0
        seed_words = []
        for f in csv_files[:10]:
            try:
                df_temp = pd.read_csv(f, encoding='utf-8-sig')
                total_rows += len(df_temp)
                # 从文件名提取种子词
                parts = f.stem.split('_')
                if len(parts) >= 2:
                    seed = parts[1]
                    seed_words.append(seed)
            except:
                pass

        print(f"\n前10个文件总行数: {total_rows:,}")
        print(f"种子词示例: {', '.join(seed_words[:10])}")

    return csv_files

def analyze_related_search(file_path):
    """分析Google相关搜索Excel数据"""
    print("\n\n" + "=" * 80)
    print("【数据源3：Google相关搜索】")
    print("=" * 80)

    try:
        df = pd.read_excel(file_path)
        print(f"\n文件: {Path(file_path).name}")
        print(f"字段名称: {list(df.columns)}")
        print(f"数据行数: {len(df):,}")

        # 获取列名
        col_name = df.columns[0]

        print("\n前10行数据:")
        for i in range(min(10, len(df))):
            value = df.iloc[i, 0]
            print(f"  {i+1}. {value}")

        print("\n数据说明:")
        print("  - 单列数据，包含Google相关搜索的关键词")
        print("  - 格式: 各种相关搜索词，可能来自不同种子词")

        # 统计数据特征
        all_keywords = df.iloc[:, 0].astype(str).tolist()
        avg_length = sum(len(k) for k in all_keywords) / len(all_keywords)
        print(f"\n平均关键词长度: {avg_length:.1f} 字符")

    except Exception as e:
        print(f"\n读取Excel文件出错: {e}")
        print("可能需要安装 openpyxl: pip install openpyxl")

def main():
    """主函数"""
    base_path = Path(r"D:\xiangmu\词根聚类需求挖掘\原始词")

    print("\n" + "=" * 80)
    print("原始数据结构分析报告")
    print("=" * 80)

    # 分析三种数据源
    semrush_files = analyze_semrush_data(base_path / "sm导出词")
    dropdown_files = analyze_dropdown_data(base_path / "下拉词")
    analyze_related_search(base_path / "相关搜索.xlsx")

    # 总结
    print("\n\n" + "=" * 80)
    print("【数据源对比总结】")
    print("=" * 80)

    print(f"""
┌─────────────────┬──────────────┬──────────────┬──────────────┐
│ 特征            │ SEMRUSH      │ 下拉词       │ 相关搜索     │
├─────────────────┼──────────────┼──────────────┼──────────────┤
│ 文件数量        │ {len(semrush_files):3d} 个CSV   │ {len(dropdown_files):3d} 个CSV   │ 1 个Excel    │
│ 数据质量        │ ★★★★★       │ ★★★★☆       │ ★★★☆☆       │
│ 字段丰富度      │ 9个字段      │ 8个字段      │ 1个字段      │
│ 搜索量数据      │ ✓ 有         │ ✗ 无         │ ✗ 无         │
│ 搜索意图        │ ✓ 有         │ ✗ 无         │ ✗ 无         │
│ 结构化程度      │ 高           │ 高           │ 低           │
└─────────────────┴──────────────┴──────────────┴──────────────┘
    """)

    print("\n推荐使用策略:")
    print("  1. 主力数据：SEMRUSH导出 (有搜索量、意图等关键指标)")
    print("  2. 补充数据：下拉词 (覆盖更多长尾词)")
    print("  3. 可选数据：相关搜索 (如果能解析出种子词来源)")

if __name__ == "__main__":
    main()

"""
步骤A2：合并CSV文件
功能：将指定文件夹下的所有CSV文件合并成一个完整文件
输入：多个CSV文件（每个种子词一个文件）
输出：merged_keywords_all.csv（包含所有数据+来源信息）
"""

import pandas as pd
import glob
from pathlib import Path
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

# 导入配置和工具
from config import A2_CONFIG, DATA_DIR, RAW_DATA_DIR
from utils import setup_logging, save_csv, print_section, print_subsection, print_stats


def select_folder_gui(default_path=None):
    """
    使用GUI选择文件夹

    参数:
        default_path: 默认路径

    返回:
        选择的文件夹路径（字符串），如果取消则返回None
    """
    # 创建隐藏的主窗口
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)

    # 显示文件夹选择对话框
    folder_path = filedialog.askdirectory(
        title="选择包含CSV文件的文件夹",
        initialdir=default_path if default_path else "C:\\"
    )

    root.destroy()

    return folder_path if folder_path else None


def confirm_folder_choice(folder_path):
    """
    确认文件夹选择

    参数:
        folder_path: 待确认的文件夹路径

    返回:
        True表示确认，False表示重新选择
    """
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)

    result = messagebox.askyesno(
        "确认文件夹",
        f"已选择文件夹：\n\n{folder_path}\n\n是否使用此文件夹？\n\n"
        "点击 '是' 继续\n点击 '否' 重新选择"
    )

    root.destroy()

    return result


def merge_csv_files(
    folder_path: str,
    output_file: str,
    file_pattern: str = "*.csv",
    encoding: str = "utf-8"
) -> pd.DataFrame:
    """
    合并指定文件夹下的所有CSV文件

    参数:
        folder_path: 文件夹路径
        output_file: 输出文件名
        file_pattern: 文件匹配模式
        encoding: 文件编码

    返回:
        合并后的DataFrame
    """
    logger = setup_logging()

    # 确保路径存在
    folder_path = Path(folder_path)
    if not folder_path.exists():
        raise FileNotFoundError(f"文件夹不存在: {folder_path}")

    # 获取所有CSV文件
    file_pattern_full = str(folder_path / file_pattern)
    csv_files = glob.glob(file_pattern_full)

    if not csv_files:
        raise FileNotFoundError(f"在 {folder_path} 中没有找到匹配的CSV文件")

    logger.info(f"找到 {len(csv_files)} 个CSV文件")

    # 用于存储所有数据
    all_dataframes = []
    total_rows = 0
    error_files = []

    # 逐个读取并合并
    for i, file_path in enumerate(csv_files, 1):
        try:
            filename = Path(file_path).name
            logger.info(f"[{i}/{len(csv_files)}] 正在读取: {filename}")

            # 读取CSV文件
            df = pd.read_csv(file_path, encoding=encoding)

            # 添加来源列
            seed_word = filename.split('_')[0]
            df['seed_word'] = seed_word
            df['source_file'] = filename

            rows = len(df)
            total_rows += rows
            logger.info(f"   行数: {rows}")

            all_dataframes.append(df)

        except Exception as e:
            error_files.append((filename, str(e)))
            logger.error(f"   错误: {e}")

    # 合并所有数据
    if all_dataframes:
        logger.info("正在合并所有数据...")
        merged_df = pd.concat(all_dataframes, ignore_index=True)

        # 保存合并后的文件
        output_path = DATA_DIR / output_file
        save_csv(merged_df, output_path, encoding=encoding)

        # 打印统计信息
        print_section("合并完成")
        print(f"总文件数: {len(csv_files)}")
        print(f"成功合并: {len(all_dataframes)}")
        print(f"失败文件: {len(error_files)}")
        print(f"总行数: {total_rows:,}")
        print(f"输出文件: {output_path}")

        if error_files:
            print_subsection("失败文件列表")
            for filename, error in error_files:
                print(f"  - {filename}: {error}")

        # 显示统计信息
        print_subsection("数据统计")
        print(f"唯一关键词数: {merged_df['Keyword'].nunique():,}")
        print(f"种子词数量: {merged_df['seed_word'].nunique()}")
        print(f"平均每个种子词: {len(merged_df)/merged_df['seed_word'].nunique():.1f} 条")

        # 显示各种子词的数据量
        print_subsection("各种子词数据量（Top 10）")
        seed_counts = merged_df['seed_word'].value_counts().head(10)
        for seed, count in seed_counts.items():
            print(f"  {seed:20s}: {count:,} 条")
        if len(merged_df['seed_word'].value_counts()) > 10:
            remaining = len(merged_df['seed_word'].value_counts()) - 10
            print(f"  {'(其他)':20s}: {remaining} 个种子词")

        # 显示数据预览
        print_subsection("数据预览（前5行）")
        print(merged_df[['Keyword', 'seed_word', 'Volume', 'Intent']].head())

        return merged_df

    else:
        logger.error("没有成功读取任何文件")
        return None


def main():
    """主函数"""
    print_section("步骤A2：合并CSV文件")

    print("\n选择输入文件夹方式:")
    print("  1. 使用弹窗选择文件夹（推荐）")
    print("  2. 使用配置文件中的路径")
    print("  3. 手动输入路径")

    choice = input("\n请选择 (1/2/3，直接回车默认选1): ").strip()

    if choice == "" or choice == "1":
        # 弹窗选择
        print("\n正在打开文件夹选择对话框...")

        while True:
            selected_folder = select_folder_gui(default_path=str(RAW_DATA_DIR))

            if not selected_folder:
                print("\n未选择文件夹，程序退出。")
                return 1

            print(f"\n已选择文件夹: {selected_folder}")

            # 检查文件夹是否存在CSV文件
            test_pattern = str(Path(selected_folder) / A2_CONFIG['file_pattern'])
            test_files = glob.glob(test_pattern)

            if not test_files:
                root = tk.Tk()
                root.withdraw()
                root.attributes('-topmost', True)
                retry = messagebox.askyesno(
                    "未找到CSV文件",
                    f"在文件夹中未找到匹配的CSV文件！\n\n"
                    f"匹配模式: {A2_CONFIG['file_pattern']}\n\n"
                    "是否重新选择文件夹？"
                )
                root.destroy()

                if not retry:
                    print("\n程序退出。")
                    return 1
                continue

            print(f"找到 {len(test_files)} 个CSV文件")

            if confirm_folder_choice(selected_folder):
                input_folder = selected_folder
                break
            else:
                continue

    elif choice == "2":
        # 使用配置文件路径
        input_folder = A2_CONFIG['input_folder']
        print(f"\n使用配置文件路径: {input_folder}")

    elif choice == "3":
        # 手动输入
        input_folder = input("\n请输入文件夹路径: ").strip()

        if not input_folder:
            print("\n未输入路径，程序退出。")
            return 1

    else:
        print("\n无效的选择，程序退出。")
        return 1

    print(f"\n配置信息:")
    print(f"  输入文件夹: {input_folder}")
    print(f"  输出文件名: {A2_CONFIG['output_file']}")
    print(f"  文件模式: {A2_CONFIG['file_pattern']}")
    print(f"  文件编码: {A2_CONFIG['encoding']}")

    try:
        # 执行合并
        merged_df = merge_csv_files(
            folder_path=input_folder,
            output_file=A2_CONFIG['output_file'],
            file_pattern=A2_CONFIG['file_pattern'],
            encoding=A2_CONFIG['encoding']
        )

        if merged_df is not None:
            print("\n" + "=" * 60)
            print("步骤A2执行成功！".center(60))
            print("=" * 60)
            print(f"\n下一步：运行 step_A3_clustering.py 进行语义聚类")

            # 显示成功消息框
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            messagebox.showinfo(
                "执行成功",
                f"CSV文件合并完成！\n\n"
                f"合并文件数: {merged_df['seed_word'].nunique()}\n"
                f"总行数: {len(merged_df):,}\n\n"
                f"输出文件: {DATA_DIR / A2_CONFIG['output_file']}"
            )
            root.destroy()

            return 0
        else:
            print("\n步骤A2执行失败！")
            return 1

    except Exception as e:
        print(f"\n发生错误: {e}")
        import traceback
        traceback.print_exc()

        # 显示错误消息框
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        messagebox.showerror(
            "执行失败",
            f"发生错误：\n\n{str(e)}"
        )
        root.destroy()

        return 1


if __name__ == "__main__":
    sys.exit(main())

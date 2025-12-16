"""
CSV查看器生成工具
功能：将CSV文件转换为可在浏览器中查看的HTML页面
支持浏览器自动翻译功能
"""

import pandas as pd
import sys
from pathlib import Path

def generate_html_viewer(csv_file, output_html, title="数据查看"):
    """
    生成HTML查看器

    参数:
        csv_file: CSV文件路径
        output_html: 输出HTML文件路径
        title: 页面标题
    """
    # 读取CSV
    df = pd.read_csv(csv_file)

    # 限制显示行数（避免页面过大）
    max_rows = 500
    if len(df) > max_rows:
        df = df.head(max_rows)
        rows_info = f"(显示前 {max_rows} 条，共 {len(df)} 条)"
    else:
        rows_info = f"(共 {len(df)} 条)"

    # 生成HTML
    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }}
        .info {{
            background: #e3f2fd;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
            border-left: 4px solid #2196F3;
        }}
        .info strong {{
            color: #1976D2;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            font-size: 14px;
        }}
        th {{
            background-color: #4CAF50;
            color: white;
            padding: 12px;
            text-align: left;
            position: sticky;
            top: 0;
            z-index: 10;
        }}
        td {{
            padding: 10px;
            border-bottom: 1px solid #ddd;
            vertical-align: top;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        tr:nth-child(even) {{
            background-color: #fafafa;
        }}
        .phrase-col {{
            max-width: 300px;
            word-wrap: break-word;
        }}
        .example-col {{
            max-width: 400px;
            word-wrap: break-word;
            font-size: 13px;
            color: #555;
        }}
        .number-col {{
            text-align: right;
            font-weight: bold;
        }}
        .translate-tip {{
            background: #fff3cd;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
            border-left: 4px solid #ffc107;
        }}
        .translate-tip strong {{
            color: #ff9800;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>

        <div class="info">
            <strong>文件信息：</strong><br>
            文件：{Path(csv_file).name}<br>
            数据行数：{len(df)} {rows_info}<br>
            列数：{len(df.columns)}
        </div>

        <div class="translate-tip">
            <strong>如何翻译此页面：</strong><br>
            • <strong>Chrome浏览器</strong>：右键点击页面 → 选择"翻译为中文"<br>
            • <strong>Edge浏览器</strong>：右键点击页面 → 选择"翻译"<br>
            • <strong>Firefox浏览器</strong>：安装"To Google Translate"扩展<br>
            • 或者复制文本到 Google翻译/DeepL 进行翻译
        </div>

        <table>
            <thead>
                <tr>
"""

    # 添加表头
    for col in df.columns:
        html_content += f"                    <th>{col}</th>\n"

    html_content += """                </tr>
            </thead>
            <tbody>
"""

    # 添加数据行
    for idx, row in df.iterrows():
        html_content += "                <tr>\n"
        for col in df.columns:
            value = row[col]

            # 处理不同类型的列
            if pd.isna(value):
                cell_value = "-"
                cell_class = ""
            elif isinstance(value, (int, float)):
                cell_value = f"{value:,.0f}" if isinstance(value, float) and value == int(value) else f"{value:,.2f}"
                cell_class = ' class="number-col"'
            else:
                cell_value = str(value)
                # 根据列名选择样式
                if 'phrase' in col.lower():
                    cell_class = ' class="phrase-col"'
                elif 'example' in col.lower():
                    cell_class = ' class="example-col"'
                else:
                    cell_class = ""

            html_content += f"                    <td{cell_class}>{cell_value}</td>\n"

        html_content += "                </tr>\n"

    html_content += """            </tbody>
        </table>
    </div>
</body>
</html>
"""

    # 保存HTML文件
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"[OK] HTML查看器已生成: {output_html}")
    print(f"     请在浏览器中打开此文件")


def main():
    """主函数"""
    print("="*60)
    print("CSV查看器生成工具".center(60))
    print("="*60)

    # 定义要转换的文件
    data_dir = Path("D:/xiangmu/词根聚类需求挖掘/data")
    output_dir = Path("D:/xiangmu/词根聚类需求挖掘/output")
    output_dir.mkdir(exist_ok=True)

    files_to_convert = [
        {
            'csv': data_dir / 'cluster_summary_A3.csv',
            'html': output_dir / 'cluster_summary_A3.html',
            'title': 'A阶段聚类汇总 - Cluster Summary A3'
        },
        {
            'csv': data_dir / 'cluster_summary_B3.csv',
            'html': output_dir / 'cluster_summary_B3.html',
            'title': 'B阶段聚类汇总 - Cluster Summary B3'
        },
        {
            'csv': data_dir / 'direction_keywords.csv',
            'html': output_dir / 'direction_keywords.html',
            'title': '筛选的方向 - Selected Directions'
        }
    ]

    print("\n正在生成HTML查看器...\n")

    for item in files_to_convert:
        csv_file = item['csv']
        html_file = item['html']
        title = item['title']

        if csv_file.exists():
            try:
                generate_html_viewer(csv_file, html_file, title)
            except Exception as e:
                print(f"[ERROR] 生成失败: {csv_file.name} - {e}")
        else:
            print(f"[SKIP] 文件不存在: {csv_file.name}")

    print("\n" + "="*60)
    print("全部完成！".center(60))
    print("="*60)
    print("\n查看方式：")
    print(f"1. 打开文件夹: {output_dir}")
    print(f"2. 双击 .html 文件在浏览器中打开")
    print(f"3. 在浏览器中右键 → 翻译为中文")
    print("\n推荐使用 Chrome 或 Edge 浏览器，翻译功能最好！")

    return 0


def generate_html_for_file(csv_file, output_html, title):
    """
    为单个CSV文件生成HTML（供其他脚本调用）

    参数:
        csv_file: CSV文件路径（Path对象或字符串）
        output_html: 输出HTML文件路径（Path对象或字符串）
        title: 页面标题

    返回:
        bool: 成功返回True，失败返回False
    """
    try:
        csv_file = Path(csv_file)
        output_html = Path(output_html)

        if not csv_file.exists():
            print(f"[SKIP] CSV文件不存在: {csv_file.name}")
            return False

        generate_html_viewer(csv_file, output_html, title)
        return True
    except Exception as e:
        print(f"[ERROR] 生成HTML失败: {csv_file.name} - {e}")
        return False


if __name__ == "__main__":
    sys.exit(main())

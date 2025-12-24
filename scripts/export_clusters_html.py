"""
直接导出小组聚类为HTML，绕过Streamlit验证数据
"""
import sys
import io
from pathlib import Path
from datetime import datetime

# 设置UTF-8编码输出（Windows兼容）
if sys.platform.startswith('win'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from storage.repository import ClusterMetaRepository

def main():
    print("正在生成小组聚类HTML报告...")

    with ClusterMetaRepository() as repo:
        clusters_B = repo.get_all_clusters('B')

        if not clusters_B:
            print("错误: 没有找到小组聚类数据")
            return

        print(f"找到 {len(clusters_B)} 个小组聚类")

        # 按父组分组
        by_parent = {}
        for c in clusters_B:
            parent_id = c.cluster_id // 10000
            if parent_id not in by_parent:
                by_parent[parent_id] = []
            by_parent[parent_id].append(c)

        # 生成HTML
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>小组聚类数据 - {datetime.now().strftime('%Y-%m-%d %H:%M')}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        h1 {{
            color: #1f77b4;
            border-bottom: 3px solid #1f77b4;
            padding-bottom: 10px;
        }}
        .summary {{
            background-color: #e3f2fd;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }}
        .parent-section {{
            background-color: white;
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .parent-header {{
            font-size: 1.3em;
            font-weight: bold;
            color: #1565c0;
            margin-bottom: 15px;
            padding: 10px;
            background-color: #bbdefb;
            border-radius: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }}
        th {{
            background-color: #1f77b4;
            color: white;
            padding: 12px;
            text-align: left;
        }}
        td {{
            padding: 10px;
            border-bottom: 1px solid #ddd;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .stats-table {{
            width: 100%;
            margin: 20px 0;
        }}
        .stats-table td {{
            padding: 8px;
        }}
    </style>
</head>
<body>
    <h1>🔄 小组聚类数据 (Clusters Level B)</h1>

    <div class="summary">
        <h2>📊 总体统计</h2>
        <table class="stats-table">
            <tr>
                <td><strong>生成时间:</strong></td>
                <td>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td>
            </tr>
            <tr>
                <td><strong>小组总数:</strong></td>
                <td>{len(clusters_B)}</td>
            </tr>
            <tr>
                <td><strong>包含的大组数:</strong></td>
                <td>{len(by_parent)}</td>
            </tr>
            <tr>
                <td><strong>总短语数:</strong></td>
                <td>{sum(c.size for c in clusters_B)}</td>
            </tr>
        </table>
    </div>
"""

        # 为每个父组创建一个section
        for parent_id in sorted(by_parent.keys()):
            small_clusters = by_parent[parent_id]
            total_phrases = sum(c.size for c in small_clusters)

            html_content += f"""
    <div class="parent-section">
        <div class="parent-header">
            大组 {parent_id} - {len(small_clusters)} 个小组, 共 {total_phrases} 个短语
        </div>
        <table>
            <thead>
                <tr>
                    <th style="width: 15%;">小组ID</th>
                    <th style="width: 10%;">大小</th>
                    <th style="width: 75%;">示例短语</th>
                </tr>
            </thead>
            <tbody>
"""

            for c in sorted(small_clusters, key=lambda x: x.size, reverse=True):
                example = c.example_phrases if c.example_phrases else "(无)"
                html_content += f"""
                <tr>
                    <td>{c.cluster_id}</td>
                    <td>{c.size}</td>
                    <td>{example}</td>
                </tr>
"""

            html_content += """
            </tbody>
        </table>
    </div>
"""

        html_content += """
</body>
</html>
"""

        # 保存文件
        output_dir = project_root / "data" / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        html_file = output_dir / "small_clusters_report.html"

        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"✅ HTML报告已生成: {html_file}")
        print(f"\n请在浏览器中打开此文件查看小组聚类数据")

if __name__ == "__main__":
    main()

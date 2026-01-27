"""
数据库查询工具
用于快速查看和分析数据库中的数据
"""
import sqlite3
import pandas as pd
from pathlib import Path

# 数据库路径
DB_PATH = Path(__file__).parent.parent / "data" / "products.db"


def get_connection():
    """获取数据库连接"""
    return sqlite3.connect(DB_PATH)


def show_tables():
    """显示所有表"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    conn.close()

    print("=" * 50)
    print("数据库表列表")
    print("=" * 50)
    for table in tables:
        print(f"  - {table[0]}")
    print()


def show_table_info(table_name):
    """显示表结构"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    conn.close()

    print("=" * 80)
    print(f"表结构: {table_name}")
    print("=" * 80)
    print(f"{'列名':<30} {'类型':<15} {'非空':<10} {'默认值':<15}")
    print("-" * 80)
    for col in columns:
        col_name = col[1]
        col_type = col[2]
        not_null = "是" if col[3] else "否"
        default = col[4] if col[4] else ""
        print(f"{col_name:<30} {col_type:<15} {not_null:<10} {default:<15}")
    print()


def count_records(table_name):
    """统计表记录数"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
    count = cursor.fetchone()[0]
    conn.close()
    return count


def show_statistics():
    """显示数据库统计信息"""
    print("=" * 50)
    print("数据库统计信息")
    print("=" * 50)

    # 关键词统计
    conn = get_connection()

    # 总关键词数
    total_keywords = count_records("keywords")
    print(f"关键词总数: {total_keywords:,}")

    # 已聚类的关键词数
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM keywords WHERE cluster_id_a IS NOT NULL;")
    clustered = cursor.fetchone()[0]
    print(f"已聚类关键词: {clustered:,} ({clustered/total_keywords*100:.1f}%)")

    # 噪音点数量
    cursor.execute("SELECT COUNT(*) FROM keywords WHERE is_noise = 1;")
    noise = cursor.fetchone()[0]
    print(f"噪音点数量: {noise:,} ({noise/total_keywords*100:.1f}%)")

    # 簇数量
    cursor.execute("SELECT COUNT(DISTINCT cluster_id_a) FROM keywords WHERE cluster_id_a IS NOT NULL AND cluster_id_a != -1;")
    num_clusters = cursor.fetchone()[0]
    print(f"簇数量: {num_clusters}")

    # 种子词数量
    cursor.execute("SELECT COUNT(DISTINCT seed_word) FROM keywords;")
    num_seeds = cursor.fetchone()[0]
    print(f"种子词数量: {num_seeds}")

    print()

    # 商品统计
    total_products = count_records("products")
    print(f"商品总数: {total_products:,}")

    # 已聚类的商品数
    cursor.execute("SELECT COUNT(*) FROM products WHERE cluster_id IS NOT NULL;")
    clustered_products = cursor.fetchone()[0]
    print(f"已聚类商品: {clustered_products:,} ({clustered_products/total_products*100:.1f}%)")

    conn.close()
    print()


def show_top_clusters(limit=10):
    """显示最大的簇"""
    conn = get_connection()
    query = """
    SELECT
        cluster_id_a,
        COUNT(*) as size,
        GROUP_CONCAT(DISTINCT seed_word) as seed_words,
        SUM(volume) as total_volume
    FROM keywords
    WHERE cluster_id_a IS NOT NULL AND cluster_id_a != -1
    GROUP BY cluster_id_a
    ORDER BY size DESC
    LIMIT ?;
    """
    df = pd.read_sql_query(query, conn, params=(limit,))
    conn.close()

    print("=" * 100)
    print(f"Top {limit} 最大的簇")
    print("=" * 100)
    print(f"{'簇ID':<10} {'大小':<10} {'总搜索量':<15} {'种子词':<50}")
    print("-" * 100)
    for _, row in df.iterrows():
        cluster_id = row['cluster_id_a']
        size = row['size']
        volume = f"{int(row['total_volume']):,}" if pd.notna(row['total_volume']) else "N/A"
        seeds = row['seed_words'][:47] + "..." if len(str(row['seed_words'])) > 50 else row['seed_words']
        print(f"{cluster_id:<10} {size:<10} {volume:<15} {seeds:<50}")
    print()


def show_seed_word_stats():
    """显示种子词统计"""
    conn = get_connection()
    query = """
    SELECT
        seed_word,
        COUNT(*) as keyword_count,
        SUM(volume) as total_volume,
        AVG(volume) as avg_volume
    FROM keywords
    GROUP BY seed_word
    ORDER BY keyword_count DESC;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    print("=" * 100)
    print("种子词统计")
    print("=" * 100)
    print(f"{'种子词':<20} {'关键词数':<15} {'总搜索量':<20} {'平均搜索量':<15}")
    print("-" * 100)
    for _, row in df.iterrows():
        seed = row['seed_word']
        count = row['keyword_count']
        total_vol = f"{int(row['total_volume']):,}" if pd.notna(row['total_volume']) else "N/A"
        avg_vol = f"{int(row['avg_volume']):,}" if pd.notna(row['avg_volume']) else "N/A"
        print(f"{seed:<20} {count:<15} {total_vol:<20} {avg_vol:<15}")
    print()


def search_keywords(search_term, limit=20):
    """搜索关键词"""
    conn = get_connection()
    query = """
    SELECT
        keyword,
        seed_word,
        volume,
        cluster_id_a,
        cluster_size,
        is_noise
    FROM keywords
    WHERE keyword LIKE ?
    ORDER BY volume DESC
    LIMIT ?;
    """
    df = pd.read_sql_query(query, conn, params=(f"%{search_term}%", limit))
    conn.close()

    print("=" * 120)
    print(f"搜索结果: '{search_term}' (前 {limit} 条)")
    print("=" * 120)
    print(f"{'关键词':<40} {'种子词':<15} {'搜索量':<15} {'簇ID':<10} {'簇大小':<10} {'噪音':<10}")
    print("-" * 120)
    for _, row in df.iterrows():
        keyword = row['keyword'][:37] + "..." if len(row['keyword']) > 40 else row['keyword']
        seed = row['seed_word']
        volume = f"{int(row['volume']):,}" if pd.notna(row['volume']) else "N/A"
        cluster = str(row['cluster_id_a']) if pd.notna(row['cluster_id_a']) else "N/A"
        size = str(row['cluster_size']) if pd.notna(row['cluster_size']) else "N/A"
        noise = "是" if row['is_noise'] else "否"
        print(f"{keyword:<40} {seed:<15} {volume:<15} {cluster:<10} {size:<10} {noise:<10}")
    print()


def show_cluster_detail(cluster_id, limit=20):
    """显示簇的详细信息"""
    conn = get_connection()

    # 簇统计
    query_stats = """
    SELECT
        COUNT(*) as size,
        GROUP_CONCAT(DISTINCT seed_word) as seed_words,
        SUM(volume) as total_volume,
        AVG(volume) as avg_volume,
        MAX(volume) as max_volume,
        MIN(volume) as min_volume
    FROM keywords
    WHERE cluster_id_a = ?;
    """
    cursor = conn.cursor()
    cursor.execute(query_stats, (cluster_id,))
    stats = cursor.fetchone()

    print("=" * 100)
    print(f"簇 #{cluster_id} 详细信息")
    print("=" * 100)
    print(f"簇大小: {stats[0]}")
    print(f"种子词: {stats[1]}")
    print(f"总搜索量: {int(stats[2]):,}" if stats[2] else "N/A")
    print(f"平均搜索量: {int(stats[3]):,}" if stats[3] else "N/A")
    print(f"最大搜索量: {int(stats[4]):,}" if stats[4] else "N/A")
    print(f"最小搜索量: {int(stats[5]):,}" if stats[5] else "N/A")
    print()

    # 关键词列表
    query_keywords = """
    SELECT
        keyword,
        seed_word,
        volume,
        intent
    FROM keywords
    WHERE cluster_id_a = ?
    ORDER BY volume DESC
    LIMIT ?;
    """
    df = pd.read_sql_query(query_keywords, conn, params=(cluster_id, limit))
    conn.close()

    print(f"Top {limit} 关键词:")
    print("-" * 100)
    print(f"{'关键词':<50} {'种子词':<15} {'搜索量':<15} {'意图':<20}")
    print("-" * 100)
    for _, row in df.iterrows():
        keyword = row['keyword'][:47] + "..." if len(row['keyword']) > 50 else row['keyword']
        seed = row['seed_word']
        volume = f"{int(row['volume']):,}" if pd.notna(row['volume']) else "N/A"
        intent = row['intent'] if pd.notna(row['intent']) else "N/A"
        print(f"{keyword:<50} {seed:<15} {volume:<15} {intent:<20}")
    print()


def export_to_csv(table_name, output_file):
    """导出表到CSV"""
    conn = get_connection()
    df = pd.read_sql_query(f"SELECT * FROM {table_name};", conn)
    conn.close()

    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"✅ 导出成功: {output_file}")
    print(f"   记录数: {len(df):,}")
    print()


def main():
    """主函数"""
    print("\n" + "=" * 50)
    print("需求挖掘系统 - 数据库查询工具")
    print("=" * 50 + "\n")

    while True:
        print("请选择操作:")
        print("  1. 显示所有表")
        print("  2. 显示表结构")
        print("  3. 显示数据库统计")
        print("  4. 显示最大的簇")
        print("  5. 显示种子词统计")
        print("  6. 搜索关键词")
        print("  7. 查看簇详情")
        print("  8. 导出数据到CSV")
        print("  0. 退出")
        print()

        choice = input("请输入选项 (0-8): ").strip()
        print()

        if choice == "1":
            show_tables()

        elif choice == "2":
            table_name = input("请输入表名 (keywords/products/cluster_summaries): ").strip()
            if table_name:
                show_table_info(table_name)

        elif choice == "3":
            show_statistics()

        elif choice == "4":
            limit = input("显示前几个簇? (默认10): ").strip()
            limit = int(limit) if limit else 10
            show_top_clusters(limit)

        elif choice == "5":
            show_seed_word_stats()

        elif choice == "6":
            search_term = input("请输入搜索关键词: ").strip()
            if search_term:
                limit = input("显示前几条结果? (默认20): ").strip()
                limit = int(limit) if limit else 20
                search_keywords(search_term, limit)

        elif choice == "7":
            cluster_id = input("请输入簇ID: ").strip()
            if cluster_id:
                limit = input("显示前几个关键词? (默认20): ").strip()
                limit = int(limit) if limit else 20
                show_cluster_detail(int(cluster_id), limit)

        elif choice == "8":
            table_name = input("请输入表名 (keywords/products): ").strip()
            if table_name:
                output_file = input(f"输出文件名 (默认: {table_name}_export.csv): ").strip()
                output_file = output_file if output_file else f"{table_name}_export.csv"
                export_to_csv(table_name, output_file)

        elif choice == "0":
            print("再见！")
            break

        else:
            print("无效的选项，请重新选择。\n")


if __name__ == "__main__":
    main()

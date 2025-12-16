# validation.py
# CSV文件字段验证工具

import pandas as pd
import os

REQUIRED_COLUMNS = {
    "stageA_clusters.csv": [
        "phrase", "seed_word", "source_type", "frequency",
        "cluster_id_A", "cluster_size", "is_noise"
    ],
    "cluster_summary_A3.csv": [
        "cluster_id_A", "cluster_size", "seed_words_in_cluster",
        "total_frequency", "example_phrases"
    ],
    "direction_keywords.csv": [
        "direction_keyword", "cluster_id_A", "cluster_size",
        "total_frequency", "seed_words_in_cluster"
    ],
    "stageB_clusters.csv": [
        "phrase", "seed_word", "frequency", "cluster_id_A",
        "cluster_id_B", "direction_keyword"
    ],
    "cluster_summary_B3.csv": [
        "direction_keyword", "cluster_id_B", "cluster_size",
        "total_frequency", "example_phrases"
    ],
}

def validate_csv_columns(file_path, file_type):
    """验证CSV文件的列名是否符合规范"""

    if file_type not in REQUIRED_COLUMNS:
        print(f"⚠️ 未定义的文件类型: {file_type}")
        print(f"支持的文件类型: {list(REQUIRED_COLUMNS.keys())}")
        return False

    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return False

    try:
        df = pd.read_csv(file_path)
        required = set(REQUIRED_COLUMNS[file_type])
        actual = set(df.columns)

        missing = required - actual
        extra = actual - required

        if missing:
            print(f"❌ {file_type} 缺失字段: {missing}")
            return False

        if extra:
            print(f"⚠️ {file_type} 额外字段: {extra}（可选字段）")

        print(f"✅ {file_type} 字段验证通过")
        return True

    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False


def validate_all_files():
    """验证所有已知的输出文件"""
    base_path = "D:/xiangmu/词根聚类需求挖掘/data"

    files = [
        (os.path.join(base_path, "stageA_clusters.csv"), "stageA_clusters.csv"),
        (os.path.join(base_path, "cluster_summary_A3.csv"), "cluster_summary_A3.csv"),
        (os.path.join(base_path, "direction_keywords.csv"), "direction_keywords.csv"),
        (os.path.join(base_path, "stageB_clusters.csv"), "stageB_clusters.csv"),
        (os.path.join(base_path, "cluster_summary_B3.csv"), "cluster_summary_B3.csv"),
    ]

    print("========== 文件字段验证 ==========\n")

    results = {}
    for file_path, file_type in files:
        if os.path.exists(file_path):
            results[file_type] = validate_csv_columns(file_path, file_type)
            print()
        else:
            print(f"⏭️ 跳过: {file_type}（文件不存在）\n")

    print("========== 验证总结 ==========")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"通过: {passed}/{total}")

    return all(results.values()) if results else False


if __name__ == "__main__":
    # 方式1：验证所有文件
    validate_all_files()

    # 方式2：验证单个文件（示例）
    # validate_csv_columns(
    #     "D:/xiangmu/词根聚类需求挖掘/data/stageA_clusters.csv",
    #     "stageA_clusters.csv"
    # )

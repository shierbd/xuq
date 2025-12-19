# Data Directory

This directory contains all data files for the keyword clustering project.

## ⚠️ IMPORTANT: Data Security

**ALL DATA FILES IN THIS DIRECTORY ARE EXCLUDED FROM GIT**

- Raw keyword data
- Processed clustering results
- Analysis outputs
- Database files

## Directory Structure

```
data/
├── raw/              # 原始数据（SEMRUSH, 下拉词, 相关搜索）
├── processed/        # 处理后的数据（聚类结果）
├── results/          # 分析结果（cluster summary, insights）
├── output/           # 输出文件
├── baseline/         # 基准数据
└── external/         # 外部数据源
```

## What's Excluded

The following file types are **completely excluded** from Git:

- `*.csv` - All CSV files
- `*.xlsx`, `*.xls` - All Excel files
- `*.db`, `*.sqlite` - All database files
- Entire directories: `data/raw/`, `data/processed/`, `data/results/`, etc.

## Local Files Only

All data files in this directory exist **only on your local machine** and will never be pushed to GitHub.

This ensures:
- ✅ Privacy protection
- ✅ Compliance with data security policies
- ✅ No accidental data leaks
- ✅ Repository size stays manageable

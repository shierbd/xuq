# 原始数据目录说明

此目录用于存放待导入的原始关键词数据。

## 目录结构

```
data/raw/
├── semrush/          # SEMRUSH数据（CSV格式）
├── dropdown/         # 下拉词数据（CSV格式）
├── related_search/   # 相关搜索数据（CSV/Excel格式）
└── README.md         # 本说明文件
```

## 数据文件格式要求

### 1. SEMRUSH数据

**位置**: `data/raw/semrush/`
**格式**: CSV文件，任意文件名（如 `semrush_data.csv`）
**编码**: UTF-8 或 GBK（程序会自动检测）

**必需列**:
- `phrase`: 短语/关键词（必需）
- `seed_word`: 种子词/词根（必需）
- `frequency`: 频次（可选，默认1）
- `volume`: 搜索量（可选，默认0）

**示例**:
```csv
phrase,seed_word,frequency,volume
best calculator app,calculator,10,5000
free calculator online,calculator,8,3200
scientific calculator download,calculator,5,1500
```

### 2. 下拉词数据

**位置**: `data/raw/dropdown/`
**格式**: CSV文件，任意文件名
**编码**: UTF-8 或 GBK

**必需列**:
- `phrase`: 短语/关键词
- `seed_word`: 种子词
- `frequency`: 频次（可选）

**示例**:
```csv
phrase,seed_word,frequency
calculator app,calculator,15
calculator for windows,calculator,12
calculator free,calculator,8
```

### 3. 相关搜索数据

**位置**: `data/raw/related_search/`
**格式**: CSV 或 Excel（.xlsx）文件
**编码**: UTF-8 或 GBK（CSV）

**必需列**:
- `phrase`: 短语/关键词
- `seed_word`: 种子词
- `frequency`: 频次（可选）

**示例**:
```csv
phrase,seed_word,frequency
people also search for calculator,calculator,20
related calculator apps,calculator,15
```

## 数据要求

1. **字段名称**: 列名不区分大小写，但必须与上述字段名匹配
2. **编码**: 推荐使用 UTF-8 with BOM 编码，也支持 GBK 编码（Windows默认）
3. **文件名**: 无特定要求，程序会自动识别目录下的第一个CSV/Excel文件
4. **数据量**: 建议每个数据源 5000-50000 条记录

## 快速开始

### 方式1：使用子目录（推荐）

1. 将 SEMRUSH 数据放到 `data/raw/semrush/` 目录
2. 将下拉词数据放到 `data/raw/dropdown/` 目录
3. 将相关搜索数据放到 `data/raw/related_search/` 目录
4. 运行导入命令：
   ```bash
   python scripts/run_phase1_import.py
   ```

### 方式2：直接放在raw目录

如果只有一个数据源，也可以直接将文件放在 `data/raw/` 目录，文件名包含关键词：
- `*semrush*.csv` → 识别为SEMRUSH数据
- `*dropdown*.csv` → 识别为下拉词数据
- `*related*.csv` → 识别为相关搜索数据

## 示例数据

### 创建示例CSV文件（Excel打开后另存为CSV）

**SEMRUSH示例** (`data/raw/semrush/example.csv`):
```csv
phrase,seed_word,frequency,volume
best calculator,calculator,25,12000
calculator app,calculator,20,8500
free calculator,calculator,15,6700
scientific calculator,calculator,18,9200
online calculator,calculator,30,15000
```

**下拉词示例** (`data/raw/dropdown/example.csv`):
```csv
phrase,seed_word,frequency
calculator for windows,calculator,10
calculator download,calculator,8
calculator free online,calculator,12
```

## 常见问题

### Q1: 编码错误 "gbk codec can't decode"

**原因**: CSV文件编码与系统默认编码不匹配

**解决方案**:
1. 在Excel中打开CSV文件
2. 点击"文件" → "另存为"
3. 选择"CSV UTF-8（逗号分隔）(*.csv)"
4. 保存并重新导入

或者使用 Notepad++ 等编辑器转换编码为 UTF-8。

### Q2: 找不到数据文件

**检查清单**:
- [ ] 文件是否在正确的目录下（`data/raw/semrush/` 等）
- [ ] 文件扩展名是否正确（.csv 或 .xlsx）
- [ ] 目录是否存在（如不存在需要手动创建）

### Q3: 列名不匹配

**错误信息**: "Missing required columns"

**解决方案**:
检查CSV文件的第一行（列名），确保包含必需字段：
- SEMRUSH: `phrase`, `seed_word`
- 下拉词: `phrase`, `seed_word`
- 相关搜索: `phrase`, `seed_word`

## 下一步

数据导入成功后，查看：
- `data/processed/integrated_round1.csv` - 清洗后的数据
- 运行 Phase 2 聚类：`python scripts/run_phase2_clustering.py`

---

**提示**: 此目录已被 .gitignore 忽略，数据文件不会被提交到Git仓库，请放心使用。

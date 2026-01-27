# 需求挖掘系统 v2.0

## 📋 项目简介

这是一个统一的需求挖掘与分析平台，包含**词根聚类（长尾词）**、**商品管理**和**Reddit**三大模块。

**核心理念**：从单词 → 短语 → 语义簇 → 需求方向 → MVP验证

### 系统架构

```
需求挖掘系统 v2.0
├── 模块一：词根聚类模块（长尾词分析）
├── 模块二：商品管理模块（Etsy商品分析）
└── 模块三：Reddit模块（预留）
```

---

## 🚀 快速开始

### 启动系统（2步上手）

1. **启动后端服务**
   ```bash
   python -m uvicorn backend.main:app --reload --port 8000
   ```

2. **启动前端界面**
   ```bash
   cd frontend
   npm run dev
   ```

3. **访问系统**
   - 前端界面: http://localhost:5173
   - 后端 API: http://127.0.0.1:8000
   - API 文档: http://127.0.0.1:8000/docs

---

## 📁 项目结构

```
需求挖掘系统/
│
├── 📂 backend/              # 统一后端服务
│   ├── main.py             # FastAPI 应用入口
│   ├── database.py         # 数据库配置
│   ├── models/             # 数据模型
│   │   ├── product.py     # 商品模型
│   │   └── keyword.py     # 关键词模型
│   └── routers/            # API 路由
│       ├── products.py    # 商品管理 API
│       └── keywords.py    # 词根聚类 API
│
├── 📂 frontend/             # Vue 3 前端
│   ├── src/
│   │   ├── components/    # 组件
│   │   ├── views/         # 页面
│   │   └── stores/        # 状态管理
│   └── package.json
│
├── 📂 data/                 # 数据文件
│   ├── products.db        # 统一数据库（SQLite）
│   ├── merged_keywords_all.csv  # 关键词数据
│   └── stageA_clusters.csv      # 聚类结果
│
├── 📂 docs/                 # 文档
│   ├── 需求文档.md              # 统一需求文档（三大模块）
│   ├── 04_快速开始指南.md        # 快速开始
│   ├── API使用示例.md           # API使用指南
│   └── 使用手册.md              # 完整使用说明
│
└── 📂 scripts/              # 聚类分析脚本
    ├── step_A3_clustering.py   # 聚类分析
    └── cluster_stats.py        # 质量分析
```

---

## 📖 文档导航

### ⭐⭐⭐ 必读（开始前）

1. **[需求文档](docs/需求文档.md)** - 统一需求文档（三大模块）
2. **[快速开始指南](docs/04_快速开始指南.md)** - 快速上手教程
3. **[使用手册](docs/使用手册.md)** - 完整使用说明

### ⭐⭐ 重要（深入使用）

4. **[API使用示例](docs/API使用示例.md)** - API接口使用指南

---

## 🎯 功能模块

### 1. 词根聚类模块

**功能**：基于语义聚类的需求挖掘

**API 端点**：
- `POST /api/keywords/import` - 导入关键词数据
- `GET /api/keywords/` - 获取关键词列表
- `GET /api/keywords/count` - 获取关键词总数
- `GET /api/keywords/clusters/overview` - 获取簇概览
- `GET /api/keywords/clusters/{cluster_id}` - 获取簇详情
- `GET /api/keywords/seed-words` - 获取种子词列表

**数据表**：
- `keywords` - 关键词数据表
- `cluster_summaries` - 簇汇总表

### 2. 商品管理模块

**功能**：Etsy商品数据分析

**API 端点**：
- `POST /api/products/import` - 导入商品数据
- `GET /api/products/` - 获取商品列表
- `GET /api/products/count` - 获取商品总数
- `GET /api/products/{product_id}` - 获取商品详情
- `PUT /api/products/{product_id}` - 更新商品信息
- `DELETE /api/products/{product_id}` - 删除商品（软删除）

**数据表**：
- `products` - 商品数据表

---

## 🔧 技术栈

### 后端
- **框架**: FastAPI 0.104+
- **数据库**: SQLite 3
- **ORM**: SQLAlchemy 2.0+
- **服务器**: Uvicorn

### 前端
- **框架**: Vue 3
- **构建工具**: Vite
- **UI 库**: Element Plus
- **状态管理**: Pinia

### AI/ML
- **嵌入模型**: Sentence Transformers (all-MiniLM-L6-v2)
- **聚类算法**: HDBSCAN
- **大模型**: Claude API

---

## 🚀 使用场景

### 场景1：导入并分析关键词数据

```bash
# 1. 启动后端
python -m uvicorn backend.main:app --reload --port 8000

# 2. 通过 API 导入数据
curl -X POST "http://127.0.0.1:8000/api/keywords/import" \
  -F "file=@data/merged_keywords_all.csv"

# 3. 查看导入结果
curl "http://127.0.0.1:8000/api/keywords/count"

# 4. 查看簇概览
curl "http://127.0.0.1:8000/api/keywords/clusters/overview"
```

### 场景2：运行聚类分析

```bash
# 使用脚本进行聚类分析
cd scripts
python step_A3_clustering.py

# 分析结果质量
python cluster_stats.py
```

### 场景3：管理商品数据

```bash
# 查看商品总数
curl "http://127.0.0.1:8000/api/products/count"

# 获取商品列表
curl "http://127.0.0.1:8000/api/products/?page=1&page_size=20"
```

---

## ⚙️ 配置说明

### 环境变量

创建 `.env` 文件：

```bash
# Claude API 配置
CLAUDE_API_KEY=your_api_key_here

# 数据库配置
DATABASE_URL=sqlite:///./data/products.db

# 服务器配置
HOST=127.0.0.1
PORT=8000
```

### 聚类参数

在 `scripts/config.py` 中配置：

```python
A3_CONFIG = {
    "min_cluster_size": 15,  # 最小簇大小
    "min_samples": 3,        # 最小邻居数
    "embedding_model": "all-MiniLM-L6-v2",
    "clustering_method": "hdbscan",
}
```

---

## 📊 数据流程图

```
种子词（seed_words）
    ↓
[A1] 种子词准备
    ↓
[A2] 扩展短语（影刀RPA/手动）
    ↓
data/merged_keywords_all.csv
    ↓
[A3] 语义聚类 ← step_A3_clustering.py
    ↓
data/stageA_clusters.csv（带cluster_id）
    ↓
cluster_stats.py → 质量报告
    ↓
[A5] 人工筛选方向（5-10个）
    ↓
data/direction_keywords.csv
    ↓
[B1] 方向扩展
    ↓
[B3] 方向内聚类
    ↓
[B6] 需求分析
    ↓
MVP实验
```

---

## 🚨 常见问题

### Q1: 如何启动统一系统？

**解决方案**：
```bash
# 终端1：启动后端
python -m uvicorn backend.main:app --reload --port 8000

# 终端2：启动前端
cd frontend
npm run dev
```

访问 http://localhost:5173 即可使用系统。

---

### Q2: 如何导入关键词数据？

**方法1：通过 API**
```bash
curl -X POST "http://127.0.0.1:8000/api/keywords/import" \
  -F "file=@data/merged_keywords_all.csv"
```

**方法2：通过前端界面**
访问前端界面，使用文件上传功能。

---

### Q3: 聚类结果簇太多（>100个）怎么办？

**解决方案**：
```python
# 修改 scripts/config.py
A3_CONFIG = {
    "min_cluster_size": 20,  # 从15改为20
    "min_samples": 3,
}
```

然后重新运行：
```bash
cd scripts
python step_A3_clustering.py
```

---

### Q4: 两个模块的数据是否互通？

**回答**：是的。两个模块使用同一个数据库（`data/products.db`），数据完全互通。未来可以实现：
- 从关键词簇中发现商品机会
- 从商品数据中提取关键词
- 交叉分析需求和供给

---

### Q5: 如何查看 API 文档？

访问 http://127.0.0.1:8000/docs 可以查看完整的 Swagger API 文档，包括：
- 所有 API 端点
- 请求参数说明
- 响应格式示例
- 在线测试功能

---

## 📚 学习路径

### 新手路径（1小时）

```
1. 阅读：README.md（本文档）（15分钟）
2. 阅读：docs/项目合并完成总结.md（15分钟）
3. 启动：后端 + 前端服务（10分钟）
4. 测试：通过 API 文档测试接口（20分钟）
```

### 开发者路径（半天）

```
1. 系统架构：docs/项目合并完成总结.md（30分钟）
2. 需求文档：docs/USER_REQUIREMENTS.md（30分钟）
3. 方法论：docs/01_需求挖掘方法论.md（1小时）
4. 字段规范：docs/02_字段命名规范.md（20分钟）
5. 代码阅读：backend/ 和 frontend/ 目录（1小时）
```

---

## 🎯 核心原则

### 1. 只分组，不删除

系统提供视图，人工做决策。

- ✅ A3聚类：只分组，不过滤
- ✅ A5筛选：标记low priority，不删除
- ✅ 噪音点：保留，人工决定是否使用

### 2. 轻量版起步，避免复杂度压垮

- Phase 1（必须）：A2 → A3 → 人工筛选
- Phase 2（重要）：B1 → B3 → B6
- Phase 3（可选）：大模型 + Trends + 需求库

### 3. 大模型输出是假设，不是事实

- A4的簇解释：需要SERP验证
- B3的5维框架：需要访谈验证
- 决策优先级：SERP+访谈 > BI > 经验 > 模型

---

## 🔗 相关资源

- **FastAPI 文档**: https://fastapi.tiangolo.com/
- **Vue 3 文档**: https://vuejs.org/
- **HDBSCAN 文档**: https://hdbscan.readthedocs.io/
- **Sentence Transformers**: https://www.sbert.net/

---

## 📝 更新日志

### v2.0.0 (2026-01-27)
- ✅ 项目合并完成（词根聚类 + 商品管理）
- ✅ 统一后端架构（FastAPI）
- ✅ 统一数据库（SQLite）
- ✅ 创建 Keywords 模型和 API
- ✅ 创建 ClusterSummary 模型
- ✅ 更新项目文档

### v1.0.0 (2025-12-15)
- ✅ 项目结构重组（代码与文档分离）
- ✅ 创建6个核心脚本（scripts目录）
- ✅ 整理4类文档（方法论、教程、分析、技术）
- ✅ 优化聚类参数（248簇 → 56簇）
- ✅ 创建质量分析工具（cluster_stats.py）
- ✅ 创建字段验证工具（validation.py）

---

## 💬 需要帮助？

- **快速问题**：查看本 README.md
- **系统架构**：查看 `docs/项目合并完成总结.md`
- **方法论问题**：查看 `docs/01_需求挖掘方法论.md`
- **API 文档**：访问 http://127.0.0.1:8000/docs
- **技术问题**：查看 `docs/technical/`

---

**开始使用**：启动后端和前端服务，访问 http://localhost:5173

**祝你挖掘出好需求！** 🚀

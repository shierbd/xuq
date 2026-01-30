# 项目上下文

**项目名称**: 需求挖掘系统
**创建日期**: 2026-01-28
**文档类型**: 项目上下文

---

## 项目背景

这是一个基于语义聚类的需求挖掘与分析平台，旨在帮助产品经理、需求分析师和创业者从海量数据中发现产品机会方向。

### 核心理念

**从数据 → 聚类 → 需求 → 产品验证**

### 目标用户

- 产品经理
- 需求分析师
- 市场研究人员
- 创业者（个人使用）

---

## 技术栈

### 前端
- **框架**: React 18.2
- **UI 库**: Ant Design 5.x
- **构建工具**: Vite 5.x
- **HTTP 客户端**: Axios
- **路由**: React Router 6

### 后端
- **框架**: FastAPI 0.104
- **ORM**: SQLAlchemy 2.0
- **服务器**: Uvicorn
- **数据验证**: Pydantic
- **文件处理**: Python-multipart

### 数据库
- **开发环境**: SQLite 3
- **生产环境**: PostgreSQL (建议)
- **位置**: `data/products.db`

### AI/ML
- **嵌入模型**: Sentence Transformers (all-MiniLM-L6-v2)
- **聚类算法**: HDBSCAN
- **机器学习**: scikit-learn
- **数值计算**: NumPy
- **大模型**: Claude API (可选)

---

## 开发规范

### 代码风格

**Python**:
- 遵循 PEP 8 规范
- 使用类型注解
- 函数和类添加文档字符串
- 变量命名: snake_case

**JavaScript/React**:
- 遵循 ESLint 规范
- 使用函数式组件
- 变量命名: camelCase
- 组件命名: PascalCase

### Git 提交规范

```
feat: 新功能
fix: 修复 Bug
docs: 文档更新
style: 代码格式调整
refactor: 重构
test: 测试相关
chore: 构建/工具相关
```

### 测试要求

- 单元测试覆盖率 >80%
- 集成测试覆盖核心功能
- API 测试使用 pytest

---

## 常用命令

### 安装依赖

```bash
# 后端依赖
pip install -r requirements.txt

# 前端依赖
cd frontend
npm install
```

### 运行开发服务器

```bash
# 启动后端（终端 1）
python -m uvicorn backend.main:app --reload --port 8000

# 启动前端（终端 2）
cd frontend
npm run dev
```

### 运行测试

```bash
# 后端测试
pytest

# 前端测试
cd frontend
npm test
```

### 数据库操作

```bash
# 初始化数据库
python -c "from backend.database import init_db; init_db()"

# 查看数据库
sqlite3 data/products.db
```

### 聚类分析

```bash
# 运行聚类分析
cd scripts
python step_A3_clustering.py

# 分析聚类质量
python cluster_stats.py
```

---

## 项目结构

```
需求挖掘系统/
├── backend/              # 后端服务
│   ├── main.py          # FastAPI 应用入口
│   ├── database.py      # 数据库配置
│   ├── models/          # 数据模型
│   ├── routers/         # API 路由
│   ├── services/        # 业务逻辑
│   └── utils/           # 工具函数
│
├── frontend/            # 前端应用
│   ├── src/
│   │   ├── components/  # 组件
│   │   ├── pages/       # 页面
│   │   ├── api/         # API 调用
│   │   └── App.jsx      # 应用入口
│   └── package.json
│
├── data/                # 数据文件
│   ├── products.db      # 数据库
│   └── *.csv            # CSV 数据
│
├── docs/                # 文档
│   ├── 需求文档.md       # 需求文档
│   ├── 使用手册.md       # 使用手册
│   └── design/          # 设计文档
│
└── scripts/             # 脚本
    └── *.py             # Python 脚本
```

---

## 核心概念

### 三大模块

1. **词根聚类模块** (Keywords Module)
   - 从英文单词种子发现产品机会
   - 数据来源: SEMrush / Reddit / Related Search
   - 核心流程: 单词 → 短语 → 语义簇 → 需求方向

2. **商品管理模块** (Products Module)
   - 分析市场供给情况
   - 数据来源: Etsy 平台
   - 核心价值: 需求-供给匹配分析

3. **Reddit 模块** (预留)
   - 从讨论中挖掘需求
   - 数据来源: Reddit 平台
   - 状态: 预留，暂未实现

### 两阶段工作流

**阶段 A**: 种子词扩展与聚类
- A1: 种子词准备
- A2: 短语扩展
- A3: 语义聚类
- A4: 簇解释（AI辅助）
- A5: 人工筛选方向

**阶段 B**: 方向深化与需求分析
- B1: 方向扩展
- B3: 方向内聚类
- B6: 需求分析（5维框架）

---

## 核心原则

### 1. 只分组，不删除
- 系统提供视图，人工做决策
- 聚类只分组，不过滤
- 筛选标记 low priority，不删除
- 噪音点保留，人工决定是否使用

### 2. 轻量版起步
- Phase 1（必须）: A2 → A3 → 人工筛选
- Phase 2（重要）: B1 → B3 → B6
- Phase 3（可选）: 大模型 + Trends + 需求库

### 3. 大模型输出是假设
- A4的簇解释需要SERP验证
- B6的5维框架需要访谈验证
- 决策优先级: SERP+访谈 > BI > 经验 > 模型

---

## 环境变量

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

---

## 访问地址

- **前端界面**: http://localhost:5173
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs

---

## 重要文档索引

- **需求文档**: `docs/需求文档.md`
- **使用手册**: `docs/使用手册.md`
- **快速开始**: `docs/04_快速开始指南.md`
- **API 示例**: `docs/API使用示例.md`
- **架构设计**: `docs/design/architecture.md`
- **数据库设计**: `docs/design/database-design.md`
- **API 设计**: `docs/design/api-design.md`

---

## 开发注意事项

### 1. 数据安全
- 不要在代码中硬编码 API 密钥
- 使用环境变量存储敏感信息
- 将 `.env` 添加到 `.gitignore`

### 2. 代码质量
- 编写清晰的代码注释
- 遵循命名规范
- 及时更新文档

### 3. 性能优化
- 使用向量缓存提升聚类性能
- 数据库查询使用索引
- 前端使用分页和懒加载

---

## 故障排查

### 前端问题
1. 检查 Node.js 版本（需要 18+）
2. 清理缓存: `rm -rf node_modules && npm install`
3. 检查环境变量配置
4. 查看浏览器控制台错误

### 后端问题
1. 检查 Python 版本（需要 3.11+）
2. 检查依赖安装: `pip list`
3. 检查环境变量配置
4. 查看日志文件: `tail -f logs/app.log`

### 数据库问题
1. 检查数据库文件是否存在
2. 检查数据库权限
3. 使用 SQLite 工具查看数据

---

*文档创建者: Claude Sonnet 4.5*
*最后更新: 2026-01-28*

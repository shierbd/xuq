# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## 🎯 最高优先级：需求驱动原则（必读）⭐⭐⭐⭐⭐

**在执行任何任务前，必须先做以下检查**：

### 第一步：读取需求文档

```bash
# 每次对话开始时，必须先读取需求文档
cat docs/USER_REQUIREMENTS.md
```

### 第二步：需求对齐检查

回答以下问题：
1. ✅ 当前任务是否符合需求文档？
2. ✅ 当前任务是否偏离了核心需求？
3. ✅ 需求文档是否需要更新？

### 第三步：需求优先级

- **P0 需求** - 必须优先处理
- **P1 需求** - 重要但可以稍后
- **P2 需求** - 可以延后

### 禁止行为

❌ 未读取需求文档就开始工作
❌ 做需求文档之外的事情
❌ 偏离核心需求

### 强制流程

```
用户请求 → 读取需求文档 → 检查是否符合需求 → 执行任务
         ↓ (如果不符合)
         → 询问用户是否要更新需求文档
```

### 需求文档位置

**主需求文档**: `docs/USER_REQUIREMENTS.md`

---

## 🚨 自动错误恢复机制（优先级第二）

### 遇到 "Error writing file" 或任何文件操作错误时：

**核心规则**:
1. ❌ 绝对不要重试相同方法超过 1 次
2. ✅ 立即切换到下一个方法
3. ✅ 按顺序尝试直到成功

**方法顺序**:
1. Edit 工具 → 失败立即切换
2. Write 工具 → 失败立即切换
3. Bash cat heredoc:
   ```bash
   cat > "file" << 'EOF'
   content
   EOF
   ```
4. Python 写入:
   ```python
   with open("file", 'w', encoding='utf-8') as f:
       f.write('''content''')
   ```
5. Python 临时文件:
   ```python
   import tempfile, shutil
   with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
       tmp.write('''content''')
   shutil.move(tmp.name, "file")
   ```
6. 备用文件名（file_alt1, file_alt2...）

**禁止**: 重试同一方法、询问用户、停止报错（除非全部失败）

---

## 📋 项目概述

**项目名称**: 词根聚类需求挖掘系统

**项目类型**: 全栈 Web 应用（Vue 3 + FastAPI + AI）

**核心功能**: 基于语义聚类的需求挖掘方法论系统，用于从英文单词种子（word roots）发现产品机会方向

**技术栈**:
- **前端**: Vue 3 + TypeScript + Vite + Element Plus
- **后端**: FastAPI + Python 3.11
- **AI**: Claude API + Sentence Transformers + HDBSCAN
- **数据**: CSV 文件存储 + 语义向量化

**核心理念**: 从单词 → 短语 → 语义簇 → 需求方向 → MVP验证

---

## 📁 项目结构

```
词根聚类需求挖掘/
├── frontend/              # Vue 3 前端 (204M)
│   ├── src/              # 源代码
│   │   ├── components/   # Vue 组件
│   │   ├── views/        # 页面视图
│   │   ├── stores/       # Pinia 状态管理
│   │   ├── hooks/        # Vue Hooks
│   │   ├── utils/        # 工具函数
│   │   └── styles/       # 样式文件
│   ├── dist/             # 构建产物
│   └── node_modules/     # 依赖包
│
├── api/                   # FastAPI 后端 (348K)
│   ├── routers/          # 路由模块
│   │   ├── phase0.py    # 阶段 0 路由
│   │   ├── phase1.py    # 阶段 1 路由
│   │   ├── phase2.py    # 阶段 2 路由
│   │   ├── phase3.py    # 阶段 3 路由
│   │   ├── phase4.py    # 阶段 4 路由
│   │   ├── phase5.py    # 阶段 5 路由
│   │   └── phase6.py    # 阶段 6 路由
│   ├── schemas/          # 数据模型
│   ├── services/         # 业务逻辑
│   └── utils/            # 工具函数
│
├── ai/                    # AI 分析模块 (25K)
│   ├── client.py         # Claude API 客户端
│   └── __init__.py
│
├── config/                # 配置管理
│   ├── settings.py       # 应用配置
│   └── __init__.py
│
├── core/                  # 核心业务逻辑
│   ├── data_processor.py # 数据处理
│   ├── root_extractor.py # 词根提取
│   └── clustering.py     # 聚类分析
│
├── utils/                 # 工具函数
├── data/                  # 数据目录 (212M)
│   ├── raw/              # 原始数据
│   ├── processed/        # 处理后数据
│   ├── results/          # 分析结果
│   ├── cache/            # 缓存数据
│   ├── output/           # 输出数据
│   └── temp/             # 临时数据
│
├── storage/               # 存储目录
├── logs/                  # 日志目录
├── uploads/               # 上传文件
├── docs/                  # 文档目录
│   ├── USER_REQUIREMENTS.md  # 用户需求文档
│   ├── 01_需求挖掘方法论.md  # 方法论文档
│   ├── 02_字段命名规范.md    # 字段规范
│   ├── 03_实施优先级指南.md  # 实施指南
│   └── 04_快速开始指南.md    # 快速开始
│
├── scripts/               # 脚本目录
└── backups/               # 备份目录
```

---

## 🎯 开发工作流

### 阶段 1: 需求分析
1. 阅读 `docs/USER_REQUIREMENTS.md`
2. 理解核心需求和优先级
3. 确认当前任务是否符合需求

### 阶段 2: 设计方案
1. 参考 `docs/01_需求挖掘方法论.md`
2. 参考 `docs/02_字段命名规范.md`
3. 设计技术方案

### 阶段 3: 开发实现
1. 遵循字段命名规范
2. 遵循项目结构
3. 编写清晰的代码注释

### 阶段 4: 测试验证
1. 单元测试
2. 集成测试
3. 功能验证

### 阶段 5: 文档更新
1. 更新 API 文档
2. 更新用户文档
3. 更新需求文档（如有变更）

---

## 📚 核心文档

### 必读文档（开始前）
1. **docs/USER_REQUIREMENTS.md** - 用户需求文档（必读）
2. **docs/01_需求挖掘方法论.md** - 完整的方法论
3. **docs/02_字段命名规范.md** - 字段命名标准
4. **docs/03_实施优先级指南.md** - Phase 1/2/3规划

### 开发文档
1. **README.md** - 项目说明
2. **docs/04_快速开始指南.md** - 快速上手

---

## 🔧 开发规范

### 1. 代码规范

#### Python 代码规范
- 使用 Python 3.11+
- 遵循 PEP 8 规范
- 使用类型注解
- 编写清晰的文档字符串

#### TypeScript 代码规范
- 使用 TypeScript 5.0+
- 遵循 ESLint 规范
- 使用严格的类型检查
- 编写清晰的注释

### 2. 命名规范

#### 文件命名
- Python: `snake_case.py`
- TypeScript: `kebab-case.ts` 或 `PascalCase.vue`
- 配置文件: `lowercase.json`

#### 变量命名
- Python: `snake_case`
- TypeScript: `camelCase`
- 常量: `UPPER_SNAKE_CASE`
- 类名: `PascalCase`

### 3. Git 提交规范

```
feat: 新功能
fix: 修复 Bug
docs: 文档更新
style: 代码格式调整
refactor: 重构
test: 测试相关
chore: 构建/工具相关
```

---

## 🚀 快速开始

### 环境配置
```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入 CLAUDE_API_KEY 等配置

# 2. 安装后端依赖
pip install -r requirements.txt

# 3. 安装前端依赖
cd frontend
npm install
cd ..
```

### 启动服务
```bash
# 启动后端（终端 1）
python -m uvicorn api.main:app --reload --port 8000

# 启动前端（终端 2）
cd frontend
npm run dev
```

### 访问地址
- **前端界面**: http://localhost:5173
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs

---

## 🎯 核心原则

### 1. 需求驱动开发
- 所有开发必须基于 `docs/USER_REQUIREMENTS.md`
- 不做需求之外的事情
- 优先级：P0 > P1 > P2

### 2. 只分组，不删除
- 系统提供视图，人工做决策
- 聚类只分组，不过滤
- 筛选标记 low priority，不删除
- 噪音点保留，人工决定是否使用

### 3. 轻量版起步，避免复杂度压垮
- Phase 1（必须）：A2 → A3 → 人工筛选
- Phase 2（重要）：B1 → B3 → B6
- Phase 3（可选）：大模型 + Trends + 需求库

### 4. 大模型输出是假设，不是事实
- A4的簇解释：需要SERP验证
- B3的5维框架：需要访谈验证
- 决策优先级：SERP+访谈 > BI > 经验 > 模型

---

## 🔒 安全规范

### 1. 敏感信息
- ❌ 不要在代码中硬编码 API 密钥
- ✅ 使用环境变量存储敏感信息
- ✅ 将 `.env` 添加到 `.gitignore`

### 2. 数据安全
- ✅ 验证所有用户输入
- ✅ 使用参数化查询防止注入
- ✅ 对敏感数据进行加密

### 3. API 安全
- ✅ 实现请求限流
- ✅ 验证 API 请求来源
- ✅ 使用 HTTPS

---

## 📝 注意事项

### 1. 开发注意事项
- 始终先读取 `docs/USER_REQUIREMENTS.md`
- 遵循字段命名规范
- 编写清晰的代码注释
- 及时更新文档

### 2. 测试注意事项
- 编写单元测试
- 进行集成测试
- 验证边界条件
- 测试错误处理

### 3. 部署注意事项
- 检查环境变量配置
- 验证依赖版本
- 测试生产环境
- 准备回滚方案

---

## 🆘 故障排查

### 前端问题
1. 检查 Node.js 版本（需要 18+）
2. 清理缓存：`rm -rf node_modules && npm install`
3. 检查环境变量配置
4. 查看浏览器控制台错误

### 后端问题
1. 检查 Python 版本（需要 3.11+）
2. 检查依赖安装：`pip list`
3. 检查环境变量配置
4. 查看日志文件：`tail -f logs/app.log`

### AI 模块问题
1. 检查 Claude API 密钥
2. 检查网络连接
3. 查看 API 调用日志
4. 验证输入数据格式

---

## 📞 获取帮助

如有问题，请：
1. 查看 `docs/USER_REQUIREMENTS.md`
2. 查看 `docs/04_快速开始指南.md`
3. 查看 `README.md`
4. 查看相关技术文档

---

**开始开发前，请务必阅读 `docs/USER_REQUIREMENTS.md`！**

---

*本文件由 Claude Sonnet 4.5 生成*
*最后更新: 2026-01-27*

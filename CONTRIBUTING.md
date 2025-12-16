# 开发者指南

## 🚀 快速设置

### 1. 克隆项目
```bash
git clone <repository-url>
cd 词根聚类需求挖掘
```

### 2. 创建虚拟环境（推荐）
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. 安装依赖
```bash
# 安装完整依赖（包含可选功能）
pip install -r requirements.txt

# 或只安装核心依赖（仅A2/A3步骤）
pip install -r scripts/requirements_minimal.txt
```

### 4. 配置环境变量（可选）
如果需要使用LLM功能，创建`.env`文件：
```bash
# .env
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

---

## 📂 项目结构

```
项目根目录/
├── scripts/               # 所有Python脚本
│   ├── core/              # 核心流程脚本（A2, A3, B3）
│   ├── tools/             # 工具脚本（统计、验证、可视化）
│   ├── selectors/         # 方向选择器
│   └── lib/               # 共享库（config, utils）
├── data/                  # 数据目录
│   ├── raw/               # 原始数据
│   ├── processed/         # 处理后的数据
│   ├── results/           # 最终结果
│   └── baseline/          # 基准输出（用于测试对比）
├── docs/                  # 文档
│   ├── tutorials/         # 使用教程
│   ├── guides/            # 工具指南
│   ├── technical/         # 技术文档
│   ├── analysis/          # 分析记录
│   └── history/           # 历史文档
├── output/                # HTML查看器输出
├── README.md              # 项目README
├── requirements.txt       # Python依赖
└── .gitignore             # Git忽略规则
```

---

## 🔧 开发规范

### 代码风格
- 遵循PEP 8规范
- 使用4空格缩进
- 函数和类添加docstring说明

### 导入规范
```python
# 标准库
import sys
from pathlib import Path

# 第三方库
import pandas as pd
import numpy as np

# 项目内部
from lib.config import A3_CONFIG
from lib.utils import setup_logging, print_section
```

### 提交规范
使用常规的commit message格式：
```
<type>: <subject>

<body>

Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

类型（type）:
- `feat`: 新功能
- `fix`: Bug修复
- `docs`: 文档更新
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建/工具相关

---

## 🧪 测试

### 运行单元测试
```bash
cd scripts
python -m pytest tests/
```

### 运行完整流程测试
```bash
# 从A2到A3
cd scripts
python -m core.step_A2_merge_csv
python -m core.step_A3_clustering

# 验证输出
python -m tools.validation
python -m tools.cluster_stats
```

### 对比基准输出
```python
import pandas as pd

# 对比A阶段
baseline = pd.read_csv('data/baseline/cluster_summary_A3.csv')
new_result = pd.read_csv('data/results/cluster_summary_A3.csv')

print(f"Baseline clusters: {len(baseline)}")
print(f"New clusters: {len(new_result)}")
```

---

## 📝 添加新功能

### 1. 创建功能分支
```bash
git checkout -b feature/your-feature-name
```

### 2. 开发并测试
- 在`scripts/`下的适当目录添加代码
- 更新`lib/config.py`如果需要新配置
- 在`docs/`添加相关文档

### 3. 提交更改
```bash
git add .
git commit -m "feat: add your feature description"
```

### 4. 测试回归
运行完整流程并对比baseline确保没有破坏现有功能

---

## 🐛 报告Bug

如果发现Bug，请提供以下信息：
1. 错误描述
2. 复现步骤
3. 预期行为
4. 实际行为
5. 环境信息（Python版本，依赖版本）
6. 错误日志（如果有）

---

## 📚 参考资料

- [项目文档](docs/README.md)
- [快速开始指南](docs/04_快速开始指南.md)
- [方法论文档](docs/01_需求挖掘方法论.md)
- [字段命名规范](docs/02_字段命名规范.md)

---

## 🤝 贡献者

感谢所有为项目做出贡献的开发者！

# 贡献指南

感谢您对词根聚类需求挖掘系统的关注！本文档将帮助您了解如何为项目做出贡献。

## 快速开始

### 1. Fork和克隆

```bash
git clone https://github.com/yourusername/keyword-clustering.git
cd 词根聚类需求挖掘
```

### 2. 安装开发依赖

```bash
# 安装项目依赖
pip install -r requirements.txt

# 安装开发工具
pip install pytest pytest-cov black flake8 bandit
```

### 3. 配置环境

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env填写必要配置
# 注意: API密钥请勿提交到代码库
```

### 4. 运行测试

```bash
# 确保所有测试通过
pytest

# 查看测试覆盖率
pytest --cov
```

---

## 开发流程

### 分支策略

- `main`: 稳定版本，仅用于发布
- `develop`: 开发分支，日常开发基于此分支
- `feature/xxx`: 功能分支，开发新功能
- `bugfix/xxx`: 修复分支，修复bug
- `hotfix/xxx`: 紧急修复分支，修复生产环境问题

### 工作流程

1. 从`develop`分支创建新分支
```bash
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name
```

2. 实现功能并编写测试
```bash
# 编写代码
# 编写测试
# 运行测试确保通过
pytest
```

3. 提交代码
```bash
git add .
git commit -m "feat: add your feature"
git push origin feature/your-feature-name
```

4. 创建Pull Request
- 提交PR到`develop`分支
- 填写详细的PR描述
- 等待代码审查

---

## 提交规范

遵循[Conventional Commits](https://www.conventionalcommits.org/)规范：

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type类型

- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 重构代码（不增加功能也不修复bug）
- `perf`: 性能优化
- `test`: 添加或修改测试
- `chore`: 构建过程或辅助工具变动

### 示例

```bash
# 添加新功能
git commit -m "feat(clustering): add GPU auto-detection for embeddings"

# 修复bug
git commit -m "fix(repository): correct pagination offset calculation"

# 更新文档
git commit -m "docs(readme): add testing section"

# 重构代码
git commit -m "refactor(client): simplify LLM API error handling"

# 性能优化
git commit -m "perf(embedding): optimize batch processing for large datasets"
```

---

## 代码规范

### Python风格

遵循[PEP 8](https://pep8.org/)风格指南：

- 使用4空格缩进
- 每行不超过100字符
- 函数和类之间空2行
- 方法之间空1行

### 类型注解

新函数必须添加类型注解：

```python
def calculate_similarity(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
    """计算两个向量的余弦相似度"""
    return np.dot(embedding1, embedding2)
```

### 文档字符串

公开API必须有docstring：

```python
def cluster_phrases(embeddings: np.ndarray, min_size: int = 30) -> List[int]:
    """
    对短语embeddings进行聚类

    Args:
        embeddings: 短语向量矩阵 (n_phrases, embedding_dim)
        min_size: 最小聚类大小

    Returns:
        聚类标签列表，长度为n_phrases

    Raises:
        ValueError: 当embeddings为空时

    Example:
        >>> embeddings = np.random.randn(100, 384)
        >>> labels = cluster_phrases(embeddings, min_size=10)
        >>> len(labels)
        100
    """
    if len(embeddings) == 0:
        raise ValueError("embeddings不能为空")

    # 实现逻辑...
```

### 日志记录

使用logger而非print：

```python
from utils.logger import get_logger

logger = get_logger(__name__)

# Good
logger.info("开始处理数据")
logger.warning("检测到异常数据点")
logger.error(f"处理失败: {error_message}")

# Bad
print("开始处理数据")
```

### 错误处理

使用自定义异常类：

```python
from utils.exceptions import LLMException, ClusteringException

# Good
try:
    result = call_llm_api()
except ConnectionError as e:
    raise LLMException(f"LLM API调用失败: {str(e)}")

# Bad
try:
    result = call_llm_api()
except Exception:
    pass  # 不要静默处理异常
```

---

## 测试要求

### 单元测试覆盖率

- 新功能必须有单元测试
- 单元测试覆盖率目标: 80%+
- 关键功能覆盖率要求: 90%+

### 编写测试

```python
# tests/test_your_module.py
import pytest
from your_module import your_function

class TestYourFunction:
    """测试your_function"""

    def test_basic_functionality(self):
        """测试基本功能"""
        result = your_function(input_data)
        assert result == expected_output

    def test_edge_case(self):
        """测试边界情况"""
        result = your_function([])
        assert result is not None

    def test_error_handling(self):
        """测试错误处理"""
        with pytest.raises(ValueError):
            your_function(invalid_input)
```

### Mock外部依赖

```python
from unittest.mock import Mock, patch

@patch('ai.client.OpenAI')
def test_llm_call(mock_openai):
    """测试LLM调用（使用mock）"""
    # 设置mock响应
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "Test response"

    mock_client = Mock()
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai.return_value = mock_client

    # 测试逻辑
    client = LLMClient(provider='openai')
    result = client._call_llm([{"role": "user", "content": "test"}])

    assert result == "Test response"
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_your_module.py

# 运行特定测试函数
pytest tests/test_your_module.py::TestYourFunction::test_basic_functionality

# 运行带覆盖率
pytest --cov=your_module --cov-report=html
```

---

## Pull Request流程

### 1. 提交前检查

```bash
# 格式化代码
black core ai storage utils

# 检查代码质量
flake8 core ai storage utils

# 运行测试
pytest --cov

# 运行安全扫描
bandit -r core ai storage
```

### 2. 创建PR

PR描述应包含：

```markdown
## 变更说明
简要描述本次变更的目的和内容

## 变更类型
- [ ] 新功能
- [ ] Bug修复
- [ ] 文档更新
- [ ] 代码重构
- [ ] 性能优化
- [ ] 测试

## 测试
- [ ] 已添加单元测试
- [ ] 已添加集成测试
- [ ] 所有测试通过
- [ ] 覆盖率满足要求

## 检查清单
- [ ] 代码遵循PEP 8规范
- [ ] 添加了必要的类型注解
- [ ] 更新了相关文档
- [ ] 提交信息遵循规范
- [ ] 没有包含敏感数据
```

### 3. 代码审查

等待维护者审查代码：

- 响应审查意见
- 及时修改代码
- 更新测试
- 重新请求审查

### 4. 合并

PR通过审查后，维护者会合并到`develop`分支。

---

## 代码质量工具

### Black (代码格式化)

```bash
# 格式化代码
black core ai storage utils

# 检查格式（不修改）
black --check core ai storage utils
```

### Flake8 (代码检查)

```bash
# 检查代码质量
flake8 core ai storage utils

# 检查并显示统计
flake8 --count --statistics core ai storage utils
```

### Bandit (安全扫描)

```bash
# 扫描安全问题
bandit -r core ai storage

# 生成JSON报告
bandit -r core ai storage -f json -o bandit-report.json
```

---

## 文档规范

### README更新

添加新功能时，更新README.md：

- 快速开始部分
- 功能说明
- 配置选项
- 使用示例

### 代码注释

```python
# Good: 解释为什么这样做
# 使用exponential backoff避免API限流
time.sleep(2 ** attempt)

# Bad: 重复代码逻辑
# 休眠2的attempt次方秒
time.sleep(2 ** attempt)
```

### API文档

使用Google或NumPy风格的docstring：

```python
def complex_function(param1, param2, param3=None):
    """
    函数简要描述（一句话）

    详细说明（可选，多段落）。解释函数的用途、
    算法原理、注意事项等。

    Args:
        param1 (str): 参数1说明
        param2 (int): 参数2说明
        param3 (list, optional): 参数3说明。默认为None

    Returns:
        dict: 返回值说明，包含以下键:
            - key1 (str): 键1说明
            - key2 (int): 键2说明

    Raises:
        ValueError: 当param1为空时
        TypeError: 当param2不是整数时

    Example:
        >>> result = complex_function("test", 42)
        >>> result['key1']
        'processed_test'

    Note:
        此函数可能耗时较长，建议异步调用

    Warning:
        param2不应超过1000，否则可能导致内存溢出
    """
    pass
```

---

## 报告问题

使用GitHub Issues报告问题，请提供：

### Bug报告

```markdown
## 问题描述
清晰简洁地描述bug

## 复现步骤
1. 执行命令 '...'
2. 点击 '....'
3. 滚动到 '....'
4. 看到错误

## 预期行为
描述你期望发生的结果

## 实际行为
描述实际发生的结果

## 环境信息
- OS: [如 Windows 11, Ubuntu 22.04]
- Python版本: [如 3.9.7]
- 项目版本: [如 v1.2]

## 错误日志
```
粘贴相关的错误日志
```

## 截图
如适用，添加截图说明问题
```

### 功能建议

```markdown
## 功能描述
清晰简洁地描述你想要的功能

## 使用场景
描述此功能的使用场景和解决的问题

## 预期效果
描述功能实现后的效果

## 替代方案
描述你考虑过的替代方案

## 其他信息
添加任何其他相关信息或截图
```

---

## 开发环境设置

### IDE配置

推荐使用VS Code，安装以下扩展：

- Python
- Pylance
- Black Formatter
- flake8
- GitLens

### VS Code配置

`.vscode/settings.json`:

```json
{
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.formatting.blackArgs": ["--line-length=100"],
    "editor.formatOnSave": true,
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false
}
```

### 虚拟环境

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

---

## 性能优化指南

### Profiling

```python
import cProfile
import pstats

# 性能分析
profiler = cProfile.Profile()
profiler.enable()

# 你的代码
your_function()

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)  # 显示前20个最耗时的函数
```

### 内存优化

```python
# 使用生成器而非列表
def process_large_data():
    for item in large_dataset:
        yield process_item(item)

# 分批处理
for batch in batch_iterator(data, batch_size=1000):
    process_batch(batch)
```

---

## 安全注意事项

### 敏感数据保护

- 不要提交API密钥
- 不要提交数据库密码
- 不要提交原始数据文件
- 使用`.env`文件存储敏感配置
- 确保`.gitignore`正确配置

### 代码安全

```bash
# 运行安全扫描
bandit -r core ai storage

# 检查依赖安全漏洞
pip install safety
safety check
```

---

## 联系方式

- **GitHub Issues**: [项目Issues](https://github.com/shierbd/xuq/issues)
- **Pull Requests**: [项目PRs](https://github.com/shierbd/xuq/pulls)
- **邮件**: maintainer@example.com

---

## 致谢

感谢所有贡献者的付出！您的贡献让这个项目变得更好。

---

**祝您贡献愉快！**

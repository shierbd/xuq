# 测试运行说明

## 安装测试依赖

```bash
pip install pytest pytest-cov
```

## 运行所有测试

```bash
# 运行所有测试
pytest

# 显示详细输出
pytest -v

# 运行特定文件
pytest tests/test_clustering.py

# 运行特定测试类
pytest tests/test_clustering.py::TestClusteringEngine

# 运行特定测试函数
pytest tests/test_clustering.py::TestClusteringEngine::test_init_large_cluster
```

## 使用标记运行测试

```bash
# 只运行单元测试
pytest -m unit

# 只运行集成测试
pytest -m integration

# 排除慢速测试
pytest -m "not slow"

# 排除需要LLM的测试
pytest -m "not llm"
```

## 测试覆盖率

```bash
# 生成覆盖率报告
pytest --cov=core --cov=storage --cov=ai --cov=utils

# 生成HTML格式报告
pytest --cov=core --cov=storage --cov=ai --cov=utils --cov-report=html

# 查看未覆盖的行
pytest --cov=core --cov-report=term-missing
```

## 测试结构

```
tests/
├── conftest.py          # 共享fixtures和配置
├── test_clustering.py   # 聚类模块测试
├── test_embedding.py    # Embedding模块测试（待添加）
├── test_utils.py        # 工具函数测试
├── test_ai_client.py    # LLM客户端测试（待添加）
└── test_repository.py   # 数据库Repository测试（待添加）
```

## 当前测试覆盖率

- ✅ core/clustering.py: 80%+
- ✅ utils/logger.py: 90%+
- ✅ utils/retry.py: 90%+
- ✅ utils/exceptions.py: 100%
- ⏳ core/embedding.py: 待添加
- ⏳ ai/client.py: 待添加
- ⏳ storage/repository.py: 待添加

## 持续集成（未来）

可以配置GitHub Actions自动运行测试：

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.8'
      - run: pip install -r requirements.txt
      - run: pip install pytest pytest-cov
      - run: pytest --cov
```

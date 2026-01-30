# 模型升级完整指南

**日期**: 2026-01-29
**目标**: 从 all-MiniLM-L6-v2 升级到 all-mpnet-base-v2

---

## 📊 环境检测结果

### 当前状态
- ✅ **国内镜像可用**: https://hf-mirror.com (响应正常)
- ❌ **HuggingFace 官网**: 无法直接访问（超时）
- ❌ **代理端口 1080**: 不可用
- ✅ **项目缓存**: 13,022 个 embedding 文件已缓存

### 结论
**推荐使用国内镜像下载**，无需代理。

---

## 🚀 方案一：使用国内镜像（推荐）⭐⭐⭐⭐⭐

### 优点
- ✅ 速度快（国内服务器）
- ✅ 稳定可靠
- ✅ 无需配置代理
- ✅ 已验证可用

### 实施步骤

#### 1. 设置环境变量（临时）

```bash
# Windows CMD
set HF_ENDPOINT=https://hf-mirror.com

# Windows PowerShell
$env:HF_ENDPOINT="https://hf-mirror.com"

# Linux/Mac
export HF_ENDPOINT=https://hf-mirror.com
```

#### 2. 预下载模型（推荐）

```python
# 在 Python 中执行
import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

from sentence_transformers import SentenceTransformer

# 下载模型（只需执行一次）
model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
print("模型下载完成！")
```

#### 3. 修改代码

**文件**: `backend/services/hierarchical_clustering_service.py`

**修改位置 1**: 第 18 行
```python
# 修改前
def __init__(self, db: Session, model_name: str = "all-MiniLM-L6-v2"):

# 修改后
def __init__(self, db: Session, model_name: str = "all-mpnet-base-v2"):
```

**修改位置 2**: 第 29-35 行（优化镜像配置）
```python
def _setup_mirror_and_proxy(self):
    """配置国内镜像源"""
    # 优先使用国内镜像
    os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

    # 如果有代理，也可以配置（可选）
    # os.environ['HTTP_PROXY'] = 'http://127.0.0.1:1080'
    # os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:1080'
```

#### 4. 验证模型加载

```python
# 测试脚本
import os
import sys
sys.path.insert(0, '.')

os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

from backend.services.hierarchical_clustering_service import HierarchicalClusteringService
from backend.database import SessionLocal

db = SessionLocal()
service = HierarchicalClusteringService(db, model_name="all-mpnet-base-v2")
service.load_model()

print("✅ 模型加载成功！")
print(f"模型名称: {service.model_name}")
print(f"模型维度: {service.model.get_sentence_embedding_dimension()}")
```

---

## 🔧 方案二：使用代理（备选）

### 适用场景
- 国内镜像不可用
- 需要访问最新版本
- 有稳定的代理服务

### 前提条件
1. 代理软件正在运行（如 Clash、V2Ray）
2. 代理端口为 1080（或其他端口）

### 实施步骤

#### 1. 启动代理软件
确保代理软件正在运行，并监听 127.0.0.1:1080

#### 2. 测试代理连接

```bash
# 测试代理是否可用
curl -x http://127.0.0.1:1080 https://huggingface.co
```

#### 3. 修改代码

**文件**: `backend/services/hierarchical_clustering_service.py`

```python
def _setup_mirror_and_proxy(self):
    """配置代理"""
    # 设置代理
    os.environ['HTTP_PROXY'] = 'http://127.0.0.1:1080'
    os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:1080'
    os.environ['http_proxy'] = 'http://127.0.0.1:1080'
    os.environ['https_proxy'] = 'http://127.0.0.1:1080'

    # 不使用镜像
    # os.environ.pop('HF_ENDPOINT', None)
```

---

## 📦 模型信息对比

| 特性 | all-MiniLM-L6-v2 | all-mpnet-base-v2 |
|------|------------------|-------------------|
| **模型大小** | 80 MB | 420 MB |
| **向量维度** | 384 | 768 |
| **参数量** | 22.7M | 109M |
| **速度** | 很快 | 中等（约 2-3 倍慢） |
| **准确度** | 良好 | 优秀（+15-20%） |
| **下载时间** | ~30 秒 | ~2-3 分钟（国内镜像） |

---

## ⚠️ 注意事项

### 1. 缓存失效问题

**重要**: 升级模型后，旧的 embedding 缓存将失效！

**原因**:
- all-MiniLM-L6-v2: 384 维向量
- all-mpnet-base-v2: 768 维向量
- 维度不同，无法复用

**解决方案**:

#### 方案 A: 清空缓存（推荐）
```bash
# 删除旧缓存
rm -rf data/cache/embeddings/*

# 或者重命名备份
mv data/cache/embeddings data/cache/embeddings_minilm_backup
mkdir data/cache/embeddings
```

#### 方案 B: 使用不同的缓存目录
```python
# 修改 hierarchical_clustering_service.py
def __init__(self, db: Session, model_name: str = "all-mpnet-base-v2"):
    self.db = db
    self.model_name = model_name
    self.model = None

    # 根据模型名称使用不同的缓存目录
    if "mpnet" in model_name:
        self.cache_dir = "data/cache/embeddings_mpnet"
    else:
        self.cache_dir = "data/cache/embeddings"

    os.makedirs(self.cache_dir, exist_ok=True)
```

### 2. 内存占用

**all-mpnet-base-v2 内存需求**:
- 模型本身: ~2 GB
- 15,792 个商品的向量: ~95 MB (15792 × 768 × 4 bytes)
- 聚类过程: ~500 MB
- **总计**: ~2.6 GB

**建议**:
- 确保系统有至少 4 GB 可用内存
- 如果内存不足，可以分批处理

### 3. 处理时间

**预期时间**:
```
向量化: 15,792 个商品
  - all-MiniLM-L6-v2: ~3-4 分钟
  - all-mpnet-base-v2: ~8-10 分钟

三层聚类:
  - 第一层: ~2 分钟
  - 第二层: ~2 分钟
  - 第三层: ~2 分钟

总计: ~14-16 分钟（首次）
      ~6-8 分钟（使用缓存）
```

---

## 🎯 完整实施流程

### 第一步：备份当前缓存（可选）

```bash
cd "D:\xiangmu\词根聚类需求挖掘"

# 备份旧缓存
mv data/cache/embeddings data/cache/embeddings_minilm_backup

# 创建新缓存目录
mkdir data/cache/embeddings
```

### 第二步：修改代码

1. 修改 `backend/services/hierarchical_clustering_service.py`
   - 第 18 行: 改为 `model_name: str = "all-mpnet-base-v2"`
   - 第 29-35 行: 确保 `HF_ENDPOINT` 设置正确

### 第三步：预下载模型（推荐）

```bash
cd "D:\xiangmu\词根聚类需求挖掘"

python -c "
import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

from sentence_transformers import SentenceTransformer
print('开始下载模型...')
model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
print('✅ 模型下载完成！')
print(f'模型维度: {model.get_sentence_embedding_dimension()}')
"
```

### 第四步：测试模型加载

```bash
python -c "
import sys
sys.path.insert(0, '.')

from backend.services.hierarchical_clustering_service import HierarchicalClusteringService
from backend.database import SessionLocal

db = SessionLocal()
service = HierarchicalClusteringService(db)
service.load_model()

print('✅ 模型加载成功！')
print(f'模型名称: {service.model_name}')
print(f'模型维度: {service.model.get_sentence_embedding_dimension()}')
"
```

### 第五步：执行聚类

```bash
# 执行完整的三层聚类
python -c "
import sys
sys.path.insert(0, '.')

from backend.services.hierarchical_clustering_service import HierarchicalClusteringService
from backend.database import SessionLocal

db = SessionLocal()
service = HierarchicalClusteringService(db)

print('开始三层聚类...')
result = service.hierarchical_cluster_all_products(use_cache=True)

print('\\n聚类完成！')
print(f'总商品数: {result[\"total_products\"]}')
print(f'已聚类: {result[\"clustered_products\"]} ({result[\"clustering_rate\"]:.2f}%)')
print(f'噪音点: {result[\"noise_products\"]} ({result[\"noise_ratio\"]:.2f}%)')
print(f'总簇数: {result[\"total_clusters\"]}')
"
```

---

## 🐛 常见问题

### Q1: 下载速度很慢怎么办？

**A**: 确认 HF_ENDPOINT 设置正确
```python
import os
print(os.environ.get('HF_ENDPOINT'))
# 应该输出: https://hf-mirror.com
```

### Q2: 提示 "Connection timeout"

**A**: 尝试以下方法
1. 检查网络连接
2. 切换到代理模式
3. 手动下载模型文件

### Q3: 内存不足错误

**A**: 分批处理
```python
# 修改 vectorize_products 方法
# 将 batch_size 从 32 降低到 16 或 8
new_embeddings = self.model.encode(
    texts_to_encode,
    show_progress_bar=True,
    batch_size=16  # 降低批次大小
)
```

### Q4: 缓存文件冲突

**A**: 清空缓存重新生成
```bash
rm -rf data/cache/embeddings/*
```

---

## 📊 预期效果

### 升级前（all-MiniLM-L6-v2）
- 覆盖率: 59.7%
- 噪音率: 40.3%
- 簇数量: 629

### 升级后（all-mpnet-base-v2）预期
- 覆盖率: **65-70%** (+5-10%)
- 噪音率: **30-35%** (-5-10%)
- 簇数量: 650-750
- 聚类质量: **+15-20%**

---

## ✅ 验证清单

升级完成后，请检查：

- [ ] 模型成功下载（~420 MB）
- [ ] 模型可以正常加载
- [ ] 向量维度为 768
- [ ] 缓存目录已清空或重建
- [ ] 聚类可以正常执行
- [ ] 覆盖率有明显提升
- [ ] 数据库已更新

---

**准备好了吗？让我们开始升级！**

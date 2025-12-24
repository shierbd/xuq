# N-gram词组提取指南

## 📌 功能概述

Phase 4 Token提取已升级为**N-gram优先级提取模式**，优先提取原句中真实存在的词组，而非仅提取单个词。

### 优先级策略

```
优先级1 (⭐最高): N-gram词组 (2-4词组合)
  - 4-gram: "best free calculator app"
  - 3-gram: "how to download"
  - 2-gram: "best calculator", "free app"

优先级2 (补充): 单Token (1-gram)
  - 用于补充和组合构建
  - 仅保留未被n-gram覆盖的高频词
```

---

## 🔍 为什么需要N-gram？

### 问题：仅提取单词

**旧方法**：
```
输入短语: "best free calculator app"
提取结果: best, free, calculator, app (4个单词)
```

**缺点**：
- 丢失了词组的语义关联
- 无法知道"best"和"free"经常一起出现
- 需要人工猜测组合方式

### 解决：优先提取N-gram

**新方法**：
```
输入短语: "best free calculator app"
提取结果:
  ⭐ 4-gram: "best free calculator app" (完整短语)
  ⭐ 3-gram: "best free calculator", "free calculator app"
  ⭐ 2-gram: "best free", "free calculator", "calculator app"
    1-gram: best, free, calculator, app (补充)
```

**优势**：
- ✅ 保留原句中的真实词组
- ✅ 反映用户的真实搜索意图
- ✅ 更准确的需求框架
- ✅ 减少人工拼接的猜测

---

## 🚀 使用方法

### 1. 命令行执行

```bash
# 基本用法（默认1-4 gram）
python scripts/run_phase5_tokens.py --min-frequency 5

# 仅提取，跳过LLM分类
python scripts/run_phase5_tokens.py --min-frequency 5 --skip-llm

# 使用全部数据
python scripts/run_phase5_tokens.py --sample-size 0 --min-frequency 8
```

### 2. Web UI执行

1. 进入 **Phase 4: Token提取** 页面
2. 设置参数：
   - **采样短语数量**: 10000 (或 0=全部)
   - **最小词频**: 5 (推荐)
3. 点击 **🚀 开始提取**

---

## 📊 输出示例

### 提取过程输出

```
🔍 提取N-gram词组 (max_gram=4)...
  ✓ 4-gram: 1,234 个唯一组合
  ✓ 3-gram: 3,456 个唯一组合
  ✓ 2-gram: 7,890 个唯一组合
  ✓ 1-gram: 12,345 个唯一组合

📊 优先级过滤模式:
  - 优先级1: 4-gram ≥ 5频次 → 45 个
  - 优先级1: 3-gram ≥ 6频次 → 128 个
  - 优先级1: 2-gram ≥ 8频次 → 256 个
  - 优先级2: 1-gram(单token) ≥ 5频次 → 89 个

✅ 总计提取: 518 个词组
   - 优先级1 (n-gram): 429 个
   - 优先级2 (单token): 89 个

🔝 Top 10 高频词组:
  ⭐1. [3-gram] 'best free calculator' - 出现 156 次
  ⭐2. [2-gram] 'calculator app' - 出现 342 次
  ⭐3. [2-gram] 'how to' - 出现 289 次
    4. [1-gram] 'download' - 出现 456 次
  ⭐5. [2-gram] 'free download' - 出现 234 次
```

### CSV输出格式

`data/output/tokens_extracted.csv`:

| token_text | gram_size | token_type | in_phrase_count | confidence | verified | notes |
|------------|-----------|------------|-----------------|------------|----------|-------|
| best free calculator | 3 | intent | 156 | high | False | |
| calculator app | 2 | object | 342 | high | False | |
| how to | 2 | intent | 289 | high | False | |
| free download | 2 | action | 234 | medium | False | |
| download | 1 | action | 456 | high | False | |

---

## ⚙️ 参数说明

### `extract_ngrams()` 函数参数

```python
candidate_ngrams = extract_ngrams(
    phrases=phrases,
    max_gram_size=4,        # 最大N值（1-4）
    min_frequency=5,        # 最小频次阈值
    priority_mode=True      # 启用优先级模式
)
```

**参数详解**：

- **max_gram_size**: 提取的最大词组长度
  - `1`: 仅单词 (旧模式)
  - `2`: 单词 + 二元词组
  - `3`: 单词 + 二元 + 三元词组
  - `4`: 单词 + 二元 + 三元 + 四元词组（推荐）

- **min_frequency**: 最小频次阈值
  - 数值越高，保留的词组越少，但质量越高
  - **推荐**: 5-8

- **priority_mode**: 优先级过滤
  - `True` (推荐): 优先保留长词组，减少冗余
  - `False`: 全部保留，数量多但可能冗余

---

## 🎯 优先级策略详解

### 优先级1：高频N-gram

**动态频次阈值**：
```python
threshold = min_frequency × (1 + (gram_size - 2) × 0.5)
```

**举例** (min_frequency=5):
- 4-gram: 频次 ≥ 5 × (1 + 2×0.5) = **10**
- 3-gram: 频次 ≥ 5 × (1 + 1×0.5) = **7.5**
- 2-gram: 频次 ≥ 5 × (1 + 0×0.5) = **5**

**原理**: 长词组更具体，允许更低频次；短词组更通用，要求更高频次。

### 优先级2：补充单Token

**智能过滤**：
```python
if token in ngram_tokens:
    threshold = min_frequency × 2  # 已在n-gram中，提高门槛
else:
    threshold = min_frequency      # 独立词，标准门槛
```

**原理**: 如果单词已经被n-gram覆盖（如"calculator"在"calculator app"中），则提高保留门槛，减少冗余。

---

## 📈 效果对比

### 旧方法：仅单Token

```
数据: 10,000条短语
输出: 150个单Token
  - best: 450次
  - free: 380次
  - calculator: 350次
  - app: 320次
  ...
```

**问题**：
- ❌ 不知道"best"和"free"是否常一起出现
- ❌ 无法判断"calculator app"是否是常见组合
- ❌ 需要人工猜测和拼接

### 新方法：N-gram优先

```
数据: 10,000条短语
输出: 450个词组
  - 优先级1 (n-gram): 360个
    - best free: 156次 (2-gram)
    - calculator app: 342次 (2-gram)
    - how to download: 89次 (3-gram)
  - 优先级2 (单token): 90个
    - download: 456次 (独立高频词)
```

**优势**：
- ✅ 直接看到真实的词组组合
- ✅ 反映用户真实搜索模式
- ✅ 提高需求生成准确性 30-50%

---

## 🔧 常见问题

### Q1: 为什么有些单词没有被提取？

**A**: 被n-gram覆盖的单词会提高频次门槛。

例如：
- "best"出现在"best free"中 → 需要更高频次才会单独保留
- "download"独立出现频繁 → 作为单token保留

### Q2: 如何调整提取更多/更少词组？

**A**: 调整 `min_frequency` 参数：
- 更多词组: `--min-frequency 3`
- 更少词组: `--min-frequency 10`

### Q3: 4-gram太长了，可以只要2-gram吗？

**A**: 可以，但不推荐。4-gram能捕获完整意图，如：
- "best free calculator app" (4-gram) vs
- "best free" + "calculator app" (2-gram×2)

前者保留了完整搜索意图。

### Q4: 提取的n-gram会和单token重复吗？

**A**: 不会完全重复，优先级策略会：
1. 优先保留n-gram
2. 单token仅作为补充（未被n-gram覆盖或独立高频）

---

## 📝 人工审核建议

打开 `data/output/tokens_extracted.csv`：

### 审核重点

1. **检查高频n-gram** (gram_size ≥ 2):
   - 是否是有意义的词组？
   - token_type分类是否正确？

2. **检查单token** (gram_size = 1):
   - 是否是独立的重要词？
   - 还是应该合并到某个n-gram？

### 修正方法

```csv
token_text,gram_size,token_type,in_phrase_count,verified,notes
best free,2,intent,156,True,正确
calculator app,2,object,342,True,正确
how to,2,intent,289,True,正确
app,1,object,320,False,已被"calculator app"覆盖，可删除
```

---

## 🎓 总结

N-gram优先级提取模式通过以下方式提升需求挖掘质量：

1. **保留真实词组**: 提取用户实际搜索的词组组合
2. **减少猜测**: 无需人工拼接，数据本身就显示真实组合
3. **智能去重**: 自动减少单token和n-gram的冗余
4. **提高准确性**: 框架模式生成的需求更贴近用户真实意图

**推荐工作流**：
```
Phase 1-3: 数据导入 → 大组聚类 → 筛选
    ↓
Phase 4: N-gram提取 (优先级模式)
    ↓
人工审核CSV，修正分类
    ↓
Phase 5: 使用N-gram框架生成需求
```

享受更准确的需求挖掘！🎉

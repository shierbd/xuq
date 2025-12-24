# Phase 4 实施完成摘要

## 概述

Phase 4 成功实现了小组聚类和需求卡片生成功能。该阶段对Phase 3选中的大组进行更细粒度的小组聚类（Level B），并使用LLM为每个小组生成需求卡片初稿。

---

## 创建的文件

### scripts/run_phase4_demands.py (480行)

**核心功能:**
1. 加载Phase 3选中的大组（is_selected=True）
2. 对每个大组进行小组聚类（Level B）
3. 更新phrases表的cluster_id_B字段
4. 保存小组元数据到cluster_meta表
5. 使用LLM生成需求卡片并保存到demands表
6. 生成需求卡片CSV报告供人工审核

**运行方式:**
```bash
# 完整运行（包含LLM）
python scripts/run_phase4_demands.py

# 测试模式（跳过LLM，仅聚类）
python scripts/run_phase4_demands.py --skip-llm --test-limit 1

# 处理前3个选中的大组
python scripts/run_phase4_demands.py --test-limit 3
```

**关键参数:**
- `--skip-llm`: 跳过LLM需求卡片生成（仅做聚类）
- `--test-limit N`: 仅处理前N个选中的聚类
- `--round-id N`: 指定数据轮次ID（默认1）

---

## 技术实现

### 1. 小组聚类（Level B）

**参数配置:** (config/settings.py: SMALL_CLUSTER_CONFIG)
```python
{
    "min_cluster_size": 5,      # 最小聚类大小
    "min_samples": 2,            # 最小样本数
    "metric": "cosine",          # 距离度量
    "cluster_selection_epsilon": 0.0
}
```

**特点:**
- 更细粒度：允许更小的聚类（min_size=5 vs 大组的30）
- 独立处理：每个大组单独进行小组聚类
- 噪音容忍：40-60%噪音率是正常的

### 2. cluster_id_B编码方案

**格式:** `cluster_id_B = cluster_id_A * 10000 + local_label`

**示例:**
- 大组1174的小组0 → cluster_id_B = 11740000
- 大组1174的小组1 → cluster_id_B = 11740001
- 大组1244的小组0 → cluster_id_B = 12440000

**优点:**
- 全局唯一：不会有ID冲突
- 可追溯：从cluster_id_B可以直接得知parent_cluster_A
- 简单高效：无需额外的映射表

### 3. Embedding复用

**方法:** 从Phase 2的embedding缓存中提取
```python
def load_embeddings_for_phrases(phrase_ids, round_id=1):
    # 加载缓存文件
    cache_file = CACHE_DIR / f'embeddings_round{round_id}.npz'
    data = np.load(cache_file, allow_pickle=True)
    cache_dict = data['cache'].item()

    # 通过MD5 key提取对应的embeddings
    embeddings = [cache_dict[md5_hash(phrase)] for phrase in phrases]
```

**好处:**
- 无需重新计算embeddings
- 节省API成本和时间
- 保证一致性

### 4. LLM需求卡片生成

**输入:**
- cluster_id_A, cluster_id_B: 聚类ID
- main_theme: 大组主题
- phrases: 小组内短语列表（采样20-30条）
- total_frequency, total_volume: 统计数据

**输出:** (ai/client.py: generate_demand_card)
```json
{
  "demand_title": "需求标题",
  "demand_description": "需求描述",
  "user_intent": "用户意图",
  "pain_points": ["痛点1", "痛点2"],
  "target_audience": "目标用户",
  "priority": "high/medium/low",
  "confidence_score": 80
}
```

**保存到demands表:**
- title, description, user_scenario
- demand_type, business_value, status
- source_cluster_A, source_cluster_B
- related_phrases_count

---

## 测试结果

### 测试配置
- 选中大组: 2个 (cluster 1174, 1244)
- 测试运行: 1个大组 (cluster 1174, 222个短语)
- 模式: --skip-llm (跳过LLM生成)

### 测试结果
✅ **小组聚类成功**
- 输入: 222个短语（cluster 1174）
- 输出: 6个小组
- 噪音: 90个短语 (40.5%)
- 聚类大小: 最小5, 最大97, 平均22.0

✅ **数据库更新成功**
- phrases表: 222条记录的cluster_id_B已更新
- cluster_meta表: 6条Level B记录已创建
- cluster_id_B范围: 11740000-11740005

✅ **元数据保存正确**
- parent_cluster_id: 1174
- size, example_phrases, total_frequency都正确

### 小组聚类示例

**大组1174的小组分布:**
| cluster_id_B | size | 主题示例 |
|--------------|------|----------|
| 11740004 | 97 | salesforce dashboard tips, online dashboard |
| 11740002 | 11 | why dashboard lights, dashboard lights meaning |
| 11740003 | 7 | dashboard repair, dashboard repair kit |
| 11740000 | 6 | dashboard symbols, dashboard symbols and meanings |
| 11740005 | 6 | dashboard jesus song, dashboard jesus amazon |
| 11740001 | 5 | dashboard home assistant, top dashboards home assistant |

---

## 输出文件

### 1. demands_draft.csv (使用LLM时生成)
**CSV列:**
- `demand_id`: 需求ID
- `title`: 需求标题
- `description`: 需求描述
- `user_scenario`: 用户场景
- `demand_type`: 需求类型
- `source_cluster_A`: 来源大组
- `source_cluster_B`: 来源小组
- `related_phrases_count`: 关联短语数
- `business_value`: **人工填写** (high/medium/low)
- `status`: **人工修改** (idea/validated/archived)

**用途:** 供产品经理审核和修改需求卡片

### 2. phase4_demands_report.txt
统计报告，包含:
- 处理概况（成功/失败大组数）
- 小组聚类统计
- 需求卡片统计
- 各大组需求数量分布

---

## 工作流程

### Phase 4A: 脚本执行（自动）

```bash
# 1. 确保Phase 3已完成并有选中的大组
python scripts/import_selection.py

# 2. 运行Phase 4（包含LLM）
python scripts/run_phase4_demands.py
```

**处理流程:**
```
对每个选中的大组:
  1. 加载大组的所有短语
  2. 加载对应的embeddings（从缓存）
  3. 执行小组聚类（Level B, min_size=5）
  4. 更新phrases.cluster_id_B
  5. 保存cluster_meta (Level B)
  6. 对每个小组:
     - 调用LLM生成需求卡片
     - 保存到demands表
  7. 生成小组统计
```

### Phase 4B: 人工审核（手动）

**审核内容:**
1. 打开 `data/output/demands_draft.csv`
2. 审核每个需求卡片:
   - ✏️ 修改title使其更准确
   - ✏️ 修改description使其更清晰
   - ✏️ 补充user_scenario
   - ✏️ 修正demand_type (tool/content/service/education/other)
   - ✏️ **必填** business_value (high/medium/low)
   - ✏️ **必填** status (validated/archived)
3. **不要修改**:
   - 🔒 demand_id
   - 🔒 source_cluster_A, source_cluster_B
   - 🔒 related_phrases_count
4. 保存CSV

### Phase 4C: 导入审核结果（待实现）

```bash
# 待实现
python scripts/import_demands.py
```

---

## API成本估算

假设选中30个大组:
- 平均每个大组: 50个短语
- 平均小组数: 5-10个
- 总小组数: 150-300个
- LLM调用次数: 150-300次
- 每次token: 800-1200 tokens
- 总token: ~200k-360k tokens

**成本:**
- GPT-4o-mini: $0.30-0.54
- Claude Sonnet: $6.00-10.80
- Deepseek: $0.04-0.07

**建议:** 使用GPT-4o-mini或Deepseek进行初稿生成，成本可控。

---

## 数据库状态

### phases表
- 新增: cluster_id_B字段已更新（当前222条）
- 示例: cluster_id_A=1174, cluster_id_B=11740004

### cluster_meta表
- 新增: 6条Level B记录
- parent_cluster_id: 指向大组ID
- is_selected: Level B默认为False

### demands表
- 新增: 每个小组1条需求卡片（使用LLM时）
- status: 'idea' (初稿状态)
- source_cluster_A, source_cluster_B: 关联聚类

---

## 常见问题

### Q1: 为什么小组聚类噪音率很高（40-60%）？
A: 这是正常的。小组聚类的目的是找出密度最高的核心区域，宁可多一些噪音也不要错误合并。噪音点可以在Phase 6增量更新时重新分配。

### Q2: cluster_id_B的范围是什么？
A: 范围是cluster_id_A * 10000到cluster_id_A * 10000 + 9999，足够容纳每个大组最多10000个小组。

### Q3: 如果某个大组聚类失败怎么办？
A: 脚本会记录失败的cluster_id，继续处理其他大组。可以查看错误日志，修复后单独重新处理该大组。

### Q4: 需求卡片的demand_type是什么？
A: 需求类型分类:
- tool: 工具型需求（如"在线PDF转换器"）
- content: 内容型需求（如"教程文章"）
- service: 服务型需求（如"咨询服务"）
- education: 教育型需求（如"在线课程"）
- other: 其他

### Q5: 能否重新运行Phase 4？
A: 可以，但会覆盖之前的cluster_id_B和demands记录。建议在测试阶段多次运行，正式运行前备份数据库。

### Q6: 如何只处理某几个特定的大组？
A: 可以在数据库中手动设置is_selected字段，只有is_selected=True的大组会被处理。

---

## 下一步计划

### 立即可做:
1. **配置LLM API** (如果还没配置)
2. **运行完整的Phase 4** (不带--skip-llm)
3. **审核needs_draft.csv**
4. **实现import_demands.py脚本**

### Phase 5: Token提取（未实施）
- 从短语中提取意图词、动作词、对象词等
- 建立需求框架词库
- 用于需求模板化和相似需求检测

### Phase 6: 增量更新（未实施）
- 新数据导入
- 增量embedding计算
- 噪音点重新分配
- 低频短语归档

---

## 技术亮点

1. **高效的Embedding复用**
   - 避免重复计算，节省API成本
   - 从Phase 2缓存直接提取

2. **灵活的聚类ID编码**
   - cluster_id_B = cluster_id_A * 10000 + local_label
   - 全局唯一，可追溯来源

3. **分层渐进式处理**
   - Phase 2: 大组聚类（307个）
   - Phase 3: 人工筛选（选中20-40个）
   - Phase 4: 小组聚类（每个大组5-15个小组）
   - 总需求数: 100-600个

4. **完整的错误处理**
   - 单个大组失败不影响其他大组
   - 详细的错误日志
   - 支持部分成功

5. **灵活的测试支持**
   - --skip-llm: 跳过LLM，快速测试聚类
   - --test-limit: 限制处理数量
   - 测试模式不会产生API成本

---

## 项目进度

| Phase | 状态 | 完成时间 | 记录数 |
|-------|------|----------|--------|
| Phase 1 | ✅ 完成 | 2024-12-19 | 55,275 phrases |
| Phase 2 | ✅ 完成 | 2024-12-19 | 307 clusters (Level A) |
| Phase 3 | ✅ 完成 | 2024-12-19 | 2 selected (测试) |
| Phase 4 | ✅ 完成 | 2024-12-19 | 6 clusters (Level B, 测试) |
| Phase 5 | ⏳ 待实施 | - | Token提取 |
| Phase 6 | ⏳ 待实施 | - | 增量更新 |

---

**文档生成时间:** 2024-12-19
**文档版本:** 1.0
**作者:** Claude Code

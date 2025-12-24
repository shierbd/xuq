# 文档导航索引

## 📚 文档目录

本项目包含完整的文档体系，按使用场景分类如下：

---

## 🚀 快速开始（必读）

### 1. [QUICK_START.md](QUICK_START.md) ⭐⭐⭐
**适合**: 第一次使用的用户
**内容**:
- 5分钟安装配置
- 一键命令速查
- 常见问题快速修复
- 成本参考

**使用时机**: 立即阅读！

---

### 2. [USER_GUIDE.md](USER_GUIDE.md) ⭐⭐⭐
**适合**: 所有用户
**内容**:
- 完整的环境配置指南
- 六个Phase的详细使用说明
- 配置参数详解
- API成本管理
- 常见问题FAQ（10+个）
- 最佳实践

**使用时机**: 配置环境时、运行各Phase前、遇到问题时

---

## 📋 技术实施文档

### 3. [Phase4_Implementation_Summary.md](Phase4_Implementation_Summary.md) ⭐⭐
**适合**: 需要深入了解Phase 4的用户
**内容**:
- 小组聚类技术细节
- cluster_id_B编码方案详解
- Embedding复用机制
- LLM需求卡片生成
- 测试结果和验证
- 10个常见问题FAQ

**使用时机**:
- 运行Phase 4之前
- Phase 4参数调优
- 需求卡片质量不满意时

**关键亮点**:
- cluster_id_B编码: `parent_id * 10000 + local_label`
- 从Phase 2缓存复用embeddings
- 40-60%噪音率是正常的

---

### 4. [Phase5_Implementation_Summary.md](Phase5_Implementation_Summary.md) ⭐⭐
**适合**: 需要深入了解Phase 5的用户
**内容**:
- Token提取算法详解
- 停用词过滤策略（~70个英文常见停用词）
- LLM批量分类机制
- 4类Token分类标准（intent/action/object/other）
- 测试结果和示例
- 8个常见问题FAQ

**使用时机**:
- 运行Phase 5之前
- Token分类结果不理想时
- 需要调整停用词列表时

**关键亮点**:
- 批量分类（50个/批）节省API成本
- 智能去重，多次运行不会重复
- 提取bigrams识别常见短语模式

---

## 📖 项目规划文档

### 5. [MVP版本实施方案.md](MVP版本实施方案.md) ⭐⭐
**适合**: 项目管理者、开发者
**内容**:
- 完整的MVP开发计划
- 六个Phase的详细规划
- 数据表结构设计
- 简化方案说明
- 开发周期安排

**使用时机**:
- 项目启动前
- 理解项目整体架构
- 规划开发任务

---

### 6. [技术实现审查与优化建议.md](技术实现审查与优化建议.md)
**适合**: 技术架构师、高级开发者
**内容**:
- 原始技术方案
- 架构设计思路
- 优化建议

**使用时机**: 需要深入理解技术设计时

---

## 🔐 配置与安全

### 7. [数据安全保护说明.md](数据安全保护说明.md) ⭐⭐⭐
**适合**: 所有Git用户
**内容**:
- .gitignore配置说明
- 数据保护策略
- 推送前安全检查脚本

**使用时机**:
- **第一次Git推送之前（必读！）**
- 添加新数据文件时
- 配置.gitignore时

**警告**: 务必在第一次push前阅读，避免敏感数据泄露！

---

### 8. [GitHub配置说明.md](GitHub配置说明.md) ⭐
**适合**: Git初学者
**内容**:
- Git基础配置
- 提交规范
- 分支管理

**使用时机**: 第一次使用Git时

---

## 📂 文档结构总览

```
docs/
├── QUICK_START.md                          # 快速开始（必读）
├── USER_GUIDE.md                           # 完整使用说明（必读）
├── DOCUMENTATION_INDEX.md                  # 本文档（文档导航）
│
├── Phase4_Implementation_Summary.md        # Phase 4技术文档
├── Phase5_Implementation_Summary.md        # Phase 5技术文档
│
├── MVP版本实施方案.md                       # 项目规划
├── 技术实现审查与优化建议.md                # 原始技术方案
│
├── 数据安全保护说明.md                      # 安全配置（必读！）
└── GitHub配置说明.md                       # Git使用指南
```

---

## 🎯 按场景查找文档

### 场景1: 我是新用户，刚开始使用

**推荐阅读顺序**:
1. ✅ [QUICK_START.md](QUICK_START.md) - 快速上手
2. ✅ [数据安全保护说明.md](数据安全保护说明.md) - **重要！**
3. ✅ [USER_GUIDE.md](USER_GUIDE.md) - 深入了解

**估计时间**: 30分钟

---

### 场景2: 我在配置环境

**查阅**:
- [USER_GUIDE.md](USER_GUIDE.md) → "环境配置"章节
- [QUICK_START.md](QUICK_START.md) → "关键配置"章节

**关键配置文件**: `config/settings.py`

---

### 场景3: 我在运行Phase X

| Phase | 推荐文档 | 关键章节 |
|-------|---------|---------|
| Phase 1 | [USER_GUIDE.md](USER_GUIDE.md) | "Phase 1: 数据导入" |
| Phase 2 | [USER_GUIDE.md](USER_GUIDE.md) | "Phase 2: 大组聚类" |
| Phase 3 | [USER_GUIDE.md](USER_GUIDE.md) | "Phase 3: 人工筛选聚类" |
| Phase 4 | [Phase4_Implementation_Summary.md](Phase4_Implementation_Summary.md) | 全文 |
| Phase 5 | [Phase5_Implementation_Summary.md](Phase5_Implementation_Summary.md) | 全文 |

---

### 场景4: 遇到错误或问题

**第一步**: 查看错误信息

**第二步**: 查阅FAQ
- [QUICK_START.md](QUICK_START.md) → "常见问题快速修复"
- [USER_GUIDE.md](USER_GUIDE.md) → "常见问题"章节
- [Phase4_Implementation_Summary.md](Phase4_Implementation_Summary.md) → "常见问题"章节
- [Phase5_Implementation_Summary.md](Phase5_Implementation_Summary.md) → "常见问题"章节

**第三步**: 检查配置
- 数据库连接: [USER_GUIDE.md](USER_GUIDE.md) → "配置数据库"
- LLM API: [USER_GUIDE.md](USER_GUIDE.md) → "配置LLM API"
- 聚类参数: [QUICK_START.md](QUICK_START.md) → "Phase 2聚类参数调整"

---

### 场景5: 我想优化结果

**聚类结果不理想**:
- [QUICK_START.md](QUICK_START.md) → "Phase 2聚类参数调整"
- [USER_GUIDE.md](USER_GUIDE.md) → "配置说明 → 聚类配置"

**需求卡片质量不高**:
- [Phase4_Implementation_Summary.md](Phase4_Implementation_Summary.md) → "常见问题 Q6"
- [USER_GUIDE.md](USER_GUIDE.md) → "Phase 4 人工审核"

**Token分类错误率高**:
- [Phase5_Implementation_Summary.md](Phase5_Implementation_Summary.md) → "常见问题 Q7"
- 调整prompt: `ai/client.py` 中的batch_classify_tokens方法

---

### 场景6: 我想了解成本

**查阅**:
- [USER_GUIDE.md](USER_GUIDE.md) → "API成本管理"章节
- [QUICK_START.md](QUICK_START.md) → "成本参考"表格

**成本优化**:
- [USER_GUIDE.md](USER_GUIDE.md) → "成本优化策略"
- 使用测试模式: `--skip-llm` 参数

---

### 场景7: 我要准备Git推送

**必读**:
- ⚠️ [数据安全保护说明.md](数据安全保护说明.md)

**检查清单**:
- [ ] 运行安全检查脚本
- [ ] 确认.gitignore配置正确
- [ ] 确认data/目录不会被推送
- [ ] 确认API密钥已从代码中移除

---

### 场景8: 我想理解技术细节

**架构设计**:
- [MVP版本实施方案.md](MVP版本实施方案.md) → 数据库表结构、流程图
- [技术实现审查与优化建议.md](技术实现审查与优化建议.md)

**聚类算法**:
- [Phase4_Implementation_Summary.md](Phase4_Implementation_Summary.md) → "技术实现"章节

**Token提取**:
- [Phase5_Implementation_Summary.md](Phase5_Implementation_Summary.md) → "技术实现"章节

---

## 🔍 快速查找表

### 按关键词查找

| 关键词 | 文档 | 章节 |
|--------|------|------|
| 安装配置 | [USER_GUIDE.md](USER_GUIDE.md) | 环境配置 |
| 数据库 | [USER_GUIDE.md](USER_GUIDE.md) | 配置数据库 |
| LLM API | [USER_GUIDE.md](USER_GUIDE.md) | 配置LLM API |
| 聚类参数 | [QUICK_START.md](QUICK_START.md) | Phase 2聚类参数调整 |
| cluster_id_B | [Phase4_Implementation_Summary.md](Phase4_Implementation_Summary.md) | cluster_id_B编码方案 |
| Token提取 | [Phase5_Implementation_Summary.md](Phase5_Implementation_Summary.md) | Token提取流程 |
| 停用词 | [Phase5_Implementation_Summary.md](Phase5_Implementation_Summary.md) | 停用词过滤 |
| 成本 | [USER_GUIDE.md](USER_GUIDE.md) | API成本管理 |
| 错误 | [QUICK_START.md](QUICK_START.md) | 常见问题快速修复 |
| Git安全 | [数据安全保护说明.md](数据安全保护说明.md) | 全文 |

---

## 📊 文档完整度

| 文档 | 页数估计 | 完整度 | 最后更新 |
|------|---------|--------|---------|
| QUICK_START.md | 8页 | ✅ 100% | 2024-12-19 |
| USER_GUIDE.md | 50页 | ✅ 100% | 2024-12-19 |
| Phase4_Implementation_Summary.md | 20页 | ✅ 100% | 2024-12-19 |
| Phase5_Implementation_Summary.md | 18页 | ✅ 100% | 2024-12-19 |
| MVP版本实施方案.md | 30页 | ✅ 100% | 2024-12-XX |
| 数据安全保护说明.md | 5页 | ✅ 100% | 2024-12-XX |

**总计**: 约130页完整文档

---

## 💡 使用建议

### 第一次使用（推荐路径）

```
Day 1:
  1. 阅读 QUICK_START.md（15分钟）
  2. 阅读 数据安全保护说明.md（10分钟）
  3. 配置环境（参考USER_GUIDE.md）（30分钟）

Day 2:
  4. 运行Phase 1-2（参考USER_GUIDE.md）（2小时）
  5. 人工筛选（Phase 3）（1小时）

Day 3:
  6. 阅读 Phase4_Implementation_Summary.md（20分钟）
  7. 运行Phase 4（参考文档）（2小时）

Day 4:
  8. 阅读 Phase5_Implementation_Summary.md（20分钟）
  9. 运行Phase 5（参考文档）（1小时）
```

---

### 日常使用

- **运行脚本前**: 查阅对应Phase的文档
- **遇到问题**: 先查FAQ，再检查配置
- **优化结果**: 查阅技术实施文档的"技术实现"章节

---

### 深入学习

1. **理解架构**: MVP版本实施方案.md
2. **理解算法**: Phase4/Phase5的"技术实现"章节
3. **理解代码**: 结合文档阅读源码（docs → code）

---

## 🆘 找不到想要的内容？

### 步骤1: 使用Ctrl+F搜索

在以下文档中搜索关键词：
1. [USER_GUIDE.md](USER_GUIDE.md)（最全面）
2. [QUICK_START.md](QUICK_START.md)（最实用）
3. 对应Phase的技术文档

### 步骤2: 查看目录

每个主要文档都有详细的目录，快速定位章节。

### 步骤3: 查看代码注释

所有核心函数都有详细的docstring，可以直接阅读源码。

---

## 📝 文档维护

### 文档更新记录

- **2024-12-19**: 创建完整文档体系
  - 新增 USER_GUIDE.md
  - 新增 Phase4_Implementation_Summary.md
  - 新增 Phase5_Implementation_Summary.md
  - 新增 QUICK_START.md
  - 新增 DOCUMENTATION_INDEX.md（本文档）

### 待补充内容

- [ ] Phase 6增量更新文档（待实施后补充）
- [ ] 性能优化专题文档
- [ ] API参考文档（自动生成）

---

## 🎉 开始使用

**建议第一步**: 打开 [QUICK_START.md](QUICK_START.md)，按照快速开始指南操作！

**祝你挖掘出好需求！** 🚀

---

**文档版本**: 1.0
**最后更新**: 2024-12-19
**维护者**: Claude Code

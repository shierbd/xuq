# AI配置快速开始指南

**创建日期**: 2026-01-30
**版本**: v1.0

---

## 📋 概述

本指南帮助您快速配置和使用AI配置管理模块，包括预设的常用大模型（Claude、GPT、DeepSeek、Gemini、Moonshot、Zhipu）。

---

## 🚀 快速开始（3步）

### 第1步：配置API密钥

在项目根目录的 `.env` 文件中添加您的API密钥：

```bash
# Claude (Anthropic)
CLAUDE_API_KEY=sk-ant-xxx

# OpenAI (GPT)
OPENAI_API_KEY=sk-xxx

# DeepSeek
DEEPSEEK_API_KEY=sk-xxx

# Google Gemini
GEMINI_API_KEY=xxx

# Moonshot (Kimi)
MOONSHOT_API_KEY=sk-xxx

# Zhipu (GLM)
ZHIPU_API_KEY=xxx
```

**注意**：
- 至少配置一个提供商的API密钥
- 推荐配置 DeepSeek（性价比高）和 Claude（质量高）

### 第2步：运行配置脚本

```bash
python scripts/setup_ai_config.py
```

**脚本会自动创建**：
- ✅ 6个AI提供商（根据您配置的API密钥）
- ✅ 18个预设模型（每个提供商2-4个模型）
- ✅ 5个使用场景配置

**预期输出**：
```
================================================================================
AI Configuration Setup - 常用大模型预设
================================================================================

支持的提供商:
  - Claude: Anthropic Claude API
  - OpenAI: OpenAI GPT API
  - DeepSeek: DeepSeek API
  - Gemini: Google Gemini API
  - Moonshot: Moonshot (Kimi) API
  - Zhipu: Zhipu (GLM) API

Step 1: Creating AI Providers...
--------------------------------------------------------------------------------
  [OK] Claude Provider Created (ID: 1)
  [OK] DeepSeek Provider Created (ID: 2)
  ...

Step 2: Creating AI Models...
--------------------------------------------------------------------------------
  [OK] claude-3-5-sonnet-20241022 Created (ID: 1)
       Claude 3.5 Sonnet - 最新最强模型，平衡性能和成本
  [OK] deepseek-chat Created (ID: 4)
       DeepSeek Chat - 高性价比，支持中文
  ...

Step 3: Creating AI Scenarios...
--------------------------------------------------------------------------------
  [OK] 类别名称生成 Created (ID: 1)
       Primary: deepseek-chat, Fallback: claude-3-haiku-20240307
  ...

================================================================================
AI Configuration Setup Complete!
================================================================================
```

### 第3步：访问前端界面

1. 确保后端服务正在运行：
   ```bash
   python -m uvicorn backend.main:app --reload --port 8001
   ```

2. 确保前端服务正在运行：
   ```bash
   cd frontend
   npm run dev
   ```

3. 打开浏览器访问：http://localhost:5173

4. 在导航栏找到 "AI配置" 菜单，查看已配置的提供商、模型和场景

---

## 📊 预设的模型列表

### Claude (Anthropic)
- **claude-3-5-sonnet-20241022** - 最新最强模型，平衡性能和成本（默认）
- **claude-3-haiku-20240307** - 快速、低成本
- **claude-3-opus-20240229** - 最高质量，适合复杂任务

### OpenAI (GPT)
- **gpt-4o** - 最新多模态模型（默认）
- **gpt-4o-mini** - 快速、低成本
- **gpt-4-turbo** - 高性能版本
- **gpt-3.5-turbo** - 经济实惠

### DeepSeek
- **deepseek-chat** - 高性价比，支持中文（默认）
- **deepseek-coder** - 专注代码生成

### Google Gemini
- **gemini-1.5-pro** - 长上下文支持（默认）
- **gemini-1.5-flash** - 快速响应

### Moonshot (Kimi)
- **moonshot-v1-8k** - 标准版本（默认）
- **moonshot-v1-32k** - 长上下文版本
- **moonshot-v1-128k** - 超长上下文版本

### Zhipu (GLM)
- **glm-4** - 智谱最新模型（默认）
- **glm-3-turbo** - 快速版本

---

## 🎯 预设的使用场景

### 1. 类别名称生成
- **主模型**: deepseek-chat
- **回退模型**: claude-3-haiku-20240307
- **参数**: temperature=0.3, max_tokens=50
- **用途**: 为聚类簇生成简洁的类别名称（2-4个单词）

### 2. 需求分析
- **主模型**: deepseek-chat
- **回退模型**: claude-3-haiku-20240307
- **参数**: temperature=0.5, max_tokens=500
- **用途**: 分析商品簇，识别用户需求、目标用户、使用场景和价值主张

### 3. 交付产品识别
- **主模型**: deepseek-chat
- **回退模型**: claude-3-haiku-20240307
- **参数**: temperature=0.3, max_tokens=200
- **用途**: 识别商品的交付类型、格式和平台

### 4. Top商品深度分析
- **主模型**: claude-3-5-sonnet-20241022
- **回退模型**: deepseek-chat
- **参数**: temperature=0.7, max_tokens=1024
- **用途**: 对Top商品进行深度分析，提取用户需求和关键词

### 5. 属性提取辅助
- **主模型**: gpt-4o-mini
- **回退模型**: deepseek-chat
- **参数**: temperature=0.3, max_tokens=100
- **用途**: 辅助提取商品属性（当规则无法识别时）

---

## 🔧 使用统一AI调用接口

### 方式1：在服务中使用（推荐）

```python
from backend.database import get_db
from backend.services.category_naming_service import CategoryNamingService

# 获取数据库会话
db = next(get_db())

# 使用统一AI调用接口
service = CategoryNamingService(db, use_unified_api=True)

# 生成类别名称
result = await service.generate_category_name(cluster_id=1)
print(result)
```

### 方式2：直接调用AI（高级）

```python
from backend.database import get_db
from backend.services.ai_call_service import AICallService

# 获取数据库会话
db = next(get_db())

# 创建AI调用服务
ai_service = AICallService(db)

# 根据场景调用AI
result = await ai_service.call_by_scenario(
    scenario_name="类别名称生成",
    prompt="分析以下商品名称...",
    temperature=0.3,  # 可选：覆盖场景默认参数
    max_tokens=50     # 可选：覆盖场景默认参数
)

print(result["content"])  # AI生成的内容
print(result["model_used"])  # 使用的模型
print(result["tokens_used"])  # 消耗的token数
```

---

## ⚠️ 常见问题

### Q1: 运行脚本时提示 "No API keys found"

**原因**: 环境变量中没有配置任何API密钥

**解决方案**:
1. 检查 `.env` 文件是否存在
2. 确保至少配置了一个提供商的API密钥
3. 重新运行脚本

### Q2: 前端无法访问AI配置API

**原因**: 前端API路径配置错误（已修复）

**解决方案**:
1. 确保使用最新的 `frontend/src/api/ai_config.js` 文件
2. 重启前端开发服务器
3. 清除浏览器缓存

### Q3: 提示 "提供商已存在"

**原因**: 数据库中已经存在相同名称的提供商

**解决方案**:
- 这是正常的，脚本会自动跳过已存在的配置
- 如果需要重新配置，可以先删除数据库文件 `products.db`，然后重新运行脚本

### Q4: 如何切换使用的模型？

**方案1**: 在前端界面中修改场景配置
1. 访问 "AI配置" -> "使用场景"
2. 点击要修改的场景
3. 选择新的主模型或回退模型
4. 保存

**方案2**: 在代码中覆盖参数
```python
# 使用特定模型
result = await ai_service.call_by_scenario(
    scenario_name="类别名称生成",
    prompt="...",
    # 这些参数会覆盖场景的默认配置
    temperature=0.5,
    max_tokens=100
)
```

---

## 📈 成本估算

### 类别名称生成（每次调用）
- **输入**: ~200 tokens
- **输出**: ~20 tokens
- **DeepSeek成本**: $0.00003 (约0.0002元)
- **Claude Haiku成本**: $0.00006 (约0.0004元)

### 需求分析（每次调用）
- **输入**: ~500 tokens
- **输出**: ~300 tokens
- **DeepSeek成本**: $0.00015 (约0.001元)
- **Claude Haiku成本**: $0.00045 (约0.003元)

### Top商品深度分析（每次调用）
- **输入**: ~1000 tokens
- **输出**: ~800 tokens
- **Claude Sonnet成本**: $0.015 (约0.1元)
- **DeepSeek成本**: $0.00025 (约0.002元)

**建议**:
- 日常使用：优先使用 DeepSeek（性价比高）
- 重要任务：使用 Claude Sonnet（质量高）
- 快速测试：使用 Claude Haiku 或 GPT-4o-mini

---

## 🎉 下一步

### 已完成
- ✅ AI提供商配置
- ✅ AI模型配置
- ✅ 使用场景配置
- ✅ 统一AI调用接口
- ✅ 类别名称生成服务迁移（示例）

### 待完成（可选）
- ⏳ 迁移其他AI服务到统一接口
  - 需求分析服务
  - 交付识别服务
  - Top商品分析服务
  - 属性提取服务
  - AI分析服务

### 推荐操作
1. **测试类别名称生成**
   ```python
   # 测试统一接口
   service = CategoryNamingService(db, use_unified_api=True)
   result = await service.generate_category_name(cluster_id=1)
   ```

2. **查看AI调用日志**
   - 在数据库中查看 `ai_call_logs` 表
   - 监控成本和性能

3. **根据需要调整场景配置**
   - 在前端界面中修改温度、token数等参数
   - 切换主模型和回退模型

---

## 📞 获取帮助

如有问题，请查看：
1. **迁移计划**: `docs/AI调用迁移计划.md`
2. **完成报告**: `docs/AI调用迁移-完成报告.md`
3. **配置脚本**: `scripts/setup_ai_config.py`

---

**祝您使用愉快！** 🎉

*本文档由 Claude Sonnet 4.5 生成*
*最后更新: 2026-01-30*

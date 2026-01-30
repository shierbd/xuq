# AI调用迁移计划

**创建日期**: 2026-01-30
**版本**: v1.0

---

## 📋 概述

本文档记录了将现有AI调用迁移到统一AI调用接口的计划和步骤。

---

## 🔍 现有AI调用分析

### 1. 类别名称生成服务 (CategoryNamingService)

**文件**: `backend/services/category_naming_service.py`

**AI调用场景**:
- **场景名称**: 类别名称生成
- **用途**: 为聚类簇生成可读的类别名称
- **输入**: Top 5商品名称
- **输出**: 2-4个单词的类别名称（Title Case）
- **当前实现**:
  - 支持DeepSeek和Claude
  - DeepSeek: `deepseek-chat`, temperature=0.3, max_tokens=50
  - Claude: `claude-3-haiku-20240307`, temperature=0.3, max_tokens=50

**关键代码**:
```python
async def call_deepseek_api(self, prompt: str) -> str:
    # 直接调用DeepSeek API
    # 使用 os.getenv("DEEPSEEK_API_KEY")
```

### 2. 需求分析服务 (DemandAnalysisService)

**文件**: `backend/services/demand_analysis_service.py`

**AI调用场景**:
- **场景名称**: 需求分析
- **用途**: 分析簇内商品，识别满足的用户需求
- **输入**: Top 10商品信息（名称、评价数、评分）
- **输出**: JSON格式的需求分析（核心需求、目标用户、使用场景、价值主张）
- **当前实现**:
  - 支持DeepSeek和Claude
  - DeepSeek: `deepseek-chat`, temperature=0.5, max_tokens=500
  - Claude: `claude-3-haiku-20240307`, temperature=0.5, max_tokens=500

**关键代码**:
```python
async def call_deepseek_api(self, prompt: str) -> Dict:
    # 直接调用DeepSeek API
    # 返回JSON格式的分析结果
```

### 3. 交付识别服务 (DeliveryIdentificationService)

**文件**: `backend/services/delivery_identification_service.py`

**AI调用场景**:
- **场景名称**: 交付产品识别
- **用途**: 从商品名称识别交付产品的类型、格式和平台
- **输入**: 商品名称
- **输出**: JSON格式（交付类型、平台、完整描述）
- **当前实现**:
  - 优先使用关键词规则
  - 规则无法识别时使用AI
  - DeepSeek: `deepseek-chat`, temperature=0.3, max_tokens=200
  - Claude: `claude-3-haiku-20240307`, temperature=0.3, max_tokens=200

**关键代码**:
```python
async def call_deepseek_api(self, prompt: str) -> Dict:
    # AI辅助识别交付形式
```

### 4. Top商品分析服务 (TopProductAnalysisService)

**文件**: `backend/services/top_product_analysis_service.py`

**AI调用场景**:
- **场景名称**: Top商品深度分析
- **用途**: 对每个簇的Top商品进行深度分析
- **输入**: 商品详细信息（名称、评分、评价数、价格、类别）
- **输出**: JSON格式（用户需求、交付形式验证、补充关键词）
- **当前实现**:
  - 支持Claude和DeepSeek
  - Claude: `claude-3-5-sonnet-20241022`, max_tokens=1024
  - DeepSeek: `deepseek-chat`, max_tokens=1024, temperature=0.7

**关键代码**:
```python
def _call_claude_api(self, prompt: str) -> str:
    client = anthropic.Anthropic(api_key=self.api_key)
    # 使用anthropic库
```

### 5. 属性提取服务 (AttributeExtractionService)

**文件**: `backend/services/attribute_extraction_service.py`

**AI调用场景**:
- **场景名称**: 属性提取AI辅助
- **用途**: 对代码规则无法提取的商品使用AI补充
- **输入**: 商品名称
- **输出**: 交付形式
- **当前实现**:
  - 优先使用代码规则
  - 规则无法识别时使用AI
  - Claude: `claude-3-5-sonnet-20241022`, max_tokens=100
  - DeepSeek: `deepseek-chat`, max_tokens=100

**关键代码**:
```python
def extract_delivery_type_with_ai(self, product_name: str) -> Optional[str]:
    # AI辅助提取交付形式
```

### 6. AI分析服务 (AIAnalysisService)

**文件**: `backend/services/ai_analysis_service.py`

**AI调用场景**:
- **场景名称**: 商品AI分析
- **用途**: 对商品进行AI深度分析
- **输入**: 商品名称列表
- **输出**: JSON格式（用户需求、交付形式验证、关键词）
- **当前实现**:
  - 支持Claude和DeepSeek
  - Claude: `claude-3-5-sonnet-20241022`, max_tokens=1024
  - DeepSeek: `deepseek-chat`, max_tokens=1024

---

## 🎯 需要创建的场景配置

基于以上分析，需要创建以下场景：

### 场景1: 类别名称生成

```json
{
  "scenario_name": "类别名称生成",
  "scenario_desc": "为聚类簇生成简洁的类别名称（2-4个单词）",
  "primary_model": "deepseek-chat",
  "fallback_model": "claude-3-haiku-20240307",
  "custom_params": {
    "temperature": 0.3,
    "max_tokens": 50
  }
}
```

### 场景2: 需求分析

```json
{
  "scenario_name": "需求分析",
  "scenario_desc": "分析商品簇，识别用户需求、目标用户、使用场景和价值主张",
  "primary_model": "deepseek-chat",
  "fallback_model": "claude-3-haiku-20240307",
  "custom_params": {
    "temperature": 0.5,
    "max_tokens": 500
  }
}
```

### 场景3: 交付产品识别

```json
{
  "scenario_name": "交付产品识别",
  "scenario_desc": "识别商品的交付类型、格式和平台",
  "primary_model": "deepseek-chat",
  "fallback_model": "claude-3-haiku-20240307",
  "custom_params": {
    "temperature": 0.3,
    "max_tokens": 200
  }
}
```

### 场景4: Top商品深度分析

```json
{
  "scenario_name": "Top商品深度分析",
  "scenario_desc": "对Top商品进行深度分析，提取用户需求和关键词",
  "primary_model": "claude-3-5-sonnet-20241022",
  "fallback_model": "deepseek-chat",
  "custom_params": {
    "temperature": 0.7,
    "max_tokens": 1024
  }
}
```

### 场景5: 属性提取辅助

```json
{
  "scenario_name": "属性提取辅助",
  "scenario_desc": "辅助提取商品属性（当规则无法识别时）",
  "primary_model": "claude-3-5-sonnet-20241022",
  "fallback_model": "deepseek-chat",
  "custom_params": {
    "temperature": 0.3,
    "max_tokens": 100
  }
}
```

---

## 📝 迁移步骤

### 第1步: 配置AI提供商和模型

**前提条件**: 需要在`.env`文件中配置API密钥

```bash
CLAUDE_API_KEY=sk-ant-xxx
DEEPSEEK_API_KEY=sk-xxx
```

**执行脚本**: `scripts/setup_ai_config.py`

```python
# 1. 创建提供商
# 2. 创建模型
# 3. 创建场景
```

### 第2步: 迁移类别名称生成服务

**文件**: `backend/services/category_naming_service.py`

**修改内容**:
1. 添加统一AI调用接口的导入
2. 修改`__init__`方法，使用场景配置
3. 替换`call_deepseek_api`和`call_claude_api`为统一接口
4. 保持向后兼容（可选参数）

**示例代码**:
```python
from backend.services.ai_call_service import AICallService

class CategoryNamingService:
    def __init__(self, db: Session, use_unified_api: bool = True):
        self.db = db
        self.use_unified_api = use_unified_api
        if use_unified_api:
            self.ai_call_service = AICallService(db)

    async def generate_category_name(self, cluster_id: int, top_n: int = 5):
        # 获取商品名称
        product_names = self.get_top_products_by_cluster(cluster_id, top_n)

        # 构建Prompt
        prompt = self.build_prompt(product_names)

        # 使用统一接口调用AI
        if self.use_unified_api:
            result = await self.ai_call_service.call_by_scenario(
                scenario_name="类别名称生成",
                prompt=prompt
            )
            category_name = result["content"]
        else:
            # 保持旧的实现作为备用
            category_name = await self.call_deepseek_api(prompt)

        # 更新数据库
        # ...
```

### 第3步: 迁移需求分析服务

**文件**: `backend/services/demand_analysis_service.py`

**修改内容**: 类似第2步

### 第4步: 迁移交付识别服务

**文件**: `backend/services/delivery_identification_service.py`

**修改内容**: 类似第2步

### 第5步: 迁移Top商品分析服务

**文件**: `backend/services/top_product_analysis_service.py`

**修改内容**: 类似第2步

### 第6步: 迁移属性提取服务

**文件**: `backend/services/attribute_extraction_service.py`

**修改内容**: 类似第2步

### 第7步: 测试验证

1. 测试类别名称生成
2. 测试需求分析
3. 测试交付识别
4. 测试Top商品分析
5. 测试属性提取

### 第8步: 更新文档

1. 更新API文档
2. 更新使用指南
3. 更新需求文档

---

## 🎨 迁移策略

### 策略1: 渐进式迁移（推荐）

**优点**:
- 风险低
- 可以逐步验证
- 保持向后兼容

**实施**:
1. 添加`use_unified_api`参数（默认False）
2. 新代码使用统一接口
3. 旧代码保持不变
4. 逐步切换到统一接口
5. 验证无误后移除旧代码

### 策略2: 一次性迁移

**优点**:
- 代码更简洁
- 维护成本低

**缺点**:
- 风险较高
- 需要全面测试

**实施**:
1. 直接替换所有AI调用
2. 全面测试
3. 修复问题

---

## ⚠️ 注意事项

### 1. API密钥配置

**问题**: 当前环境变量中没有API密钥

**解决方案**:
1. 在`.env`文件中配置API密钥
2. 或在数据库中配置提供商时输入API密钥

### 2. 模型名称映射

**现有模型**:
- `deepseek-chat`
- `claude-3-haiku-20240307`
- `claude-3-5-sonnet-20241022`

**需要在数据库中创建对应的模型记录**

### 3. 温度和Token参数

**不同场景使用不同参数**:
- 类别名称生成: temperature=0.3, max_tokens=50
- 需求分析: temperature=0.5, max_tokens=500
- 交付识别: temperature=0.3, max_tokens=200
- Top商品分析: temperature=0.7, max_tokens=1024
- 属性提取: temperature=0.3, max_tokens=100

**统一接口支持参数覆盖**

### 4. 错误处理

**现有代码的错误处理**:
- 大多数服务返回`{"success": False, "error": "..."}`
- 统一接口也应该保持这种格式

### 5. 向后兼容

**建议**:
- 保留旧的API调用方法作为备用
- 添加`use_unified_api`参数控制
- 逐步迁移，验证无误后移除旧代码

---

## 📊 迁移收益

### 1. 简化代码

**之前**:
```python
# 需要手动管理API密钥、端点、模型配置
if self.ai_provider == "deepseek":
    self.api_key = os.getenv("DEEPSEEK_API_KEY")
    self.api_url = "https://api.deepseek.com/v1/chat/completions"
    self.model = "deepseek-chat"
```

**之后**:
```python
# 只需指定场景名称
result = await self.ai_call_service.call_by_scenario(
    scenario_name="类别名称生成",
    prompt=prompt
)
```

### 2. 提高可靠性

- 自动回退机制
- 主模型失败时自动切换到回退模型
- 记录调用日志

### 3. 降低维护成本

- 集中配置管理
- 易于切换模型
- 统一的调用接口

### 4. 支持多提供商

- 轻松添加新的AI提供商
- 统一的响应格式
- 灵活的模型选择

---

## 🚀 下一步行动

### 立即执行

1. **配置API密钥** - 在`.env`文件中添加API密钥
2. **运行配置脚本** - 创建提供商、模型和场景
3. **迁移第一个服务** - 从类别名称生成开始

### 后续计划

1. 逐步迁移其他服务
2. 测试验证
3. 更新文档
4. 移除旧代码

---

## 📞 联系信息

**创建人**: Claude Sonnet 4.5
**创建日期**: 2026-01-30
**版本**: v1.0

---

**文档结束**

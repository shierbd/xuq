# 统一AI调用接口 - 使用指南

**创建日期**: 2026-01-30
**版本**: v1.0

---

## 📋 概述

统一AI调用接口提供了一个简单、可靠的方式来调用AI服务，支持：
- 场景化配置
- 主模型和回退模型自动切换
- 调用日志记录
- 多提供商支持（Claude、DeepSeek等）

---

## 🚀 快速开始

### 1. 准备工作

在使用统一AI调用接口之前，需要先配置：

1. **添加AI提供商**（AI1.1）
   - 配置API密钥
   - 配置API端点

2. **添加AI模型**（AI1.2）
   - 选择提供商
   - 配置模型参数

3. **创建使用场景**（AI1.3）
   - 定义场景名称
   - 选择主模型
   - 选择回退模型（可选）

### 2. 基本使用

#### Python后端调用

```python
from backend.services.ai_call_service import AICallService
from backend.database import get_db

# 获取数据库会话
db = next(get_db())

# 创建AI调用服务
service = AICallService(db)

# 调用AI
result = await service.call_by_scenario(
    scenario_name="类别名称生成",
    prompt="为以下产品生成类别名称：wireless mouse"
)

print(result["content"])  # AI生成的内容
print(result["model_used"])  # 使用的模型名称
print(result["is_fallback"])  # 是否使用了回退模型
```

#### REST API调用

```bash
curl -X POST http://localhost:8001/api/ai-config/call \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_name": "类别名称生成",
    "prompt": "为以下产品生成类别名称：wireless mouse",
    "system_prompt": "你是一个专业的产品分类专家",
    "temperature": 0.7,
    "max_tokens": 1000
  }'
```

#### 前端JavaScript调用

```javascript
import apiClient from '@/api/client';

async function callAI() {
  try {
    const response = await apiClient.post('/api/ai-config/call', {
      scenario_name: '类别名称生成',
      prompt: '为以下产品生成类别名称：wireless mouse',
      system_prompt: '你是一个专业的产品分类专家',
      temperature: 0.7,
      max_tokens: 1000
    });

    if (response.data.success) {
      const result = response.data.data;
      console.log('AI响应:', result.content);
      console.log('使用模型:', result.model_used);
      console.log('是否回退:', result.is_fallback);
    }
  } catch (error) {
    console.error('AI调用失败:', error);
  }
}
```

---

## 📖 详细说明

### API参数

#### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| scenario_name | string | 是 | 场景名称（必须是已创建的场景） |
| prompt | string | 是 | 用户提示词 |
| system_prompt | string | 否 | 系统提示词 |
| temperature | float | 否 | 温度参数（0-2），覆盖模型默认值 |
| max_tokens | int | 否 | 最大token数，覆盖模型默认值 |

#### 响应格式

```json
{
  "success": true,
  "message": "AI调用成功",
  "data": {
    "success": true,
    "content": "AI生成的内容",
    "model_used": "claude-3-5-sonnet-20241022",
    "is_fallback": false,
    "usage": {
      "input_tokens": 100,
      "output_tokens": 200
    },
    "scenario_name": "类别名称生成"
  }
}
```

#### 回退模型响应

当主模型失败且使用回退模型时：

```json
{
  "success": true,
  "message": "AI调用成功",
  "data": {
    "success": true,
    "content": "AI生成的内容",
    "model_used": "deepseek-chat",
    "is_fallback": true,
    "primary_error": "主模型调用失败的原因",
    "usage": {
      "input_tokens": 100,
      "output_tokens": 200
    },
    "scenario_name": "类别名称生成"
  }
}
```

---

## 🎯 使用场景示例

### 场景1: 类别名称生成

```python
result = await service.call_by_scenario(
    scenario_name="类别名称生成",
    prompt=f"为以下产品生成类别名称：{product_title}",
    system_prompt="你是一个专业的产品分类专家，请生成简洁准确的类别名称"
)

category_name = result["content"]
```

### 场景2: 产品描述翻译

```python
result = await service.call_by_scenario(
    scenario_name="产品翻译",
    prompt=f"将以下产品描述翻译成中文：{english_description}",
    system_prompt="你是一个专业的翻译专家，请提供准确流畅的翻译"
)

chinese_description = result["content"]
```

### 场景3: 需求分析

```python
result = await service.call_by_scenario(
    scenario_name="需求分析",
    prompt=f"分析以下用户需求：{user_requirement}",
    system_prompt="你是一个产品经理，请深入分析用户需求",
    temperature=0.3,  # 使用较低温度以获得更确定的结果
    max_tokens=2000
)

analysis = result["content"]
```

---

## 🔄 回退机制

### 工作原理

1. **尝试主模型**
   - 使用场景配置的主模型
   - 如果成功，返回结果

2. **主模型失败**
   - 捕获异常
   - 检查是否配置了回退模型

3. **尝试回退模型**
   - 使用场景配置的回退模型
   - 如果成功，返回结果（标记is_fallback=true）

4. **回退模型也失败**
   - 抛出异常，包含主模型和回退模型的错误信息

### 配置建议

- **主模型**: 选择质量最高的模型（如Claude Sonnet）
- **回退模型**: 选择稳定性高、成本较低的模型（如DeepSeek）

---

## 📊 调用日志

每次AI调用都会记录日志，包含：
- 时间戳
- 场景ID
- 模型ID
- 提示词长度
- 响应长度
- 是否成功
- 是否使用回退模型
- 错误信息（如果有）

日志格式：
```json
{
  "timestamp": "2026-01-30T10:30:00",
  "scenario_id": 1,
  "model_id": 2,
  "prompt_length": 100,
  "response_length": 500,
  "success": true,
  "is_fallback": false,
  "error_message": null
}
```

---

## ⚠️ 错误处理

### 常见错误

#### 1. 场景不存在

```json
{
  "detail": "场景 'xxx' 不存在"
}
```

**解决方案**: 检查场景名称是否正确，或创建该场景

#### 2. 场景已禁用

```json
{
  "detail": "场景 'xxx' 已禁用"
}
```

**解决方案**: 在场景管理页面启用该场景

#### 3. 主模型和回退模型均失败

```json
{
  "detail": "主模型和回退模型均失败 - 主模型: xxx, 回退模型: xxx"
}
```

**解决方案**:
- 检查API密钥是否正确
- 检查网络连接
- 检查模型配置

---

## 🎨 最佳实践

### 1. 场景命名

使用清晰、描述性的场景名称：
- ✅ 好: "类别名称生成"、"产品翻译"、"需求分析"
- ❌ 差: "场景1"、"test"、"ai"

### 2. 主模型和回退模型选择

- **高质量任务**: 主模型用Claude Sonnet/Opus，回退用Claude Haiku
- **翻译任务**: 主模型用DeepSeek，回退用Claude Haiku
- **成本敏感任务**: 主模型用DeepSeek，回退用其他低成本模型

### 3. 温度参数设置

- **创意任务** (如文案生成): temperature=0.8-1.0
- **分析任务** (如需求分析): temperature=0.5-0.7
- **确定性任务** (如分类): temperature=0.1-0.3

### 4. 错误处理

```python
try:
    result = await service.call_by_scenario(
        scenario_name="类别名称生成",
        prompt=prompt
    )

    # 检查是否使用了回退模型
    if result["is_fallback"]:
        logger.warning(f"使用了回退模型: {result['primary_error']}")

    return result["content"]

except Exception as e:
    logger.error(f"AI调用失败: {str(e)}")
    # 返回默认值或重试
    return default_value
```

---

## 📈 性能优化

### 1. 缓存策略

对于相同的输入，可以缓存AI响应：

```python
import hashlib
import json

def get_cache_key(scenario_name, prompt):
    data = f"{scenario_name}:{prompt}"
    return hashlib.md5(data.encode()).hexdigest()

# 使用Redis缓存
cache_key = get_cache_key(scenario_name, prompt)
cached_result = redis.get(cache_key)

if cached_result:
    return json.loads(cached_result)

result = await service.call_by_scenario(...)
redis.setex(cache_key, 3600, json.dumps(result))  # 缓存1小时
```

### 2. 批量调用

对于多个独立的AI调用，可以并发执行：

```python
import asyncio

async def batch_call():
    tasks = [
        service.call_by_scenario("场景1", prompt1),
        service.call_by_scenario("场景2", prompt2),
        service.call_by_scenario("场景3", prompt3),
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

---

## 🔧 故障排查

### 问题1: 调用超时

**症状**: 请求长时间无响应

**可能原因**:
- 网络问题
- API端点不可达
- 提供商服务故障

**解决方案**:
1. 检查网络连接
2. 检查提供商状态页面
3. 增加timeout配置
4. 配置回退模型

### 问题2: API密钥无效

**症状**: 返回401或403错误

**可能原因**:
- API密钥错误
- API密钥过期
- API密钥权限不足

**解决方案**:
1. 在提供商管理页面更新API密钥
2. 使用"测试连接"功能验证
3. 检查API密钥权限

### 问题3: 响应质量不佳

**症状**: AI生成的内容不符合预期

**可能原因**:
- 提示词不够清晰
- 温度参数设置不当
- 模型选择不合适

**解决方案**:
1. 优化提示词，提供更多上下文
2. 调整temperature参数
3. 尝试不同的模型
4. 使用system_prompt提供角色定位

---

## 📚 相关文档

- [AI1.1: AI提供商管理](./模块四-Phase1完成报告.md)
- [AI1.2: AI模型管理](./模块四-Phase1完成报告.md)
- [AI1.3: 使用场景管理](./模块四-AI1.3完成报告.md)
- [API文档](http://localhost:8001/docs)

---

**文档版本**: v1.0
**最后更新**: 2026-01-30
**维护者**: Claude Sonnet 4.5

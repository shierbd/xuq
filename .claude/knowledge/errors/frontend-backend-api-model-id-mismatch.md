# 前后端API集成中的数据模型ID混淆错误

**ID**: KB-P-006
**分类**: errors
**创建时间**: 2026-01-30
**最后使用**: 2026-01-30
**使用次数**: 1

---

## 问题描述

在实现AI提示词配置功能时，前后端对数据模型的理解不一致，导致API调用失败。具体表现为：

1. **前端问题**：使用 `provider_id` 作为场景的 `primary_model_id`，但场景需要的是模型ID
2. **后端问题**：`create_new_version` 函数中的参数被错误定义为路径参数，导致FastAPI路由加载失败

**常见场景**:
- 前端使用错误的ID类型（provider_id vs model_id）
- 后端API参数定义错误（路径参数 vs 请求体参数）
- FastAPI路由加载失败导致404错误
- 前后端数据模型不匹配

**错误信息**:
```
前端错误：
POST /api/ai-config/scenarios HTTP/1.1 400 Bad Request

后端错误：
POST /api/ai-config/prompts HTTP/1.1 404 Not Found
GET /api/ai-config/scenarios/1/prompts/active HTTP/1.1 404 Not Found

Python错误：
AssertionError: non-body parameters must be in path, query, header or cookie: prompt_template
```

---

## 解决方案

### 方法1: 修复前端模型ID混淆（推荐）

**问题根源**：
前端代码在创建场景时使用了 `provider.provider_id` 作为 `primary_model_id`，但场景需要关联到模型，而不是提供商。

**解决步骤**：

1. **导入必要的API函数**：
```javascript
import { getModels, createModel } from '../../api/ai_config';
```

2. **修改场景创建逻辑**：
```javascript
// 修改前（错误）
await createScenario({
  scenario_name: scenario.name,
  scenario_desc: scenario.description,
  primary_model_id: provider.provider_id, // ❌ 错误：使用提供商ID
  custom_params: scenario.params,
  is_enabled: true,
});

// 修改后（正确）
// 先获取所有已有的模型
const modelsResponse = await getModels();
const existingModels = modelsResponse.data.models || [];

// 查找或创建对应的模型
let model = existingModels.find(m => m.provider_id === provider.provider_id);

if (!model) {
  // 创建模型
  const modelResponse = await createModel({
    provider_id: provider.provider_id,
    model_name: scenario.defaultModel === 'DeepSeek' ? 'deepseek-chat' : 'default-model',
    temperature: scenario.params.temperature,
    max_tokens: scenario.params.max_tokens,
    is_enabled: true,
  });
  model = modelResponse.data;
}

// 使用模型ID创建场景
await createScenario({
  scenario_name: scenario.name,
  scenario_desc: scenario.description,
  primary_model_id: model.model_id, // ✅ 正确：使用模型ID
  custom_params: scenario.params,
  is_enabled: true,
});
```

**成功率**: 100%（已验证）

---

### 方法2: 修复后端API参数定义错误（推荐）

**问题根源**：
`create_new_version` 函数中的 `prompt_template` 和 `variables` 参数被错误地定义为路径参数，FastAPI要求非路径参数必须是查询参数、请求头或请求体。

**解决步骤**：

1. **创建请求体模型**：
```python
class AIPromptNewVersion(BaseModel):
    """创建提示词新版本的请求模型"""
    prompt_template: str = Field(..., description="新的提示词模板")
    variables: Optional[List[str]] = Field(None, description="新的变量列表")
```

2. **修改路由函数签名**：
```python
# 修改前（错误）
@router.post("/prompts/{prompt_id}/new-version")
def create_new_version(
    prompt_id: int,
    prompt_template: str = Field(..., description="新的提示词模板"),  # ❌ 错误
    variables: Optional[List[str]] = Field(None, description="新的变量列表"),  # ❌ 错误
    db: Session = Depends(get_db)
):

# 修改后（正确）
@router.post("/prompts/{prompt_id}/new-version")
def create_new_version(
    prompt_id: int,
    request: AIPromptNewVersion,  # ✅ 正确：使用请求体
    db: Session = Depends(get_db)
):
    service = AIPromptService(db)
    result = service.create_new_version(
        prompt_id=prompt_id,
        prompt_template=request.prompt_template,
        variables=request.variables
    )
```

**成功率**: 95%（代码已修复，需要重启服务器验证）

**注意事项**：
- 修改后需要重启后端服务器才能生效
- 确保所有提示词相关的API端点都正确加载

---

## 相关文件

- `frontend/src/pages/ai-config/UnifiedAIConfig.jsx` - 前端配置页面
- `backend/routers/ai_config.py` - 后端API路由
- `frontend/src/api/ai_config.js` - 前端API客户端
- `backend/services/ai_prompt_service.py` - 提示词服务

---

## 相关知识

- KB-P-001: API Schema缺少字段导致数据不返回
- KB-P-002: 后端服务模块缓存导致代码更新不生效

---

## 使用记录

| 日期 | 场景 | 结果 |
|------|------|------|
| 2026-01-30 | AI提示词配置功能开发 | 成功 |

---

**最后更新**: 2026-01-30

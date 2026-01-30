# API Schema 缺少字段导致数据不返回

**ID**: KB-P-001
**分类**: errors
**创建时间**: 2026-01-29
**最后使用**: 2026-01-29
**使用次数**: 1

---

## 问题描述

在 FastAPI 项目中，数据库和 ORM 模型都有某个字段，但 API 响应中不返回该字段。

**常见场景**:
- 数据库中有数据，但 API 返回 null 或不包含该字段
- ORM 模型的 `to_dict()` 方法包含该字段，但 API 仍不返回
- 直接查询数据库可以看到数据，但通过 API 获取不到

**症状**:
- API 响应缺少预期字段
- 前端无法获取某些数据
- OpenAPI 文档中不显示该字段

---

## 根本原因

FastAPI 使用 Pydantic Schema 进行数据序列化。即使数据库和 ORM 模型有该字段，如果 Pydantic Schema 中没有定义，该字段也不会出现在 API 响应中。

**数据流**:
```
数据库 ✅ 有数据
   ↓
ORM 模型 ✅ 有字段
   ↓
to_dict() ✅ 包含字段
   ↓
Pydantic Schema ❌ 缺少字段 ← 问题根源
   ↓
API 响应 ❌ 不返回字段
```

---

## 解决方案

### 方法1: 在 Pydantic Schema 中添加字段（推荐）

**步骤**:

1. 找到对应的 Response Schema 文件（通常在 `schemas/` 目录）

2. 在 Schema 类中添加缺失的字段：

```python
from typing import Optional
from pydantic import BaseModel

class ProductResponse(BaseModel):
    product_id: int
    product_name: str
    cluster_name: Optional[str] = None
    cluster_name_cn: Optional[str] = None  # ← 添加缺失的字段

    class Config:
        from_attributes = True  # Pydantic v2
        # orm_mode = True  # Pydantic v1
```

3. 重启后端服务

4. 验证 API 响应：
```bash
curl -s "http://localhost:8001/api/endpoint" | python -m json.tool
```

**成功率**: 100%

**注意事项**:
- 字段类型要与数据库模型一致
- 使用 `Optional` 标记可选字段
- 设置合适的默认值（通常是 `None`）
- 确保 `Config.from_attributes = True`（Pydantic v2）

---

## 预防措施

### 1. 修改数据库模型时的检查清单

修改数据库模型后，必须同步更新：
- [ ] ORM 模型 (models/)
- [ ] Pydantic Schema (schemas/)
- [ ] API 文档
- [ ] 前端类型定义（如果有）

### 2. 分层验证

遇到数据不显示问题时，逐层检查：
```
数据库 → ORM → Schema → API → 前端
```

在每一层验证数据是否存在：
- **数据库层**: 直接查询数据库
- **ORM 层**: 打印 `model.to_dict()`
- **Schema 层**: 检查 Schema 定义
- **API 层**: 测试 API 端点
- **前端层**: 检查浏览器控制台

### 3. 使用类型检查工具

使用 mypy 或 pyright 进行类型检查，可以提前发现 Schema 定义问题。

---

## 相关文件

- `backend/schemas/product_schema.py` - Pydantic Schema 定义
- `backend/models/product.py` - ORM 模型定义
- `backend/routers/products.py` - API 路由定义

---

## 相关知识

- KB-P-002: 后端服务模块缓存问题

---

## 使用记录

| 日期 | 场景 | 结果 |
|------|------|------|
| 2026-01-29 | API 不返回 cluster_name_cn 字段 | 成功 |

---

**最后更新**: 2026-01-29

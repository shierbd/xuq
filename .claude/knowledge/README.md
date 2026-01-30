# 项目知识库

本目录包含项目开发过程中积累的问题、解决方案、代码模式和技术决策。

---

## 📁 目录结构

```
.claude/knowledge/
├── index.yaml              # 知识库索引（自动生成）
├── README.md              # 本文件
├── errors/                # 错误和问题记录
│   ├── api-schema-missing-field.md
│   ├── backend-service-module-cache.md
│   └── windows-command-encoding.md
├── solutions/             # 功能实现方案
├── patterns/              # 代码模式和最佳实践
└── decisions/             # 技术决策记录
```

---

## 📊 知识库统计

**总条目数**: 3
- **errors**: 3 个
- **solutions**: 0 个
- **patterns**: 0 个
- **decisions**: 0 个

**最后更新**: 2026-01-29

---

## 🔍 快速查找

### 按分类浏览

- **错误记录** (`errors/`): 开发过程中遇到的错误和问题
- **解决方案** (`solutions/`): 功能实现的完整方案
- **代码模式** (`patterns/`): 可复用的代码模式和最佳实践
- **技术决策** (`decisions/`): 重要的技术选型和架构决策

### 按关键词搜索

```bash
# 搜索包含特定关键词的知识条目
grep -r "关键词" .claude/knowledge/

# 查看索引中的所有关键词
grep "keywords:" .claude/knowledge/index.yaml -A 5
```

---

## 📚 现有知识条目

### KB-P-001: API Schema 缺少字段导致数据不返回

**分类**: errors
**关键词**: API Schema, Pydantic, FastAPI, 数据序列化, 字段缺失
**文件**: [errors/api-schema-missing-field.md](errors/api-schema-missing-field.md)

**问题**: 数据库和 ORM 模型都有某个字段，但 API 响应中不返回该字段。

**解决方案**: 在 Pydantic Schema 中添加缺失的字段。

---

### KB-P-002: 后端服务模块缓存导致代码更新不生效

**分类**: errors
**关键词**: 模块缓存, 端口占用, 多进程, uvicorn, 服务重启
**文件**: [errors/backend-service-module-cache.md](errors/backend-service-module-cache.md)

**问题**: 修改代码后重启服务，但代码更新不生效，服务继续使用旧版本。

**解决方案**: 清理所有旧进程并重启服务。

---

### KB-P-003: Windows 命令编码问题

**分类**: errors
**关键词**: Windows, 编码, taskkill, GBK, UTF-8, 跨平台
**文件**: [errors/windows-command-encoding.md](errors/windows-command-encoding.md)

**问题**: 在 Windows 环境下使用 Bash 或 Python 执行系统命令时出现编码错误。

**解决方案**: 使用正确的命令格式和编码处理。

---

## 🔧 使用方法

### 查看知识条目

```bash
# 查看特定知识条目
cat .claude/knowledge/errors/api-schema-missing-field.md

# 查看索引
cat .claude/knowledge/index.yaml
```

### 搜索相关知识

```bash
# 按关键词搜索
grep -r "Pydantic" .claude/knowledge/

# 按问题描述搜索
grep -r "API 不返回" .claude/knowledge/
```

### 添加新知识条目

使用命令：
```bash
/add-knowledge-project
```

系统会自动分析上下文并生成知识条目。

---

## 💡 最佳实践

### 何时添加知识条目

**适合添加**:
- ✅ 解决了非平凡的问题
- ✅ 实现了有价值的功能方案
- ✅ 发现了有用的代码模式
- ✅ 做出了重要的技术决策

**不适合添加**:
- ❌ 简单的语法错误
- ❌ 一次性的临时解决方案
- ❌ 项目特定且不可复用的代码

### 编写知识条目的建议

1. **标题清晰** - 用 10-30 字概括问题或方案
2. **问题描述详细** - 提供足够的上下文
3. **解决方案完整** - 包含详细步骤和代码示例
4. **标注成功率** - 如果尝试了多种方法，标注哪个最有效
5. **添加关联** - 链接到相关的知识条目

---

## 🔗 相关资源

- **全局知识库**: `~/.claude/knowledge/` - 跨项目复用的知识
- **项目文档**: `docs/` - 项目需求和设计文档
- **测试报告**: `docs/翻译功能测试报告.md` - 功能测试记录

---

## 📈 知识库维护

### 定期更新

- 每次解决重要问题后，及时添加知识条目
- 定期回顾和更新现有知识条目
- 删除过时或不再适用的知识

### 质量保证

- 确保每个知识条目都有清晰的问题描述
- 验证解决方案的有效性
- 添加实际使用案例

---

**知识库版本**: 1.0.0
**创建日期**: 2026-01-29
**最后更新**: 2026-01-29

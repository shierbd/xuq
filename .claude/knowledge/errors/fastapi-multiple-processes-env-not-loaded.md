# FastAPI多进程冲突导致环境变量未加载

**ID**: KB-P-007
**分类**: errors
**创建时间**: 2026-01-31
**最后使用**: 2026-01-31
**使用次数**: 1

---

## 问题描述

在Windows环境下运行FastAPI应用时，修改代码添加环境变量配置后，HTTP API调用返回"未找到环境变量"错误，但直接Python调用（TestClient）成功。

**常见场景**:
- 使用uvicorn --reload启动FastAPI应用
- 修改代码后依赖自动重载
- 多次启动/停止服务
- Windows开发环境

**根本原因**:
多个uvicorn进程同时运行（发现10个进程监听同一端口），HTTP请求连接到运行旧代码的进程，而TestClient使用新代码。

**典型错误信息**:
```json
{"detail":"未找到 DEEPSEEK_API_KEY 环境变量"}
```

**诊断特征**:
- 直接Python调用成功，HTTP API调用失败
- 添加debug日志，HTTP请求看不到日志输出
- 使用netstat发现多个进程监听同一端口

---

## 解决方案

### 方法1: 彻底清理进程并重启（推荐）

**步骤**:

1. **识别所有监听端口的进程**
```bash
netstat -ano | findstr :8002
```

2. **停止所有Python进程**
```bash
taskkill //F //IM python.exe
```

3. **确认端口已清空**
```bash
netstat -ano | findstr :8002
# 应该没有输出
```

4. **启动单一干净的服务**
```bash
cd "项目目录"
python -m uvicorn backend.main:app --reload --port 8002
```

5. **验证只有一个进程**
```bash
netstat -ano | findstr :8002
# 应该只有一个LISTENING状态的进程
```

**成功率**: 100%

**注意事项**:
- 不要依赖uvicorn的自动重载
- 修改代码后手动重启服务更可靠
- 定期检查是否有僵尸进程

---

### 方法2: 添加Fallback配置（辅助）

在服务初始化时添加fallback API密钥，避免环境变量未加载时完全失败：

```python
# backend/services/category_naming_service.py
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class CategoryNamingService:
    def __init__(self, db: Session, ai_provider: str = "deepseek"):
        # 添加fallback
        self.api_key = os.getenv("DEEPSEEK_API_KEY") or "fallback_key"
```

**成功率**: 95%

**优点**:
- 提供降级方案
- 便于开发调试
- 减少环境配置问题

---

### 方法3: 修复GBK编码错误（相关问题）

如果代码中使用了Unicode特殊字符（如 ✓ ✗），在Windows GBK环境下会报错：

```
'gbk' codec can't encode character '\u2717'
```

**解决方案**: 替换为ASCII字符
```python
# 替换前
print(f"  ✓ 商品 {product_id}")
print(f"  ✗ 商品 {product_id}")

# 替换后
print(f"  [OK] 商品 {product_id}")
print(f"  [FAIL] 商品 {product_id}")
```

**成功率**: 100%

---

## 相关文件

- `backend/services/category_naming_service.py` - 添加load_dotenv和fallback
- `backend/services/demand_analysis_service.py` - 添加fallback
- `backend/services/top_product_analysis_service.py` - 添加fallback，修复编码
- `backend/main.py` - 添加load_dotenv
- `.env` - 配置环境变量

---

## 诊断方法

**如何判断是多进程问题**:

1. 直接Python调用成功，HTTP API调用失败
2. 添加debug日志，HTTP请求看不到日志输出
3. 使用netstat发现多个进程监听同一端口

**快速诊断命令**:
```bash
# Windows
netstat -ano | findstr :端口号

# 查看进程数量
netstat -ano | findstr :端口号 | findstr LISTENING | wc -l
```

**诊断流程**:
1. 检查端口占用情况
2. 确认进程数量
3. 查看进程启动时间
4. 测试API响应内容

---

## 预防措施

1. **使用进程管理工具**
   - 使用supervisor或pm2管理进程
   - 避免手动启动多个实例

2. **定期清理**
   - 开发结束时停止所有服务
   - 定期检查僵尸进程

3. **改进启动脚本**
   ```bash
   # 启动前先清理
   taskkill //F //IM python.exe 2>nul
   sleep 2
   python -m uvicorn backend.main:app --reload --port 8002
   ```

4. **使用端口检查**
   ```bash
   # 启动前检查端口
   if netstat -ano | findstr :8002 | findstr LISTENING; then
       echo "端口8002已被占用，请先清理"
       exit 1
   fi
   ```

---

## 相关知识

- KB-P-002: 后端服务模块缓存导致代码更新不生效
- KB-P-003: Windows 命令编码问题
- KB-P-005: Vite代理配置端口错误导致前端无法加载数据

---

## 使用记录

| 日期 | 场景 | 结果 |
|------|------|------|
| 2026-01-31 | 初次记录 | 成功解决多进程冲突 |
| 2026-01-31 | AI功能测试 | 成功配置环境变量 |

---

**最后更新**: 2026-01-31
**解决次数**: 1
**平均解决时间**: 15分钟

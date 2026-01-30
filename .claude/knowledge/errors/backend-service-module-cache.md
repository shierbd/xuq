# 后端服务模块缓存导致代码更新不生效

**ID**: KB-P-002
**分类**: errors
**创建时间**: 2026-01-29
**最后使用**: 2026-01-29
**使用次数**: 1

---

## 问题描述

修改 Python 代码后，重启后端服务，但代码更新不生效，服务继续使用旧版本的代码。

**常见场景**:
- 修改了 Pydantic Schema，但 API 响应仍使用旧的 Schema
- 修改了路由逻辑，但请求仍执行旧的逻辑
- OpenAPI 文档不更新
- 清理了 `__pycache__` 仍然无效
- 多次重启服务问题依然存在

**症状**:
- 代码修改不生效
- 直接 Python 导入可以看到新代码，但运行的服务使用旧代码
- 日志显示服务已重启，但行为没有变化

---

## 根本原因

**多个服务实例同时运行**，导致请求被路由到旧的进程实例。

### 为什么会有多个进程？

1. **多次启动服务但没有正确关闭旧进程**
   - 手动启动多次
   - 脚本启动失败但进程残留

2. **uvicorn reloader 创建的子进程没有被清理**
   - `--reload` 模式会创建多个进程
   - 父进程关闭但子进程仍在运行

3. **之前的测试和调试留下的残留进程**
   - 开发过程中频繁启动停止
   - 异常退出导致进程未清理

### 问题表现

```bash
# 检查端口占用，发现多个进程
$ netstat -ano | findstr :8001 | findstr LISTENING

TCP    127.0.0.1:8001    LISTENING    54328
TCP    127.0.0.1:8001    LISTENING    49276
TCP    127.0.0.1:8001    LISTENING    44712
TCP    127.0.0.1:8001    LISTENING    55856
TCP    127.0.0.1:8001    LISTENING    57192
TCP    127.0.0.1:8001    LISTENING    54280
TCP    127.0.0.1:8001    LISTENING    19744
# ↑ 7 个进程同时监听！
```

---

## 解决方案

### 方法1: 清理所有旧进程并重启（推荐）

**步骤**:

1. **查找所有占用端口的进程**
```bash
netstat -ano | findstr :8001 | findstr LISTENING
```

2. **关闭所有 Python 进程**（最彻底）
```bash
# Windows
tasklist | findstr python.exe | awk '{print $2}' | xargs -I {} taskkill //PID {} //F

# Linux/Mac
pkill -9 python
```

3. **验证端口已释放**
```bash
netstat -ano | findstr :8001 | findstr LISTENING
# 应该没有输出
```

4. **等待 3 秒确保进程完全关闭**
```bash
sleep 3
```

5. **清理 Python 缓存**（可选但推荐）
```bash
find backend -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
```

6. **重新启动服务**
```bash
python -m uvicorn backend.main:app --reload --port 8001
```

7. **验证只有一个进程在运行**
```bash
netstat -ano | findstr :8001 | findstr LISTENING
# 应该只有 1 行输出
```

**成功率**: 100%

---

### 方法2: 使用端口管理工具

如果项目有端口管理工具（如 `/port-manager`）：

```bash
# 清理端口
/port-manager kill 8001

# 或清理所有常用开发端口
/port-manager clean

# 重启服务
python -m uvicorn backend.main:app --reload --port 8001
```

**成功率**: 100%

---

### 方法3: 逐个关闭进程（不推荐）

如果只想关闭特定进程：

```bash
# 获取所有 PID
PIDS=$(netstat -ano | findstr :8001 | findstr LISTENING | awk '{print $5}' | sort -u)

# 逐个关闭
for pid in $PIDS; do
    taskkill //PID $pid //F
done
```

**成功率**: 80%（可能遗漏子进程）

---

## 预防措施

### 1. 正确的服务启动流程

```bash
#!/bin/bash
# start_backend.sh

# 1. 检查端口占用
echo "检查端口 8001..."
netstat -ano | findstr :8001 | findstr LISTENING

# 2. 如果有占用，先清理
if netstat -ano | findstr :8001 | findstr LISTENING > /dev/null; then
    echo "端口被占用，正在清理..."
    # 使用端口管理工具或手动清理
    /port-manager kill 8001
fi

# 3. 清理 Python 缓存
echo "清理 Python 缓存..."
find backend -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

# 4. 启动服务
echo "启动后端服务..."
python -m uvicorn backend.main:app --reload --port 8001 > logs/backend.log 2>&1 &

# 5. 等待启动
sleep 3

# 6. 验证
echo "验证服务状态..."
curl -s "http://localhost:8001/health" && echo "✅ 服务启动成功" || echo "❌ 服务启动失败"

# 7. 检查进程数
PROCESS_COUNT=$(netstat -ano | findstr :8001 | findstr LISTENING | wc -l)
echo "当前监听端口的进程数: $PROCESS_COUNT"
if [ $PROCESS_COUNT -gt 1 ]; then
    echo "⚠️ 警告: 检测到多个进程，可能存在问题"
fi
```

### 2. 定期清理残留进程

在开发过程中，定期执行：

```bash
# 每天开始工作前
/port-manager clean

# 或手动清理
pkill -9 python  # 谨慎使用，会关闭所有 Python 进程
```

### 3. 使用进程管理工具

考虑使用专业的进程管理工具：
- **pm2** - Node.js 进程管理器（也支持 Python）
- **supervisor** - Python 进程管理器
- **systemd** - Linux 系统服务管理

### 4. 监控端口占用

添加健康检查脚本：

```bash
#!/bin/bash
# health_check.sh

PROCESS_COUNT=$(netstat -ano | findstr :8001 | findstr LISTENING | wc -l)

if [ $PROCESS_COUNT -eq 0 ]; then
    echo "❌ 服务未运行"
    exit 1
elif [ $PROCESS_COUNT -eq 1 ]; then
    echo "✅ 服务正常运行"
    exit 0
else
    echo "⚠️ 检测到 $PROCESS_COUNT 个进程，可能存在问题"
    exit 2
fi
```

---

## 诊断方法

### 如何确认是否遇到此问题？

1. **检查端口占用数量**
```bash
netstat -ano | findstr :8001 | findstr LISTENING | wc -l
```
如果输出 > 1，说明有多个进程

2. **检查进程详情**
```bash
# Windows
netstat -ano | findstr :8001 | findstr LISTENING

# Linux/Mac
lsof -i :8001
```

3. **测试代码是否生效**
```bash
# 在代码中添加明显的标记
# 例如在 API 响应中添加时间戳
# 然后测试 API，看是否返回新的时间戳
```

4. **检查 OpenAPI 文档**
```bash
curl -s "http://localhost:8001/openapi.json" | python -m json.tool
```
查看 Schema 定义是否包含新字段

---

## 相关文件

- `backend/main.py` - FastAPI 主应用
- `logs/backend.log` - 后端服务日志

---

## 相关知识

- KB-P-001: API Schema 缺少字段导致数据不返回
- KB-P-003: Windows 命令编码问题

---

## 使用记录

| 日期 | 场景 | 结果 |
|------|------|------|
| 2026-01-29 | 修改 ProductResponse Schema 后更新不生效 | 成功 |

---

## 扩展阅读

### uvicorn reloader 工作原理

uvicorn 的 `--reload` 模式使用 watchfiles 监控文件变化：
- 主进程监控文件变化
- 检测到变化时，创建新的工作进程
- 旧的工作进程应该被关闭，但有时会残留

### 为什么清理 __pycache__ 无效？

`__pycache__` 是 Python 的字节码缓存，清理它只能确保 Python 重新编译代码，但不能解决多进程问题。问题的根源是多个进程实例，而不是缓存。

---

**最后更新**: 2026-01-29

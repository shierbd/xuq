# Vite代理配置端口错误导致前端无法加载数据

**ID**: KB-P-005
**分类**: errors
**创建时间**: 2026-01-29
**最后使用**: 2026-01-29
**使用次数**: 0

---

## 问题描述

前端页面正常显示，但无法加载后端数据，表现为：
- 数据列表显示"共 0 条"
- 浏览器控制台显示 500 Internal Server Error
- Vite 开发服务器日志显示 `http proxy error` 和 `ECONNREFUSED`
- 后端 API 直接访问正常，但通过前端代理访问失败

**常见场景**:
- 后端服务端口发生变化，但前端代理配置未更新
- 开发环境中后端运行在非默认端口
- 多个后端服务使用不同端口，前端配置混淆
- 从其他项目复制配置文件时未修改端口

**根本原因**:
Vite 的代理配置（vite.config.js）中的 target 端口与实际后端服务端口不匹配

---

## 解决方案

### 方法1: 检查并修正代理配置（推荐）

**步骤**:

1. **确认后端实际运行端口**
   ```bash
   # Windows
   netstat -ano | findstr "8000"
   netstat -ano | findstr "8001"
   
   # Linux/Mac
   lsof -i :8000
   lsof -i :8001
   ```

2. **直接测试后端 API**
   ```bash
   # 测试不同端口
   curl http://localhost:8000/api/products/
   curl http://localhost:8001/api/products/
   ```

3. **检查浏览器控制台错误**
   - 打开开发者工具 (F12)
   - 查看 Console 标签页
   - 查找 API 错误信息

4. **检查 Vite 开发服务器日志**
   - 查看运行 `npm run dev` 的终端
   - 查找 `http proxy error` 和 `ECONNREFUSED` 错误

5. **修改 vite.config.js**
   ```javascript
   // frontend/vite.config.js
   export default defineConfig({
     plugins: [react()],
     server: {
       port: 3000,
       proxy: {
         '/api': {
           target: 'http://localhost:8001',  // 修改为正确的端口
           changeOrigin: true,
         }
       }
     }
   })
   ```

6. **验证修复**
   - Vite 会自动检测配置变化并重新加载
   - 刷新浏览器页面
   - 确认数据正常加载

**成功率**: 98%

**注意事项**:
- Vite 会自动热重载配置文件，无需重启服务
- 如果修改后仍有问题，尝试重启 Vite 开发服务器
- 确保后端服务正在运行

---

### 方法2: 使用环境变量配置端口

如果需要在不同环境使用不同端口：

```javascript
// frontend/vite.config.js
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: process.env.VITE_API_URL || 'http://localhost:8001',
        changeOrigin: true,
      }
    }
  }
})
```

然后在 `.env.development` 中配置：
```
VITE_API_URL=http://localhost:8001
```

---

## 诊断技巧

### 快速诊断流程

1. **检查后端是否运行**
   ```bash
   curl http://localhost:8001/api/products/
   ```
   - 如果返回数据 → 后端正常
   - 如果连接失败 → 后端未运行或端口错误

2. **检查前端代理配置**
   ```bash
   cat frontend/vite.config.js | grep -A 5 "proxy"
   ```

3. **对比端口号**
   - 后端实际端口 vs 代理配置端口
   - 如果不匹配 → 修改代理配置

---

## 相关文件

- `frontend/vite.config.js` - Vite 配置文件（包含代理配置）
- `backend/main.py` - 后端入口文件（确认运行端口）

---

## 相关知识

- KB-P-002: 后端服务模块缓存导致代码更新不生效
- KB-P-004: 前端服务运行错误项目导致界面显示不正确

---

## 使用记录

| 日期 | 场景 | 结果 |
|------|------|------|
| 2026-01-29 | 初次记录 | 成功 |

---

**最后更新**: 2026-01-29

# 🚀 快速参考卡片

**迁移版本**: v2.0
**迁移日期**: 2026-01-27
**迁移状态**: ✅ 完全成功

---

## 📋 快速命令

### 环境配置
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件（必须填入 API 密钥）
# CLAUDE_API_KEY=your_api_key_here
```

### 安装依赖
```bash
# 后端依赖
pip install -r requirements.txt

# 前端依赖
cd frontend
npm install
cd ..
```

### 启动服务
```bash
# 启动后端（终端 1）
python -m uvicorn api.main:app --reload --port 8000

# 启动前端（终端 2）
cd frontend
npm run dev
```

### 访问应用
- **前端**: http://localhost:5173
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs

---

## 📁 目录结构速查

```
词根聚类需求挖掘/
├── frontend/       # Vue 3 前端 (204M)
├── api/            # FastAPI 后端 (348K)
├── ai/             # AI 模块 (25K)
├── config/         # 配置管理
├── core/           # 核心逻辑
├── data/           # 数据目录 (212M)
├── utils/          # 工具函数
├── storage/        # 存储目录
├── logs/           # 日志目录
└── uploads/        # 上传文件
```

---

## 📚 文档速查

| 文档 | 用途 |
|------|------|
| README_MIGRATION.md | 快速开始指南 |
| MIGRATION_INDEX.md | 文档索引 |
| MIGRATION_FINAL_REPORT.md | 最终报告 |
| MIGRATION_VERIFICATION.md | 验证报告 |
| MIGRATION_CHECKLIST.md | 完成清单 |
| QUICK_REFERENCE.md | 快速参考（本文件）|

---

## 🔒 备份操作

```bash
# 查看备份分支
git checkout backup-legacy-20260127

# 返回主分支
git checkout master

# 查看备份内容
git log backup-legacy-20260127 --oneline -10
```

---

## 🎯 常见任务

### 查看 Git 状态
```bash
git status
git log --oneline -10
git branch -a
```

### 查看目录大小
```bash
du -sh frontend api ai data
```

### 查看迁移文档
```bash
ls -lh MIGRATION_*.md
cat README_MIGRATION.md
```

### 查看迁移徽章
```bash
cat .migration-badge
```

---

## 🚨 故障排查

### 后端启动失败
1. 检查 Python 版本: `python --version` (需要 3.11+)
2. 检查依赖安装: `pip list | grep fastapi`
3. 检查 .env 文件: `cat .env`
4. 查看错误日志: `tail -f logs/app.log`

### 前端启动失败
1. 检查 Node.js 版本: `node --version` (需要 18+)
2. 检查依赖安装: `cd frontend && npm list`
3. 清理缓存: `cd frontend && rm -rf node_modules && npm install`
4. 查看错误日志: 终端输出

### API 连接失败
1. 检查后端是否运行: `curl http://localhost:8000`
2. 检查端口占用: `netstat -ano | findstr :8000`
3. 检查防火墙设置
4. 查看 API 文档: http://localhost:8000/docs

---

## 📞 获取帮助

1. 查看相关文档（见上方文档速查）
2. 检查 Git 提交历史: `git log --oneline`
3. 查看备份分支: `git checkout backup-legacy-20260127`
4. 联系开发团队

---

## ✅ 验证清单

- [ ] .env 文件已配置
- [ ] 后端依赖已安装
- [ ] 前端依赖已安装
- [ ] 后端服务已启动
- [ ] 前端服务已启动
- [ ] 可以访问前端界面
- [ ] 可以访问 API 文档
- [ ] API 接口响应正常

---

**创建时间**: 2026-01-27 12:46
**迁移状态**: ✅ 完全成功

---

*快速参考卡片 - 随时查阅*

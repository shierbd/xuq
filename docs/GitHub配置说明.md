# GitHub仓库配置说明

## 📦 仓库信息

- **仓库地址**: https://github.com/shierbd/xuq.git
- **访问令牌**: 已保存在 `.env` 文件中
- **创建时间**: 2024-12-19

## 🔒 安全说明

1. **`.env` 文件已添加到 `.gitignore`**: 确保您的访问令牌不会被推送到GitHub
2. **访问令牌权限**: 当前令牌具有完整的仓库访问权限
3. **保密建议**: 不要将 `.env` 文件分享给他人

## 🚀 使用方法

### 1. 首次推送代码到GitHub

```bash
# 进入项目目录
cd "D:\xiangmu\词根聚类需求挖掘"

# 查看当前状态
git status

# 添加所有文件（.gitignore会自动排除敏感文件）
git add .

# 提交更改
git commit -m "Initial commit: 词根聚类需求挖掘系统"

# 推送到GitHub (首次推送)
git push -u origin refactor/project-structure-v2
```

### 2. 日常推送代码

```bash
# 查看修改的文件
git status

# 添加修改的文件
git add .

# 提交更改
git commit -m "描述你的更改"

# 推送到远程
git push
```

### 3. 拉取远程更新

```bash
# 拉取并合并远程更新
git pull origin refactor/project-structure-v2
```

### 4. 查看远程仓库信息

```bash
# 查看远程仓库配置
git remote -v

# 查看远程分支
git branch -r

# 查看提交历史
git log --oneline
```

## 📋 当前Git配置

```
Remote: origin
URL: https://github.com/shierbd/xuq.git
Current Branch: refactor/project-structure-v2

注意: 实际推送使用的URL包含访问令牌，已配置在Git中
令牌信息存储在 .env 文件（本地保存，不会推送到GitHub）
```

## 🔧 常用Git命令

### 创建新分支
```bash
# 创建并切换到新分支
git checkout -b feature/new-feature

# 推送新分支到远程
git push -u origin feature/new-feature
```

### 切换分支
```bash
# 查看所有分支
git branch -a

# 切换到已有分支
git checkout branch-name
```

### 合并分支
```bash
# 切换到目标分支（如main）
git checkout main

# 合并其他分支
git merge feature/new-feature

# 推送合并结果
git push
```

### 撤销修改
```bash
# 撤销工作区的修改（未add）
git checkout -- filename

# 撤销暂存区的修改（已add，未commit）
git reset HEAD filename

# 撤销最近一次commit（保留修改）
git reset --soft HEAD^

# 完全撤销最近一次commit（删除修改）
git reset --hard HEAD^
```

## ⚠️ 注意事项

1. **首次推送前检查**:
   ```bash
   # 确保 .env 文件不在追踪列表中
   git status
   # 如果看到 .env 在列表中，运行：
   git rm --cached .env
   ```

2. **定期更新 .gitignore**:
   - 确保所有敏感文件都被排除
   - 包括: `.env`, `*.key`, API密钥文件等

3. **大文件处理**:
   - 如果需要推送大型CSV文件，考虑使用Git LFS
   - 或者将大文件添加到 `.gitignore`

4. **分支管理建议**:
   - `main`: 稳定版本
   - `develop`: 开发版本
   - `feature/*`: 功能分支
   - `hotfix/*`: 紧急修复分支

## 📝 推荐的Commit Message格式

```
<type>: <subject>

<body>

<footer>
```

**Type类型**:
- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 重构代码
- `test`: 测试相关
- `chore`: 构建/工具链更新

**示例**:
```bash
git commit -m "feat: 添加增量更新机制

- 实现新词自动分配到大组
- 添加embedding缓存版本管理
- 支持多轮迭代过滤规则

Closes #123"
```

## 🔗 相关资源

- GitHub仓库: https://github.com/shierbd/xuq
- Git官方文档: https://git-scm.com/doc
- GitHub文档: https://docs.github.com/

## 📧 问题反馈

如果遇到推送问题或令牌失效，请：
1. 检查 `.env` 文件中的令牌是否正确
2. 前往 GitHub Settings > Developer settings > Personal access tokens 重新生成
3. 更新 `.env` 文件中的 `GITHUB_TOKEN` 值

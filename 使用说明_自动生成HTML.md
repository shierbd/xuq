# 🎯 自动生成HTML功能 - 使用说明

## ✅ 已完成集成

现在系统已经实现了**自动、可持续的HTML生成功能**！

每次运行聚类脚本时，会自动生成HTML查看器，您无需手动操作。

---

## 📋 工作流程

### 方式1：完整流程（推荐）

```bash
# 进入scripts目录
cd D:\xiangmu\词根聚类需求挖掘\scripts

# 1. A阶段聚类（自动生成cluster_summary_A3.html）
python step_A3_clustering.py

# 2. 自动选择方向（可选，也可以用manual_direction_selector.py人工选择）
python auto_select_directions.py

# 3. B阶段聚类（自动生成cluster_summary_B3.html + direction_keywords.html）
python step_B3_cluster_stageB.py
```

### 方式2：仅重新生成HTML

如果您已经有CSV文件，只想重新生成HTML：

```bash
cd D:\xiangmu\词根聚类需求挖掘\scripts
python generate_html_viewer.py
```

---

## 📁 自动生成的HTML文件

运行完成后，在 `output/` 目录下会自动生成3个HTML文件：

| HTML文件 | 来源CSV | 说明 | 何时生成 |
|---------|---------|------|----------|
| **cluster_summary_A3.html** | cluster_summary_A3.csv | A阶段聚类汇总（63个簇） | 运行step_A3后自动生成 |
| **cluster_summary_B3.html** | cluster_summary_B3.csv | B阶段聚类汇总（9个子簇） | 运行step_B3后自动生成 |
| **direction_keywords.html** | direction_keywords.csv | 筛选的5个方向 | 运行step_B3后自动生成 |

---

## 🌐 如何查看和翻译HTML

### 步骤1：打开文件
1. 打开文件夹：`D:\xiangmu\词根聚类需求挖掘\output\`
2. 双击任意 `.html` 文件

### 步骤2：翻译为中文

**Chrome浏览器（推荐）：**
1. 右键点击页面空白处
2. 选择"翻译为中文（简体）"
3. 完成！

**Edge浏览器：**
1. 右键点击页面空白处
2. 选择"翻译"
3. 选择目标语言为"中文"

**Firefox浏览器：**
- 需要先安装"To Google Translate"扩展
- 或手动复制文本到Google翻译

---

## 💡 典型使用场景

### 场景1：首次运行系统
```bash
cd scripts
python step_A3_clustering.py          # ✅ 自动生成 cluster_summary_A3.html
python auto_select_directions.py       # 选择方向
python step_B3_cluster_stageB.py      # ✅ 自动生成 cluster_summary_B3.html 和 direction_keywords.html
```

结果：`output/` 目录下自动生成3个HTML文件

### 场景2：更新种子词后重新聚类
```bash
# 修改种子词文件后
cd scripts
python step_A3_clustering.py          # ✅ 自动生成新的 cluster_summary_A3.html
# 打开 output/cluster_summary_A3.html 查看新结果
```

结果：HTML文件自动更新

### 场景3：调整参数后重新聚类
```bash
# 修改config.py中的参数后
cd scripts
python step_A3_clustering.py          # ✅ 自动生成新的 HTML
python auto_select_directions.py
python step_B3_cluster_stageB.py      # ✅ 自动生成新的 HTML
```

结果：所有HTML文件自动更新

---

## 🎨 HTML文件特点

### 用户友好的设计
- ✅ 响应式布局，适配各种屏幕
- ✅ 清晰的表格样式，易于阅读
- ✅ 鼠标悬停高亮，方便查找
- ✅ 粘性表头，滚动时表头固定
- ✅ 数字右对齐，易于比较

### 翻译友好
- ✅ 包含中英文双语标题
- ✅ 明确的翻译操作提示
- ✅ 浏览器自动识别语言

### 数据展示
- ✅ 显示文件元信息（行数、列数）
- ✅ 限制显示500行（避免页面过大）
- ✅ 自动格式化数字（千分位分隔）
- ✅ 代表性短语自动换行

---

## 🔍 常见问题

### Q1：运行聚类脚本时没有生成HTML？
**检查点：**
1. 确认CSV文件已成功生成
2. 查看控制台是否有"[OK] HTML查看器"的消息
3. 检查 `output/` 目录是否存在

### Q2：HTML文件打开是乱码？
**解决方法：**
- HTML文件使用UTF-8编码
- 确保使用现代浏览器（Chrome/Edge/Firefox）
- 不要用记事本打开HTML文件

### Q3：浏览器没有翻译选项？
**解决方法：**
- Chrome：确保在设置中启用了"翻译"功能
- Edge：确保在设置中启用了"Microsoft Translator"
- Firefox：需要安装翻译扩展

### Q4：HTML生成失败不影响主流程吗？
**答：是的！**
- HTML生成失败只会显示警告，不会中断聚类流程
- CSV文件始终会正常生成
- 您可以稍后单独运行 `generate_html_viewer.py`

---

## 🚀 优势总结

### ✅ 完全自动化
- 无需手动操作
- 每次聚类自动更新HTML
- 不影响原有流程

### ✅ 可持续使用
- 不是一次性工具
- 每次运行都会重新生成
- 始终显示最新数据

### ✅ 多次运行友好
- HTML文件会自动覆盖更新
- 无需手动删除旧文件
- 始终保持最新版本

### ✅ 无需额外依赖
- 只使用Python标准库（pandas）
- 不需要安装额外工具
- 不需要网络连接

---

## 📊 示例输出

运行完整流程后，控制台输出：

```
------------------------------------------------------------
10.5 生成HTML查看器
------------------------------------------------------------
[OK] HTML查看器已生成: D:\xiangmu\词根聚类需求挖掘\output\cluster_summary_A3.html
     请在浏览器中打开此文件
[OK] HTML查看器: D:\xiangmu\词根聚类需求挖掘\output\cluster_summary_A3.html
     提示: 双击打开，右键翻译为中文
```

---

## 📝 技术细节

### 集成位置
1. **step_A3_clustering.py** (第485-504行)
   - 在保存CSV后自动调用
   - 生成 `cluster_summary_A3.html`

2. **step_B3_cluster_stageB.py** (第311-343行)
   - 在保存CSV后自动调用
   - 生成 `cluster_summary_B3.html` 和 `direction_keywords.html`

### 错误处理
- 使用 try-except 捕获异常
- HTML生成失败不影响主流程
- 显示友好的错误提示

---

## 🎉 总结

现在您拥有一个**完全自动化、可持续使用**的HTML生成系统！

**使用方式：**
1. 像往常一样运行聚类脚本
2. HTML文件会自动生成在 `output/` 目录
3. 双击打开，右键翻译为中文
4. 享受可读的中文结果！

**无需担心：**
- ❌ 不用手动运行HTML生成脚本
- ❌ 不用记住额外的命令
- ❌ 不用担心忘记生成HTML
- ❌ 不用担心HTML和CSV不一致

**一切都是自动的！** 🚀

---

最后更新：2025-12-16

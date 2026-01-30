# Reddit模块说明

## 📊 模块概览

**目录**: `frontend/src/pages/reddit/`
**页面数**: 2个
**路由前缀**: `/reddit/`

---

## 🎯 模块目标

从Reddit社区发现用户需求和痛点，验证产品机会方向。

---

## 🔄 工作流程

```
R1 数据采集 → R2 数据分析 → R3 需求提取
```

---

## 📄 页面列表

### R1阶段：数据采集

**页面**: `DataCollection.jsx`
**路由**: `/reddit/collection`

**功能说明**:
- 配置Reddit数据采集任务
- 输入目标Subreddit和关键词
- 选择排序方式（Hot/New/Top/Rising）
- 查看采集任务列表和状态
- 支持任务描述和备注

**主要组件**:
- 采集配置表单（Subreddit、关键词、排序方式）
- 统计卡片（任务总数、已完成、总帖子数、进行中）
- 任务列表表格（任务ID、状态、帖子数量、操作）

**数据流**:
```
用户输入 → 创建采集任务 → 后台采集 → 存储到数据库
```

---

### R2阶段：数据分析

**页面**: `DataAnalysis.jsx`
**路由**: `/reddit/analysis`

**功能说明**:
- 浏览和分析采集的Reddit帖子
- 查看帖子热度（点赞数、评论数）
- 分析情感倾向（积极/中性/消极）
- 筛选和搜索帖子
- 查看帖子详情

**主要组件**:
- 统计卡片（帖子总数、总点赞数、总评论数、平均点赞）
- 帖子列表表格（Subreddit、标题、作者、点赞、评论、情感、时间）
- 筛选区域（搜索、Subreddit筛选）
- 标签页（帖子列表、需求分析、情感分析）

**数据流**:
```
数据库帖子 → 情感分析 → 需求提取 → 可视化展示
```

---

## 🔗 API接口

**文件**: `frontend/src/api/reddit.js`

**接口列表**:
1. `getCollectionTasks()` - 获取采集任务列表
2. `createCollectionTask()` - 创建采集任务
3. `getRedditPosts()` - 获取帖子列表
4. `getRedditPostDetail()` - 获取帖子详情
5. `getRedditStats()` - 获取统计数据
6. `analyzeSentiment()` - 执行情感分析
7. `exportRedditData()` - 导出数据

---

## 🎨 UI设计

### 主色调
- **主色**: 橙色系 (#ff4500 - Reddit品牌色)
- **辅助色**: 蓝色系（点赞）、绿色系（积极情感）

### 图标
- RedditOutlined - Reddit图标
- DownloadOutlined - 数据采集
- BarChartOutlined - 数据分析
- HeartOutlined - 点赞
- CommentOutlined - 评论

### 风格
- 社交媒体型，强调用户互动和情感分析
- 数据可视化，展示热度和趋势

---

## 📊 数据结构

### 采集任务 (Collection Task)
```javascript
{
  task_id: 1,
  subreddit: 'Entrepreneur',
  keywords: 'startup idea, business opportunity',
  sort_by: 'hot',
  status: 'completed',
  posts_count: 150,
  created_at: '2026-01-27 10:00:00',
  description: '采集创业相关讨论'
}
```

### Reddit帖子 (Reddit Post)
```javascript
{
  post_id: 1,
  subreddit: 'Entrepreneur',
  title: 'Looking for startup ideas in the productivity space',
  content: 'I want to build a SaaS product...',
  author: 'user123',
  score: 245,
  num_comments: 67,
  created_at: '2026-01-27 10:30:00',
  sentiment: 'positive'
}
```

---

## 🚀 访问地址

- **R1-数据采集**: http://localhost:3000/reddit/collection
- **R2-数据分析**: http://localhost:3000/reddit/analysis

---

## 🔄 与其他模块的关系

### 与词根聚类模块
- Reddit帖子中的关键词可以作为种子词输入
- 用户讨论的痛点可以验证聚类方向

### 与商品管理模块
- Reddit需求可以指导商品开发方向
- 用户痛点可以匹配现有商品解决方案

---

## 📈 未来扩展

### R3阶段：需求提取（待开发）
- 自动提取用户痛点
- 识别高频需求
- 生成需求报告

### R4阶段：趋势分析（待开发）
- 时间序列分析
- 热度趋势预测
- 话题演变追踪

### R5阶段：竞品分析（待开发）
- 识别竞品讨论
- 分析用户评价
- 发现差异化机会

---

**最后更新**: 2026-01-28
**版本**: v2.0

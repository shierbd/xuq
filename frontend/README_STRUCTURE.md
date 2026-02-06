# 前端目录结构说明

## 📁 按模块组织的目录结构

```
frontend/src/
├── api/                          # API 客户端
│   ├── client.js                 # Axios 基础配置
│   ├── keywords.js               # 词根聚类模块 API
│   ├── products.js               # 商品管理模块 API
│   └── import_export.js          # 导入导出 API
│
├── pages/                        # 页面组件（按模块分组）
│   ├── keywords/                 # 词根聚类模块页面
│   │   ├── SeedWordManagement.jsx        # A1-种子词管理
│   │   ├── KeywordImport.jsx             # A2-关键词导入
│   │   ├── KeywordList.jsx               # 关键词列表
│   │   ├── ClusterOverview.jsx           # A3-簇概览
│   │   ├── ClusterDetail.jsx             # 簇详情
│   │   ├── ClusterAnnotation.jsx         # A4-AI簇标注
│   │   ├── DirectionSelection.jsx        # A5-方向筛选
│   │   └── DirectionManagement.jsx       # B阶段-方向管理
│   │
│   └── products/                 # 商品管理模块页面
│       ├── ProductManagement.jsx         # P1-商品管理
│       ├── DataImport.jsx                # P1-数据导入
│       ├── BatchImport.jsx               # P1-批量导入
│       └── DataExport.jsx                # P1-数据导出
│
├── components/                   # 共享组件
│   └── ProductTable.jsx          # 商品表格组件
│
├── hooks/                        # 自定义 Hooks
├── stores/                       # 状态管理
├── styles/                       # 全局样式
├── utils/                        # 工具函数
├── App.jsx                       # 应用入口
└── main.jsx                      # React 入口
```

## 🎯 模块说明

### 词根聚类模块 (keywords/)
**目标**: 从英文单词种子发现产品机会方向

**页面列表**:
- A1: 种子词管理 - 管理46个英文单词种子
- A2: 关键词导入 - 导入SEMrush/Reddit采集的关键词
- A3: 簇概览 - 展示63个语义簇
- A4: AI簇标注 - 使用AI为簇生成标签和解释
- A5: 方向筛选 - 筛选5-10个有价值方向
- B阶段: 方向管理 - 方向深化与需求分析

### 商品管理模块 (products/)
**目标**: 分析市场供给情况，识别交付产品类型

**页面列表**:
 - P1: 商品管理 - 商品列表与聚类分析
- P1: 数据导入 - 导入Etsy商品数据
- P1: 数据导出 - 导出各阶段数据
- P1: 批量导入 - 导入文件夹内商品数据

## 📝 导入路径规范

### 页面组件导入 API
```javascript
// keywords 模块页面
import { getKeywords } from '../../api/keywords';

// products 模块页面
import { getProducts } from '../../api/products';
```

### 页面组件导入共享组件
```javascript
// keywords 模块页面
import SomeComponent from '../../components/SomeComponent';

// products 模块页面
import ProductTable from '../../components/ProductTable';
```

### App.jsx 导入页面组件
```javascript
// 词根聚类模块页面
import SeedWordManagement from './pages/keywords/SeedWordManagement';

// 商品管理模块页面
import ProductManagement from './pages/products/ProductManagement';
```

## 🚀 路由配置

### 词根聚类模块路由
- `/seed-words` - A1种子词管理
- `/keyword-import` - A2关键词导入
- `/keywords` - 关键词列表
- `/clusters` - A3簇概览
- `/clusters/:clusterId` - 簇详情
- `/cluster-annotation` - A4 AI簇标注
- `/direction-selection` - A5方向筛选
- `/directions` - B阶段方向管理

### 商品管理模块路由
- `/` - 商品管理
- `/import` - 数据导入
- `/batch-import` - 批量导入
- `/export` - 数据导出

## 📦 模块独立性

每个模块的页面都在各自的目录下，具有以下优势：

1. **清晰的模块边界**: 每个模块的代码物理隔离
2. **独立开发**: 不同模块可以并行开发
3. **易于维护**: 模块内的修改不影响其他模块
4. **便于扩展**: 新增模块只需创建新目录

## 🔧 开发规范

### 新增页面
1. 在对应模块目录下创建页面组件
2. 在 App.jsx 中添加导入和路由
3. 在导航菜单中添加菜单项

### 新增模块
1. 在 `pages/` 下创建新模块目录
2. 在 `api/` 下创建对应的 API 客户端
3. 在 App.jsx 中添加模块的导入、路由和菜单

---

**最后更新**: 2026-02-04
**版本**: v2.0

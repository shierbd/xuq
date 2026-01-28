/**
 * 主应用入口 - 带路由和导航
 */
import React, { useState, useCallback } from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation, useNavigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ConfigProvider, Layout, Menu } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import {
  ShoppingOutlined,
  UploadOutlined,
  RobotOutlined,
  DownloadOutlined,
  HistoryOutlined,
  BarChartOutlined,
  ClusterOutlined,
  FileTextOutlined,
  EyeOutlined,
  StarOutlined,
  FilterOutlined,
  RocketOutlined,
  TagOutlined,
  RedditOutlined,
  FolderOpenOutlined,
} from '@ant-design/icons';
// 商品管理模块页面
import ProductManagement from './pages/products/ProductManagement';
import DataImport from './pages/products/DataImport';
import BatchImport from './pages/products/BatchImport';
import AIAnnotation from './pages/products/AIAnnotation';
import DataExport from './pages/products/DataExport';
import ImportHistory from './pages/products/ImportHistory';

// 词根聚类模块页面
import ClusterOverview from './pages/keywords/ClusterOverview';
import KeywordList from './pages/keywords/KeywordList';
import ClusterDetail from './pages/keywords/ClusterDetail';
import SeedWordManagement from './pages/keywords/SeedWordManagement';
import KeywordImport from './pages/keywords/KeywordImport';
import ClusterAnnotation from './pages/keywords/ClusterAnnotation';
import DirectionSelection from './pages/keywords/DirectionSelection';
import DirectionManagement from './pages/keywords/DirectionManagement';

// Reddit模块页面
import DataCollection from './pages/reddit/DataCollection';
import DataAnalysis from './pages/reddit/DataAnalysis';

import './App.css';

const { Header, Sider, Content } = Layout;

// 创建QueryClient实例
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5分钟
    },
  },
});

// 导航菜单项
const menuItems = [
  {
    key: 'keyword-module',
    label: '词根聚类模块',
    icon: <ClusterOutlined />,
    children: [
      {
        key: '/seed-words',
        icon: <TagOutlined />,
        label: 'A1-种子词管理',
      },
      {
        key: '/keyword-import',
        icon: <UploadOutlined />,
        label: 'A2-关键词导入',
      },
      {
        key: '/keywords',
        icon: <FileTextOutlined />,
        label: '关键词列表',
      },
      {
        key: '/clusters',
        icon: <BarChartOutlined />,
        label: 'A3-簇概览',
      },
      {
        key: '/cluster-annotation',
        icon: <RobotOutlined />,
        label: 'A4-AI簇标注',
      },
      {
        key: '/direction-selection',
        icon: <FilterOutlined />,
        label: 'A5-方向筛选',
      },
      {
        key: '/directions',
        icon: <RocketOutlined />,
        label: 'B阶段-方向管理',
      },
    ],
  },
  {
    key: 'product-module',
    label: '商品管理模块',
    icon: <ShoppingOutlined />,
    children: [
      {
        key: '/',
        icon: <EyeOutlined />,
        label: '商品管理',
      },
      {
        key: '/import',
        icon: <UploadOutlined />,
        label: '数据导入',
      },
      {
        key: '/batch-import',
        icon: <FolderOpenOutlined />,
        label: '批量导入',
      },
      {
        key: '/annotation',
        icon: <RobotOutlined />,
        label: 'AI标注',
      },
      {
        key: '/export',
        icon: <DownloadOutlined />,
        label: '数据导出',
      },
      {
        key: '/history',
        icon: <HistoryOutlined />,
        label: '导入历史',
      },
    ],
  },
  {
    key: 'reddit-module',
    label: 'Reddit模块',
    icon: <RedditOutlined />,
    children: [
      {
        key: '/reddit/collection',
        icon: <DownloadOutlined />,
        label: 'R1-数据采集',
      },
      {
        key: '/reddit/analysis',
        icon: <BarChartOutlined />,
        label: 'R2-数据分析',
      },
    ],
  },
];

function AppContent() {
  const location = useLocation();
  const navigate = useNavigate();
  const [collapsed, setCollapsed] = useState(false);

  // 处理菜单点击事件 - 使用 useCallback 避免无限循环
  const handleMenuClick = useCallback(({ key }) => {
    // 只有当点击的不是父级菜单项时才导航
    if (key && !key.includes('-module')) {
      navigate(key);
    }
  }, [navigate]);

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        style={{
          overflow: 'auto',
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
        }}
      >
        <div
          style={{
            height: 32,
            margin: 16,
            background: 'rgba(255, 255, 255, 0.2)',
            borderRadius: 6,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            fontWeight: 'bold',
          }}
        >
          {!collapsed && '需求挖掘系统'}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          onClick={handleMenuClick}
          items={menuItems}
        />
      </Sider>
      <Layout style={{ marginLeft: collapsed ? 80 : 200, transition: 'all 0.2s' }}>
        <Header
          style={{
            padding: '0 24px',
            background: '#fff',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <h1 style={{ margin: 0, fontSize: 20, fontWeight: 600, color: '#1890ff' }}>
            需求挖掘系统 v2.0
          </h1>
          <div style={{ color: '#999' }}>v2.0.0</div>
        </Header>
        <Content style={{ margin: 0, overflow: 'initial' }}>
          <Routes>
            {/* 词根聚类模块 - A阶段 */}
            <Route path="/seed-words" element={<SeedWordManagement />} />
            <Route path="/keyword-import" element={<KeywordImport />} />
            <Route path="/keywords" element={<KeywordList />} />
            <Route path="/clusters" element={<ClusterOverview />} />
            <Route path="/clusters/:clusterId" element={<ClusterDetail />} />
            <Route path="/cluster-annotation" element={<ClusterAnnotation />} />
            <Route path="/direction-selection" element={<DirectionSelection />} />

            {/* 词根聚类模块 - B阶段 */}
            <Route path="/directions" element={<DirectionManagement />} />

            {/* 商品管理模块 */}
            <Route path="/" element={<ProductManagement />} />
            <Route path="/import" element={<DataImport />} />
            <Route path="/batch-import" element={<BatchImport />} />
            <Route path="/annotation" element={<AIAnnotation />} />
            <Route path="/export" element={<DataExport />} />
            <Route path="/history" element={<ImportHistory />} />

            {/* Reddit模块 */}
            <Route path="/reddit/collection" element={<DataCollection />} />
            <Route path="/reddit/analysis" element={<DataAnalysis />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ConfigProvider locale={zhCN}>
        <Router>
          <AppContent />
        </Router>
      </ConfigProvider>
    </QueryClientProvider>
  );
}

export default App;

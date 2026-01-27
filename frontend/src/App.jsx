/**
 * 主应用入口 - 带路由和导航
 */
import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
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
} from '@ant-design/icons';
import ProductManagement from './pages/ProductManagement';
import DataImport from './pages/DataImport';
import AIAnnotation from './pages/AIAnnotation';
import DataExport from './pages/DataExport';
import ImportHistory from './pages/ImportHistory';
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
    key: '/',
    icon: <ShoppingOutlined />,
    label: <Link to="/">商品管理</Link>,
  },
  {
    key: '/import',
    icon: <UploadOutlined />,
    label: <Link to="/import">数据导入</Link>,
  },
  {
    key: '/annotation',
    icon: <RobotOutlined />,
    label: <Link to="/annotation">AI标注</Link>,
  },
  {
    key: '/export',
    icon: <DownloadOutlined />,
    label: <Link to="/export">数据导出</Link>,
  },
  {
    key: '/history',
    icon: <HistoryOutlined />,
    label: <Link to="/history">导入历史</Link>,
  },
];

function AppContent() {
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);

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
          {!collapsed && '商品管理系统'}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
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
            Phase 7 商品筛选与AI标注系统
          </h1>
          <div style={{ color: '#999' }}>v2.0.0</div>
        </Header>
        <Content style={{ margin: 0, overflow: 'initial' }}>
          <Routes>
            <Route path="/" element={<ProductManagement />} />
            <Route path="/import" element={<DataImport />} />
            <Route path="/annotation" element={<AIAnnotation />} />
            <Route path="/export" element={<DataExport />} />
            <Route path="/history" element={<ImportHistory />} />
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

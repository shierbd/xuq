/**
 * [AI1.1, AI1.2, AI1.3] AI配置管理 - 主页面
 */
import React, { useState } from 'react';
import { Card, Tabs } from 'antd';
import { SettingOutlined, ApiOutlined, AppstoreOutlined } from '@ant-design/icons';
import AIProviderManagement from './AIProviderManagement';
import AIModelManagement from './AIModelManagement';
import AIScenarioManagement from './AIScenarioManagement';

const AIConfig = () => {
  const [activeTab, setActiveTab] = useState('providers');

  const items = [
    {
      key: 'providers',
      label: (
        <span>
          <ApiOutlined />
          AI提供商
        </span>
      ),
      children: <AIProviderManagement />,
    },
    {
      key: 'models',
      label: (
        <span>
          <SettingOutlined />
          AI模型
        </span>
      ),
      children: <AIModelManagement />,
    },
    {
      key: 'scenarios',
      label: (
        <span>
          <AppstoreOutlined />
          使用场景
        </span>
      ),
      children: <AIScenarioManagement />,
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Card
        title={
          <div>
            <h2 style={{ margin: 0, fontSize: '20px' }}>AI配置管理</h2>
            <p style={{ margin: '8px 0 0 0', color: '#999', fontSize: '14px' }}>
              统一管理AI提供商、模型和使用场景配置
            </p>
          </div>
        }
        bordered={false}
      >
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={items}
          size="large"
        />
      </Card>
    </div>
  );
};

export default AIConfig;

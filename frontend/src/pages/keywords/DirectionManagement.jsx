/**
 * 词根聚类模块 - B阶段：方向管理页面
 */
import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Card,
  Table,
  Tag,
  Space,
  Button,
  Tabs,
  Statistic,
  Row,
  Col,
  Alert,
  Progress,
  message,
  Descriptions,
} from 'antd';
import {
  RocketOutlined,
  ClusterOutlined,
  FileTextOutlined,
  ThunderboltOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons';
import './DirectionManagement.css';

const { TabPane } = Tabs;

const DirectionManagement = () => {
  const [activeTab, setActiveTab] = useState('overview');

  // 模拟方向数据
  const directions = [
    {
      direction_id: 1,
      direction_keyword: 'pdf tools',
      priority: 'high',
      status: 'B3',
      expanded_count: 1500,
      cluster_count: 25,
      analyzed: true,
    },
    {
      direction_id: 2,
      direction_keyword: 'image converter',
      priority: 'medium',
      status: 'B1',
      expanded_count: 800,
      cluster_count: 0,
      analyzed: false,
    },
  ];

  // 模拟子簇数据
  const subClusters = [
    {
      cluster_id: 101,
      direction_keyword: 'pdf tools',
      cluster_size: 85,
      cluster_label: 'PDF压缩工具',
      top_keywords: ['compress pdf', 'reduce pdf size', 'pdf compressor'],
      demand_analyzed: true,
    },
    {
      cluster_id: 102,
      direction_keyword: 'pdf tools',
      cluster_size: 72,
      cluster_label: 'PDF转换工具',
      top_keywords: ['pdf to word', 'convert pdf', 'pdf converter'],
      demand_analyzed: false,
    },
  ];

  const directionColumns = [
    {
      title: '方向关键词',
      dataIndex: 'direction_keyword',
      key: 'direction_keyword',
      width: 150,
      render: (text) => <strong style={{ color: '#1890ff' }}>{text}</strong>,
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      width: 100,
      render: (priority) => {
        const color =
          priority === 'high' ? 'red' : priority === 'medium' ? 'orange' : 'default';
        const text = priority === 'high' ? '高' : priority === 'medium' ? '中' : '低';
        return <Tag color={color}>{text}</Tag>;
      },
    },
    {
      title: '当前阶段',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status) => <Tag color="purple">{status}</Tag>,
    },
    {
      title: '扩展数量',
      dataIndex: 'expanded_count',
      key: 'expanded_count',
      width: 120,
      sorter: (a, b) => a.expanded_count - b.expanded_count,
      render: (count) => (
        <span style={{ color: '#52c41a', fontWeight: 500 }}>
          {count ? `${count} 个` : '-'}
        </span>
      ),
    },
    {
      title: '子簇数量',
      dataIndex: 'cluster_count',
      key: 'cluster_count',
      width: 120,
      sorter: (a, b) => a.cluster_count - b.cluster_count,
      render: (count) => (
        <span style={{ color: '#1890ff', fontWeight: 500 }}>
          {count ? `${count} 个` : '-'}
        </span>
      ),
    },
    {
      title: '需求分析',
      dataIndex: 'analyzed',
      key: 'analyzed',
      width: 120,
      render: (analyzed) =>
        analyzed ? (
          <Tag color="success" icon={<CheckCircleOutlined />}>
            已完成
          </Tag>
        ) : (
          <Tag color="default" icon={<ClockCircleOutlined />}>
            未开始
          </Tag>
        ),
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      render: (_, record) => (
        <Space>
          {record.status === 'B1' && (
            <Button
              type="primary"
              size="small"
              onClick={() => message.info('B1: 方向扩展功能开发中')}
            >
              开始扩展
            </Button>
          )}
          {record.status === 'B3' && !record.analyzed && (
            <Button
              type="primary"
              size="small"
              onClick={() => message.info('B6: 需求分析功能开发中')}
            >
              需求分析
            </Button>
          )}
          <Button
            size="small"
            onClick={() => message.info(`查看方向 ${record.direction_keyword} 详情`)}
          >
            查看详情
          </Button>
        </Space>
      ),
    },
  ];

  const subClusterColumns = [
    {
      title: '子簇ID',
      dataIndex: 'cluster_id',
      key: 'cluster_id',
      width: 100,
      render: (id) => <Tag color="blue">#{id}</Tag>,
    },
    {
      title: '所属方向',
      dataIndex: 'direction_keyword',
      key: 'direction_keyword',
      width: 150,
      render: (text) => <Tag color="purple">{text}</Tag>,
    },
    {
      title: '子簇大小',
      dataIndex: 'cluster_size',
      key: 'cluster_size',
      width: 100,
      sorter: (a, b) => a.cluster_size - b.cluster_size,
    },
    {
      title: '子簇标签',
      dataIndex: 'cluster_label',
      key: 'cluster_label',
      width: 150,
    },
    {
      title: '代表性关键词',
      dataIndex: 'top_keywords',
      key: 'top_keywords',
      ellipsis: true,
      render: (keywords) => keywords?.join(', '),
    },
    {
      title: '需求分析',
      dataIndex: 'demand_analyzed',
      key: 'demand_analyzed',
      width: 120,
      render: (analyzed) =>
        analyzed ? (
          <Tag color="success" icon={<CheckCircleOutlined />}>
            已完成
          </Tag>
        ) : (
          <Tag color="default" icon={<ClockCircleOutlined />}>
            未开始
          </Tag>
        ),
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_, record) => (
        <Space>
          {!record.demand_analyzed && (
            <Button
              type="primary"
              size="small"
              onClick={() => message.info('B6: 需求分析功能开发中')}
            >
              分析需求
            </Button>
          )}
          <Button
            size="small"
            onClick={() => message.info(`查看子簇 #${record.cluster_id} 详情`)}
          >
            查看
          </Button>
        </Space>
      ),
    },
  ];

  const totalExpanded = directions.reduce((sum, d) => sum + d.expanded_count, 0);
  const totalClusters = directions.reduce((sum, d) => sum + d.cluster_count, 0);
  const analyzedCount = directions.filter((d) => d.analyzed).length;
  const progress = directions.length > 0 ? (analyzedCount / directions.length) * 100 : 0;

  return (
    <div className="direction-management-container">
      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="方向总数"
              value={directions.length}
              prefix={<RocketOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="总扩展关键词"
              value={totalExpanded}
              prefix={<FileTextOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="总子簇数"
              value={totalClusters}
              prefix={<ClusterOutlined />}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="已分析方向"
              value={analyzedCount}
              suffix={`/ ${directions.length}`}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 进度条 */}
      <Card style={{ marginBottom: 24 }}>
        <div style={{ marginBottom: 8 }}>
          <strong>B阶段整体进度</strong>
        </div>
        <Progress
          percent={Math.round(progress)}
          status={analyzedCount < directions.length ? 'active' : 'success'}
          strokeColor={{
            '0%': '#108ee9',
            '100%': '#87d068',
          }}
        />
      </Card>

      {/* 主内容 */}
      <Card
        title={
          <Space>
            <RocketOutlined />
            <span>B阶段：方向深化与需求分析</span>
          </Space>
        }
      >
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          {/* 方向概览 */}
          <TabPane tab="方向概览" key="overview">
            <Alert
              message="B阶段工作流程"
              description={
                <div>
                  <p><strong>B1: 方向扩展</strong> - 针对每个方向再次扩展500-2000条短语</p>
                  <p><strong>B3: 方向内聚类</strong> - 对扩展结果进行聚类，生成10-30个子簇</p>
                  <p><strong>B6: 需求分析</strong> - 使用5维框架分析每个子簇的需求</p>
                  <p style={{ marginBottom: 0 }}>
                    <strong>5维框架：</strong>What（做什么）、Why（为什么）、Who（什么人）、When（什么场景）、How（如何解决）
                  </p>
                </div>
              }
              type="info"
              showIcon
              style={{ marginBottom: 16 }}
            />

            <Table
              columns={directionColumns}
              dataSource={directions}
              rowKey="direction_id"
              pagination={false}
              scroll={{ x: 1200 }}
            />
          </TabPane>

          {/* 子簇列表 */}
          <TabPane tab={`子簇列表 (${subClusters.length})`} key="subclusters">
            <Alert
              message="子簇说明"
              description="子簇是在方向内部进行二次聚类的结果，每个子簇代表一个更细分的需求点"
              type="info"
              showIcon
              style={{ marginBottom: 16 }}
            />

            <Table
              columns={subClusterColumns}
              dataSource={subClusters}
              rowKey="cluster_id"
              pagination={{
                pageSize: 20,
                showSizeChanger: true,
                showTotal: (total) => `共 ${total} 个子簇`,
              }}
              scroll={{ x: 1200 }}
            />
          </TabPane>

          {/* 需求分析 */}
          <TabPane tab="需求分析" key="analysis">
            <Alert
              message="需求分析说明"
              description="使用5维框架对每个子簇进行深度需求分析，生成可执行的MVP方案"
              type="info"
              showIcon
              style={{ marginBottom: 16 }}
            />

            <Card title="示例：PDF压缩工具需求分析" style={{ marginBottom: 16 }}>
              <Descriptions column={1} bordered>
                <Descriptions.Item label="What - 用户要做什么">
                  压缩PDF文件大小，减少存储空间和传输时间
                </Descriptions.Item>
                <Descriptions.Item label="Why - 为什么要做">
                  邮件附件大小限制、网盘空间不足、上传速度慢
                </Descriptions.Item>
                <Descriptions.Item label="Who - 什么人群">
                  办公人员、学生、设计师、需要频繁处理PDF的用户
                </Descriptions.Item>
                <Descriptions.Item label="When - 什么场景">
                  发送邮件前、上传文档前、存储文件前
                </Descriptions.Item>
                <Descriptions.Item label="How - 如何解决">
                  在线工具：无需安装，拖拽上传，自动压缩，保持质量
                </Descriptions.Item>
                <Descriptions.Item label="MVP方案">
                  开发一个简单的在线PDF压缩工具，支持拖拽上传，提供3种压缩级别（高质量、平衡、高压缩），免费用户每天5次
                </Descriptions.Item>
                <Descriptions.Item label="验证建议">
                  1. SERP分析：查看竞品功能和用户评价
                  <br />
                  2. 用户访谈：了解真实使用场景和痛点
                  <br />
                  3. 落地页测试：验证需求强度和付费意愿
                </Descriptions.Item>
              </Descriptions>
            </Card>

            <Alert
              message="功能开发中"
              description="B6阶段的需求分析功能正在开发中，将支持批量分析和导出报告"
              type="warning"
              showIcon
            />
          </TabPane>

          {/* 批量操作 */}
          <TabPane tab="批量操作" key="batch">
            <Space direction="vertical" style={{ width: '100%' }} size="large">
              <Card title="B1: 批量方向扩展">
                <p>针对所有方向进行关键词扩展，每个方向扩展500-2000条短语</p>
                <Button
                  type="primary"
                  icon={<ThunderboltOutlined />}
                  onClick={() => message.info('B1: 批量方向扩展功能开发中')}
                >
                  开始批量扩展
                </Button>
              </Card>

              <Card title="B3: 批量方向内聚类">
                <p>对所有已扩展的方向进行聚类分析，生成子簇</p>
                <Button
                  type="primary"
                  icon={<ClusterOutlined />}
                  onClick={() => message.info('B3: 批量聚类功能开发中')}
                >
                  开始批量聚类
                </Button>
              </Card>

              <Card title="B6: 批量需求分析">
                <p>使用5维框架对所有子簇进行需求分析</p>
                <Button
                  type="primary"
                  icon={<RobotOutlined />}
                  onClick={() => message.info('B6: 批量需求分析功能开发中')}
                >
                  开始批量分析
                </Button>
              </Card>
            </Space>
          </TabPane>
        </Tabs>
      </Card>
    </div>
  );
};

export default DirectionManagement;

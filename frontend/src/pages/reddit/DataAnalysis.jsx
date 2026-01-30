/**
 * Reddit模块 - R2阶段：数据分析页面
 */
import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Card,
  Table,
  Tag,
  Space,
  Button,
  Input,
  Select,
  Statistic,
  Row,
  Col,
  Alert,
  Tabs,
  message,
} from 'antd';
import {
  BarChartOutlined,
  FileTextOutlined,
  FilterOutlined,
  EyeOutlined,
  HeartOutlined,
  CommentOutlined,
} from '@ant-design/icons';
import './DataAnalysis.css';

const { Search } = Input;
const { Option } = Select;
const { TabPane } = Tabs;

const DataAnalysis = () => {
  const [searchText, setSearchText] = useState('');
  const [subreddit, setSubreddit] = useState(null);
  const [activeTab, setActiveTab] = useState('posts');

  // 模拟Reddit帖子数据
  const posts = [
    {
      post_id: 1,
      subreddit: 'Entrepreneur',
      title: 'Looking for startup ideas in the productivity space',
      content: 'I want to build a SaaS product that helps people be more productive...',
      author: 'user123',
      score: 245,
      num_comments: 67,
      created_at: '2026-01-27 10:30:00',
      sentiment: 'positive',
    },
    {
      post_id: 2,
      subreddit: 'startups',
      title: 'What are the biggest pain points for small businesses?',
      content: 'Trying to validate my idea for a business management tool...',
      author: 'user456',
      score: 189,
      num_comments: 43,
      created_at: '2026-01-27 09:15:00',
      sentiment: 'neutral',
    },
  ];

  const columns = [
    {
      title: 'Subreddit',
      dataIndex: 'subreddit',
      key: 'subreddit',
      width: 120,
      render: (text) => <Tag color="orange">{text}</Tag>,
    },
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      ellipsis: true,
      render: (text) => <strong>{text}</strong>,
    },
    {
      title: '作者',
      dataIndex: 'author',
      key: 'author',
      width: 120,
    },
    {
      title: '点赞',
      dataIndex: 'score',
      key: 'score',
      width: 100,
      sorter: (a, b) => a.score - b.score,
      render: (score) => (
        <Space>
          <HeartOutlined style={{ color: '#ff4d4f' }} />
          <span style={{ fontWeight: 500 }}>{score}</span>
        </Space>
      ),
    },
    {
      title: '评论',
      dataIndex: 'num_comments',
      key: 'num_comments',
      width: 100,
      sorter: (a, b) => a.num_comments - b.num_comments,
      render: (count) => (
        <Space>
          <CommentOutlined style={{ color: '#1890ff' }} />
          <span style={{ fontWeight: 500 }}>{count}</span>
        </Space>
      ),
    },
    {
      title: '情感',
      dataIndex: 'sentiment',
      key: 'sentiment',
      width: 100,
      render: (sentiment) => {
        const color =
          sentiment === 'positive'
            ? 'green'
            : sentiment === 'negative'
            ? 'red'
            : 'default';
        const text =
          sentiment === 'positive'
            ? '积极'
            : sentiment === 'negative'
            ? '消极'
            : '中性';
        return <Tag color={color}>{text}</Tag>;
      },
    },
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_, record) => (
        <Button
          type="link"
          size="small"
          icon={<EyeOutlined />}
          onClick={() => message.info(`查看帖子 #${record.post_id} 详情`)}
        >
          查看
        </Button>
      ),
    },
  ];

  const totalScore = posts.reduce((sum, p) => sum + p.score, 0);
  const totalComments = posts.reduce((sum, p) => sum + p.num_comments, 0);
  const avgScore = posts.length > 0 ? Math.round(totalScore / posts.length) : 0;

  return (
    <div className="data-analysis-container">
      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="帖子总数"
              value={posts.length}
              prefix={<FileTextOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="总点赞数"
              value={totalScore}
              prefix={<HeartOutlined />}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="总评论数"
              value={totalComments}
              prefix={<CommentOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="平均点赞"
              value={avgScore}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 主内容 */}
      <Card
        title={
          <Space>
            <BarChartOutlined />
            <span>R2阶段：Reddit数据分析</span>
          </Space>
        }
      >
        <Alert
          message="数据分析说明"
          description="分析Reddit帖子的热度、情感倾向和用户需求，发现潜在的产品机会"
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />

        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          {/* 帖子列表 */}
          <TabPane tab={`帖子列表 (${posts.length})`} key="posts">
            {/* 筛选区域 */}
            <Space style={{ marginBottom: 16 }} wrap>
              <Search
                placeholder="搜索标题或内容"
                allowClear
                style={{ width: 300 }}
                onSearch={(value) => setSearchText(value)}
              />
              <Select
                placeholder="选择Subreddit"
                style={{ width: 150 }}
                value={subreddit}
                onChange={setSubreddit}
                allowClear
              >
                <Option value="Entrepreneur">Entrepreneur</Option>
                <Option value="startups">startups</Option>
                <Option value="SaaS">SaaS</Option>
              </Select>
              <Button icon={<FilterOutlined />} onClick={() => setSubreddit(null)}>
                重置筛选
              </Button>
            </Space>

            {/* 帖子表格 */}
            <Table
              columns={columns}
              dataSource={posts}
              rowKey="post_id"
              pagination={{
                pageSize: 20,
                showSizeChanger: true,
                showTotal: (total) => `共 ${total} 个帖子`,
              }}
              scroll={{ x: 1200 }}
            />
          </TabPane>

          {/* 需求分析 */}
          <TabPane tab="需求分析" key="analysis">
            <Alert
              message="功能开发中"
              description="R2阶段的需求分析功能正在开发中，将支持：痛点提取、需求聚类、热度分析"
              type="warning"
              showIcon
            />
          </TabPane>

          {/* 情感分析 */}
          <TabPane tab="情感分析" key="sentiment">
            <Alert
              message="功能开发中"
              description="情感分析功能正在开发中，将支持：情感分类、情感趋势、关键词提取"
              type="warning"
              showIcon
            />
          </TabPane>
        </Tabs>
      </Card>
    </div>
  );
};

export default DataAnalysis;

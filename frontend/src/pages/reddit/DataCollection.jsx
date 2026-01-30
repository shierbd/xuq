/**
 * Reddit模块 - R1阶段：数据采集页面
 */
import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Card,
  Button,
  Input,
  Space,
  Table,
  Tag,
  Statistic,
  Row,
  Col,
  Alert,
  Progress,
  message,
  Form,
  Select,
} from 'antd';
import {
  RedditOutlined,
  SearchOutlined,
  DownloadOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons';
import './DataCollection.css';

const { TextArea } = Input;
const { Option } = Select;

const DataCollection = () => {
  const queryClient = useQueryClient();
  const [form] = Form.useForm();
  const [collecting, setCollecting] = useState(false);

  // 模拟采集任务数据
  const [tasks, setTasks] = useState([
    {
      task_id: 1,
      subreddit: 'Entrepreneur',
      keywords: 'startup idea, business opportunity',
      status: 'completed',
      posts_count: 150,
      created_at: '2026-01-27 10:00:00',
    },
  ]);

  // 开始采集
  const handleStartCollection = (values) => {
    message.info('Reddit数据采集功能开发中');
    console.log('采集参数:', values);
  };

  const columns = [
    {
      title: '任务ID',
      dataIndex: 'task_id',
      key: 'task_id',
      width: 100,
      render: (id) => <Tag color="blue">#{id}</Tag>,
    },
    {
      title: 'Subreddit',
      dataIndex: 'subreddit',
      key: 'subreddit',
      width: 150,
      render: (text) => <strong>{text}</strong>,
    },
    {
      title: '关键词',
      dataIndex: 'keywords',
      key: 'keywords',
      ellipsis: true,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status) =>
        status === 'completed' ? (
          <Tag color="success" icon={<CheckCircleOutlined />}>
            已完成
          </Tag>
        ) : (
          <Tag color="processing" icon={<ClockCircleOutlined />}>
            采集中
          </Tag>
        ),
    },
    {
      title: '帖子数量',
      dataIndex: 'posts_count',
      key: 'posts_count',
      width: 120,
      sorter: (a, b) => a.posts_count - b.posts_count,
      render: (count) => (
        <span style={{ color: '#1890ff', fontWeight: 500 }}>{count}</span>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<DownloadOutlined />}
            onClick={() => message.info('导出功能开发中')}
          >
            导出
          </Button>
          <Button
            type="link"
            size="small"
            onClick={() => message.info('查看详情功能开发中')}
          >
            查看
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div className="data-collection-container">
      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="采集任务总数"
              value={tasks.length}
              prefix={<RedditOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="已完成任务"
              value={tasks.filter((t) => t.status === 'completed').length}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="总帖子数"
              value={tasks.reduce((sum, t) => sum + t.posts_count, 0)}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="进行中任务"
              value={tasks.filter((t) => t.status === 'collecting').length}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 采集配置 */}
      <Card
        title={
          <Space>
            <RedditOutlined />
            <span>R1阶段：Reddit数据采集</span>
          </Space>
        }
        style={{ marginBottom: 24 }}
      >
        <Alert
          message="Reddit数据采集说明"
          description={
            <ul style={{ marginBottom: 0, paddingLeft: 20 }}>
              <li>输入目标Subreddit和关键词，系统将自动采集相关帖子</li>
              <li>支持多个关键词，用逗号分隔</li>
              <li>采集的数据包括：标题、内容、评论、点赞数、时间等</li>
              <li>采集完成后可以进行R2阶段的数据清洗和分析</li>
            </ul>
          }
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />

        <Form form={form} layout="vertical" onFinish={handleStartCollection}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="subreddit"
                label="Subreddit"
                rules={[{ required: true, message: '请输入Subreddit名称' }]}
              >
                <Input
                  placeholder="例如: Entrepreneur, startups, SaaS"
                  prefix={<RedditOutlined />}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="sort_by"
                label="排序方式"
                initialValue="hot"
                rules={[{ required: true, message: '请选择排序方式' }]}
              >
                <Select>
                  <Option value="hot">Hot (热门)</Option>
                  <Option value="new">New (最新)</Option>
                  <Option value="top">Top (最高)</Option>
                  <Option value="rising">Rising (上升)</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="keywords"
            label="关键词"
            rules={[{ required: true, message: '请输入关键词' }]}
          >
            <Input
              placeholder="例如: startup idea, business opportunity, product validation"
            />
          </Form.Item>

          <Form.Item name="description" label="任务描述">
            <TextArea
              rows={3}
              placeholder="描述这次采集的目的和用途"
            />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button
                type="primary"
                htmlType="submit"
                icon={<SearchOutlined />}
                loading={collecting}
              >
                开始采集
              </Button>
              <Button onClick={() => form.resetFields()}>重置</Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>

      {/* 采集任务列表 */}
      <Card
        title={
          <Space>
            <ClockCircleOutlined />
            <span>采集任务列表</span>
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={tasks}
          rowKey="task_id"
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 个任务`,
          }}
        />
      </Card>
    </div>
  );
};

export default DataCollection;

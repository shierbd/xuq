/**
 * 词根聚类模块 - A5阶段：方向筛选页面
 */
import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Card,
  Table,
  Tag,
  Space,
  Button,
  Input,
  Select,
  Modal,
  Form,
  InputNumber,
  Statistic,
  Row,
  Col,
  Alert,
  message,
  Popconfirm,
} from 'antd';
import {
  FilterOutlined,
  PlusOutlined,
  DeleteOutlined,
  CheckCircleOutlined,
  StarOutlined,
  TrophyOutlined,
} from '@ant-design/icons';
import { getClustersOverview } from '../../api/keywords';
import './DirectionSelection.css';

const { TextArea } = Input;
const { Option } = Select;

const DirectionSelection = () => {
  const queryClient = useQueryClient();
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [selectedCluster, setSelectedCluster] = useState(null);
  const [selectedDirections, setSelectedDirections] = useState([]);
  const [form] = Form.useForm();

  // 获取已标注的簇
  const { data: clustersData, isLoading } = useQuery({
    queryKey: ['clusters-overview', { stage: 'A', exclude_noise: true }],
    queryFn: () => getClustersOverview({ stage: 'A', exclude_noise: true }),
  });

  const clusters = clustersData?.data || [];
  const annotatedClusters = clusters.filter((c) => c.cluster_label);

  // 模拟已选方向数据
  const [directions, setDirections] = useState([
    {
      direction_id: 1,
      direction_keyword: 'pdf tools',
      from_cluster_id: 5,
      priority: 'high',
      business_value: 'high',
      trends_score: 85,
      notes: 'PDF工具类需求旺盛，市场空间大',
    },
  ]);

  // 添加方向
  const handleAddDirection = (values) => {
    const newDirection = {
      direction_id: directions.length + 1,
      direction_keyword: values.direction_keyword,
      from_cluster_id: selectedCluster.cluster_id,
      priority: values.priority,
      business_value: values.business_value,
      trends_score: values.trends_score,
      notes: values.notes,
    };

    setDirections([...directions, newDirection]);
    message.success('方向添加成功');
    setIsModalVisible(false);
    form.resetFields();
    setSelectedCluster(null);
  };

  // 删除方向
  const handleDeleteDirection = (directionId) => {
    setDirections(directions.filter((d) => d.direction_id !== directionId));
    message.success('方向删除成功');
  };

  // 打开添加对话框
  const handleSelectCluster = (cluster) => {
    setSelectedCluster(cluster);
    form.setFieldsValue({
      direction_keyword: cluster.top_keywords?.[0] || '',
      priority: 'medium',
      business_value: 'medium',
      trends_score: 50,
    });
    setIsModalVisible(true);
  };

  // 导出方向
  const handleExport = () => {
    message.info('导出功能开发中');
  };

  // 进入B阶段
  const handleEnterStageB = () => {
    if (directions.length === 0) {
      message.warning('请先选择至少一个方向');
      return;
    }

    Modal.confirm({
      title: '确认进入B阶段',
      content: `已选择 ${directions.length} 个方向，确认进入B阶段进行方向深化？`,
      onOk: () => {
        message.success('已进入B阶段，可以开始方向扩展');
        // 跳转到方向管理页面
        window.location.href = '/directions';
      },
    });
  };

  const clusterColumns = [
    {
      title: '簇ID',
      dataIndex: 'cluster_id',
      key: 'cluster_id',
      width: 80,
      render: (id) => <Tag color="blue">#{id}</Tag>,
    },
    {
      title: '簇大小',
      dataIndex: 'cluster_size',
      key: 'cluster_size',
      width: 100,
      sorter: (a, b) => a.cluster_size - b.cluster_size,
    },
    {
      title: '簇标签',
      dataIndex: 'cluster_label',
      key: 'cluster_label',
      width: 150,
      render: (label) => label || '-',
    },
    {
      title: '种子词',
      dataIndex: 'seed_words',
      key: 'seed_words',
      width: 200,
      render: (seeds) => (
        <Space size={[0, 4]} wrap>
          {seeds?.slice(0, 2).map((seed, idx) => (
            <Tag key={idx} color="green">
              {seed}
            </Tag>
          ))}
          {seeds?.length > 2 && <Tag>+{seeds.length - 2}</Tag>}
        </Space>
      ),
    },
    {
      title: '代表性关键词',
      dataIndex: 'top_keywords',
      key: 'top_keywords',
      ellipsis: true,
      render: (keywords) => keywords?.slice(0, 3).join(', '),
    },
    {
      title: '总搜索量',
      dataIndex: 'total_volume',
      key: 'total_volume',
      width: 120,
      sorter: (a, b) => (a.total_volume || 0) - (b.total_volume || 0),
      render: (volume) => (
        <span style={{ color: '#1890ff', fontWeight: 500 }}>
          {volume ? `${(volume / 10000).toFixed(1)}万` : '-'}
        </span>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_, record) => {
        const isSelected = directions.some(
          (d) => d.from_cluster_id === record.cluster_id
        );
        return (
          <Button
            type={isSelected ? 'default' : 'primary'}
            size="small"
            icon={isSelected ? <CheckCircleOutlined /> : <PlusOutlined />}
            onClick={() => handleSelectCluster(record)}
            disabled={isSelected}
          >
            {isSelected ? '已选择' : '选为方向'}
          </Button>
        );
      },
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
      title: '来源簇',
      dataIndex: 'from_cluster_id',
      key: 'from_cluster_id',
      width: 100,
      render: (id) => <Tag color="blue">#{id}</Tag>,
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
      title: '商业价值',
      dataIndex: 'business_value',
      key: 'business_value',
      width: 100,
      render: (value) => {
        const color =
          value === 'high' ? 'green' : value === 'medium' ? 'blue' : 'default';
        const text = value === 'high' ? '高' : value === 'medium' ? '中' : '低';
        return <Tag color={color}>{text}</Tag>;
      },
    },
    {
      title: 'Trends评分',
      dataIndex: 'trends_score',
      key: 'trends_score',
      width: 120,
      sorter: (a, b) => a.trends_score - b.trends_score,
      render: (score) => (
        <span style={{ color: score >= 70 ? '#52c41a' : '#faad14', fontWeight: 500 }}>
          {score}
        </span>
      ),
    },
    {
      title: '备注',
      dataIndex: 'notes',
      key: 'notes',
      ellipsis: true,
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_, record) => (
        <Popconfirm
          title="确认删除"
          description="删除后需要重新选择方向"
          onConfirm={() => handleDeleteDirection(record.direction_id)}
          okText="确认"
          cancelText="取消"
        >
          <Button type="link" size="small" danger icon={<DeleteOutlined />}>
            删除
          </Button>
        </Popconfirm>
      ),
    },
  ];

  return (
    <div className="direction-selection-container">
      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="已标注簇数"
              value={annotatedClusters.length}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="已选方向数"
              value={directions.length}
              prefix={<StarOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="高优先级"
              value={directions.filter((d) => d.priority === 'high').length}
              prefix={<TrophyOutlined />}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="平均Trends评分"
              value={
                directions.length > 0
                  ? Math.round(
                      directions.reduce((sum, d) => sum + d.trends_score, 0) /
                        directions.length
                    )
                  : 0
              }
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 已选方向 */}
      <Card
        title={
          <Space>
            <StarOutlined />
            <span>已选方向 ({directions.length})</span>
          </Space>
        }
        extra={
          <Space>
            <Button onClick={handleExport}>导出方向</Button>
            <Button
              type="primary"
              onClick={handleEnterStageB}
              disabled={directions.length === 0}
            >
              进入B阶段 ({directions.length})
            </Button>
          </Space>
        }
        style={{ marginBottom: 24 }}
      >
        {directions.length === 0 ? (
          <Alert
            message="还没有选择方向"
            description="请从下方的簇列表中选择有价值的方向"
            type="info"
            showIcon
          />
        ) : (
          <Table
            columns={directionColumns}
            dataSource={directions}
            rowKey="direction_id"
            pagination={false}
            scroll={{ x: 1000 }}
          />
        )}
      </Card>

      {/* 簇列表 */}
      <Card
        title={
          <Space>
            <FilterOutlined />
            <span>A5阶段：方向筛选</span>
          </Space>
        }
      >
        <Alert
          message="筛选提示"
          description={
            <ul style={{ marginBottom: 0, paddingLeft: 20 }}>
              <li>从已标注的簇中选择5-10个有商业价值的方向</li>
              <li>建议结合Google Trends验证方向的市场热度</li>
              <li>优先选择搜索量大、竞争度适中的方向</li>
              <li>选择完成后，可以进入B阶段进行方向深化</li>
            </ul>
          }
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />

        <Table
          columns={clusterColumns}
          dataSource={annotatedClusters}
          rowKey="cluster_id"
          loading={isLoading}
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 个已标注簇`,
          }}
          scroll={{ x: 1200 }}
        />
      </Card>

      {/* 添加方向对话框 */}
      <Modal
        title="添加为方向"
        open={isModalVisible}
        onOk={() => form.submit()}
        onCancel={() => {
          setIsModalVisible(false);
          form.resetFields();
          setSelectedCluster(null);
        }}
        width={700}
      >
        {selectedCluster && (
          <div style={{ marginBottom: 16 }}>
            <Alert
              message={`簇 #${selectedCluster.cluster_id}: ${selectedCluster.cluster_label || '未标注'}`}
              description={
                <div>
                  <p>
                    <strong>种子词：</strong>
                    {selectedCluster.seed_words?.join(', ')}
                  </p>
                  <p style={{ marginBottom: 0 }}>
                    <strong>代表性关键词：</strong>
                    {selectedCluster.top_keywords?.slice(0, 5).join(', ')}
                  </p>
                </div>
              }
              type="info"
            />
          </div>
        )}

        <Form form={form} layout="vertical" onFinish={handleAddDirection}>
          <Form.Item
            name="direction_keyword"
            label="方向关键词"
            rules={[{ required: true, message: '请输入方向关键词' }]}
          >
            <Input placeholder="例如: pdf tools, image converter" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="priority"
                label="优先级"
                rules={[{ required: true, message: '请选择优先级' }]}
              >
                <Select>
                  <Option value="high">高</Option>
                  <Option value="medium">中</Option>
                  <Option value="low">低</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="business_value"
                label="商业价值"
                rules={[{ required: true, message: '请选择商业价值' }]}
              >
                <Select>
                  <Option value="high">高</Option>
                  <Option value="medium">中</Option>
                  <Option value="low">低</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="trends_score"
            label="Trends评分 (0-100)"
            rules={[{ required: true, message: '请输入Trends评分' }]}
          >
            <InputNumber min={0} max={100} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item name="notes" label="备注">
            <TextArea rows={3} placeholder="记录选择这个方向的原因和考虑因素" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default DirectionSelection;

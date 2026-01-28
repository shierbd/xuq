/**
 * 词根聚类模块 - A4阶段：AI簇标注页面
 */
import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Card,
  Button,
  Table,
  Tag,
  Space,
  Statistic,
  Row,
  Col,
  Alert,
  Progress,
  message,
  Modal,
  Input,
  Checkbox,
} from 'antd';
import {
  RobotOutlined,
  ThunderboltOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  EyeOutlined,
} from '@ant-design/icons';
import { getClustersOverview } from '../../api/keywords';
import './ClusterAnnotation.css';

const { TextArea } = Input;

const ClusterAnnotation = () => {
  const queryClient = useQueryClient();
  const [batchSize, setBatchSize] = useState(10);
  const [useCustomPrompt, setUseCustomPrompt] = useState(false);
  const [customPrompt, setCustomPrompt] = useState('');
  const [annotating, setAnnotating] = useState(false);
  const [selectedClusters, setSelectedClusters] = useState([]);

  // 默认提示词
  const defaultPrompt = `请分析以下关键词簇，完成以下任务：

1. 为这个簇生成一个简洁的标签（3-5个词）
2. 解释这个簇的核心主题和语义含义
3. 分析这个簇代表的用户需求或意图

簇信息：
- 簇ID：{cluster_id}
- 簇大小：{cluster_size}
- 种子词：{seed_words}
- 代表性关键词：{top_keywords}

请以JSON格式返回结果：
{
    "cluster_label": "簇标签",
    "cluster_explanation": "簇解释",
    "user_intent": "用户意图",
    "business_value": "商业价值评估（high/medium/low）"
}`;

  // 获取簇概览
  const { data: clustersData, isLoading } = useQuery({
    queryKey: ['clusters-overview', { stage: 'A', exclude_noise: true }],
    queryFn: () => getClustersOverview({ stage: 'A', exclude_noise: true }),
  });

  const clusters = clustersData?.data || [];
  const annotatedCount = clusters.filter((c) => c.cluster_label).length;
  const pendingCount = clusters.filter((c) => !c.cluster_label).length;

  // 标注Mutation（模拟）
  const annotateMutation = useMutation({
    mutationFn: async (clusterIds) => {
      // 模拟API调用
      await new Promise((resolve) => setTimeout(resolve, 2000));
      return {
        success: clusterIds.length,
        message: `成功标注 ${clusterIds.length} 个簇`,
      };
    },
    onSuccess: (data) => {
      message.success(data.message);
      setAnnotating(false);
      setSelectedClusters([]);
      queryClient.invalidateQueries(['clusters-overview']);
    },
    onError: (error) => {
      message.error(`标注失败: ${error.message}`);
      setAnnotating(false);
    },
  });

  // 开始标注
  const handleStartAnnotation = () => {
    if (selectedClusters.length === 0) {
      message.warning('请先选择要标注的簇');
      return;
    }

    Modal.confirm({
      title: '确认开始AI标注',
      content: `即将标注 ${selectedClusters.length} 个簇，是否继续？`,
      onOk: () => {
        setAnnotating(true);
        annotateMutation.mutate(selectedClusters);
      },
    });
  };

  // 标注全部
  const handleAnnotateAll = () => {
    const pendingClusters = clusters
      .filter((c) => !c.cluster_label)
      .map((c) => c.cluster_id);

    if (pendingClusters.length === 0) {
      message.warning('没有待标注的簇');
      return;
    }

    Modal.confirm({
      title: '确认标注全部簇',
      content: `即将标注全部 ${pendingClusters.length} 个待标注簇，这可能需要较长时间，是否继续？`,
      onOk: () => {
        setAnnotating(true);
        annotateMutation.mutate(pendingClusters);
      },
    });
  };

  const columns = [
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
      title: '标注状态',
      dataIndex: 'cluster_label',
      key: 'status',
      width: 120,
      render: (label) =>
        label ? (
          <Tag color="success" icon={<CheckCircleOutlined />}>
            已标注
          </Tag>
        ) : (
          <Tag color="warning" icon={<ClockCircleOutlined />}>
            待标注
          </Tag>
        ),
    },
    {
      title: '簇标签',
      dataIndex: 'cluster_label',
      key: 'cluster_label',
      width: 150,
      render: (label) => label || '-',
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
          onClick={() => message.info(`查看簇 #${record.cluster_id} 详情（功能开发中）`)}
        >
          查看
        </Button>
      ),
    },
  ];

  const rowSelection = {
    selectedRowKeys: selectedClusters,
    onChange: (selectedRowKeys) => {
      setSelectedClusters(selectedRowKeys);
    },
    getCheckboxProps: (record) => ({
      disabled: !!record.cluster_label, // 已标注的不能选择
    }),
  };

  const progress = clusters.length > 0 ? (annotatedCount / clusters.length) * 100 : 0;

  return (
    <div className="cluster-annotation-container">
      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="簇总数"
              value={clusters.length}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="待标注"
              value={pendingCount}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="已标注"
              value={annotatedCount}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="已选择"
              value={selectedClusters.length}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 进度条 */}
      <Card style={{ marginBottom: 24 }}>
        <div style={{ marginBottom: 8 }}>
          <strong>标注进度</strong>
        </div>
        <Progress
          percent={Math.round(progress)}
          status={pendingCount > 0 ? 'active' : 'success'}
          strokeColor={{
            '0%': '#108ee9',
            '100%': '#87d068',
          }}
        />
      </Card>

      {/* 标注配置 */}
      <Card
        title={
          <Space>
            <RobotOutlined />
            <span>A4阶段：AI簇标注</span>
          </Space>
        }
        extra={
          <Space>
            <Button
              type="primary"
              icon={<ThunderboltOutlined />}
              onClick={handleStartAnnotation}
              loading={annotateMutation.isPending}
              disabled={selectedClusters.length === 0 || annotating}
            >
              标注选中 ({selectedClusters.length})
            </Button>
            <Button
              icon={<RobotOutlined />}
              onClick={handleAnnotateAll}
              loading={annotateMutation.isPending}
              disabled={pendingCount === 0 || annotating}
            >
              标注全部 ({pendingCount})
            </Button>
          </Space>
        }
      >
        {/* 提示词配置 */}
        <div style={{ marginBottom: 16 }}>
          <Checkbox
            checked={useCustomPrompt}
            onChange={(e) => setUseCustomPrompt(e.target.checked)}
          >
            使用自定义提示词
          </Checkbox>
        </div>

        {useCustomPrompt && (
          <div style={{ marginBottom: 16 }}>
            <Alert
              message="提示词说明"
              description="使用 {cluster_id}, {cluster_size}, {seed_words}, {top_keywords} 作为占位符"
              type="info"
              showIcon
              style={{ marginBottom: 8 }}
            />
            <TextArea
              value={customPrompt || defaultPrompt}
              onChange={(e) => setCustomPrompt(e.target.value)}
              rows={10}
              placeholder="输入自定义提示词..."
            />
          </div>
        )}

        {/* 簇列表 */}
        <Table
          columns={columns}
          dataSource={clusters}
          rowKey="cluster_id"
          rowSelection={rowSelection}
          loading={isLoading}
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 个簇`,
          }}
          scroll={{ x: 1200 }}
        />

        {/* 提示信息 */}
        {pendingCount === 0 && (
          <Alert
            message="所有簇都已标注完成"
            description="您可以在簇概览中查看标注结果，或进行A5阶段的方向筛选"
            type="success"
            showIcon
            style={{ marginTop: 16 }}
          />
        )}

        {pendingCount > 0 && (
          <Alert
            message="标注提示"
            description={
              <ul style={{ marginBottom: 0, paddingLeft: 20 }}>
                <li>选择要标注的簇，点击"标注选中"进行批量标注</li>
                <li>或点击"标注全部"一次性标注所有待标注簇</li>
                <li>AI标注结果仅供参考，建议结合SERP验证</li>
                <li>标注完成后，可以进行A5阶段的人工筛选</li>
              </ul>
            }
            type="info"
            showIcon
            style={{ marginTop: 16 }}
          />
        )}
      </Card>
    </div>
  );
};

export default ClusterAnnotation;

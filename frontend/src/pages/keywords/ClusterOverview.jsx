/**
 * 词根聚类模块 - 簇概览页面
 */
import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Card,
  Table,
  Tag,
  Space,
  Statistic,
  Row,
  Col,
  Input,
  Switch,
  Spin,
  Alert,
  Button,
  message,
} from 'antd';
import {
  SearchOutlined,
  ClusterOutlined,
  FileTextOutlined,
  EyeOutlined,
} from '@ant-design/icons';
import { getClustersOverview, getKeywordCount } from '../../api/keywords';
import './ClusterOverview.css';

const { Search } = Input;

const ClusterOverview = () => {
  const [excludeNoise, setExcludeNoise] = useState(true);
  const [minSize, setMinSize] = useState(null);
  const [stage, setStage] = useState('A');

  // 获取关键词总数
  const { data: countData } = useQuery({
    queryKey: ['keyword-count'],
    queryFn: getKeywordCount,
  });

  // 获取簇概览
  const { data: clustersData, isLoading, error } = useQuery({
    queryKey: ['clusters-overview', { stage, excludeNoise, minSize }],
    queryFn: () => getClustersOverview({ stage, exclude_noise: excludeNoise, min_size: minSize }),
  });

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
      render: (size) => <strong>{size.toLocaleString()}</strong>,
    },
    {
      title: '种子词',
      dataIndex: 'seed_words',
      key: 'seed_words',
      width: 200,
      render: (seeds) => (
        <Space size={[0, 4]} wrap>
          {seeds?.slice(0, 3).map((seed, idx) => (
            <Tag key={idx} color="green">{seed}</Tag>
          ))}
          {seeds?.length > 3 && <Tag>+{seeds.length - 3}</Tag>}
        </Space>
      ),
    },
    {
      title: '代表性关键词',
      dataIndex: 'top_keywords',
      key: 'top_keywords',
      ellipsis: true,
      render: (keywords) => (
        <div style={{ fontSize: 12, color: '#666' }}>
          {keywords?.slice(0, 3).join(', ')}
          {keywords?.length > 3 && '...'}
        </div>
      ),
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
      width: 100,
      render: (_, record) => (
        <Button
          type="link"
          icon={<EyeOutlined />}
          onClick={() => handleViewDetail(record.cluster_id)}
        >
          查看详情
        </Button>
      ),
    },
  ];

  const handleViewDetail = (clusterId) => {
    message.info(`查看簇 #${clusterId} 的详情（功能开发中）`);
  };

  const handleSearch = (value) => {
    if (value) {
      setMinSize(parseInt(value) || null);
    } else {
      setMinSize(null);
    }
  };

  if (error) {
    return (
      <div style={{ padding: 24 }}>
        <Alert
          message="加载失败"
          description={error.message}
          type="error"
          showIcon
        />
      </div>
    );
  }

  return (
    <div className="cluster-overview-container">
      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="关键词总数"
              value={countData?.data?.total || 0}
              prefix={<FileTextOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="簇数量"
              value={clustersData?.total || 0}
              prefix={<ClusterOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="平均簇大小"
              value={
                clustersData?.data?.length > 0
                  ? Math.round(
                      clustersData.data.reduce((sum, c) => sum + c.cluster_size, 0) /
                        clustersData.data.length
                    )
                  : 0
              }
              suffix="个"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="总搜索量"
              value={
                clustersData?.data?.length > 0
                  ? (
                      clustersData.data.reduce((sum, c) => sum + (c.total_volume || 0), 0) /
                      10000
                    ).toFixed(0)
                  : 0
              }
              suffix="万/月"
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 筛选和表格 */}
      <Card
        title={
          <Space>
            <ClusterOutlined />
            <span>簇概览</span>
          </Space>
        }
        extra={
          <Space>
            <span>排除噪音点:</span>
            <Switch checked={excludeNoise} onChange={setExcludeNoise} />
            <Search
              placeholder="最小簇大小"
              allowClear
              style={{ width: 150 }}
              onSearch={handleSearch}
            />
          </Space>
        }
      >
        <Spin spinning={isLoading}>
          <Table
            columns={columns}
            dataSource={clustersData?.data || []}
            rowKey="cluster_id"
            pagination={{
              pageSize: 20,
              showSizeChanger: true,
              showTotal: (total) => `共 ${total} 个簇`,
            }}
            size="middle"
          />
        </Spin>
      </Card>
    </div>
  );
};

export default ClusterOverview;

/**
 * 词根聚类模块 - 簇详情页面
 */
import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Card,
  Table,
  Tag,
  Space,
  Statistic,
  Row,
  Col,
  Spin,
  Alert,
  Button,
  Descriptions,
  Divider,
} from 'antd';
import {
  ArrowLeftOutlined,
  ClusterOutlined,
  FileTextOutlined,
  SearchOutlined,
} from '@ant-design/icons';
import { getClusterDetail } from '../../api/keywords';
import './ClusterDetail.css';

const ClusterDetail = () => {
  const { clusterId } = useParams();
  const navigate = useNavigate();
  const [stage, setStage] = useState('A');

  // 获取簇详情
  const { data: clusterData, isLoading, error } = useQuery({
    queryKey: ['cluster-detail', clusterId, stage],
    queryFn: () => getClusterDetail(clusterId, { stage }),
  });

  const columns = [
    {
      title: '关键词',
      dataIndex: 'keyword',
      key: 'keyword',
      width: 200,
      render: (text, record) => (
        <Space>
          <strong>{text}</strong>
          {record.is_seed && <Tag color="gold">种子词</Tag>}
        </Space>
      ),
    },
    {
      title: '搜索量',
      dataIndex: 'search_volume',
      key: 'search_volume',
      width: 120,
      sorter: (a, b) => (a.search_volume || 0) - (b.search_volume || 0),
      render: (volume) => (
        <span style={{ color: '#1890ff', fontWeight: 500 }}>
          {volume ? volume.toLocaleString() : '-'}
        </span>
      ),
    },
    {
      title: '竞争度',
      dataIndex: 'competition',
      key: 'competition',
      width: 100,
      render: (comp) => {
        if (!comp) return '-';
        const color = comp === 'HIGH' ? 'red' : comp === 'MEDIUM' ? 'orange' : 'green';
        return <Tag color={color}>{comp}</Tag>;
      },
    },
    {
      title: 'CPC',
      dataIndex: 'cpc',
      key: 'cpc',
      width: 100,
      sorter: (a, b) => (a.cpc || 0) - (b.cpc || 0),
      render: (cpc) => (cpc ? `$${cpc.toFixed(2)}` : '-'),
    },
    {
      title: '词长',
      dataIndex: 'word_count',
      key: 'word_count',
      width: 80,
      sorter: (a, b) => (a.word_count || 0) - (b.word_count || 0),
      render: (count) => count || '-',
    },
    {
      title: '相似度',
      dataIndex: 'similarity_to_centroid',
      key: 'similarity_to_centroid',
      width: 100,
      sorter: (a, b) => (a.similarity_to_centroid || 0) - (b.similarity_to_centroid || 0),
      render: (sim) => (sim ? `${(sim * 100).toFixed(1)}%` : '-'),
    },
  ];

  if (error) {
    return (
      <div style={{ padding: 24 }}>
        <Alert
          message="加载失败"
          description={error.message}
          type="error"
          showIcon
        />
        <Button
          type="primary"
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate('/clusters')}
          style={{ marginTop: 16 }}
        >
          返回簇概览
        </Button>
      </div>
    );
  }

  const cluster = clusterData?.data;
  const keywords = cluster?.keywords || [];
  const seedWords = keywords.filter((k) => k.is_seed);
  const totalVolume = keywords.reduce((sum, k) => sum + (k.search_volume || 0), 0);
  const avgCpc = keywords.filter((k) => k.cpc).length > 0
    ? keywords.reduce((sum, k) => sum + (k.cpc || 0), 0) / keywords.filter((k) => k.cpc).length
    : 0;

  return (
    <div className="cluster-detail-container">
      {/* 返回按钮 */}
      <Button
        icon={<ArrowLeftOutlined />}
        onClick={() => navigate('/clusters')}
        style={{ marginBottom: 16 }}
      >
        返回簇概览
      </Button>

      <Spin spinning={isLoading}>
        {/* 簇基本信息 */}
        <Card
          title={
            <Space>
              <ClusterOutlined />
              <span>簇 #{clusterId} 详情</span>
            </Space>
          }
          style={{ marginBottom: 24 }}
        >
          <Row gutter={16}>
            <Col span={6}>
              <Card>
                <Statistic
                  title="簇大小"
                  value={cluster?.cluster_size || 0}
                  prefix={<FileTextOutlined />}
                  valueStyle={{ color: '#3f8600' }}
                  suffix="个关键词"
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="种子词数量"
                  value={seedWords.length}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="总搜索量"
                  value={totalVolume > 0 ? (totalVolume / 10000).toFixed(1) : 0}
                  suffix="万/月"
                  valueStyle={{ color: '#cf1322' }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="平均 CPC"
                  value={avgCpc > 0 ? avgCpc.toFixed(2) : 0}
                  prefix="$"
                  valueStyle={{ color: '#faad14' }}
                />
              </Card>
            </Col>
          </Row>

          <Divider />

          <Descriptions title="簇信息" column={2}>
            <Descriptions.Item label="簇ID">
              <Tag color="blue">#{clusterId}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="阶段">
              <Tag color="purple">{stage}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="种子词" span={2}>
              <Space size={[0, 4]} wrap>
                {seedWords.slice(0, 10).map((seed, idx) => (
                  <Tag key={idx} color="gold">
                    {seed.keyword}
                  </Tag>
                ))}
                {seedWords.length > 10 && <Tag>+{seedWords.length - 10}</Tag>}
              </Space>
            </Descriptions.Item>
            <Descriptions.Item label="代表性关键词" span={2}>
              <Space size={[0, 4]} wrap>
                {cluster?.top_keywords?.slice(0, 10).map((kw, idx) => (
                  <Tag key={idx} color="green">
                    {kw}
                  </Tag>
                ))}
                {cluster?.top_keywords?.length > 10 && (
                  <Tag>+{cluster.top_keywords.length - 10}</Tag>
                )}
              </Space>
            </Descriptions.Item>
          </Descriptions>
        </Card>

        {/* 关键词列表 */}
        <Card
          title={
            <Space>
              <SearchOutlined />
              <span>簇内关键词列表</span>
            </Space>
          }
        >
          <Table
            columns={columns}
            dataSource={keywords}
            rowKey="keyword_id"
            pagination={{
              pageSize: 20,
              showSizeChanger: true,
              showTotal: (total) => `共 ${total} 个关键词`,
            }}
            scroll={{ x: 1000 }}
            size="middle"
          />
        </Card>
      </Spin>
    </div>
  );
};

export default ClusterDetail;

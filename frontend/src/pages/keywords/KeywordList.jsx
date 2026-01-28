/**
 * 词根聚类模块 - 关键词列表页面
 */
import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Card,
  Table,
  Tag,
  Space,
  Input,
  Select,
  Button,
  Statistic,
  Row,
  Col,
  Spin,
  Alert,
} from 'antd';
import {
  SearchOutlined,
  FileTextOutlined,
  FilterOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { getKeywords, getKeywordCount, getSeedWords } from '../../api/keywords';
import './KeywordList.css';

const { Search } = Input;
const { Option } = Select;

const KeywordList = () => {
  const [searchText, setSearchText] = useState('');
  const [stage, setStage] = useState('A');
  const [clusterId, setClusterId] = useState(null);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);

  // 获取关键词总数
  const { data: countData } = useQuery({
    queryKey: ['keyword-count'],
    queryFn: getKeywordCount,
  });

  // 获取种子词列表
  const { data: seedWordsData } = useQuery({
    queryKey: ['seed-words'],
    queryFn: getSeedWords,
  });

  // 获取关键词列表
  const { data: keywordsData, isLoading, error, refetch } = useQuery({
    queryKey: ['keywords', { stage, clusterId, searchText, page, pageSize }],
    queryFn: () =>
      getKeywords({
        stage,
        cluster_id: clusterId,
        search: searchText || undefined,
        page,
        page_size: pageSize,
      }),
  });

  const columns = [
    {
      title: '关键词',
      dataIndex: 'keyword',
      key: 'keyword',
      width: 200,
      fixed: 'left',
      render: (text, record) => (
        <Space>
          <strong>{text}</strong>
          {record.is_seed && <Tag color="gold">种子词</Tag>}
        </Space>
      ),
    },
    {
      title: '簇ID',
      dataIndex: 'cluster_id',
      key: 'cluster_id',
      width: 100,
      render: (id) => {
        if (id === -1) return <Tag color="default">噪音点</Tag>;
        return <Tag color="blue">#{id}</Tag>;
      },
    },
    {
      title: '搜索量',
      dataIndex: 'search_volume',
      key: 'search_volume',
      width: 120,
      sorter: (a, b) => (a.search_volume || 0) - (b.search_volume || 0),
      render: (volume) => (
        <span style={{ color: '#1890ff' }}>
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
      render: (cpc) => (cpc ? `$${cpc.toFixed(2)}` : '-'),
    },
    {
      title: '词长',
      dataIndex: 'word_count',
      key: 'word_count',
      width: 80,
      render: (count) => count || '-',
    },
    {
      title: '阶段',
      dataIndex: 'stage',
      key: 'stage',
      width: 80,
      render: (stage) => <Tag color="purple">{stage}</Tag>,
    },
  ];

  const handleSearch = (value) => {
    setSearchText(value);
    setPage(1);
  };

  const handleReset = () => {
    setSearchText('');
    setStage('A');
    setClusterId(null);
    setPage(1);
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
    <div className="keyword-list-container">
      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card>
            <Statistic
              title="关键词总数"
              value={countData?.data?.total || 0}
              prefix={<FileTextOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="种子词数量"
              value={seedWordsData?.data?.length || 0}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="当前显示"
              value={keywordsData?.data?.length || 0}
              suffix={`/ ${keywordsData?.total || 0}`}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 筛选和表格 */}
      <Card
        title={
          <Space>
            <FileTextOutlined />
            <span>关键词列表</span>
          </Space>
        }
        extra={
          <Space>
            <Button icon={<ReloadOutlined />} onClick={() => refetch()}>
              刷新
            </Button>
          </Space>
        }
      >
        {/* 筛选区域 */}
        <Space style={{ marginBottom: 16 }} wrap>
          <Search
            placeholder="搜索关键词"
            allowClear
            style={{ width: 300 }}
            onSearch={handleSearch}
            enterButton={<SearchOutlined />}
          />
          <Select
            placeholder="选择阶段"
            style={{ width: 120 }}
            value={stage}
            onChange={(value) => {
              setStage(value);
              setPage(1);
            }}
          >
            <Option value="A">阶段 A</Option>
            <Option value="B">阶段 B</Option>
          </Select>
          <Select
            placeholder="选择簇"
            style={{ width: 150 }}
            value={clusterId}
            onChange={(value) => {
              setClusterId(value);
              setPage(1);
            }}
            allowClear
          >
            <Option value={-1}>噪音点</Option>
            {Array.from({ length: 100 }, (_, i) => (
              <Option key={i} value={i}>
                簇 #{i}
              </Option>
            ))}
          </Select>
          <Button icon={<FilterOutlined />} onClick={handleReset}>
            重置筛选
          </Button>
        </Space>

        {/* 表格 */}
        <Spin spinning={isLoading}>
          <Table
            columns={columns}
            dataSource={keywordsData?.data || []}
            rowKey="keyword_id"
            pagination={{
              current: page,
              pageSize: pageSize,
              total: keywordsData?.total || 0,
              showSizeChanger: true,
              showTotal: (total) => `共 ${total} 个关键词`,
              onChange: (newPage, newPageSize) => {
                setPage(newPage);
                setPageSize(newPageSize);
              },
            }}
            scroll={{ x: 1000 }}
            size="middle"
          />
        </Spin>
      </Card>
    </div>
  );
};

export default KeywordList;

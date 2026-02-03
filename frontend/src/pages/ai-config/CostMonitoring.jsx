/**
 * AI成本监控页面
 * 提供AI使用成本的统计、分析和可视化
 */
import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, DatePicker, Space, Table, Tag, Tabs, Alert, Button, Select, message } from 'antd';
import { DollarOutlined, ApiOutlined, CheckCircleOutlined, ClockCircleOutlined, BarChartOutlined, ReloadOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import {
  getCostStatistics,
  getCostByScenario,
  getCostByModel,
  getCostByProvider,
  getCostTrend,
  getRecentCostLogs
} from '../../api/ai_config';

const { RangePicker } = DatePicker;
const { Option } = Select;

const CostMonitoring = () => {
  const [loading, setLoading] = useState(false);
  const [dateRange, setDateRange] = useState([
    dayjs().subtract(7, 'days'),
    dayjs()
  ]);
  const [statistics, setStatistics] = useState(null);
  const [costByScenario, setCostByScenario] = useState([]);
  const [costByModel, setCostByModel] = useState([]);
  const [costByProvider, setCostByProvider] = useState([]);
  const [costTrend, setCostTrend] = useState([]);
  const [recentLogs, setRecentLogs] = useState([]);
  const [trendGranularity, setTrendGranularity] = useState('day');

  // 加载所有数据
  const loadAllData = async () => {
    setLoading(true);
    try {
      const params = {
        start_date: dateRange[0].format('YYYY-MM-DD'),
        end_date: dateRange[1].format('YYYY-MM-DD')
      };

      // 并行加载所有数据
      const [statsRes, scenarioRes, modelRes, providerRes, trendRes, logsRes] = await Promise.all([
        getCostStatistics(params),
        getCostByScenario(params),
        getCostByModel(params),
        getCostByProvider(params),
        getCostTrend({ ...params, granularity: trendGranularity }),
        getRecentCostLogs({ limit: 20 })
      ]);

      if (statsRes.success) {
        setStatistics(statsRes.data);
      }
      if (scenarioRes.success) {
        setCostByScenario(scenarioRes.data.scenarios || []);
      }
      if (modelRes.success) {
        setCostByModel(modelRes.data.models || []);
      }
      if (providerRes.success) {
        setCostByProvider(providerRes.data.providers || []);
      }
      if (trendRes.success) {
        setCostTrend(trendRes.data.trend || []);
      }
      if (logsRes.success) {
        setRecentLogs(logsRes.data.logs || []);
      }
    } catch (error) {
      console.error('加载数据失败:', error);
      message.error('加载数据失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  // 初始加载
  useEffect(() => {
    loadAllData();
  }, []);

  // 日期范围变化时重新加载
  const handleDateRangeChange = (dates) => {
    if (dates && dates.length === 2) {
      setDateRange(dates);
    }
  };

  // 刷新数据
  const handleRefresh = () => {
    loadAllData();
  };

  // 场景成本表格列
  const scenarioColumns = [
    {
      title: '场景名称',
      dataIndex: 'scenario_name',
      key: 'scenario_name',
      width: 200,
    },
    {
      title: '调用次数',
      dataIndex: 'call_count',
      key: 'call_count',
      width: 120,
      sorter: (a, b) => a.call_count - b.call_count,
    },
    {
      title: '总成本',
      dataIndex: 'total_cost',
      key: 'total_cost',
      width: 120,
      sorter: (a, b) => a.total_cost - b.total_cost,
      render: (cost) => `$${cost.toFixed(4)}`,
    },
    {
      title: '平均耗时',
      dataIndex: 'avg_duration',
      key: 'avg_duration',
      width: 120,
      sorter: (a, b) => a.avg_duration - b.avg_duration,
      render: (duration) => `${duration.toFixed(2)}s`,
    },
  ];

  // 模型成本表格列
  const modelColumns = [
    {
      title: '模型名称',
      dataIndex: 'model_name',
      key: 'model_name',
      width: 200,
    },
    {
      title: '调用次数',
      dataIndex: 'call_count',
      key: 'call_count',
      width: 100,
      sorter: (a, b) => a.call_count - b.call_count,
    },
    {
      title: '输入Token',
      dataIndex: 'total_input_tokens',
      key: 'total_input_tokens',
      width: 120,
      sorter: (a, b) => a.total_input_tokens - b.total_input_tokens,
      render: (tokens) => tokens.toLocaleString(),
    },
    {
      title: '输出Token',
      dataIndex: 'total_output_tokens',
      key: 'total_output_tokens',
      width: 120,
      sorter: (a, b) => a.total_output_tokens - b.total_output_tokens,
      render: (tokens) => tokens.toLocaleString(),
    },
    {
      title: '总成本',
      dataIndex: 'total_cost',
      key: 'total_cost',
      width: 120,
      sorter: (a, b) => a.total_cost - b.total_cost,
      render: (cost) => `$${cost.toFixed(4)}`,
    },
    {
      title: '平均耗时',
      dataIndex: 'avg_duration',
      key: 'avg_duration',
      width: 120,
      sorter: (a, b) => a.avg_duration - b.avg_duration,
      render: (duration) => `${duration.toFixed(2)}s`,
    },
  ];

  // 提供商成本表格列
  const providerColumns = [
    {
      title: '提供商',
      dataIndex: 'provider_name',
      key: 'provider_name',
      width: 150,
    },
    {
      title: '调用次数',
      dataIndex: 'call_count',
      key: 'call_count',
      width: 120,
      sorter: (a, b) => a.call_count - b.call_count,
    },
    {
      title: '总成本',
      dataIndex: 'total_cost',
      key: 'total_cost',
      width: 120,
      sorter: (a, b) => a.total_cost - b.total_cost,
      render: (cost) => `$${cost.toFixed(4)}`,
    },
    {
      title: '平均耗时',
      dataIndex: 'avg_duration',
      key: 'avg_duration',
      width: 120,
      sorter: (a, b) => a.avg_duration - b.avg_duration,
      render: (duration) => `${duration.toFixed(2)}s`,
    },
  ];

  // 日志表格列
  const logColumns = [
    {
      title: '时间',
      dataIndex: 'created_time',
      key: 'created_time',
      width: 180,
      render: (time) => dayjs(time).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: '场景',
      dataIndex: 'scenario_name',
      key: 'scenario_name',
      width: 150,
    },
    {
      title: '模型',
      dataIndex: 'model_name',
      key: 'model_name',
      width: 150,
    },
    {
      title: '输入Token',
      dataIndex: 'input_tokens',
      key: 'input_tokens',
      width: 100,
      render: (tokens) => tokens.toLocaleString(),
    },
    {
      title: '输出Token',
      dataIndex: 'output_tokens',
      key: 'output_tokens',
      width: 100,
      render: (tokens) => tokens.toLocaleString(),
    },
    {
      title: '成本',
      dataIndex: 'cost',
      key: 'cost',
      width: 100,
      render: (cost) => `$${cost.toFixed(4)}`,
    },
    {
      title: '耗时',
      dataIndex: 'duration',
      key: 'duration',
      width: 100,
      render: (duration) => `${duration.toFixed(2)}s`,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status) => (
        <Tag color={status === 'success' ? 'success' : 'error'}>
          {status === 'success' ? '成功' : '失败'}
        </Tag>
      ),
    },
  ];

  // 趋势表格列
  const trendColumns = [
    {
      title: '时间',
      dataIndex: 'time_period',
      key: 'time_period',
      width: 180,
    },
    {
      title: '调用次数',
      dataIndex: 'call_count',
      key: 'call_count',
      width: 120,
    },
    {
      title: '总成本',
      dataIndex: 'total_cost',
      key: 'total_cost',
      width: 120,
      render: (cost) => `$${cost.toFixed(4)}`,
    },
    {
      title: '平均耗时',
      dataIndex: 'avg_duration',
      key: 'avg_duration',
      width: 120,
      render: (duration) => `${duration.toFixed(2)}s`,
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Card
        title={
          <div>
            <h2 style={{ margin: 0, fontSize: '20px' }}>
              <BarChartOutlined /> AI成本监控
            </h2>
            <p style={{ margin: '8px 0 0 0', color: '#999', fontSize: '14px' }}>
              实时监控AI使用成本，优化资源配置
            </p>
          </div>
        }
        extra={
          <Space>
            <RangePicker
              value={dateRange}
              onChange={handleDateRangeChange}
              format="YYYY-MM-DD"
              style={{ width: 260 }}
            />
            <Button
              icon={<ReloadOutlined />}
              onClick={handleRefresh}
              loading={loading}
            >
              刷新
            </Button>
          </Space>
        }
        bordered={false}
      >
        {/* 统计卡片 */}
        {statistics && (
          <>
            <Row gutter={16} style={{ marginBottom: 24 }}>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="总成本"
                    value={statistics.total_cost}
                    precision={4}
                    prefix={<DollarOutlined />}
                    suffix="USD"
                    valueStyle={{ color: '#cf1322' }}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="总调用次数"
                    value={statistics.total_calls}
                    prefix={<ApiOutlined />}
                    valueStyle={{ color: '#1890ff' }}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="成功率"
                    value={statistics.success_rate * 100}
                    precision={2}
                    prefix={<CheckCircleOutlined />}
                    suffix="%"
                    valueStyle={{ color: '#3f8600' }}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="平均耗时"
                    value={statistics.avg_duration}
                    precision={2}
                    prefix={<ClockCircleOutlined />}
                    suffix="秒"
                    valueStyle={{ color: '#faad14' }}
                  />
                </Card>
              </Col>
            </Row>

            <Row gutter={16} style={{ marginBottom: 24 }}>
              <Col span={6}>
                <Card size="small">
                  <Statistic
                    title="成功调用"
                    value={statistics.success_calls}
                    valueStyle={{ fontSize: '18px', color: '#52c41a' }}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card size="small">
                  <Statistic
                    title="失败调用"
                    value={statistics.failed_calls}
                    valueStyle={{ fontSize: '18px', color: '#ff4d4f' }}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card size="small">
                  <Statistic
                    title="总输入Token"
                    value={statistics.total_input_tokens}
                    valueStyle={{ fontSize: '18px' }}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card size="small">
                  <Statistic
                    title="总输出Token"
                    value={statistics.total_output_tokens}
                    valueStyle={{ fontSize: '18px' }}
                  />
                </Card>
              </Col>
            </Row>
          </>
        )}

        {/* 成本趋势 */}
        <Card
          title="成本趋势"
          size="small"
          style={{ marginBottom: 16 }}
          extra={
            <Select
              value={trendGranularity}
              onChange={(value) => {
                setTrendGranularity(value);
                loadAllData();
              }}
              style={{ width: 120 }}
            >
              <Option value="hour">按小时</Option>
              <Option value="day">按天</Option>
              <Option value="month">按月</Option>
            </Select>
          }
        >
          <Table
            dataSource={costTrend}
            columns={trendColumns}
            rowKey="time_period"
            pagination={{ pageSize: 10 }}
            loading={loading}
            size="small"
          />
        </Card>

        {/* 详细分析 */}
        <Tabs
          defaultActiveKey="scenario"
          items={[
            {
              key: 'scenario',
              label: '按场景统计',
              children: (
                <Table
                  dataSource={costByScenario}
                  columns={scenarioColumns}
                  rowKey="scenario_id"
                  pagination={{ pageSize: 10 }}
                  loading={loading}
                  size="small"
                />
              ),
            },
            {
              key: 'model',
              label: '按模型统计',
              children: (
                <Table
                  dataSource={costByModel}
                  columns={modelColumns}
                  rowKey="model_id"
                  pagination={{ pageSize: 10 }}
                  loading={loading}
                  size="small"
                />
              ),
            },
            {
              key: 'provider',
              label: '按提供商统计',
              children: (
                <Table
                  dataSource={costByProvider}
                  columns={providerColumns}
                  rowKey="provider_id"
                  pagination={{ pageSize: 10 }}
                  loading={loading}
                  size="small"
                />
              ),
            },
            {
              key: 'logs',
              label: '最近日志',
              children: (
                <>
                  <Alert
                    message="日志说明"
                    description="显示最近20条AI调用日志，包括成功和失败的调用记录"
                    type="info"
                    showIcon
                    style={{ marginBottom: 16 }}
                  />
                  <Table
                    dataSource={recentLogs}
                    columns={logColumns}
                    rowKey="log_id"
                    pagination={{ pageSize: 10 }}
                    loading={loading}
                    size="small"
                    scroll={{ x: 1200 }}
                  />
                </>
              ),
            },
          ]}
        />
      </Card>
    </div>
  );
};

export default CostMonitoring;

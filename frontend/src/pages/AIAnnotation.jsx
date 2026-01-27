/**
 * AI标注页面组件
 */
import React, { useState } from 'react';
import {
  Card,
  Button,
  InputNumber,
  Checkbox,
  Input,
  Space,
  Statistic,
  Row,
  Col,
  Alert,
  Progress,
  message,
  Modal,
} from 'antd';
import {
  RobotOutlined,
  ThunderboltOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getAnnotationStatus,
  annotateProducts,
  annotateProductsSync,
} from '../api/import_export';
import { getProducts } from '../api/products';
import './AIAnnotation.css';

const { TextArea } = Input;

const AIAnnotation = () => {
  const queryClient = useQueryClient();
  const [batchSize, setBatchSize] = useState(10);
  const [useCustomPrompt, setUseCustomPrompt] = useState(false);
  const [customPrompt, setCustomPrompt] = useState('');
  const [annotating, setAnnotating] = useState(false);

  // 默认提示词
  const defaultPrompt = `请分析以下商品信息，完成两个任务：

1. 生成3个中文标签，描述商品的类别、特点或用途
2. 判断这个商品解决了什么用户需求

商品信息：
- 名称：{product_name}
- 描述：{description}
- 价格：${price}
- 评分：{rating}星
- 评价数：{review_count}条

请以JSON格式返回结果：
{
    "tags": ["标签1", "标签2", "标签3"],
    "product_brief": "商品简介",
    "core_need": "核心需求",
    "virtual_product_fit": "high/medium/low",
    "fit_reason": "适配原因"
}`;

  // 获取标注状态
  const { data: statusData, refetch: refetchStatus } = useQuery({
    queryKey: ['annotation-status'],
    queryFn: getAnnotationStatus,
    refetchInterval: annotating ? 5000 : false, // 标注时每5秒刷新
  });

  // 获取待标注商品
  const { data: pendingProducts } = useQuery({
    queryKey: ['pending-products'],
    queryFn: () => getProducts({ ai_status: 'pending', page_size: 100 }),
  });

  // 标注Mutation（异步）
  const annotateMutation = useMutation({
    mutationFn: (productIds) =>
      annotateProducts(productIds, batchSize, useCustomPrompt ? customPrompt : null),
    onSuccess: (data) => {
      message.success(data.message);
      setAnnotating(true);
      // 5秒后停止轮询
      setTimeout(() => {
        setAnnotating(false);
        queryClient.invalidateQueries(['products']);
        queryClient.invalidateQueries(['statistics']);
        refetchStatus();
      }, 5000);
    },
    onError: (error) => {
      message.error(`标注失败: ${error.message}`);
      setAnnotating(false);
    },
  });

  // 标注Mutation（同步）
  const annotateSyncMutation = useMutation({
    mutationFn: (productIds) =>
      annotateProductsSync(productIds, batchSize, useCustomPrompt ? customPrompt : null),
    onSuccess: (data) => {
      message.success(data.message);
      queryClient.invalidateQueries(['products']);
      queryClient.invalidateQueries(['statistics']);
      refetchStatus();
    },
    onError: (error) => {
      message.error(`标注失败: ${error.message}`);
    },
  });

  // 开始标注
  const handleStartAnnotation = () => {
    const pendingCount = statusData?.pending || 0;

    if (pendingCount === 0) {
      message.warning('没有待标注的商品');
      return;
    }

    // 获取待标注商品ID
    const productIds = pendingProducts?.items?.map(p => p.product_id) || [];

    if (productIds.length === 0) {
      message.warning('无法获取待标注商品');
      return;
    }

    Modal.confirm({
      title: '确认开始AI标注',
      content: `即将标注 ${Math.min(productIds.length, batchSize)} 个商品，是否继续？`,
      onOk: () => {
        const idsToAnnotate = productIds.slice(0, batchSize);

        if (idsToAnnotate.length <= 10) {
          // 少量商品使用同步模式
          annotateSyncMutation.mutate(idsToAnnotate);
        } else {
          // 大量商品使用异步模式
          annotateMutation.mutate(idsToAnnotate);
        }
      },
    });
  };

  // 标注全部
  const handleAnnotateAll = () => {
    const pendingCount = statusData?.pending || 0;

    if (pendingCount === 0) {
      message.warning('没有待标注的商品');
      return;
    }

    Modal.confirm({
      title: '确认标注全部商品',
      content: `即将标注全部 ${pendingCount} 个待标注商品，这可能需要较长时间，是否继续？`,
      onOk: () => {
        const productIds = pendingProducts?.items?.map(p => p.product_id) || [];
        annotateMutation.mutate(productIds);
      },
    });
  };

  const pendingCount = statusData?.pending || 0;
  const completedCount = statusData?.completed || 0;
  const failedCount = statusData?.failed || 0;
  const totalCount = statusData?.total || 0;
  const progress = totalCount > 0 ? (completedCount / totalCount) * 100 : 0;

  return (
    <div className="ai-annotation">
      <Card
        title={
          <span>
            <RobotOutlined /> AI标注管理
          </span>
        }
        className="annotation-card"
      >
        {/* 状态统计 */}
        <div className="status-section">
          <Row gutter={16}>
            <Col span={6}>
              <Card>
                <Statistic
                  title="总商品数"
                  value={totalCount}
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
                  title="已完成"
                  value={completedCount}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="失败"
                  value={failedCount}
                  valueStyle={{ color: '#cf1322' }}
                />
              </Card>
            </Col>
          </Row>

          <div style={{ marginTop: 16 }}>
            <Progress
              percent={Math.round(progress)}
              status={pendingCount > 0 ? 'active' : 'success'}
              strokeColor={{
                '0%': '#108ee9',
                '100%': '#87d068',
              }}
            />
          </div>
        </div>

        {/* 配置区域 */}
        <div className="config-section">
          <Card title={<span><SettingOutlined /> 标注配置</span>} size="small">
            <Space direction="vertical" style={{ width: '100%' }} size="large">
              <div>
                <label>批次大小：</label>
                <InputNumber
                  min={1}
                  max={100}
                  value={batchSize}
                  onChange={setBatchSize}
                  style={{ width: 200, marginLeft: 8 }}
                />
                <span style={{ marginLeft: 8, color: '#999' }}>
                  每批处理的商品数量
                </span>
              </div>

              <div>
                <Checkbox
                  checked={useCustomPrompt}
                  onChange={(e) => setUseCustomPrompt(e.target.checked)}
                >
                  使用自定义提示词
                </Checkbox>
              </div>

              {useCustomPrompt && (
                <div className="prompt-editor">
                  <Alert
                    message="提示词说明"
                    description="使用 {product_name}, {description}, {price}, {rating}, {review_count} 作为占位符"
                    type="info"
                    showIcon
                    style={{ marginBottom: 8 }}
                  />
                  <TextArea
                    value={customPrompt || defaultPrompt}
                    onChange={(e) => setCustomPrompt(e.target.value)}
                    rows={12}
                    placeholder="输入自定义提示词..."
                  />
                </div>
              )}
            </Space>
          </Card>
        </div>

        {/* 操作按钮 */}
        <div className="action-section">
          <Space size="large">
            <Button
              type="primary"
              size="large"
              icon={<ThunderboltOutlined />}
              onClick={handleStartAnnotation}
              loading={annotateMutation.isPending || annotateSyncMutation.isPending}
              disabled={pendingCount === 0}
            >
              开始标注 ({Math.min(pendingCount, batchSize)} 个)
            </Button>

            <Button
              size="large"
              icon={<RobotOutlined />}
              onClick={handleAnnotateAll}
              loading={annotateMutation.isPending}
              disabled={pendingCount === 0}
            >
              标注全部 ({pendingCount} 个)
            </Button>

            <Button
              size="large"
              onClick={() => {
                refetchStatus();
                message.info('已刷新状态');
              }}
            >
              刷新状态
            </Button>
          </Space>
        </div>

        {/* 提示信息 */}
        {pendingCount === 0 && (
          <Alert
            message="所有商品都已标注完成"
            description="您可以在商品列表中查看标注结果"
            type="success"
            showIcon
            style={{ marginTop: 24 }}
          />
        )}

        {pendingCount > 0 && (
          <Alert
            message="标注提示"
            description={
              <ul style={{ marginBottom: 0, paddingLeft: 20 }}>
                <li>少量商品（≤10个）使用同步模式，即时返回结果</li>
                <li>大量商品（&gt;10个）使用异步模式，后台处理</li>
                <li>标注过程中请勿关闭页面</li>
                <li>可以自定义提示词以获得更好的标注效果</li>
              </ul>
            }
            type="info"
            showIcon
            style={{ marginTop: 24 }}
          />
        )}
      </Card>
    </div>
  );
};

export default AIAnnotation;

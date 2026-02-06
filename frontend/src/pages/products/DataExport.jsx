/**
 * 数据导出页面组件
 */
import React, { useState } from 'react';
import {
  Card,
  Radio,
  Button,
  Space,
  Alert,
  message,
  Divider,
} from 'antd';
import {
  DownloadOutlined,
  FileExcelOutlined,
  FileTextOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation } from '@tanstack/react-query';
import { exportProducts } from '../../api/import_export';
import { getStatistics } from '../../api/products';
import './DataExport.css';

const DataExport = () => {
  const [format, setFormat] = useState('excel');
  const [exportType, setExportType] = useState('products');

  // 获取统计信息
  const { data: statsData } = useQuery({
    queryKey: ['statistics'],
    queryFn: getStatistics,
  });

  // 导出Mutation
  const exportMutation = useMutation({
    mutationFn: () => exportProducts(format, exportType),
    onSuccess: (blob) => {
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      const ext = format === 'excel' ? 'xlsx' : 'csv';
      const nameMap = {
        products: 'products',
        clustered: 'clustered_products',
        'cluster-summary': 'cluster_summary',
      };
      link.download = `${nameMap[exportType] || 'products'}_${Date.now()}.${ext}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      message.success('导出成功！');
    },
    onError: (error) => {
      message.error(`导出失败: ${error.message}`);
    },
  });

  const handleExport = () => {
    exportMutation.mutate();
  };

  const totalCount = statsData?.data?.total_products || 0;
  const avgRating = statsData?.data?.rating_stats?.avg || 0;
  const avgPrice = statsData?.data?.price_stats?.avg || 0;
  const totalReviews = statsData?.data?.review_stats?.total || 0;

  return (
    <div className="data-export">
      <Card
        title={
          <span>
            <DownloadOutlined /> 数据导出
          </span>
        }
        className="export-card"
      >
        <div className="export-config">
          <Card title="导出配置" size="small">
            <Space direction="vertical" style={{ width: '100%' }} size="large">
              <div>
                <h4>导出格式</h4>
                <Radio.Group value={format} onChange={(e) => setFormat(e.target.value)}>
                  <Radio value="excel">
                    <FileExcelOutlined /> Excel (.xlsx)
                  </Radio>
                  <Radio value="csv">
                    <FileTextOutlined /> CSV (.csv)
                  </Radio>
                </Radio.Group>
              </div>

              <Divider />

              <div>
                <h4>导出类型</h4>
                <Radio.Group value={exportType} onChange={(e) => setExportType(e.target.value)}>
                  <Space direction="vertical">
                    <Radio value="products">原始商品数据（{totalCount} 个）</Radio>
                    <Radio value="clustered">聚类结果（含 cluster_id）</Radio>
                    <Radio value="cluster-summary">簇级汇总</Radio>
                  </Space>
                </Radio.Group>
              </div>

              <Divider />

              <Button
                type="primary"
                icon={<DownloadOutlined />}
                onClick={handleExport}
                loading={exportMutation.isPending}
                block
              >
                开始导出
              </Button>
            </Space>
          </Card>
        </div>

        <Alert
          message="导出提示"
          description={`当前商品总数：${totalCount}，平均评分：${avgRating.toFixed(2)}，平均价格：${avgPrice.toFixed(2)}，总评价数：${totalReviews.toLocaleString()}`}
          type="info"
          showIcon
          style={{ marginTop: 24 }}
        />
      </Card>
    </div>
  );
};

export default DataExport;

/**
 * 数据导出页面组件
 */
import React, { useState } from 'react';
import {
  Card,
  Radio,
  Checkbox,
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
import { exportProducts, getExportFields } from '../../api/import_export';
import { getStatistics } from '../../api/products';
import './DataExport.css';

const DataExport = () => {
  const [format, setFormat] = useState('excel');
  const [scope, setScope] = useState('all');
  const [selectedFields, setSelectedFields] = useState([]);

  // 获取统计信息
  const { data: statsData } = useQuery({
    queryKey: ['statistics'],
    queryFn: getStatistics,
  });

  // 获取可导出字段
  const { data: fieldsData } = useQuery({
    queryKey: ['export-fields'],
    queryFn: getExportFields,
  });

  // 导出Mutation
  const exportMutation = useMutation({
    mutationFn: () => exportProducts(format, scope, selectedFields),
    onSuccess: (blob) => {
      // 创建下载链接
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `products_${Date.now()}.${format === 'excel' ? 'xlsx' : 'csv'}`;
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

  // 处理字段选择
  const handleFieldChange = (checkedValues) => {
    setSelectedFields(checkedValues);
  };

  // 全选/取消全选
  const handleSelectAll = (group) => {
    const groupFields = fieldsData?.[group] || [];
    const allSelected = groupFields.every(field => selectedFields.includes(field));

    if (allSelected) {
      // 取消全选
      setSelectedFields(prev => prev.filter(f => !groupFields.includes(f)));
    } else {
      // 全选
      setSelectedFields(prev => [...new Set([...prev, ...groupFields])]);
    }
  };

  // 执行导出
  const handleExport = () => {
    if (selectedFields.length === 0) {
      message.warning('请至少选择一个导出字段');
      return;
    }

    exportMutation.mutate();
  };

  const totalCount = statsData?.total || 0;
  const annotatedCount = statsData?.by_ai_status?.completed || 0;

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
        {/* 导出配置 */}
        <div className="export-config">
          <Card title="导出配置" size="small">
            <Space direction="vertical" style={{ width: '100%' }} size="large">
              {/* 导出格式 */}
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

              {/* 导出范围 */}
              <div>
                <h4>导出范围</h4>
                <Radio.Group value={scope} onChange={(e) => setScope(e.target.value)}>
                  <Space direction="vertical">
                    <Radio value="all">
                      全部商品 ({totalCount} 个)
                    </Radio>
                    <Radio value="annotated">
                      已标注商品 ({annotatedCount} 个)
                    </Radio>
                    <Radio value="filtered" disabled>
                      当前筛选结果（暂不支持）
                    </Radio>
                  </Space>
                </Radio.Group>
              </div>

              <Divider />

              {/* 字段选择 */}
              <div>
                <h4>选择导出字段</h4>
                <Alert
                  message="请选择要导出的字段"
                  description="至少选择一个字段"
                  type="info"
                  showIcon
                  style={{ marginBottom: 16 }}
                />

                <div className="field-selection">
                  {/* 基础字段 */}
                  <div className="field-group">
                    <div className="field-group-title">
                      基础字段
                      <Button
                        type="link"
                        size="small"
                        onClick={() => handleSelectAll('basic_fields')}
                      >
                        {fieldsData?.basic_fields?.every(f => selectedFields.includes(f))
                          ? '取消全选'
                          : '全选'}
                      </Button>
                    </div>
                    <Checkbox.Group
                      value={selectedFields}
                      onChange={handleFieldChange}
                    >
                      <Space direction="vertical">
                        {fieldsData?.basic_fields?.map(field => (
                          <Checkbox key={field} value={field}>
                            {field}
                          </Checkbox>
                        ))}
                      </Space>
                    </Checkbox.Group>
                  </div>

                  {/* AI分析字段 */}
                  <div className="field-group">
                    <div className="field-group-title">
                      AI分析字段
                      <Button
                        type="link"
                        size="small"
                        onClick={() => handleSelectAll('ai_fields')}
                      >
                        {fieldsData?.ai_fields?.every(f => selectedFields.includes(f))
                          ? '取消全选'
                          : '全选'}
                      </Button>
                    </div>
                    <Checkbox.Group
                      value={selectedFields}
                      onChange={handleFieldChange}
                    >
                      <Space direction="vertical">
                        {fieldsData?.ai_fields?.map(field => (
                          <Checkbox key={field} value={field}>
                            {field}
                          </Checkbox>
                        ))}
                      </Space>
                    </Checkbox.Group>
                  </div>

                  {/* 翻译字段 */}
                  <div className="field-group">
                    <div className="field-group-title">
                      翻译字段
                      <Button
                        type="link"
                        size="small"
                        onClick={() => handleSelectAll('translation_fields')}
                      >
                        {fieldsData?.translation_fields?.every(f => selectedFields.includes(f))
                          ? '取消全选'
                          : '全选'}
                      </Button>
                    </div>
                    <Checkbox.Group
                      value={selectedFields}
                      onChange={handleFieldChange}
                    >
                      <Space direction="vertical">
                        {fieldsData?.translation_fields?.map(field => (
                          <Checkbox key={field} value={field}>
                            {field}
                          </Checkbox>
                        ))}
                      </Space>
                    </Checkbox.Group>
                  </div>

                  {/* 元数据字段 */}
                  <div className="field-group">
                    <div className="field-group-title">
                      元数据字段
                      <Button
                        type="link"
                        size="small"
                        onClick={() => handleSelectAll('metadata_fields')}
                      >
                        {fieldsData?.metadata_fields?.every(f => selectedFields.includes(f))
                          ? '取消全选'
                          : '全选'}
                      </Button>
                    </div>
                    <Checkbox.Group
                      value={selectedFields}
                      onChange={handleFieldChange}
                    >
                      <Space direction="vertical">
                        {fieldsData?.metadata_fields?.map(field => (
                          <Checkbox key={field} value={field}>
                            {field}
                          </Checkbox>
                        ))}
                      </Space>
                    </Checkbox.Group>
                  </div>
                </div>
              </div>
            </Space>
          </Card>
        </div>

        {/* 导出按钮 */}
        <div className="export-actions">
          <Space>
            <Button
              type="primary"
              size="large"
              icon={<DownloadOutlined />}
              onClick={handleExport}
              loading={exportMutation.isPending}
              disabled={selectedFields.length === 0}
            >
              导出数据 ({selectedFields.length} 个字段)
            </Button>
          </Space>
        </div>

        {/* 提示信息 */}
        <Alert
          message="导出说明"
          description={
            <ul style={{ marginBottom: 0, paddingLeft: 20 }}>
              <li>Excel格式支持更好的格式化和公式</li>
              <li>CSV格式更通用，可以在各种工具中打开</li>
              <li>导出的文件会自动下载到您的下载文件夹</li>
              <li>大量数据导出可能需要较长时间，请耐心等待</li>
            </ul>
          }
          type="info"
          showIcon
          style={{ marginTop: 24 }}
        />
      </Card>
    </div>
  );
};

export default DataExport;

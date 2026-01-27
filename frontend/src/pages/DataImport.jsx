/**
 * 数据导入页面组件
 */
import React, { useState } from 'react';
import {
  Card,
  Upload,
  Button,
  Select,
  Checkbox,
  Table,
  message,
  Steps,
  Space,
  InputNumber,
  Alert,
  Progress,
} from 'antd';
import {
  UploadOutlined,
  InboxOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { importProducts } from '../api/import_export';
import './DataImport.css';

const { Dragger } = Upload;
const { Option } = Select;
const { Step } = Steps;

const DataImport = () => {
  const queryClient = useQueryClient();
  const [currentStep, setCurrentStep] = useState(0);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [previewData, setPreviewData] = useState([]);
  const [platform, setPlatform] = useState('etsy');
  const [skipDuplicates, setSkipDuplicates] = useState(true);
  const [fieldMapping, setFieldMapping] = useState({});

  // 核心字段定义
  const coreFields = [
    { key: 'product_name', label: '商品名称', required: true },
    { key: 'description', label: '商品描述', required: false },
    { key: 'price', label: '价格', required: false },
    { key: 'sales', label: '销量', required: false },
    { key: 'rating', label: '评分', required: false },
    { key: 'review_count', label: '评价数', required: false },
    { key: 'url', label: '商品链接', required: false },
    { key: 'shop_name', label: '店铺名称', required: false },
  ];

  // 导入Mutation
  const importMutation = useMutation({
    mutationFn: () => importProducts(uploadedFile, platform, fieldMapping, skipDuplicates),
    onSuccess: (data) => {
      message.success(data.message);
      queryClient.invalidateQueries(['products']);
      queryClient.invalidateQueries(['statistics']);
      setCurrentStep(3);
    },
    onError: (error) => {
      message.error(`导入失败: ${error.message}`);
    },
  });

  // 处理文件上传
  const handleFileUpload = (file) => {
    setUploadedFile(file);

    // 读取文件预览
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const text = e.target.result;
        const lines = text.split('\n').slice(0, 6); // 前5行数据
        const rows = lines.map(line => line.split(','));

        // 转换为表格数据
        const tableData = rows.slice(0, 5).map((row, idx) => ({
          key: idx,
          ...row.reduce((acc, cell, cellIdx) => {
            acc[`col_${cellIdx}`] = cell;
            return acc;
          }, {})
        }));

        setPreviewData(tableData);
        setCurrentStep(1);
      } catch (error) {
        message.error('文件解析失败');
      }
    };
    reader.readAsText(file);

    return false; // 阻止自动上传
  };

  // 处理字段映射
  const handleFieldMappingChange = (fieldKey, colIndex) => {
    setFieldMapping(prev => ({
      ...prev,
      [`col_${colIndex}`]: fieldKey
    }));
  };

  // 执行导入
  const handleImport = () => {
    // 验证必填字段
    const hasProductName = Object.values(fieldMapping).includes('product_name');
    if (!hasProductName) {
      message.error('请至少映射"商品名称"字段');
      return;
    }

    setCurrentStep(2);
    importMutation.mutate();
  };

  // 重置
  const handleReset = () => {
    setCurrentStep(0);
    setUploadedFile(null);
    setPreviewData([]);
    setFieldMapping({});
  };

  // 生成预览表格列
  const previewColumns = previewData.length > 0
    ? Object.keys(previewData[0])
        .filter(key => key !== 'key')
        .map(key => ({
          title: key.replace('col_', '列 '),
          dataIndex: key,
          key: key,
          width: 150,
          ellipsis: true,
        }))
    : [];

  return (
    <div className="data-import">
      <Card title="📥 数据导入" className="import-card">
        <Steps current={currentStep} style={{ marginBottom: 24 }}>
          <Step title="上传文件" icon={<UploadOutlined />} />
          <Step title="字段映射" />
          <Step title="执行导入" />
          <Step title="完成" icon={<CheckCircleOutlined />} />
        </Steps>

        {/* 步骤1: 文件上传 */}
        {currentStep === 0 && (
          <div className="upload-section">
            <Alert
              message="支持CSV和Excel文件"
              description="可以上传无列名的文件，系统会按列顺序进行映射"
              type="info"
              showIcon
              style={{ marginBottom: 16 }}
            />

            <Dragger
              accept=".csv,.xlsx,.xls"
              beforeUpload={handleFileUpload}
              maxCount={1}
              showUploadList={false}
            >
              <p className="ant-upload-drag-icon">
                <InboxOutlined />
              </p>
              <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
              <p className="ant-upload-hint">
                支持CSV、Excel格式，单次上传一个文件
              </p>
            </Dragger>
          </div>
        )}

        {/* 步骤2: 字段映射 */}
        {currentStep === 1 && (
          <div className="mapping-section">
            <Alert
              message="数据预览（前5行）"
              type="info"
              showIcon
              style={{ marginBottom: 16 }}
            />

            <Table
              dataSource={previewData}
              columns={previewColumns}
              pagination={false}
              scroll={{ x: 'max-content' }}
              size="small"
              style={{ marginBottom: 24 }}
            />

            <Card title="字段映射配置" size="small">
              <Space direction="vertical" style={{ width: '100%' }} size="large">
                <div>
                  <label>平台选择：</label>
                  <Select
                    value={platform}
                    onChange={setPlatform}
                    style={{ width: 200, marginLeft: 8 }}
                  >
                    <Option value="etsy">Etsy</Option>
                    <Option value="gumroad">Gumroad</Option>
                    <Option value="amazon">Amazon</Option>
                  </Select>
                </div>

                <div>
                  <Checkbox
                    checked={skipDuplicates}
                    onChange={(e) => setSkipDuplicates(e.target.checked)}
                  >
                    跳过重复数据（根据URL去重）
                  </Checkbox>
                </div>

                <div>
                  <h4>字段映射（将列索引映射到字段名）</h4>
                  <div className="field-mapping-grid">
                    {coreFields.map(field => (
                      <div key={field.key} className="field-mapping-item">
                        <label>
                          {field.label}
                          {field.required && <span style={{ color: 'red' }}> *</span>}
                        </label>
                        <InputNumber
                          min={-1}
                          max={previewColumns.length - 1}
                          placeholder="-1 (不映射)"
                          onChange={(value) => handleFieldMappingChange(field.key, value)}
                          style={{ width: '100%' }}
                        />
                      </div>
                    ))}
                  </div>
                  <Alert
                    message="提示"
                    description="输入列的索引号（从0开始），-1表示不映射该字段"
                    type="info"
                    showIcon
                    style={{ marginTop: 16 }}
                  />
                </div>
              </Space>
            </Card>

            <div style={{ marginTop: 24, textAlign: 'right' }}>
              <Space>
                <Button onClick={handleReset}>重新上传</Button>
                <Button type="primary" onClick={handleImport}>
                  开始导入
                </Button>
              </Space>
            </div>
          </div>
        )}

        {/* 步骤3: 执行导入 */}
        {currentStep === 2 && (
          <div className="importing-section">
            <div style={{ textAlign: 'center', padding: '40px 0' }}>
              <Progress
                type="circle"
                percent={importMutation.isPending ? 50 : 100}
                status={importMutation.isPending ? 'active' : 'success'}
              />
              <p style={{ marginTop: 16, fontSize: 16 }}>
                {importMutation.isPending ? '正在导入数据...' : '导入完成！'}
              </p>
            </div>
          </div>
        )}

        {/* 步骤4: 完成 */}
        {currentStep === 3 && (
          <div className="complete-section">
            <Alert
              message="导入成功"
              description={
                <div>
                  <p>数据已成功导入到数据库</p>
                  <p>您可以在商品列表中查看导入的数据</p>
                </div>
              }
              type="success"
              showIcon
              style={{ marginBottom: 16 }}
            />

            <div style={{ textAlign: 'center' }}>
              <Space>
                <Button onClick={handleReset}>继续导入</Button>
                <Button type="primary" onClick={() => window.location.href = '/'}>
                  查看商品列表
                </Button>
              </Space>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
};

export default DataImport;

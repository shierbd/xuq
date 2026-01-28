/**
 * 批量导入页面组件
 */
import React, { useState } from 'react';
import {
  Card,
  Input,
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
  Statistic,
  Row,
  Col,
  Tag,
  Collapse,
} from 'antd';
import {
  FolderOpenOutlined,
  CheckCircleOutlined,
  FileExcelOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { useMutation } from '@tanstack/react-query';
import { previewFolderFiles, batchImportFromFolder } from '../../api/batch_import';
import './BatchImport.css';

const { Option } = Select;
const { Step } = Steps;
const { Panel } = Collapse;

const BatchImport = () => {
  const [currentStep, setCurrentStep] = useState(0);
  const [folderPath, setFolderPath] = useState('D:\\数据\\etsy');
  const [filePattern, setFilePattern] = useState('*.xlsx');
  const [fileList, setFileList] = useState([]);
  const [platform, setPlatform] = useState('etsy');
  const [skipDuplicates, setSkipDuplicates] = useState(true);
  const [fieldMapping, setFieldMapping] = useState({});
  const [importResult, setImportResult] = useState(null);

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

  // 预览文件列表Mutation
  const previewMutation = useMutation({
    mutationFn: () => previewFolderFiles(folderPath, filePattern),
    onSuccess: (data) => {
      setFileList(data.files || []);
      setCurrentStep(1);
      message.success(`找到 ${data.total_files} 个文件`);
    },
    onError: (error) => {
      message.error(`预览失败: ${error.message}`);
    },
  });

  // 批量导入Mutation
  const importMutation = useMutation({
    mutationFn: () => batchImportFromFolder(folderPath, platform, fieldMapping, skipDuplicates, filePattern),
    onSuccess: (data) => {
      setImportResult(data);
      setCurrentStep(3);
      if (data.success) {
        message.success('批量导入完成');
      } else {
        message.warning(data.message);
      }
    },
    onError: (error) => {
      message.error(`批量导入失败: ${error.message}`);
    },
  });

  // 处理字段映射
  const handleFieldMappingChange = (fieldKey, colIndex) => {
    setFieldMapping(prev => {
      const newMapping = { ...prev };
      if (colIndex === -1 || colIndex === null || colIndex === undefined) {
        delete newMapping[fieldKey];
      } else {
        newMapping[fieldKey] = colIndex;
      }
      return newMapping;
    });
  };

  // 执行预览
  const handlePreview = () => {
    if (!folderPath.trim()) {
      message.error('请输入文件夹路径');
      return;
    }
    previewMutation.mutate();
  };

  // 执行导入
  const handleImport = () => {
    // 验证必填字段
    const hasProductName = 'product_name' in fieldMapping;
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
    setFileList([]);
    setFieldMapping({});
    setImportResult(null);
  };

  // 文件列表表格列
  const fileColumns = [
    {
      title: '文件名',
      dataIndex: 'name',
      key: 'name',
      ellipsis: true,
      render: (text) => (
        <Space>
          <FileExcelOutlined style={{ color: '#52c41a' }} />
          {text}
        </Space>
      ),
    },
    {
      title: '文件大小',
      dataIndex: 'size_mb',
      key: 'size_mb',
      width: 120,
      render: (size) => `${size} MB`,
    },
  ];

  // 导入结果表格列
  const resultColumns = [
    {
      title: '文件名',
      dataIndex: 'file_name',
      key: 'file_name',
      ellipsis: true,
    },
    {
      title: '状态',
      dataIndex: 'success',
      key: 'success',
      width: 100,
      render: (success) => (
        <Tag color={success ? 'success' : 'error'}>
          {success ? '成功' : '失败'}
        </Tag>
      ),
    },
    {
      title: '导入数',
      dataIndex: 'imported',
      key: 'imported',
      width: 100,
    },
    {
      title: '重复数',
      dataIndex: 'duplicates',
      key: 'duplicates',
      width: 100,
    },
    {
      title: '无效数',
      dataIndex: 'invalid',
      key: 'invalid',
      width: 100,
    },
    {
      title: '消息',
      dataIndex: 'message',
      key: 'message',
      ellipsis: true,
    },
  ];

  return (
    <div className="batch-import">
      <Card title="📦 批量导入" className="batch-import-card">
        <Steps current={currentStep} style={{ marginBottom: 24 }}>
          <Step title="选择文件夹" icon={<FolderOpenOutlined />} />
          <Step title="配置映射" />
          <Step title="执行导入" />
          <Step title="完成" icon={<CheckCircleOutlined />} />
        </Steps>

        {/* 步骤1: 选择文件夹 */}
        {currentStep === 0 && (
          <div className="folder-selection">
            <Alert
              message="📁 批量导入说明"
              description={
                <div>
                  <p><strong>功能说明：</strong></p>
                  <ul style={{ marginBottom: 8, paddingLeft: 20 }}>
                    <li>支持从指定文件夹批量导入多个文件</li>
                    <li>自动扫描文件夹中的所有匹配文件</li>
                    <li>统一配置字段映射，应用到所有文件</li>
                    <li>显示每个文件的导入结果和统计信息</li>
                  </ul>
                  <p><strong>使用场景：</strong></p>
                  <ul style={{ marginBottom: 0, paddingLeft: 20 }}>
                    <li>批量导入多个关键词的商品数据</li>
                    <li>导入不同类目的商品数据</li>
                    <li>定期批量更新商品数据</li>
                  </ul>
                </div>
              }
              type="info"
              showIcon
              style={{ marginBottom: 16 }}
            />

            <Space direction="vertical" style={{ width: '100%' }} size="large">
              <div>
                <label><strong>文件夹路径：</strong></label>
                <Input
                  value={folderPath}
                  onChange={(e) => setFolderPath(e.target.value)}
                  placeholder="例如: D:\数据\etsy"
                  style={{ marginTop: 8 }}
                  size="large"
                  prefix={<FolderOpenOutlined />}
                />
                <div style={{ marginTop: 8, color: '#999', fontSize: 12 }}>
                  提示：请输入包含 Excel 或 CSV 文件的文件夹完整路径
                </div>
              </div>

              <div>
                <label><strong>文件匹配模式：</strong></label>
                <Select
                  value={filePattern}
                  onChange={setFilePattern}
                  style={{ width: 200, marginTop: 8 }}
                >
                  <Option value="*.xlsx">*.xlsx (Excel 2007+)</Option>
                  <Option value="*.xls">*.xls (Excel 97-2003)</Option>
                  <Option value="*.csv">*.csv (CSV 文件)</Option>
                  <Option value="*.*">*.* (所有文件)</Option>
                </Select>
                <span style={{ marginLeft: 8, color: '#999', fontSize: 12 }}>
                  （选择要导入的文件类型）
                </span>
              </div>

              <div style={{ textAlign: 'center', marginTop: 24 }}>
                <Button
                  type="primary"
                  size="large"
                  icon={<FolderOpenOutlined />}
                  onClick={handlePreview}
                  loading={previewMutation.isPending}
                >
                  扫描文件夹
                </Button>
              </div>
            </Space>
          </div>
        )}

        {/* 步骤2: 配置映射 */}
        {currentStep === 1 && (
          <div className="mapping-section">
            <Alert
              message={`📊 找到 ${fileList.length} 个文件`}
              description="请配置字段映射，将应用到所有文件"
              type="success"
              showIcon
              style={{ marginBottom: 16 }}
            />

            <Collapse defaultActiveKey={['1', '2']} style={{ marginBottom: 16 }}>
              <Panel header={`文件列表 (${fileList.length} 个)`} key="1">
                <Table
                  dataSource={fileList}
                  columns={fileColumns}
                  pagination={{ pageSize: 10 }}
                  size="small"
                  rowKey="path"
                />
              </Panel>

              <Panel header="字段映射配置" key="2">
                <Alert
                  message="💡 配置说明"
                  description={
                    <div>
                      <p><strong>字段映射规则：</strong></p>
                      <ul style={{ marginBottom: 8, paddingLeft: 20 }}>
                        <li>输入列的索引号（从 0 开始计数）</li>
                        <li>例如：第1列输入 0，第2列输入 1，以此类推</li>
                        <li>输入 -1 表示不映射该字段（跳过）</li>
                        <li><strong style={{ color: '#ff4d4f' }}>商品名称为必填字段</strong>，其他字段可选</li>
                      </ul>
                      <p style={{ marginBottom: 0 }}><strong>注意：</strong>此映射将应用到所有文件，请确保所有文件的列结构一致</p>
                    </div>
                  }
                  type="warning"
                  showIcon
                  style={{ marginBottom: 16 }}
                />

                <Space direction="vertical" style={{ width: '100%' }} size="large">
                  <div>
                    <label><strong>平台选择：</strong></label>
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
                      跳过重复数据
                    </Checkbox>
                    <span style={{ marginLeft: 8, color: '#999', fontSize: 12 }}>
                      （根据商品名称 + 店铺名称去重）
                    </span>
                  </div>

                  <div>
                    <h4>🔗 字段映射</h4>
                    <div className="field-mapping-grid">
                      {coreFields.map(field => (
                        <div key={field.key} className="field-mapping-item">
                          <label>
                            {field.label}
                            {field.required && <span style={{ color: 'red' }}> *</span>}
                          </label>
                          <InputNumber
                            min={-1}
                            max={20}
                            placeholder="-1 (不映射)"
                            value={fieldMapping[field.key]}
                            onChange={(value) => handleFieldMappingChange(field.key, value)}
                            style={{ width: '100%' }}
                          />
                        </div>
                      ))}
                    </div>
                  </div>
                </Space>
              </Panel>
            </Collapse>

            <div style={{ textAlign: 'right' }}>
              <Space>
                <Button onClick={handleReset}>重新选择</Button>
                <Button type="primary" onClick={handleImport}>
                  开始批量导入
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
                {importMutation.isPending ? '正在批量导入数据...' : '批量导入完成！'}
              </p>
              <p style={{ color: '#999' }}>
                请耐心等待，正在处理 {fileList.length} 个文件
              </p>
            </div>
          </div>
        )}

        {/* 步骤4: 完成 */}
        {currentStep === 3 && importResult && (
          <div className="complete-section">
            <Alert
              message={importResult.success ? '✅ 批量导入完成' : '⚠️ 批量导入完成（部分失败）'}
              description={importResult.message}
              type={importResult.success ? 'success' : 'warning'}
              showIcon
              style={{ marginBottom: 16 }}
            />

            <Row gutter={16} style={{ marginBottom: 24 }}>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="总文件数"
                    value={importResult.total_files}
                    suffix="个"
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="成功处理"
                    value={importResult.processed_files}
                    valueStyle={{ color: '#3f8600' }}
                    suffix="个"
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="失败文件"
                    value={importResult.failed_files}
                    valueStyle={{ color: '#cf1322' }}
                    suffix="个"
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="总导入数"
                    value={importResult.total_imported}
                    valueStyle={{ color: '#1890ff' }}
                    suffix="条"
                  />
                </Card>
              </Col>
            </Row>

            <Card title="📋 详细结果" style={{ marginBottom: 16 }}>
              <Table
                dataSource={importResult.file_results}
                columns={resultColumns}
                pagination={{ pageSize: 10 }}
                size="small"
                rowKey="file_path"
              />
            </Card>

            <div style={{ textAlign: 'center' }}>
              <Space>
                <Button onClick={handleReset} icon={<ReloadOutlined />}>
                  继续批量导入
                </Button>
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

export default BatchImport;

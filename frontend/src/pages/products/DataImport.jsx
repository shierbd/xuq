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
import { importProducts } from '../../api/import_export';
import * as XLSX from 'xlsx';
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

    const reader = new FileReader();

    // 根据文件类型选择不同的读取方式
    const fileExtension = file.name.split('.').pop().toLowerCase();

    if (fileExtension === 'csv') {
      // CSV文件使用文本方式读取
      reader.onload = (e) => {
        try {
          const text = e.target.result;
          const lines = text.split('\n').filter(line => line.trim()); // 过滤空行
          const rows = lines.slice(0, 6).map(line => {
            // 处理CSV中的引号和逗号
            const cells = [];
            let cell = '';
            let inQuotes = false;

            for (let i = 0; i < line.length; i++) {
              const char = line[i];
              if (char === '"') {
                inQuotes = !inQuotes;
              } else if (char === ',' && !inQuotes) {
                cells.push(cell.trim());
                cell = '';
              } else {
                cell += char;
              }
            }
            cells.push(cell.trim()); // 添加最后一个单元格
            return cells;
          });

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
          console.error('CSV解析错误:', error);
          message.error('CSV文件解析失败');
        }
      };
      reader.readAsText(file, 'UTF-8');
    } else if (fileExtension === 'xlsx' || fileExtension === 'xls') {
      // Excel文件使用二进制方式读取
      reader.onload = (e) => {
        try {
          const data = new Uint8Array(e.target.result);
          const workbook = XLSX.read(data, { type: 'array' });

          // 获取第一个工作表
          const firstSheetName = workbook.SheetNames[0];
          const worksheet = workbook.Sheets[firstSheetName];

          // 转换为JSON数组（不包含表头）
          const jsonData = XLSX.utils.sheet_to_json(worksheet, {
            header: 1,  // 使用数组格式而不是对象格式
            defval: ''  // 空单元格默认值
          });

          // 取前5行数据
          const rows = jsonData.slice(0, 5);

          // 转换为表格数据
          const tableData = rows.map((row, idx) => ({
            key: idx,
            ...row.reduce((acc, cell, cellIdx) => {
              acc[`col_${cellIdx}`] = cell !== null && cell !== undefined ? String(cell) : '';
              return acc;
            }, {})
          }));

          setPreviewData(tableData);
          setCurrentStep(1);
        } catch (error) {
          console.error('Excel解析错误:', error);
          message.error('Excel文件解析失败');
        }
      };
      reader.readAsArrayBuffer(file);
    } else {
      message.error('不支持的文件格式，请上传CSV或Excel文件');
      return false;
    }

    return false; // 阻止自动上传
  };

  // 处理字段映射
  const handleFieldMappingChange = (fieldKey, colIndex) => {
    setFieldMapping(prev => {
      const newMapping = { ...prev };

      // 如果是 -1 或 null，删除该字段的映射
      if (colIndex === -1 || colIndex === null || colIndex === undefined) {
        delete newMapping[fieldKey];
      } else {
        // 否则设置映射：字段名 -> 列索引
        newMapping[fieldKey] = colIndex;
      }

      return newMapping;
    });
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
              message="📋 数据导入说明"
              description={
                <div>
                  <p><strong>支持的文件格式：</strong></p>
                  <ul style={{ marginBottom: 8, paddingLeft: 20 }}>
                    <li>CSV 文件（.csv）</li>
                    <li>Excel 文件（.xlsx, .xls）</li>
                  </ul>
                  <p><strong>文件要求：</strong></p>
                  <ul style={{ marginBottom: 8, paddingLeft: 20 }}>
                    <li>可以上传无列名的文件，系统会按列顺序进行映射</li>
                    <li>必须包含商品名称字段（其他字段可选）</li>
                    <li>支持自定义字段映射，灵活适配不同数据格式</li>
                  </ul>
                  <p><strong>导入流程：</strong></p>
                  <ol style={{ marginBottom: 0, paddingLeft: 20 }}>
                    <li>上传文件 → 系统自动解析并预览前5行数据</li>
                    <li>配置字段映射 → 将文件列映射到系统字段</li>
                    <li>执行导入 → 系统自动清洗数据并导入数据库</li>
                    <li>查看结果 → 显示导入统计信息</li>
                  </ol>
                </div>
              }
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
              message="📊 数据预览（前5行）"
              description="请检查数据是否正确解析，然后配置字段映射"
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

            <Card title="⚙️ 字段映射配置" size="small">
              <Space direction="vertical" style={{ width: '100%' }} size="large">
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
                      <p><strong>数据处理：</strong></p>
                      <ul style={{ marginBottom: 0, paddingLeft: 20 }}>
                        <li>系统会自动清洗数据（去除空格、格式化数字等）</li>
                        <li>评价数支持多种格式：1234、1.2k、1,234 等</li>
                        <li>价格会自动去除货币符号并转换为数字</li>
                        <li>评分会自动转换为 0-5 的数值</li>
                      </ul>
                    </div>
                  }
                  type="warning"
                  showIcon
                  style={{ marginBottom: 16 }}
                />

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
                  <span style={{ marginLeft: 8, color: '#999', fontSize: 12 }}>
                    （用于标识数据来源）
                  </span>
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
                  <h4>🔗 字段映射（将文件列映射到系统字段）</h4>
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
                          value={fieldMapping[field.key]}
                          onChange={(value) => handleFieldMappingChange(field.key, value)}
                          style={{ width: '100%' }}
                        />
                      </div>
                    ))}
                  </div>
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
              message="✅ 导入成功"
              description={
                <div>
                  <p><strong>数据已成功导入到数据库</strong></p>
                  <p style={{ marginTop: 8 }}>
                    <strong>导入统计：</strong>
                  </p>
                  <ul style={{ marginBottom: 8, paddingLeft: 20 }}>
                    <li>总行数：{importMutation.data?.data?.total_rows || 0} 行</li>
                    <li>有效数据：{importMutation.data?.data?.valid_rows || 0} 行</li>
                    <li>成功导入：{importMutation.data?.data?.imported || 0} 条</li>
                    <li>重复跳过：{importMutation.data?.data?.duplicates || 0} 条</li>
                    <li>无效数据：{importMutation.data?.data?.invalid_rows || 0} 行</li>
                  </ul>
                  <p style={{ marginTop: 8, color: '#52c41a' }}>
                    您可以在商品管理页面查看导入的数据
                  </p>
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

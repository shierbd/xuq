/**
 * 词根聚类模块 - A2阶段：关键词导入页面
 */
import React, { useState } from 'react';
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query';
import {
  Card,
  Upload,
  Button,
  Space,
  Alert,
  Progress,
  Table,
  Tag,
  Statistic,
  Row,
  Col,
  message,
  Steps,
  Divider,
} from 'antd';
import {
  UploadOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  InboxOutlined,
} from '@ant-design/icons';
import { importKeywords, getKeywordCount } from '../../api/keywords';
import './KeywordImport.css';

const { Dragger } = Upload;
const { Step } = Steps;

const KeywordImport = () => {
  const queryClient = useQueryClient();
  const [fileList, setFileList] = useState([]);
  const [uploadResult, setUploadResult] = useState(null);
  const [currentStep, setCurrentStep] = useState(0);

  // 获取关键词总数
  const { data: countData } = useQuery({
    queryKey: ['keyword-count'],
    queryFn: getKeywordCount,
  });

  // 导入Mutation
  const importMutation = useMutation({
    mutationFn: (file) => importKeywords(file),
    onSuccess: (data) => {
      message.success('关键词导入成功');
      setUploadResult(data);
      setCurrentStep(2);
      queryClient.invalidateQueries(['keyword-count']);
      queryClient.invalidateQueries(['keywords']);
      setFileList([]);
    },
    onError: (error) => {
      message.error(`导入失败: ${error.message}`);
      setCurrentStep(0);
    },
  });

  // 上传配置
  const uploadProps = {
    name: 'file',
    multiple: false,
    fileList,
    accept: '.csv,.xlsx,.xls',
    beforeUpload: (file) => {
      const isValidType =
        file.type === 'text/csv' ||
        file.type === 'application/vnd.ms-excel' ||
        file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';

      if (!isValidType) {
        message.error('只支持 CSV 和 Excel 文件');
        return false;
      }

      const isLt50M = file.size / 1024 / 1024 < 50;
      if (!isLt50M) {
        message.error('文件大小不能超过 50MB');
        return false;
      }

      setFileList([file]);
      setCurrentStep(1);
      return false;
    },
    onRemove: () => {
      setFileList([]);
      setCurrentStep(0);
    },
  };

  // 开始导入
  const handleImport = () => {
    if (fileList.length === 0) {
      message.warning('请先选择文件');
      return;
    }
    importMutation.mutate(fileList[0]);
  };

  // 重置
  const handleReset = () => {
    setFileList([]);
    setUploadResult(null);
    setCurrentStep(0);
  };

  const resultColumns = [
    {
      title: '字段',
      dataIndex: 'field',
      key: 'field',
      width: 150,
    },
    {
      title: '值',
      dataIndex: 'value',
      key: 'value',
      render: (value) => <strong style={{ color: '#1890ff' }}>{value}</strong>,
    },
  ];

  const resultData = uploadResult
    ? [
        { field: '导入总数', value: uploadResult.total || 0 },
        { field: '成功数量', value: uploadResult.success || 0 },
        { field: '失败数量', value: uploadResult.failed || 0 },
        { field: '重复数量', value: uploadResult.duplicates || 0 },
      ]
    : [];

  return (
    <div className="keyword-import-container">
      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card>
            <Statistic
              title="当前关键词总数"
              value={countData?.data?.total || 0}
              prefix={<FileTextOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="本次导入数量"
              value={uploadResult?.success || 0}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="导入后总数"
              value={(countData?.data?.total || 0) + (uploadResult?.success || 0)}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 导入流程 */}
      <Card
        title={
          <Space>
            <UploadOutlined />
            <span>A2阶段：关键词导入</span>
          </Space>
        }
      >
        <Steps current={currentStep} style={{ marginBottom: 32 }}>
          <Step title="选择文件" icon={<InboxOutlined />} />
          <Step title="上传导入" icon={<ClockCircleOutlined />} />
          <Step title="导入完成" icon={<CheckCircleOutlined />} />
        </Steps>

        {/* 文件格式说明 */}
        <Alert
          message="文件格式要求"
          description={
            <div>
              <p><strong>支持格式：</strong>CSV (.csv) 或 Excel (.xlsx, .xls)</p>
              <p><strong>必需字段：</strong></p>
              <ul style={{ marginBottom: 0, paddingLeft: 20 }}>
                <li>keyword - 关键词短语（必填）</li>
                <li>seed_word - 来源种子词（必填）</li>
                <li>source - 数据来源（semrush/reddit/related_search）</li>
                <li>volume - 月搜索量（可选）</li>
                <li>competition - 竞争度（可选）</li>
                <li>cpc - 每次点击成本（可选）</li>
              </ul>
              <p style={{ marginTop: 8 }}><strong>示例：</strong>compress pdf, compress, semrush, 12000, HIGH, 1.5</p>
            </div>
          }
          type="info"
          showIcon
          style={{ marginBottom: 24 }}
        />

        {/* 上传区域 */}
        {currentStep === 0 && (
          <Dragger {...uploadProps} style={{ marginBottom: 24 }}>
            <p className="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
            <p className="ant-upload-hint">
              支持 CSV 和 Excel 格式，单个文件不超过 50MB
            </p>
          </Dragger>
        )}

        {/* 上传中 */}
        {currentStep === 1 && (
          <div style={{ marginBottom: 24 }}>
            <Alert
              message="文件已选择"
              description={`文件名: ${fileList[0]?.name}`}
              type="success"
              showIcon
              style={{ marginBottom: 16 }}
            />
            <Space>
              <Button
                type="primary"
                icon={<UploadOutlined />}
                onClick={handleImport}
                loading={importMutation.isPending}
              >
                开始导入
              </Button>
              <Button onClick={handleReset}>重新选择</Button>
            </Space>
          </div>
        )}

        {/* 导入结果 */}
        {currentStep === 2 && uploadResult && (
          <div>
            <Alert
              message="导入完成"
              description={`成功导入 ${uploadResult.success} 条关键词`}
              type="success"
              showIcon
              style={{ marginBottom: 16 }}
            />

            <Table
              columns={resultColumns}
              dataSource={resultData}
              rowKey="field"
              pagination={false}
              size="small"
              style={{ marginBottom: 16 }}
            />

            {uploadResult.errors && uploadResult.errors.length > 0 && (
              <Alert
                message="导入错误"
                description={
                  <ul style={{ marginBottom: 0, paddingLeft: 20 }}>
                    {uploadResult.errors.slice(0, 5).map((err, idx) => (
                      <li key={idx}>{err}</li>
                    ))}
                    {uploadResult.errors.length > 5 && (
                      <li>...还有 {uploadResult.errors.length - 5} 个错误</li>
                    )}
                  </ul>
                }
                type="warning"
                showIcon
                style={{ marginBottom: 16 }}
              />
            )}

            <Space>
              <Button type="primary" onClick={handleReset}>
                继续导入
              </Button>
              <Button onClick={() => (window.location.href = '/keywords')}>
                查看关键词列表
              </Button>
            </Space>
          </div>
        )}

        <Divider />

        {/* 导入提示 */}
        <Alert
          message="导入提示"
          description={
            <ul style={{ marginBottom: 0, paddingLeft: 20 }}>
              <li>导入前请确保文件格式正确，包含必需字段</li>
              <li>系统会自动去重，重复的关键词不会被导入</li>
              <li>导入后可以在"关键词列表"页面查看和管理</li>
              <li>导入完成后，可以进行A3阶段的语义聚类分析</li>
            </ul>
          }
          type="info"
          showIcon
        />
      </Card>
    </div>
  );
};

export default KeywordImport;

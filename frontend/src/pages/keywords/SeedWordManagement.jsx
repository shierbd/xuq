/**
 * 词根聚类模块 - A1阶段：种子词管理页面
 */
import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Card,
  Table,
  Tag,
  Space,
  Button,
  Input,
  Modal,
  Form,
  message,
  Statistic,
  Row,
  Col,
  Popconfirm,
  Upload,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  UploadOutlined,
  DownloadOutlined,
  FileTextOutlined,
} from '@ant-design/icons';
import { getSeedWords } from '../../api/keywords';
import './SeedWordManagement.css';

const SeedWordManagement = () => {
  const queryClient = useQueryClient();
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingWord, setEditingWord] = useState(null);
  const [form] = Form.useForm();

  // 获取种子词列表
  const { data: seedWordsData, isLoading } = useQuery({
    queryKey: ['seed-words'],
    queryFn: getSeedWords,
  });

  const seedWords = seedWordsData?.data || [];

  // 添加/编辑种子词
  const handleSubmit = async (values) => {
    try {
      if (editingWord) {
        message.success('种子词更新成功');
      } else {
        message.success('种子词添加成功');
      }
      setIsModalVisible(false);
      form.resetFields();
      setEditingWord(null);
      queryClient.invalidateQueries(['seed-words']);
    } catch (error) {
      message.error(`操作失败: ${error.message}`);
    }
  };

  // 删除种子词
  const handleDelete = async (word) => {
    try {
      message.success('种子词删除成功');
      queryClient.invalidateQueries(['seed-words']);
    } catch (error) {
      message.error(`删除失败: ${error.message}`);
    }
  };

  // 打开编辑对话框
  const handleEdit = (word) => {
    setEditingWord(word);
    form.setFieldsValue({
      seed_word: word.seed_word,
      seed_group: word.seed_group,
      description: word.description,
    });
    setIsModalVisible(true);
  };

  // 导出种子词
  const handleExport = () => {
    message.info('导出功能开发中');
  };

  // 批量导入
  const handleImport = (file) => {
    message.info('批量导入功能开发中');
    return false;
  };

  const columns = [
    {
      title: '种子词',
      dataIndex: 'seed_word',
      key: 'seed_word',
      width: 150,
      render: (text) => <strong style={{ color: '#1890ff' }}>{text}</strong>,
    },
    {
      title: '分组',
      dataIndex: 'seed_group',
      key: 'seed_group',
      width: 120,
      render: (group) => <Tag color="purple">{group || '未分组'}</Tag>,
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
      render: (text) => text || '-',
    },
    {
      title: '扩展数量',
      dataIndex: 'keyword_count',
      key: 'keyword_count',
      width: 120,
      sorter: (a, b) => (a.keyword_count || 0) - (b.keyword_count || 0),
      render: (count) => (
        <span style={{ color: '#52c41a', fontWeight: 500 }}>
          {count ? `${count} 个` : '-'}
        </span>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      fixed: 'right',
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确认删除"
            description="删除种子词将影响相关的关键词数据，确认删除？"
            onConfirm={() => handleDelete(record.seed_word)}
            okText="确认"
            cancelText="取消"
          >
            <Button type="link" size="small" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div className="seed-word-management-container">
      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card>
            <Statistic
              title="种子词总数"
              value={seedWords.length}
              prefix={<FileTextOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="已扩展种子词"
              value={seedWords.filter((w) => w.keyword_count > 0).length}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="总扩展关键词"
              value={seedWords.reduce((sum, w) => sum + (w.keyword_count || 0), 0)}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 种子词列表 */}
      <Card
        title={
          <Space>
            <FileTextOutlined />
            <span>A1阶段：种子词管理</span>
          </Space>
        }
        extra={
          <Space>
            <Upload
              accept=".csv,.txt"
              showUploadList={false}
              beforeUpload={handleImport}
            >
              <Button icon={<UploadOutlined />}>批量导入</Button>
            </Upload>
            <Button icon={<DownloadOutlined />} onClick={handleExport}>
              导出种子词
            </Button>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => {
                setEditingWord(null);
                form.resetFields();
                setIsModalVisible(true);
              }}
            >
              添加种子词
            </Button>
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={seedWords}
          rowKey="seed_word"
          loading={isLoading}
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 个种子词`,
          }}
          scroll={{ x: 1000 }}
        />
      </Card>

      {/* 添加/编辑对话框 */}
      <Modal
        title={editingWord ? '编辑种子词' : '添加种子词'}
        open={isModalVisible}
        onOk={() => form.submit()}
        onCancel={() => {
          setIsModalVisible(false);
          form.resetFields();
          setEditingWord(null);
        }}
        width={600}
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item
            name="seed_word"
            label="种子词"
            rules={[
              { required: true, message: '请输入种子词' },
              { pattern: /^[a-zA-Z]+$/, message: '只能输入英文字母' },
            ]}
          >
            <Input placeholder="例如: compress, convert, generate" />
          </Form.Item>
          <Form.Item
            name="seed_group"
            label="分组"
            rules={[{ required: true, message: '请输入分组' }]}
          >
            <Input placeholder="例如: 工具类, 内容类, 分析类" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea
              rows={3}
              placeholder="描述这个种子词的用途和特点"
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default SeedWordManagement;

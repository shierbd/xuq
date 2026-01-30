/**
 * [AI1.1] AI提供商管理组件
 */
import React, { useState, useEffect } from 'react';
import {
  Table,
  Button,
  Space,
  Tag,
  Modal,
  Form,
  Input,
  InputNumber,
  Switch,
  message,
  Popconfirm,
} from 'antd';
import {
  PlusOutlined,
  ReloadOutlined,
  EditOutlined,
  DeleteOutlined,
  ApiOutlined,
} from '@ant-design/icons';
import {
  getProviders,
  createProvider,
  updateProvider,
  deleteProvider,
  toggleProvider,
  testProviderConnection,
} from '../../api/ai_config';

const AIProviderManagement = () => {
  const [loading, setLoading] = useState(false);
  const [providers, setProviders] = useState([]);
  const [modalVisible, setModalVisible] = useState(false);
  const [modalTitle, setModalTitle] = useState('添加提供商');
  const [editingId, setEditingId] = useState(null);
  const [form] = Form.useForm();

  // 加载提供商列表
  const loadProviders = async () => {
    setLoading(true);
    try {
      const response = await getProviders();
      if (response.data.success) {
        setProviders(response.data.data.providers);
      }
    } catch (error) {
      message.error('加载提供商列表失败');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  // 格式化日期
  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('zh-CN');
  };

  // 添加提供商
  const handleAdd = () => {
    setModalTitle('添加提供商');
    setEditingId(null);
    form.resetFields();
    form.setFieldsValue({
      timeout: 30,
      max_retries: 3,
      is_enabled: true,
    });
    setModalVisible(true);
  };

  // 编辑提供商
  const handleEdit = (record) => {
    setModalTitle('编辑提供商');
    setEditingId(record.provider_id);
    form.setFieldsValue({
      provider_name: record.provider_name,
      api_key: '', // 不显示原密钥
      api_endpoint: record.api_endpoint,
      timeout: record.timeout,
      max_retries: record.max_retries,
      is_enabled: record.is_enabled,
    });
    setModalVisible(true);
  };

  // 提交表单
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setLoading(true);

      if (editingId) {
        // 更新
        await updateProvider(editingId, values);
        message.success('提供商更新成功');
      } else {
        // 创建
        await createProvider(values);
        message.success('提供商创建成功');
      }

      setModalVisible(false);
      await loadProviders();
    } catch (error) {
      if (error.errorFields) {
        // 表单验证错误
        return;
      }
      message.error(error.response?.data?.detail || '操作失败');
    } finally {
      setLoading(false);
    }
  };

  // 删除提供商
  const handleDelete = async (record) => {
    setLoading(true);
    try {
      await deleteProvider(record.provider_id);
      message.success('提供商删除成功');
      await loadProviders();
    } catch (error) {
      message.error(error.response?.data?.detail || '删除失败');
    } finally {
      setLoading(false);
    }
  };

  // 切换启用状态
  const handleToggle = async (record) => {
    setLoading(true);
    try {
      await toggleProvider(record.provider_id);
      message.success(`提供商已${record.is_enabled ? '禁用' : '启用'}`);
      await loadProviders();
    } catch (error) {
      message.error(error.response?.data?.detail || '操作失败');
    } finally {
      setLoading(false);
    }
  };

  // 测试连接
  const handleTest = async (record) => {
    setLoading(true);
    try {
      const response = await testProviderConnection(record.provider_id);
      if (response.data.success) {
        message.success('连接测试成功');
      } else {
        message.error(response.data.message || '连接测试失败');
      }
    } catch (error) {
      message.error(error.response?.data?.detail || '测试失败');
    } finally {
      setLoading(false);
    }
  };

  // 表格列定义
  const columns = [
    {
      title: 'ID',
      dataIndex: 'provider_id',
      key: 'provider_id',
      width: 80,
    },
    {
      title: '提供商名称',
      dataIndex: 'provider_name',
      key: 'provider_name',
      width: 150,
    },
    {
      title: 'API端点',
      dataIndex: 'api_endpoint',
      key: 'api_endpoint',
      ellipsis: true,
    },
    {
      title: '超时(秒)',
      dataIndex: 'timeout',
      key: 'timeout',
      width: 100,
    },
    {
      title: '重试次数',
      dataIndex: 'max_retries',
      key: 'max_retries',
      width: 100,
    },
    {
      title: '状态',
      dataIndex: 'is_enabled',
      key: 'is_enabled',
      width: 100,
      render: (enabled) => (
        <Tag color={enabled ? 'success' : 'default'}>
          {enabled ? '已启用' : '已禁用'}
        </Tag>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_time',
      key: 'created_time',
      width: 180,
      render: formatDate,
    },
    {
      title: '操作',
      key: 'action',
      width: 300,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Button size="small" onClick={() => handleTest(record)}>
            测试连接
          </Button>
          <Button size="small" onClick={() => handleToggle(record)}>
            {record.is_enabled ? '禁用' : '启用'}
          </Button>
          <Button
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title={`确定要删除提供商 "${record.provider_name}" 吗？`}
            onConfirm={() => handleDelete(record)}
            okText="确定"
            cancelText="取消"
          >
            <Button size="small" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  useEffect(() => {
    loadProviders();
  }, []);

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Space>
          <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
            添加提供商
          </Button>
          <Button icon={<ReloadOutlined />} onClick={loadProviders}>
            刷新
          </Button>
        </Space>
      </div>

      <Table
        loading={loading}
        dataSource={providers}
        columns={columns}
        rowKey="provider_id"
        scroll={{ x: 1200 }}
        pagination={{
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 条`,
        }}
      />

      <Modal
        title={modalTitle}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        width={600}
        confirmLoading={loading}
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            timeout: 30,
            max_retries: 3,
            is_enabled: true,
          }}
        >
          <Form.Item
            label="提供商名称"
            name="provider_name"
            rules={[{ required: true, message: '请输入提供商名称' }]}
          >
            <Input placeholder="例如: Claude, DeepSeek" />
          </Form.Item>

          <Form.Item
            label="API密钥"
            name="api_key"
            rules={[{ required: !editingId, message: '请输入API密钥' }]}
          >
            <Input.Password placeholder="输入API密钥" />
          </Form.Item>

          <Form.Item
            label="API端点"
            name="api_endpoint"
            rules={[
              { required: true, message: '请输入API端点' },
              { type: 'url', message: '请输入有效的URL' },
            ]}
          >
            <Input placeholder="https://api.example.com" />
          </Form.Item>

          <Form.Item
            label="超时时间(秒)"
            name="timeout"
            rules={[{ required: true, message: '请输入超时时间' }]}
          >
            <InputNumber min={1} max={300} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            label="最大重试次数"
            name="max_retries"
            rules={[{ required: true, message: '请输入最大重试次数' }]}
          >
            <InputNumber min={0} max={10} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item label="启用状态" name="is_enabled" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default AIProviderManagement;

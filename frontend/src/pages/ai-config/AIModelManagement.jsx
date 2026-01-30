/**
 * [AI1.2] AI模型管理组件
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
  Select,
  Slider,
  message,
  Popconfirm,
} from 'antd';
import {
  PlusOutlined,
  ReloadOutlined,
  EditOutlined,
  DeleteOutlined,
  StarOutlined,
  StarFilled,
} from '@ant-design/icons';
import {
  getModels,
  createModel,
  updateModel,
  deleteModel,
  toggleModel,
  setDefaultModel,
  getProviders,
} from '../../api/ai_config';

const AIModelManagement = () => {
  const [loading, setLoading] = useState(false);
  const [models, setModels] = useState([]);
  const [providers, setProviders] = useState([]);
  const [filterProviderId, setFilterProviderId] = useState(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [modalTitle, setModalTitle] = useState('添加模型');
  const [editingId, setEditingId] = useState(null);
  const [form] = Form.useForm();

  // 能力标签选项
  const capabilityOptions = [
    { label: '翻译', value: 'translation' },
    { label: '分析', value: 'analysis' },
    { label: '生成', value: 'generation' },
    { label: '对话', value: 'conversation' },
    { label: '代码', value: 'code' },
    { label: '图像', value: 'image' },
  ];

  // 加载提供商列表
  const loadProviders = async () => {
    try {
      const response = await getProviders();
      if (response.data.success) {
        setProviders(response.data.data.providers);
      }
    } catch (error) {
      console.error('加载提供商列表失败', error);
    }
  };

  // 加载模型列表
  const loadModels = async () => {
    setLoading(true);
    try {
      const params = {};
      if (filterProviderId) {
        params.provider_id = filterProviderId;
      }
      const response = await getModels(params);
      if (response.data.success) {
        setModels(response.data.data.models);
      }
    } catch (error) {
      message.error('加载模型列表失败');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  // 解析能力标签
  const parseCapabilities = (capabilities) => {
    if (!capabilities || capabilities.length === 0) return [];
    return capabilities;
  };

  // 添加模型
  const handleAdd = () => {
    setModalTitle('添加模型');
    setEditingId(null);
    form.resetFields();
    form.setFieldsValue({
      temperature: 0.7,
      max_tokens: 4096,
      is_default: false,
      is_enabled: true,
    });
    setModalVisible(true);
  };

  // 编辑模型
  const handleEdit = (record) => {
    setModalTitle('编辑模型');
    setEditingId(record.model_id);
    form.setFieldsValue({
      provider_id: record.provider_id,
      model_name: record.model_name,
      model_version: record.model_version || '',
      temperature: record.temperature,
      max_tokens: record.max_tokens,
      input_price: record.input_price,
      output_price: record.output_price,
      capabilities: parseCapabilities(record.capabilities),
      is_default: record.is_default,
      is_enabled: record.is_enabled,
    });
    setModalVisible(true);
  };

  // 提交表单
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setLoading(true);

      // 处理能力标签
      const submitData = {
        ...values,
        capabilities: values.capabilities && values.capabilities.length > 0
          ? values.capabilities
          : null,
      };

      if (editingId) {
        // 更新
        await updateModel(editingId, submitData);
        message.success('模型更新成功');
      } else {
        // 创建
        await createModel(submitData);
        message.success('模型创建成功');
      }

      setModalVisible(false);
      await loadModels();
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

  // 删除模型
  const handleDelete = async (record) => {
    setLoading(true);
    try {
      await deleteModel(record.model_id);
      message.success('模型删除成功');
      await loadModels();
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
      await toggleModel(record.model_id);
      message.success(`模型已${record.is_enabled ? '禁用' : '启用'}`);
      await loadModels();
    } catch (error) {
      message.error(error.response?.data?.detail || '操作失败');
    } finally {
      setLoading(false);
    }
  };

  // 设置默认模型
  const handleSetDefault = async (record) => {
    setLoading(true);
    try {
      await setDefaultModel(record.model_id);
      message.success('默认模型设置成功');
      await loadModels();
    } catch (error) {
      message.error(error.response?.data?.detail || '设置失败');
    } finally {
      setLoading(false);
    }
  };

  // 获取提供商名称
  const getProviderName = (providerId) => {
    const provider = providers.find(p => p.provider_id === providerId);
    return provider ? provider.provider_name : providerId;
  };

  // 表格列定义
  const columns = [
    {
      title: 'ID',
      dataIndex: 'model_id',
      key: 'model_id',
      width: 80,
    },
    {
      title: '提供商',
      dataIndex: 'provider_id',
      key: 'provider_id',
      width: 120,
      render: (providerId) => getProviderName(providerId),
    },
    {
      title: '模型名称',
      dataIndex: 'model_name',
      key: 'model_name',
      width: 200,
      ellipsis: true,
    },
    {
      title: '版本',
      dataIndex: 'model_version',
      key: 'model_version',
      width: 120,
    },
    {
      title: '温度',
      dataIndex: 'temperature',
      key: 'temperature',
      width: 80,
    },
    {
      title: '最大Token',
      dataIndex: 'max_tokens',
      key: 'max_tokens',
      width: 120,
    },
    {
      title: '价格($/1M tokens)',
      key: 'price',
      width: 180,
      render: (_, record) => (
        <div>
          <div>输入: {record.input_price || 'N/A'}</div>
          <div>输出: {record.output_price || 'N/A'}</div>
        </div>
      ),
    },
    {
      title: '能力标签',
      dataIndex: 'capabilities',
      key: 'capabilities',
      width: 200,
      render: (capabilities) => (
        <>
          {parseCapabilities(capabilities).map((cap) => (
            <Tag key={cap} size="small" style={{ marginBottom: 4 }}>
              {cap}
            </Tag>
          ))}
        </>
      ),
    },
    {
      title: '状态',
      key: 'status',
      width: 120,
      render: (_, record) => (
        <Space direction="vertical" size="small">
          {record.is_default && (
            <Tag color="warning" icon={<StarFilled />}>
              默认
            </Tag>
          )}
          <Tag color={record.is_enabled ? 'success' : 'default'}>
            {record.is_enabled ? '已启用' : '已禁用'}
          </Tag>
        </Space>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 300,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small" wrap>
          {!record.is_default && (
            <Button
              size="small"
              icon={<StarOutlined />}
              onClick={() => handleSetDefault(record)}
            >
              设为默认
            </Button>
          )}
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
            title={`确定要删除模型 "${record.model_name}" 吗？`}
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
    loadModels();
  }, []);

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Space>
          <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
            添加模型
          </Button>
          <Button icon={<ReloadOutlined />} onClick={loadModels}>
            刷新
          </Button>
          <Select
            placeholder="筛选提供商"
            allowClear
            style={{ width: 200 }}
            value={filterProviderId}
            onChange={(value) => {
              setFilterProviderId(value);
              loadModels();
            }}
          >
            {providers.map((provider) => (
              <Select.Option key={provider.provider_id} value={provider.provider_id}>
                {provider.provider_name}
              </Select.Option>
            ))}
          </Select>
        </Space>
      </div>

      <Table
        loading={loading}
        dataSource={models}
        columns={columns}
        rowKey="model_id"
        scroll={{ x: 1600 }}
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
        width={700}
        confirmLoading={loading}
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            temperature: 0.7,
            max_tokens: 4096,
            is_default: false,
            is_enabled: true,
          }}
        >
          <Form.Item
            label="提供商"
            name="provider_id"
            rules={[{ required: true, message: '请选择提供商' }]}
          >
            <Select placeholder="选择提供商">
              {providers.map((provider) => (
                <Select.Option key={provider.provider_id} value={provider.provider_id}>
                  {provider.provider_name}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            label="模型名称"
            name="model_name"
            rules={[{ required: true, message: '请输入模型名称' }]}
          >
            <Input placeholder="例如: claude-3-5-sonnet-20241022" />
          </Form.Item>

          <Form.Item label="模型版本" name="model_version">
            <Input placeholder="例如: v1.0" />
          </Form.Item>

          <Form.Item
            label="温度参数"
            name="temperature"
            rules={[{ required: true, message: '请设置温度参数' }]}
          >
            <Slider min={0} max={2} step={0.1} marks={{ 0: '0', 1: '1', 2: '2' }} />
          </Form.Item>

          <Form.Item
            label="最大Token数"
            name="max_tokens"
            rules={[{ required: true, message: '请输入最大Token数' }]}
          >
            <InputNumber min={1} max={200000} step={1024} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item label="输入价格 ($/1M tokens)" name="input_price">
            <InputNumber
              min={0}
              precision={2}
              step={0.01}
              style={{ width: '100%' }}
              placeholder="例如: 3.00"
            />
          </Form.Item>

          <Form.Item label="输出价格 ($/1M tokens)" name="output_price">
            <InputNumber
              min={0}
              precision={2}
              step={0.01}
              style={{ width: '100%' }}
              placeholder="例如: 15.00"
            />
          </Form.Item>

          <Form.Item label="能力标签" name="capabilities">
            <Select
              mode="multiple"
              placeholder="选择能力标签"
              options={capabilityOptions}
            />
          </Form.Item>

          <Form.Item label="设为默认" name="is_default" valuePropName="checked">
            <Switch />
          </Form.Item>

          <Form.Item label="启用状态" name="is_enabled" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default AIModelManagement;

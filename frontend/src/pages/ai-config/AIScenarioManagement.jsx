/**
 * [AI1.3] AI场景管理组件
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
  Switch,
  Select,
  message,
  Popconfirm,
  Tooltip,
} from 'antd';
import {
  PlusOutlined,
  ReloadOutlined,
  EditOutlined,
  DeleteOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';
import {
  getScenarios,
  createScenario,
  updateScenario,
  deleteScenario,
  toggleScenario,
  getScenarioWithModels,
  getModels,
} from '../../api/ai_config';

const { TextArea } = Input;

const AIScenarioManagement = () => {
  const [loading, setLoading] = useState(false);
  const [scenarios, setScenarios] = useState([]);
  const [models, setModels] = useState([]);
  const [modalVisible, setModalVisible] = useState(false);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [modalTitle, setModalTitle] = useState('添加场景');
  const [editingId, setEditingId] = useState(null);
  const [scenarioDetail, setScenarioDetail] = useState(null);
  const [form] = Form.useForm();

  // 加载模型列表
  const loadModels = async () => {
    try {
      const response = await getModels({ is_enabled: true });
      if (response.data.success) {
        setModels(response.data.data.models);
      }
    } catch (error) {
      console.error('加载模型列表失败', error);
    }
  };

  // 加载场景列表
  const loadScenarios = async () => {
    setLoading(true);
    try {
      const response = await getScenarios();
      if (response.data.success) {
        setScenarios(response.data.data.scenarios);
      }
    } catch (error) {
      message.error('加载场景列表失败');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  // 查看场景详情
  const handleViewDetail = async (record) => {
    setLoading(true);
    try {
      const response = await getScenarioWithModels(record.scenario_id);
      if (response.data.success) {
        setScenarioDetail(response.data.data);
        setDetailModalVisible(true);
      }
    } catch (error) {
      message.error('获取场景详情失败');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  // 添加场景
  const handleAdd = () => {
    setModalTitle('添加场景');
    setEditingId(null);
    form.resetFields();
    form.setFieldsValue({
      is_enabled: true,
    });
    setModalVisible(true);
  };

  // 编辑场景
  const handleEdit = (record) => {
    setModalTitle('编辑场景');
    setEditingId(record.scenario_id);
    form.setFieldsValue({
      scenario_name: record.scenario_name,
      scenario_desc: record.scenario_desc || '',
      primary_model_id: record.primary_model_id,
      fallback_model_id: record.fallback_model_id,
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
        await updateScenario(editingId, values);
        message.success('场景更新成功');
      } else {
        // 创建
        await createScenario(values);
        message.success('场景创建成功');
      }

      setModalVisible(false);
      await loadScenarios();
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

  // 删除场景
  const handleDelete = async (record) => {
    setLoading(true);
    try {
      await deleteScenario(record.scenario_id);
      message.success('场景删除成功');
      await loadScenarios();
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
      await toggleScenario(record.scenario_id);
      message.success(`场景已${record.is_enabled ? '禁用' : '启用'}`);
      await loadScenarios();
    } catch (error) {
      message.error(error.response?.data?.detail || '操作失败');
    } finally {
      setLoading(false);
    }
  };

  // 获取模型名称
  const getModelName = (modelId) => {
    const model = models.find(m => m.model_id === modelId);
    return model ? model.model_name : modelId;
  };

  // 表格列定义
  const columns = [
    {
      title: 'ID',
      dataIndex: 'scenario_id',
      key: 'scenario_id',
      width: 80,
    },
    {
      title: '场景名称',
      dataIndex: 'scenario_name',
      key: 'scenario_name',
      width: 200,
      ellipsis: true,
    },
    {
      title: '场景描述',
      dataIndex: 'scenario_desc',
      key: 'scenario_desc',
      width: 250,
      ellipsis: true,
      render: (text) => text || '-',
    },
    {
      title: '主模型',
      dataIndex: 'primary_model_id',
      key: 'primary_model_id',
      width: 200,
      ellipsis: true,
      render: (modelId) => (
        <Tag color="blue">{getModelName(modelId)}</Tag>
      ),
    },
    {
      title: '回退模型',
      dataIndex: 'fallback_model_id',
      key: 'fallback_model_id',
      width: 200,
      ellipsis: true,
      render: (modelId) => modelId ? (
        <Tag color="orange">{getModelName(modelId)}</Tag>
      ) : '-',
    },
    {
      title: '状态',
      key: 'status',
      width: 100,
      render: (_, record) => (
        <Tag color={record.is_enabled ? 'success' : 'default'}>
          {record.is_enabled ? '已启用' : '已禁用'}
        </Tag>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_time',
      key: 'created_time',
      width: 180,
      render: (time) => new Date(time).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'action',
      width: 300,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small" wrap>
          <Button
            size="small"
            icon={<InfoCircleOutlined />}
            onClick={() => handleViewDetail(record)}
          >
            详情
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
            title={`确定要删除场景 "${record.scenario_name}" 吗？`}
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
    loadModels();
    loadScenarios();
  }, []);

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Space>
          <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
            添加场景
          </Button>
          <Button icon={<ReloadOutlined />} onClick={loadScenarios}>
            刷新
          </Button>
        </Space>
      </div>

      <Table
        loading={loading}
        dataSource={scenarios}
        columns={columns}
        rowKey="scenario_id"
        scroll={{ x: 1400 }}
        pagination={{
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 条`,
        }}
      />

      {/* 添加/编辑场景模态框 */}
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
            is_enabled: true,
          }}
        >
          <Form.Item
            label="场景名称"
            name="scenario_name"
            rules={[{ required: true, message: '请输入场景名称' }]}
          >
            <Input placeholder="例如: 类别名称生成" />
          </Form.Item>

          <Form.Item
            label="场景描述"
            name="scenario_desc"
          >
            <TextArea
              rows={3}
              placeholder="描述该场景的用途和特点"
            />
          </Form.Item>

          <Form.Item
            label={
              <span>
                主模型
                <Tooltip title="该场景优先使用的AI模型">
                  <InfoCircleOutlined style={{ marginLeft: 4, color: '#999' }} />
                </Tooltip>
              </span>
            }
            name="primary_model_id"
            rules={[{ required: true, message: '请选择主模型' }]}
          >
            <Select placeholder="选择主模型" showSearch optionFilterProp="children">
              {models.map((model) => (
                <Select.Option key={model.model_id} value={model.model_id}>
                  {model.model_name}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            label={
              <span>
                回退模型
                <Tooltip title="当主模型不可用时使用的备用模型">
                  <InfoCircleOutlined style={{ marginLeft: 4, color: '#999' }} />
                </Tooltip>
              </span>
            }
            name="fallback_model_id"
          >
            <Select placeholder="选择回退模型（可选）" allowClear showSearch optionFilterProp="children">
              {models.map((model) => (
                <Select.Option key={model.model_id} value={model.model_id}>
                  {model.model_name}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item label="启用状态" name="is_enabled" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Form>
      </Modal>

      {/* 场景详情模态框 */}
      <Modal
        title="场景详情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setDetailModalVisible(false)}>
            关闭
          </Button>,
        ]}
        width={700}
      >
        {scenarioDetail && (
          <div>
            <div style={{ marginBottom: 16 }}>
              <strong>场景名称：</strong>{scenarioDetail.scenario_name}
            </div>
            <div style={{ marginBottom: 16 }}>
              <strong>场景描述：</strong>{scenarioDetail.scenario_desc || '-'}
            </div>
            <div style={{ marginBottom: 16 }}>
              <strong>状态：</strong>
              <Tag color={scenarioDetail.is_enabled ? 'success' : 'default'}>
                {scenarioDetail.is_enabled ? '已启用' : '已禁用'}
              </Tag>
            </div>
            <div style={{ marginBottom: 16 }}>
              <strong>主模型：</strong>
              {scenarioDetail.primary_model && (
                <div style={{ marginLeft: 20, marginTop: 8 }}>
                  <div>模型名称：{scenarioDetail.primary_model.model_name}</div>
                  <div>模型ID：{scenarioDetail.primary_model.model_id}</div>
                  <div>提供商ID：{scenarioDetail.primary_model.provider_id}</div>
                </div>
              )}
            </div>
            <div style={{ marginBottom: 16 }}>
              <strong>回退模型：</strong>
              {scenarioDetail.fallback_model ? (
                <div style={{ marginLeft: 20, marginTop: 8 }}>
                  <div>模型名称：{scenarioDetail.fallback_model.model_name}</div>
                  <div>模型ID：{scenarioDetail.fallback_model.model_id}</div>
                  <div>提供商ID：{scenarioDetail.fallback_model.provider_id}</div>
                </div>
              ) : '-'}
            </div>
            <div style={{ marginBottom: 16 }}>
              <strong>自定义参数：</strong>
              {scenarioDetail.custom_params ? (
                <pre style={{ background: '#f5f5f5', padding: 8, borderRadius: 4 }}>
                  {JSON.stringify(scenarioDetail.custom_params, null, 2)}
                </pre>
              ) : '-'}
            </div>
            <div>
              <strong>创建时间：</strong>{scenarioDetail.created_time}
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default AIScenarioManagement;

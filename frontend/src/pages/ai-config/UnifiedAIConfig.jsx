/**
 * 统一AI配置页面 - 简单但完整
 * 用户可以：
 * 1. 选择大模型 + 填写密钥
 * 2. 查看已配置的模型
 * 3. 配置使用场景（可选）
 */
import React, { useState, useEffect } from 'react';
import { Card, Form, Select, Input, Button, message, Space, Alert, Tag, Divider, Collapse, Switch, Table, Modal } from 'antd';
import { SaveOutlined, CheckCircleOutlined, CloseCircleOutlined, SettingOutlined, ApiOutlined, EditOutlined } from '@ant-design/icons';
import { getProviders, createProvider, updateProvider, getModels, createModel, getScenarios, createScenario, updateScenario, getActivePrompt, createPrompt, updatePrompt } from '../../api/ai_config';

const { Option } = Select;
const { Panel } = Collapse;

// 预设的大模型配置
const PRESET_MODELS = [
  {
    id: 'deepseek-chat',
    name: 'DeepSeek Chat',
    provider: 'DeepSeek',
    description: '高性价比，支持中文，推荐日常使用',
    apiEndpoint: 'https://api.deepseek.com',
    envKey: 'DEEPSEEK_API_KEY',
    price: '输入: $0.14/M, 输出: $0.28/M',
    recommended: true,
  },
  {
    id: 'claude-sonnet',
    name: 'Claude 3.5 Sonnet',
    provider: 'Claude',
    description: '最新最强模型，质量最高，适合重要任务',
    apiEndpoint: 'https://api.anthropic.com',
    envKey: 'CLAUDE_API_KEY',
    price: '输入: $3/M, 输出: $15/M',
    recommended: true,
  },
  {
    id: 'gpt-4o',
    name: 'GPT-4o',
    provider: 'OpenAI',
    description: '最新多模态模型，功能强大',
    apiEndpoint: 'https://api.openai.com',
    envKey: 'OPENAI_API_KEY',
    price: '输入: $2.5/M, 输出: $10/M',
    recommended: false,
  },
  {
    id: 'gpt-4o-mini',
    name: 'GPT-4o Mini',
    provider: 'OpenAI',
    description: '快速、低成本，适合快速测试',
    apiEndpoint: 'https://api.openai.com',
    envKey: 'OPENAI_API_KEY',
    price: '输入: $0.15/M, 输出: $0.6/M',
    recommended: false,
  },
  {
    id: 'gemini-pro',
    name: 'Gemini 1.5 Pro',
    provider: 'Gemini',
    description: '长上下文支持，适合处理大量文本',
    apiEndpoint: 'https://generativelanguage.googleapis.com',
    envKey: 'GEMINI_API_KEY',
    price: '输入: $1.25/M, 输出: $5/M',
    recommended: false,
  },
];

// 预设的使用场景
const PRESET_SCENARIOS = [
  {
    name: '类别名称生成',
    description: '为聚类簇生成简洁的类别名称（2-4个单词）',
    defaultModel: 'DeepSeek',
    params: { temperature: 0.3, max_tokens: 50 },
  },
  {
    name: '需求分析',
    description: '分析商品簇，识别用户需求、目标用户、使用场景',
    defaultModel: 'DeepSeek',
    params: { temperature: 0.5, max_tokens: 500 },
  },
  {
    name: '交付产品识别',
    description: '识别商品的交付类型、格式和平台',
    defaultModel: 'DeepSeek',
    params: { temperature: 0.3, max_tokens: 200 },
  },
];

const UnifiedAIConfig = () => {
  const [form] = Form.useForm();
  const [promptForm] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [selectedModel, setSelectedModel] = useState(null);
  const [configuredProviders, setConfiguredProviders] = useState([]);
  const [scenarios, setScenarios] = useState([]);
  const [promptModalVisible, setPromptModalVisible] = useState(false);
  const [currentScenario, setCurrentScenario] = useState(null);
  const [currentPrompt, setCurrentPrompt] = useState(null);

  // 加载已配置的提供商和场景
  useEffect(() => {
    loadConfiguredProviders();
    loadScenarios();
  }, []);

  const loadConfiguredProviders = async () => {
    try {
      const response = await getProviders();
      if (response.success) {
        setConfiguredProviders(response.data.providers || []);
      }
    } catch (error) {
      console.error('加载配置失败:', error);
    }
  };

  const loadScenarios = async () => {
    try {
      const response = await getScenarios();
      if (response.success) {
        setScenarios(response.data.scenarios || []);
      }
    } catch (error) {
      console.error('加载场景失败:', error);
    }
  };

  // 处理模型选择
  const handleModelChange = (modelId) => {
    const model = PRESET_MODELS.find(m => m.id === modelId);
    setSelectedModel(model);

    // 检查是否已配置
    const existingProvider = configuredProviders.find(
      p => p.provider_name === model.provider
    );

    if (existingProvider) {
      form.setFieldsValue({
        apiKey: '********',
      });
    } else {
      form.setFieldsValue({
        apiKey: '',
      });
    }
  };

  // 保存配置
  const handleSave = async (values) => {
    if (!selectedModel) {
      message.error('请先选择一个大模型');
      return;
    }

    setLoading(true);
    try {
      const existingProvider = configuredProviders.find(
        p => p.provider_name === selectedModel.provider
      );

      const providerData = {
        provider_name: selectedModel.provider,
        api_key: values.apiKey,
        api_endpoint: selectedModel.apiEndpoint,
        timeout: 60,
        max_retries: 3,
        is_enabled: true,
      };

      if (existingProvider) {
        await updateProvider(existingProvider.provider_id, providerData);
        message.success(`${selectedModel.name} 配置已更新！`);
      } else {
        await createProvider(providerData);
        message.success(`${selectedModel.name} 配置成功！`);
      }

      await loadConfiguredProviders();
      form.resetFields();
      setSelectedModel(null);
    } catch (error) {
      console.error('保存失败:', error);
      message.error('保存失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  // 一键配置场景
  const handleAutoConfigureScenarios = async () => {
    if (configuredProviders.length === 0) {
      message.warning('请先配置至少一个大模型');
      return;
    }

    setLoading(true);
    try {
      let successCount = 0;

      // 先获取所有已有的模型
      const modelsResponse = await getModels();
      const existingModels = modelsResponse.data.models || [];

      for (const scenario of PRESET_SCENARIOS) {
        // 查找对应的提供商
        const provider = configuredProviders.find(
          p => p.provider_name === scenario.defaultModel
        );

        if (provider) {
          // 检查场景是否已存在
          const existingScenario = scenarios.find(s => s.scenario_name === scenario.name);

          if (!existingScenario) {
            try {
              // 查找或创建对应的模型
              let model = existingModels.find(m => m.provider_id === provider.provider_id);

              if (!model) {
                // 创建模型
                const modelResponse = await createModel({
                  provider_id: provider.provider_id,
                  model_name: scenario.defaultModel === 'DeepSeek' ? 'deepseek-chat' : 'default-model',
                  temperature: scenario.params.temperature,
                  max_tokens: scenario.params.max_tokens,
                  is_enabled: true,
                });
                model = modelResponse.data;
              }

              // 创建场景
              await createScenario({
                scenario_name: scenario.name,
                scenario_desc: scenario.description,
                primary_model_id: model.model_id,
                custom_params: scenario.params,
                is_enabled: true,
              });
              successCount++;
            } catch (error) {
              console.error(`创建场景 ${scenario.name} 失败:`, error);
            }
          }
        }
      }

      if (successCount > 0) {
        message.success(`成功配置 ${successCount} 个使用场景！`);
        await loadScenarios();
      } else {
        message.info('所有场景已配置');
      }
    } catch (error) {
      console.error('配置场景失败:', error);
      message.error('配置场景失败');
    } finally {
      setLoading(false);
    }
  };

  // 打开提示词编辑弹窗
  const handleEditPrompt = async (scenario) => {
    setCurrentScenario(scenario);
    setPromptModalVisible(true);
    setLoading(true);

    try {
      // 获取该场景的激活提示词
      const response = await getActivePrompt(scenario.scenario_id);
      // apiClient已经返回了response.data，所以直接访问response.success和response.data
      if (response && response.success && response.data) {
        setCurrentPrompt(response.data);
        promptForm.setFieldsValue({
          prompt_name: response.data.prompt_name,
          prompt_template: response.data.prompt_template,
        });
      } else {
        // 没有提示词，设置默认值
        setCurrentPrompt(null);
        promptForm.setFieldsValue({
          prompt_name: `${scenario.scenario_name}提示词`,
          prompt_template: '',
        });
      }
    } catch (error) {
      console.error('加载提示词失败:', error);
      message.error('加载提示词失败');
      // 设置默认值
      setCurrentPrompt(null);
      promptForm.setFieldsValue({
        prompt_name: `${scenario.scenario_name}提示词`,
        prompt_template: '',
      });
    } finally {
      setLoading(false);
    }
  };

  // 保存提示词
  const handleSavePrompt = async (values) => {
    if (!currentScenario) return;

    setLoading(true);
    try {
      if (currentPrompt) {
        // 更新现有提示词
        await updatePrompt(currentPrompt.prompt_id, {
          prompt_name: values.prompt_name,
          prompt_template: values.prompt_template,
        });
        message.success('提示词更新成功！');
      } else {
        // 创建新提示词
        await createPrompt({
          scenario_id: currentScenario.scenario_id,
          prompt_name: values.prompt_name,
          prompt_template: values.prompt_template,
          is_active: true,
        });
        message.success('提示词创建成功！');
      }

      setPromptModalVisible(false);
      promptForm.resetFields();
      setCurrentScenario(null);
      setCurrentPrompt(null);
    } catch (error) {
      console.error('保存提示词失败:', error);
      message.error('保存提示词失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  // 关闭提示词弹窗
  const handleClosePromptModal = () => {
    setPromptModalVisible(false);
    promptForm.resetFields();
    setCurrentScenario(null);
    setCurrentPrompt(null);
  };

  // 检查模型是否已配置
  const isModelConfigured = (model) => {
    return configuredProviders.some(p => p.provider_name === model.provider && p.is_enabled);
  };

  // 已配置模型的表格列
  const providerColumns = [
    {
      title: '大模型',
      dataIndex: 'provider_name',
      key: 'provider_name',
      render: (name) => {
        const model = PRESET_MODELS.find(m => m.provider === name);
        return (
          <div>
            <strong>{model?.name || name}</strong>
            {model?.recommended && <Tag color="green" style={{ marginLeft: 8 }}>推荐</Tag>}
          </div>
        );
      },
    },
    {
      title: '状态',
      dataIndex: 'is_enabled',
      key: 'is_enabled',
      render: (enabled) => (
        <Tag color={enabled ? 'success' : 'default'}>
          {enabled ? <><CheckCircleOutlined /> 已启用</> : <><CloseCircleOutlined /> 已禁用</>}
        </Tag>
      ),
    },
    {
      title: '配置时间',
      dataIndex: 'created_time',
      key: 'created_time',
      render: (time) => new Date(time).toLocaleString('zh-CN'),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Card
        title={
          <div>
            <h2 style={{ margin: 0, fontSize: '20px' }}>
              <ApiOutlined /> AI大模型配置
            </h2>
            <p style={{ margin: '8px 0 0 0', color: '#999', fontSize: '14px' }}>
              简单配置，一键使用 - 选择大模型，填写密钥，开始使用AI功能
            </p>
          </div>
        }
        bordered={false}
      >
        {/* 步骤说明 */}
        <Alert
          message="配置步骤"
          description={
            <div>
              <p style={{ margin: '8px 0' }}>
                <strong>第1步</strong>：选择一个大模型（推荐 DeepSeek 或 Claude）
              </p>
              <p style={{ margin: '8px 0' }}>
                <strong>第2步</strong>：填写API密钥并保存
              </p>
              <p style={{ margin: '8px 0 0 0', color: '#999' }}>
                💡 配置后系统会自动使用该模型进行AI分析
              </p>
            </div>
          }
          type="info"
          showIcon
          style={{ marginBottom: 24 }}
        />

        {/* 配置表单 */}
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSave}
        >
          <Form.Item
            label={<span style={{ fontSize: '16px', fontWeight: 500 }}>选择大模型</span>}
            name="model"
            rules={[{ required: true, message: '请选择一个大模型' }]}
          >
            <Select
              placeholder="请选择一个大模型"
              size="large"
              onChange={handleModelChange}
              style={{ width: '100%' }}
            >
              {PRESET_MODELS.map(model => (
                <Option key={model.id} value={model.id}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div>
                      <strong>{model.name}</strong>
                      {model.recommended && <Tag color="green" style={{ marginLeft: 8 }}>推荐</Tag>}
                      {isModelConfigured(model) && <Tag color="blue" style={{ marginLeft: 8 }}>已配置</Tag>}
                    </div>
                  </div>
                </Option>
              ))}
            </Select>
          </Form.Item>

          {selectedModel && (
            <Card size="small" style={{ marginBottom: 24, backgroundColor: '#f5f5f5' }}>
              <div style={{ marginBottom: 12 }}>
                <strong style={{ fontSize: '16px' }}>{selectedModel.name}</strong>
                {selectedModel.recommended && <Tag color="green" style={{ marginLeft: 8 }}>推荐使用</Tag>}
                {isModelConfigured(selectedModel) && (
                  <Tag color="blue" style={{ marginLeft: 8 }}>
                    <CheckCircleOutlined /> 已配置
                  </Tag>
                )}
              </div>
              <p style={{ margin: '8px 0', color: '#666' }}>{selectedModel.description}</p>
              <p style={{ margin: '8px 0', color: '#999', fontSize: '13px' }}>
                💰 价格：{selectedModel.price}
              </p>
            </Card>
          )}

          <Form.Item
            label={<span style={{ fontSize: '16px', fontWeight: 500 }}>API密钥</span>}
            name="apiKey"
            rules={[
              { required: true, message: '请填写API密钥' },
              { min: 10, message: 'API密钥长度至少10个字符' },
            ]}
          >
            <Input.Password
              placeholder="请输入API密钥，例如：sk-xxx..."
              size="large"
              disabled={!selectedModel}
            />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              size="large"
              icon={<SaveOutlined />}
              loading={loading}
              disabled={!selectedModel}
              block
            >
              保存配置
            </Button>
          </Form.Item>
        </Form>

        {/* 已配置的模型 */}
        {configuredProviders.length > 0 && (
          <>
            <Divider />
            <div>
              <h3 style={{ marginBottom: 16 }}>
                <CheckCircleOutlined style={{ color: '#52c41a' }} /> 已配置的大模型
              </h3>
              <Table
                dataSource={configuredProviders}
                columns={providerColumns}
                rowKey="provider_id"
                pagination={false}
                size="small"
              />
            </div>
          </>
        )}

        {/* 高级配置（可折叠） */}
        <Divider />
        <Collapse ghost>
          <Panel
            header={
              <div>
                <SettingOutlined /> 高级配置（可选）
                <span style={{ marginLeft: 8, color: '#999', fontSize: '13px' }}>
                  配置使用场景，让不同功能使用不同的模型
                </span>
              </div>
            }
            key="advanced"
          >
            <Alert
              message="什么是使用场景？"
              description={
                <div>
                  <p style={{ margin: '8px 0' }}>
                    使用场景可以让不同的功能使用不同的模型。例如：
                  </p>
                  <ul style={{ margin: '8px 0', paddingLeft: 20 }}>
                    <li>类别名称生成：使用 DeepSeek（便宜）</li>
                    <li>需求分析：使用 Claude（质量高）</li>
                    <li>交付识别：使用 GPT-4o Mini（快速）</li>
                  </ul>
                  <p style={{ margin: '8px 0 0 0', color: '#999' }}>
                    💡 如果不配置，系统会使用默认模型
                  </p>
                </div>
              }
              type="info"
              showIcon
              style={{ marginBottom: 16 }}
            />

            <Button
              type="primary"
              icon={<SettingOutlined />}
              onClick={handleAutoConfigureScenarios}
              loading={loading}
              disabled={configuredProviders.length === 0}
              block
            >
              一键配置使用场景（推荐）
            </Button>

            {scenarios.length > 0 && (
              <div style={{ marginTop: 16 }}>
                <h4>已配置的场景：</h4>
                <Space direction="vertical" style={{ width: '100%' }}>
                  {scenarios.map(scenario => (
                    <Card key={scenario.scenario_id} size="small">
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div style={{ flex: 1 }}>
                          <strong>{scenario.scenario_name}</strong>
                          <p style={{ margin: '4px 0 0 0', color: '#999', fontSize: '13px' }}>
                            {scenario.scenario_desc}
                          </p>
                        </div>
                        <Space>
                          <Button
                            type="link"
                            icon={<EditOutlined />}
                            onClick={() => handleEditPrompt(scenario)}
                            size="small"
                          >
                            配置提示词
                          </Button>
                          <Tag color={scenario.is_enabled ? 'success' : 'default'}>
                            {scenario.is_enabled ? '已启用' : '已禁用'}
                          </Tag>
                        </Space>
                      </div>
                    </Card>
                  ))}
                </Space>
              </div>
            )}
          </Panel>
        </Collapse>

        {/* 提示词编辑弹窗 */}
        <Modal
          title={`配置提示词 - ${currentScenario?.scenario_name || ''}`}
          open={promptModalVisible}
          onCancel={handleClosePromptModal}
          footer={null}
          width={800}
        >
          <Alert
            message="提示词说明"
            description={
              <div>
                <p style={{ margin: '8px 0' }}>
                  提示词是发送给AI的指令模板，用于指导AI如何处理任务。
                </p>
                <p style={{ margin: '8px 0' }}>
                  您可以使用变量（如 {'{'}keyword{'}'}, {'{'}description{'}'}）来动态替换内容。
                </p>
                <p style={{ margin: '8px 0 0 0', color: '#999' }}>
                  💡 提示：清晰、具体的提示词能获得更好的AI输出结果
                </p>
              </div>
            }
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />

          <Form
            form={promptForm}
            layout="vertical"
            onFinish={handleSavePrompt}
          >
            <Form.Item
              label="提示词名称"
              name="prompt_name"
              rules={[{ required: true, message: '请输入提示词名称' }]}
            >
              <Input placeholder="例如：类别名称生成提示词" />
            </Form.Item>

            <Form.Item
              label="提示词模板"
              name="prompt_template"
              rules={[
                { required: true, message: '请输入提示词模板' },
                { min: 10, message: '提示词至少10个字符' }
              ]}
            >
              <Input.TextArea
                rows={10}
                placeholder={`请输入提示词模板，例如：

你是一个专业的产品分类专家。请根据以下关键词生成一个简洁的类别名称（2-4个单词）。

关键词：{keywords}

要求：
1. 名称要简洁明了
2. 能准确概括关键词的共同特征
3. 使用英文
4. 只返回类别名称，不要其他内容`}
                style={{ fontFamily: 'monospace' }}
              />
            </Form.Item>

            <Form.Item>
              <Space>
                <Button type="primary" htmlType="submit" loading={loading} icon={<SaveOutlined />}>
                  保存提示词
                </Button>
                <Button onClick={handleClosePromptModal}>
                  取消
                </Button>
              </Space>
            </Form.Item>
          </Form>
        </Modal>
      </Card>
    </div>
  );
};

export default UnifiedAIConfig;

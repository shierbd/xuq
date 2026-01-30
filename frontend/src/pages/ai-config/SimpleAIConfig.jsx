/**
 * 简化版AI配置 - 一键配置大模型
 * 用户只需要：选择大模型 → 填写密钥 → 保存
 */
import React, { useState, useEffect } from 'react';
import { Card, Form, Select, Input, Button, message, Space, Alert, Tag, Divider } from 'antd';
import { SaveOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';
import { getProviders, createProvider, updateProvider } from '../../api/ai_config';

const { Option } = Select;

// 预设的大模型配置
const PRESET_MODELS = [
  {
    id: 'deepseek-chat',
    name: 'DeepSeek Chat',
    provider: 'DeepSeek',
    description: '高性价比，支持中文，推荐日常使用',
    apiEndpoint: 'https://api.deepseek.com',
    envKey: 'DEEPSEEK_API_KEY',
    price: '输入: $0.14/M tokens, 输出: $0.28/M tokens',
    recommended: true,
  },
  {
    id: 'claude-sonnet',
    name: 'Claude 3.5 Sonnet',
    provider: 'Claude',
    description: '最新最强模型，质量最高，适合重要任务',
    apiEndpoint: 'https://api.anthropic.com',
    envKey: 'CLAUDE_API_KEY',
    price: '输入: $3/M tokens, 输出: $15/M tokens',
    recommended: true,
  },
  {
    id: 'gpt-4o',
    name: 'GPT-4o',
    provider: 'OpenAI',
    description: '最新多模态模型，功能强大',
    apiEndpoint: 'https://api.openai.com',
    envKey: 'OPENAI_API_KEY',
    price: '输入: $2.5/M tokens, 输出: $10/M tokens',
    recommended: false,
  },
  {
    id: 'gpt-4o-mini',
    name: 'GPT-4o Mini',
    provider: 'OpenAI',
    description: '快速、低成本，适合快速测试',
    apiEndpoint: 'https://api.openai.com',
    envKey: 'OPENAI_API_KEY',
    price: '输入: $0.15/M tokens, 输出: $0.6/M tokens',
    recommended: false,
  },
  {
    id: 'gemini-pro',
    name: 'Gemini 1.5 Pro',
    provider: 'Gemini',
    description: '长上下文支持，适合处理大量文本',
    apiEndpoint: 'https://generativelanguage.googleapis.com',
    envKey: 'GEMINI_API_KEY',
    price: '输入: $1.25/M tokens, 输出: $5/M tokens',
    recommended: false,
  },
  {
    id: 'moonshot-8k',
    name: 'Moonshot 8K (Kimi)',
    provider: 'Moonshot',
    description: '国产大模型，支持中文',
    apiEndpoint: 'https://api.moonshot.cn',
    envKey: 'MOONSHOT_API_KEY',
    price: '输入/输出: $1/M tokens',
    recommended: false,
  },
];

const SimpleAIConfig = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [selectedModel, setSelectedModel] = useState(null);
  const [configuredProviders, setConfiguredProviders] = useState([]);

  // 加载已配置的提供商
  useEffect(() => {
    loadConfiguredProviders();
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
        apiKey: '********', // 不显示真实密钥
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
      // 检查提供商是否已存在
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
        // 更新现有提供商
        await updateProvider(existingProvider.provider_id, providerData);
        message.success(`${selectedModel.name} 配置已更新！`);
      } else {
        // 创建新提供商
        await createProvider(providerData);
        message.success(`${selectedModel.name} 配置成功！`);
      }

      // 重新加载配置
      await loadConfiguredProviders();

      // 清空表单
      form.resetFields();
      setSelectedModel(null);
    } catch (error) {
      console.error('保存失败:', error);
      message.error('保存失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  // 检查模型是否已配置
  const isModelConfigured = (model) => {
    return configuredProviders.some(p => p.provider_name === model.provider && p.is_enabled);
  };

  return (
    <div style={{ padding: '24px' }}>
      <Card
        title={
          <div>
            <h2 style={{ margin: 0, fontSize: '20px' }}>AI大模型配置</h2>
            <p style={{ margin: '8px 0 0 0', color: '#999', fontSize: '14px' }}>
              选择一个大模型，填写API密钥，保存即可使用
            </p>
          </div>
        }
        bordered={false}
      >
        {/* 使用说明 */}
        <Alert
          message="配置步骤"
          description={
            <div>
              <p style={{ margin: '8px 0' }}>
                <strong>第1步</strong>：从下面选择一个大模型（推荐 DeepSeek 或 Claude）
              </p>
              <p style={{ margin: '8px 0' }}>
                <strong>第2步</strong>：填写该模型的API密钥
              </p>
              <p style={{ margin: '8px 0' }}>
                <strong>第3步</strong>：点击"保存配置"按钮
              </p>
              <p style={{ margin: '8px 0 0 0', color: '#999' }}>
                💡 提示：配置后系统会自动使用该模型进行AI分析
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
          {/* 选择大模型 */}
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
                      {model.recommended && (
                        <Tag color="green" style={{ marginLeft: 8 }}>推荐</Tag>
                      )}
                      {isModelConfigured(model) && (
                        <Tag color="blue" style={{ marginLeft: 8 }}>已配置</Tag>
                      )}
                    </div>
                  </div>
                </Option>
              ))}
            </Select>
          </Form.Item>

          {/* 显示选中模型的详细信息 */}
          {selectedModel && (
            <Card
              size="small"
              style={{ marginBottom: 24, backgroundColor: '#f5f5f5' }}
            >
              <div style={{ marginBottom: 12 }}>
                <strong style={{ fontSize: '16px' }}>{selectedModel.name}</strong>
                {selectedModel.recommended && (
                  <Tag color="green" style={{ marginLeft: 8 }}>推荐使用</Tag>
                )}
                {isModelConfigured(selectedModel) && (
                  <Tag color="blue" style={{ marginLeft: 8 }}>
                    <CheckCircleOutlined /> 已配置
                  </Tag>
                )}
              </div>
              <p style={{ margin: '8px 0', color: '#666' }}>
                {selectedModel.description}
              </p>
              <p style={{ margin: '8px 0', color: '#999', fontSize: '13px' }}>
                💰 价格：{selectedModel.price}
              </p>
              <Divider style={{ margin: '12px 0' }} />
              <p style={{ margin: 0, color: '#999', fontSize: '13px' }}>
                📝 需要的环境变量：<code>{selectedModel.envKey}</code>
              </p>
            </Card>
          )}

          {/* 填写API密钥 */}
          <Form.Item
            label={<span style={{ fontSize: '16px', fontWeight: 500 }}>API密钥</span>}
            name="apiKey"
            rules={[
              { required: true, message: '请填写API密钥' },
              { min: 10, message: 'API密钥长度至少10个字符' },
            ]}
            extra={
              selectedModel && (
                <div style={{ marginTop: 8 }}>
                  <p style={{ margin: 0, color: '#999' }}>
                    💡 如何获取API密钥？
                  </p>
                  <p style={{ margin: '4px 0 0 0', color: '#999' }}>
                    {selectedModel.provider === 'DeepSeek' && '访问 https://platform.deepseek.com 注册并获取'}
                    {selectedModel.provider === 'Claude' && '访问 https://console.anthropic.com 注册并获取'}
                    {selectedModel.provider === 'OpenAI' && '访问 https://platform.openai.com 注册并获取'}
                    {selectedModel.provider === 'Gemini' && '访问 https://makersuite.google.com 注册并获取'}
                    {selectedModel.provider === 'Moonshot' && '访问 https://platform.moonshot.cn 注册并获取'}
                  </p>
                </div>
              )
            }
          >
            <Input.Password
              placeholder="请输入API密钥，例如：sk-xxx..."
              size="large"
              disabled={!selectedModel}
            />
          </Form.Item>

          {/* 保存按钮 */}
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

        {/* 已配置的模型列表 */}
        {configuredProviders.length > 0 && (
          <>
            <Divider />
            <div>
              <h3 style={{ marginBottom: 16 }}>已配置的大模型</h3>
              <Space direction="vertical" style={{ width: '100%' }}>
                {configuredProviders.map(provider => {
                  const model = PRESET_MODELS.find(m => m.provider === provider.provider_name);
                  return (
                    <Card
                      key={provider.provider_id}
                      size="small"
                      style={{ backgroundColor: provider.is_enabled ? '#f6ffed' : '#f5f5f5' }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <div>
                          <strong>{model?.name || provider.provider_name}</strong>
                          {provider.is_enabled ? (
                            <Tag color="success" style={{ marginLeft: 8 }}>
                              <CheckCircleOutlined /> 已启用
                            </Tag>
                          ) : (
                            <Tag color="default" style={{ marginLeft: 8 }}>
                              <CloseCircleOutlined /> 已禁用
                            </Tag>
                          )}
                        </div>
                        <div style={{ color: '#999', fontSize: '13px' }}>
                          {new Date(provider.created_time).toLocaleDateString()}
                        </div>
                      </div>
                    </Card>
                  );
                })}
              </Space>
            </div>
          </>
        )}
      </Card>
    </div>
  );
};

export default SimpleAIConfig;

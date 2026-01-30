/**
 * [AI1.1, AI1.2] AI配置管理模块 - API客户端
 * 提供AI提供商和AI模型的管理接口
 */
import apiClient from './client';

// ==================== AI提供商管理 ====================

/**
 * 创建AI提供商
 * @param {Object} data - 提供商数据
 * @returns {Promise}
 */
export const createProvider = (data) => {
  return apiClient.post('/ai-config/providers', data);
};

/**
 * 获取AI提供商列表
 * @param {Object} params - 查询参数
 * @returns {Promise}
 */
export const getProviders = (params = {}) => {
  return apiClient.get('/ai-config/providers', { params });
};

/**
 * 获取单个AI提供商
 * @param {number} providerId - 提供商ID
 * @returns {Promise}
 */
export const getProvider = (providerId) => {
  return apiClient.get(`/ai-config/providers/${providerId}`);
};

/**
 * 更新AI提供商
 * @param {number} providerId - 提供商ID
 * @param {Object} data - 更新数据
 * @returns {Promise}
 */
export const updateProvider = (providerId, data) => {
  return apiClient.put(`/ai-config/providers/${providerId}`, data);
};

/**
 * 删除AI提供商
 * @param {number} providerId - 提供商ID
 * @returns {Promise}
 */
export const deleteProvider = (providerId) => {
  return apiClient.delete(`/ai-config/providers/${providerId}`);
};

/**
 * 切换AI提供商启用状态
 * @param {number} providerId - 提供商ID
 * @returns {Promise}
 */
export const toggleProvider = (providerId) => {
  return apiClient.post(`/ai-config/providers/${providerId}/toggle`);
};

/**
 * 测试AI提供商连接
 * @param {number} providerId - 提供商ID
 * @returns {Promise}
 */
export const testProviderConnection = (providerId) => {
  return apiClient.post(`/ai-config/providers/${providerId}/test`);
};

/**
 * 获取AI提供商统计信息
 * @returns {Promise}
 */
export const getProviderStatistics = () => {
  return apiClient.get('/ai-config/providers/statistics');
};

// ==================== AI模型管理 ====================

/**
 * 创建AI模型
 * @param {Object} data - 模型数据
 * @returns {Promise}
 */
export const createModel = (data) => {
  return apiClient.post('/ai-config/models', data);
};

/**
 * 获取AI模型列表
 * @param {Object} params - 查询参数
 * @returns {Promise}
 */
export const getModels = (params = {}) => {
  return apiClient.get('/ai-config/models', { params });
};

/**
 * 获取单个AI模型（包含提供商信息）
 * @param {number} modelId - 模型ID
 * @returns {Promise}
 */
export const getModel = (modelId) => {
  return apiClient.get(`/ai-config/models/${modelId}`);
};

/**
 * 更新AI模型
 * @param {number} modelId - 模型ID
 * @param {Object} data - 更新数据
 * @returns {Promise}
 */
export const updateModel = (modelId, data) => {
  return apiClient.put(`/ai-config/models/${modelId}`, data);
};

/**
 * 删除AI模型
 * @param {number} modelId - 模型ID
 * @returns {Promise}
 */
export const deleteModel = (modelId) => {
  return apiClient.delete(`/ai-config/models/${modelId}`);
};

/**
 * 切换AI模型启用状态
 * @param {number} modelId - 模型ID
 * @returns {Promise}
 */
export const toggleModel = (modelId) => {
  return apiClient.post(`/ai-config/models/${modelId}/toggle`);
};

/**
 * 设置默认AI模型
 * @param {number} modelId - 模型ID
 * @returns {Promise}
 */
export const setDefaultModel = (modelId) => {
  return apiClient.post(`/ai-config/models/${modelId}/set-default`);
};

/**
 * 获取AI模型统计信息
 * @returns {Promise}
 */
export const getModelStatistics = () => {
  return apiClient.get('/ai-config/models/statistics');
};
// ==================== AI场景管理 ====================

/**
 * 创建AI场景
 * @param {Object} data - 场景数据
 * @returns {Promise}
 */
export const createScenario = (data) => {
  return apiClient.post('/ai-config/scenarios', data);
};

/**
 * 获取AI场景列表
 * @param {Object} params - 查询参数
 * @returns {Promise}
 */
export const getScenarios = (params = {}) => {
  return apiClient.get('/ai-config/scenarios', { params });
};

/**
 * 获取单个AI场景
 * @param {number} scenarioId - 场景ID
 * @returns {Promise}
 */
export const getScenario = (scenarioId) => {
  return apiClient.get(`/ai-config/scenarios/${scenarioId}`);
};

/**
 * 获取AI场景及其关联的模型信息
 * @param {number} scenarioId - 场景ID
 * @returns {Promise}
 */
export const getScenarioWithModels = (scenarioId) => {
  return apiClient.get(`/ai-config/scenarios/${scenarioId}/with-models`);
};

/**
 * 更新AI场景
 * @param {number} scenarioId - 场景ID
 * @param {Object} data - 更新数据
 * @returns {Promise}
 */
export const updateScenario = (scenarioId, data) => {
  return apiClient.put(`/ai-config/scenarios/${scenarioId}`, data);
};

/**
 * 删除AI场景
 * @param {number} scenarioId - 场景ID
 * @returns {Promise}
 */
export const deleteScenario = (scenarioId) => {
  return apiClient.delete(`/ai-config/scenarios/${scenarioId}`);
};

/**
 * 切换AI场景启用状态
 * @param {number} scenarioId - 场景ID
 * @returns {Promise}
 */
export const toggleScenario = (scenarioId) => {
  return apiClient.post(`/ai-config/scenarios/${scenarioId}/toggle`);
};

/**
 * 获取AI场景统计信息
 * @returns {Promise}
 */
export const getScenarioStatistics = () => {
  return apiClient.get('/ai-config/scenarios/statistics');
};

// ==================== AI提示词管理 ====================

/**
 * 创建AI提示词
 * @param {Object} data - 提示词数据
 * @returns {Promise}
 */
export const createPrompt = (data) => {
  return apiClient.post('/ai-config/prompts', data);
};

/**
 * 获取AI提示词列表
 * @param {Object} params - 查询参数
 * @returns {Promise}
 */
export const getPrompts = (params = {}) => {
  return apiClient.get('/ai-config/prompts', { params });
};

/**
 * 获取场景的所有提示词
 * @param {number} scenarioId - 场景ID
 * @param {Object} params - 查询参数
 * @returns {Promise}
 */
export const getPromptsByScenario = (scenarioId, params = {}) => {
  return apiClient.get(`/ai-config/scenarios/${scenarioId}/prompts`, { params });
};

/**
 * 获取场景的激活提示词
 * @param {number} scenarioId - 场景ID
 * @returns {Promise}
 */
export const getActivePrompt = (scenarioId) => {
  return apiClient.get(`/ai-config/scenarios/${scenarioId}/prompts/active`);
};

/**
 * 获取单个AI提示词（包含场景信息）
 * @param {number} promptId - 提示词ID
 * @returns {Promise}
 */
export const getPrompt = (promptId) => {
  return apiClient.get(`/ai-config/prompts/${promptId}`);
};

/**
 * 更新AI提示词
 * @param {number} promptId - 提示词ID
 * @param {Object} data - 更新数据
 * @returns {Promise}
 */
export const updatePrompt = (promptId, data) => {
  return apiClient.put(`/ai-config/prompts/${promptId}`, data);
};

/**
 * 删除AI提示词
 * @param {number} promptId - 提示词ID
 * @returns {Promise}
 */
export const deletePrompt = (promptId) => {
  return apiClient.delete(`/ai-config/prompts/${promptId}`);
};

/**
 * 激活提示词
 * @param {number} promptId - 提示词ID
 * @returns {Promise}
 */
export const activatePrompt = (promptId) => {
  return apiClient.post(`/ai-config/prompts/${promptId}/activate`);
};

/**
 * 创建提示词的新版本
 * @param {number} promptId - 提示词ID
 * @param {Object} data - 新版本数据
 * @returns {Promise}
 */
export const createPromptNewVersion = (promptId, data) => {
  return apiClient.post(`/ai-config/prompts/${promptId}/new-version`, data);
};

/**
 * 渲染提示词模板
 * @param {number} promptId - 提示词ID
 * @param {Object} data - 变量值
 * @returns {Promise}
 */
export const renderPrompt = (promptId, data) => {
  return apiClient.post(`/ai-config/prompts/${promptId}/render`, data);
};

/**
 * 获取AI提示词统计信息
 * @returns {Promise}
 */
export const getPromptStatistics = () => {
  return apiClient.get('/ai-config/prompts/statistics');
};

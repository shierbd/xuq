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

// ==================== AI成本监控 ====================

/**
 * 获取成本统计信息
 * @param {Object} params - 查询参数
 * @param {string} params.start_date - 开始日期 (YYYY-MM-DD)
 * @param {string} params.end_date - 结束日期 (YYYY-MM-DD)
 * @param {number} params.scenario_id - 场景ID
 * @param {number} params.model_id - 模型ID
 * @param {number} params.provider_id - 提供商ID
 * @returns {Promise}
 */
export const getCostStatistics = (params = {}) => {
  return apiClient.get('/ai-config/cost/statistics', { params });
};

/**
 * 按场景统计成本
 * @param {Object} params - 查询参数
 * @param {string} params.start_date - 开始日期 (YYYY-MM-DD)
 * @param {string} params.end_date - 结束日期 (YYYY-MM-DD)
 * @returns {Promise}
 */
export const getCostByScenario = (params = {}) => {
  return apiClient.get('/ai-config/cost/by-scenario', { params });
};

/**
 * 按模型统计成本
 * @param {Object} params - 查询参数
 * @param {string} params.start_date - 开始日期 (YYYY-MM-DD)
 * @param {string} params.end_date - 结束日期 (YYYY-MM-DD)
 * @returns {Promise}
 */
export const getCostByModel = (params = {}) => {
  return apiClient.get('/ai-config/cost/by-model', { params });
};

/**
 * 按提供商统计成本
 * @param {Object} params - 查询参数
 * @param {string} params.start_date - 开始日期 (YYYY-MM-DD)
 * @param {string} params.end_date - 结束日期 (YYYY-MM-DD)
 * @returns {Promise}
 */
export const getCostByProvider = (params = {}) => {
  return apiClient.get('/ai-config/cost/by-provider', { params });
};

/**
 * 获取成本趋势
 * @param {Object} params - 查询参数
 * @param {string} params.start_date - 开始日期 (YYYY-MM-DD)
 * @param {string} params.end_date - 结束日期 (YYYY-MM-DD)
 * @param {string} params.granularity - 粒度 (day, hour, month)
 * @returns {Promise}
 */
export const getCostTrend = (params = {}) => {
  return apiClient.get('/ai-config/cost/trend', { params });
};

/**
 * 获取最近的成本日志
 * @param {Object} params - 查询参数
 * @param {number} params.skip - 跳过数量
 * @param {number} params.limit - 限制数量
 * @param {string} params.status - 状态筛选
 * @param {number} params.scenario_id - 场景ID筛选
 * @returns {Promise}
 */
export const getRecentCostLogs = (params = {}) => {
  return apiClient.get('/ai-config/cost/recent-logs', { params });
};

// ==================== AI配置导入导出 ====================

/**
 * 导出AI配置
 * @param {Object} params - 导出参数
 * @param {boolean} params.include_providers - 是否包含提供商
 * @param {boolean} params.include_models - 是否包含模型
 * @param {boolean} params.include_scenarios - 是否包含场景
 * @param {boolean} params.include_prompts - 是否包含提示词
 * @returns {Promise}
 */
export const exportConfig = (params = {}) => {
  return apiClient.get('/ai-config/config/export', { params });
};

/**
 * 导入AI配置
 * @param {Object} data - 导入数据
 * @param {Object} data.config_data - 配置数据
 * @param {boolean} data.overwrite - 是否覆盖现有配置
 * @returns {Promise}
 */
export const importConfig = (data) => {
  return apiClient.post('/ai-config/config/import', data);
};

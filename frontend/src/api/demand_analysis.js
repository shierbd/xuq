/**
 * 需求分析 API 接口
 * [REQ-004] P3.1: 需求分析（AI辅助）
 */
import apiClient from './client';

/**
 * 批量分析簇的用户需求
 * @param {Object} params - 分析参数
 * @param {Array<number>} params.cluster_ids - 簇ID列表（可选，不传则处理所有簇）
 * @param {number} params.top_n - 使用 Top N 商品（默认10）
 * @param {number} params.batch_size - 批次大小（默认5）
 * @param {string} params.ai_provider - AI 提供商（默认 "deepseek"）
 * @param {number} params.max_clusters - 最多分析的簇数量（可选，不传则不限制）
 * @param {boolean} params.skip_analyzed - 是否跳过已分析的簇（默认 true）
 * @param {boolean} params.force_reanalyze - 是否强制重新分析已分析的簇（默认 false）
 * @returns {Promise} 分析结果
 */
export const analyzeDemands = async (params = {}) => {
  return apiClient.post('/demand-analysis/analyze', {
    cluster_ids: params.cluster_ids || null,
    top_n: params.top_n || 10,
    batch_size: params.batch_size || 5,
    ai_provider: params.ai_provider || 'deepseek',
    max_clusters: params.max_clusters || null,
    skip_analyzed: params.skip_analyzed !== undefined ? params.skip_analyzed : true,
    force_reanalyze: params.force_reanalyze || false
  });
};

/**
 * 分析单个簇的用户需求
 * @param {number} clusterId - 簇ID
 * @param {Object} params - 分析参数
 * @param {number} params.top_n - 使用 Top N 商品（默认10）
 * @param {string} params.ai_provider - AI 提供商（默认 "deepseek"）
 * @returns {Promise} 分析结果
 */
export const analyzeClusterDemand = async (clusterId, params = {}) => {
  return apiClient.post(`/demand-analysis/analyze/${clusterId}`, null, {
    params: {
      top_n: params.top_n || 10,
      ai_provider: params.ai_provider || 'deepseek'
    }
  });
};

/**
 * 获取需求分析统计信息
 * @returns {Promise} 统计信息
 */
export const getDemandAnalysisStatistics = async () => {
  return apiClient.get('/demand-analysis/statistics');
};

/**
 * 获取簇内商品信息
 * @param {number} clusterId - 簇ID
 * @param {number} limit - 返回商品数量（默认10）
 * @returns {Promise} 商品信息列表
 */
export const getClusterProducts = async (clusterId, limit = 10) => {
  return apiClient.get(`/demand-analysis/cluster-products/${clusterId}`, {
    params: { limit }
  });
};

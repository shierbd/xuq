/**
 * [REQ-011] P5.2: Top商品AI深度分析 API
 */
import apiClient from './client';

/**
 * 批量分析所有簇的Top商品
 * @param {number} topN - 每个簇取Top N个商品
 * @param {string} aiProvider - AI提供商 ('claude' 或 'deepseek')
 * @returns {Promise}
 */
export const analyzeAllTopProducts = (topN = 3, aiProvider = 'deepseek') => {
  return apiClient.post('/api/top-product-analysis/analyze', null, {
    params: {
      top_n: topN,
      ai_provider: aiProvider
    }
  });
};

/**
 * 分析单个簇的Top商品
 * @param {number} clusterId - 簇ID
 * @param {number} topN - Top N个商品
 * @param {string} aiProvider - AI提供商
 * @returns {Promise}
 */
export const analyzeSingleCluster = (clusterId, topN = 3, aiProvider = 'deepseek') => {
  return apiClient.post(`/api/top-product-analysis/analyze/${clusterId}`, null, {
    params: {
      top_n: topN,
      ai_provider: aiProvider
    }
  });
};

/**
 * 获取分析统计信息
 * @returns {Promise}
 */
export const getAnalysisStatistics = () => {
  return apiClient.get('/api/top-product-analysis/statistics');
};

/**
 * 获取每个簇的Top商品列表
 * @param {number} topN - 每个簇取Top N个商品
 * @returns {Promise}
 */
export const getTopProductsByCluster = (topN = 3) => {
  return apiClient.get('/api/top-product-analysis/top-products', {
    params: {
      top_n: topN
    }
  });
};

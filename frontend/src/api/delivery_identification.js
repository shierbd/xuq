/**
 * 交付产品识别 API 接口
 * [REQ-005] P3.2: 交付产品识别（AI辅助）
 */
import apiClient from './client';

/**
 * 批量识别商品的交付形式
 * @param {Object} params - 识别参数
 * @param {Array<number>} params.product_ids - 商品ID列表（可选，不传则处理所有商品）
 * @param {boolean} params.use_ai_for_unmatched - 对规则无法识别的商品使用 AI（默认 false）
 * @param {number} params.batch_size - 批次大小（默认100）
 * @param {string} params.ai_provider - AI 提供商（默认 "deepseek"）
 * @returns {Promise} 识别结果
 */
export const identifyProducts = async (params = {}) => {
  return apiClient.post('/delivery-identification/identify', {
    product_ids: params.product_ids || null,
    use_ai_for_unmatched: params.use_ai_for_unmatched || false,
    batch_size: params.batch_size || 100,
    ai_provider: params.ai_provider || 'deepseek'
  });
};

/**
 * 识别单个商品的交付形式
 * @param {number} productId - 商品ID
 * @param {Object} params - 识别参数
 * @param {boolean} params.use_ai - 是否使用 AI（默认 false）
 * @param {string} params.ai_provider - AI 提供商（默认 "deepseek"）
 * @returns {Promise} 识别结果
 */
export const identifyProduct = async (productId, params = {}) => {
  return apiClient.post(`/delivery-identification/identify/${productId}`, null, {
    params: {
      use_ai: params.use_ai || false,
      ai_provider: params.ai_provider || 'deepseek'
    }
  });
};

/**
 * 获取交付产品识别统计信息
 * @returns {Promise} 统计信息
 */
export const getDeliveryIdentificationStatistics = async () => {
  return apiClient.get('/delivery-identification/statistics');
};

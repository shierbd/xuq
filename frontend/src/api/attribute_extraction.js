/**
 * 商品属性提取 API 接口
 * [REQ-010] P5.1: 商品属性提取（代码规则）
 * [REQ-012] P5.3: AI辅助兜底
 */
import apiClient from './client';

/**
 * 批量提取所有商品的属性
 * @param {Object} params - 提取参数
 * @param {number} params.batch_size - 批次大小（默认100）
 * @returns {Promise} 提取结果
 */
export const extractAllAttributes = async (params = {}) => {
  return apiClient.post('/attribute-extraction/extract', {
    batch_size: params.batch_size || 100
  });
};

/**
 * 提取单个商品的属性
 * @param {number} productId - 商品ID
 * @returns {Promise} 提取结果
 */
export const extractProductAttributes = async (productId) => {
  return apiClient.post(`/attribute-extraction/extract/${productId}`);
};

/**
 * AI辅助兜底 - 处理代码规则无法识别的商品
 * @param {Object} params - AI辅助参数
 * @param {number} params.max_products - 最大处理数量（可选）
 * @param {number} params.batch_size - 批次大小（默认10）
 * @returns {Promise} 处理结果
 */
export const extractMissingAttributes = async (params = {}) => {
  return apiClient.post('/attribute-extraction/extract-missing', {
    max_products: params.max_products || null,
    batch_size: params.batch_size || 10
  });
};

/**
 * 获取属性提取统计信息
 * @returns {Promise} 统计信息
 */
export const getAttributeExtractionStatistics = async () => {
  return apiClient.get('/attribute-extraction/statistics');
};

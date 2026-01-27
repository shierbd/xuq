/**
 * 商品API接口
 */
import apiClient from './client';

/**
 * 获取商品列表
 */
export const getProducts = async (params) => {
  return apiClient.get('/products/', { params });
};

/**
 * 获取单个商品
 */
export const getProduct = async (productId) => {
  return apiClient.get(`/products/${productId}`);
};

/**
 * 批量获取商品
 */
export const getProductsByIds = async (ids) => {
  return apiClient.get('/products/batch/by-ids', {
    params: { ids: ids.join(',') }
  });
};

/**
 * 获取统计信息
 */
export const getStatistics = async () => {
  return apiClient.get('/products/stats/summary');
};

/**
 * 获取唯一标签
 */
export const getUniqueTags = async () => {
  return apiClient.get('/products/tags/unique');
};

/**
 * 批量翻译商品（异步）
 */
export const translateProducts = async (productIds) => {
  return apiClient.post('/translation/batch', { product_ids: productIds });
};

/**
 * 批量翻译商品（同步）
 */
export const translateProductsSync = async (productIds) => {
  return apiClient.post('/translation/batch/sync', { product_ids: productIds });
};

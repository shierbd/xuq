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
 * 更新商品
 */
export const updateProduct = async (productId, data) => {
  return apiClient.put(`/products/${productId}`, data);
};

/**
 * 删除商品
 */
export const deleteProduct = async (productId) => {
  return apiClient.delete(`/products/${productId}`);
};

/**
 * 批量删除商品
 */
export const batchDeleteProducts = async (productIds) => {
  return apiClient.post('/products/batch-delete', { product_ids: productIds });
};

/**
 * 批量获取商品
 */
export const getStatistics = async () => {
  return apiClient.get('/products/stats/summary');
};

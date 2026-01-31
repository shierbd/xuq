/**
 * 词根聚类模块 API 客户端
 */
import client from './client';

/**
 * 获取关键词总数
 */
export const getKeywordCount = async () => {
  const response = await client.get('/keywords/count');
  return response.data;
};

/**
 * 获取关键词列表
 */
export const getKeywords = async (params = {}) => {
  const response = await client.get('/keywords/', { params });
  return response.data;
};

/**
 * 获取种子词列表
 */
export const getSeedWords = async () => {
  const response = await client.get('/keywords/seed-words');
  return response.data;
};

/**
 * 获取簇概览
 */
export const getClustersOverview = async (params = {}) => {
  const response = await client.get('/keywords/clusters/overview', { params });
  return response.data;
};

/**
 * 获取簇详情
 */
export const getClusterDetail = async (clusterId, params = {}) => {
  const response = await client.get(`/keywords/clusters/${clusterId}`, { params });
  return response.data;
};

/**
 * 导入关键词数据
 */
export const importKeywords = async (file) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await client.post('/keywords/import', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

/**
 * Reddit模块 API客户端
 */
import client from './client';

/**
 * 获取Reddit采集任务列表
 */
export const getCollectionTasks = async (params = {}) => {
  const response = await client.get('/reddit/tasks', { params });
  return response.data;
};

/**
 * 创建Reddit采集任务
 */
export const createCollectionTask = async (data) => {
  const response = await client.post('/reddit/tasks', data);
  return response.data;
};

/**
 * 获取Reddit帖子列表
 */
export const getRedditPosts = async (params = {}) => {
  const response = await client.get('/reddit/posts', { params });
  return response.data;
};

/**
 * 获取Reddit帖子详情
 */
export const getRedditPostDetail = async (postId) => {
  const response = await client.get(`/reddit/posts/${postId}`);
  return response.data;
};

/**
 * 获取Reddit数据统计
 */
export const getRedditStats = async (params = {}) => {
  const response = await client.get('/reddit/stats', { params });
  return response.data;
};

/**
 * 执行Reddit情感分析
 */
export const analyzeSentiment = async (data) => {
  const response = await client.post('/reddit/sentiment', data);
  return response.data;
};

/**
 * 导出Reddit数据
 */
export const exportRedditData = async (params = {}) => {
  const response = await client.get('/reddit/export', {
    params,
    responseType: 'blob',
  });
  return response.data;
};

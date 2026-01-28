/**
 * 数据导入API接口
 */
import apiClient from './client';

/**
 * 上传并导入商品数据
 */
export const importProducts = async (file, platform, fieldMapping, skipDuplicates = true) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('platform', platform);
  formData.append('field_mapping', JSON.stringify(fieldMapping));
  formData.append('skip_duplicates', skipDuplicates);

  return apiClient.post('/products/import', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

/**
 * 获取导入历史记录
 */
export const getImportLogs = async (limit = 50, offset = 0) => {
  return apiClient.get('/import/logs', {
    params: { limit, offset }
  });
};

/**
 * 获取单个导入记录详情
 */
export const getImportLog = async (logId) => {
  return apiClient.get(`/import/logs/${logId}`);
};

/**
 * 批量AI标注（异步）
 */
export const annotateProducts = async (productIds, batchSize = 10, customPrompt = null) => {
  return apiClient.post('/ai-annotation/batch', {
    product_ids: productIds,
    batch_size: batchSize,
    custom_prompt: customPrompt
  });
};

/**
 * 批量AI标注（同步）
 */
export const annotateProductsSync = async (productIds, batchSize = 10, customPrompt = null) => {
  return apiClient.post('/ai-annotation/batch/sync', {
    product_ids: productIds,
    batch_size: batchSize,
    custom_prompt: customPrompt
  });
};

/**
 * 获取AI标注状态
 */
export const getAnnotationStatus = async () => {
  return apiClient.get('/ai-annotation/status');
};

/**
 * 导出商品数据
 */
export const exportProducts = async (format, scope, fields, filters = null) => {
  return apiClient.post('/export/', {
    format,
    scope,
    fields,
    filters
  }, {
    responseType: 'blob'
  });
};

/**
 * 获取可导出的字段列表
 */
export const getExportFields = async () => {
  return apiClient.get('/export/fields');
};

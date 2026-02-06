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
 * 导出商品数据
 * @param {string} format - csv 或 excel
 * @param {string} exportType - products | clustered | cluster-summary
 */
export const exportProducts = async (format = 'excel', exportType = 'products') => {
  const endpointMap = {
    products: '/products/export/products',
    clustered: '/products/export/clustered',
    'cluster-summary': '/products/export/cluster-summary',
  };

  const endpoint = endpointMap[exportType] || endpointMap.products;

  return apiClient.get(endpoint, {
    params: { format },
    responseType: 'blob'
  });
};

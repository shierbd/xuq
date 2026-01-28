/**
 * 批量导入API接口
 */
import apiClient from './client';

/**
 * 预览文件夹中的文件列表
 */
export const previewFolderFiles = async (folderPath, filePattern = '*.xlsx') => {
  return apiClient.post('/batch-import/preview', {
    folder_path: folderPath,
    file_pattern: filePattern
  });
};

/**
 * 批量导入文件夹中的所有文件
 */
export const batchImportFromFolder = async (folderPath, platform, fieldMapping, skipDuplicates = true, filePattern = '*.xlsx') => {
  return apiClient.post('/batch-import/', {
    folder_path: folderPath,
    platform: platform,
    field_mapping: fieldMapping,
    skip_duplicates: skipDuplicates,
    file_pattern: filePattern
  });
};

/**
 * 获取批量导入任务状态
 */
export const getBatchImportStatus = async (taskId) => {
  return apiClient.get(`/batch-import/status/${taskId}`);
};

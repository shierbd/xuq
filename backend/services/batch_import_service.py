"""
批量导入服务 - 处理文件夹批量导入的业务逻辑
"""
import os
import glob
from typing import Dict, List
from sqlalchemy.orm import Session
from backend.services.import_service import ImportService
from datetime import datetime


class BatchImportService:
    """批量导入服务"""

    def __init__(self, db: Session):
        self.db = db
        self.import_service = ImportService(db)

    def batch_import_from_folder(
        self,
        folder_path: str,
        platform: str = "etsy",
        field_mapping: Dict = None,
        skip_duplicates: bool = True,
        file_pattern: str = "*.xlsx"
    ) -> Dict:
        """
        从文件夹批量导入文件

        Args:
            folder_path: 文件夹路径
            platform: 平台标识
            field_mapping: 字段映射
            skip_duplicates: 是否跳过重复
            file_pattern: 文件匹配模式

        Returns:
            Dict: 批量导入结果统计
        """
        # 验证路径
        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"文件夹路径不存在: {folder_path}")

        if not os.path.isdir(folder_path):
            raise ValueError(f"路径不是文件夹: {folder_path}")

        # 获取匹配的文件
        pattern = os.path.join(folder_path, file_pattern)
        files = glob.glob(pattern)

        if not files:
            return {
                "success": False,
                "message": f"未找到匹配的文件: {file_pattern}",
                "total_files": 0,
                "processed_files": 0,
                "failed_files": 0,
                "total_imported": 0,
                "total_duplicates": 0,
                "total_invalid": 0,
                "file_results": []
            }

        # 初始化统计
        stats = {
            "success": True,
            "message": "批量导入完成",
            "total_files": len(files),
            "processed_files": 0,
            "failed_files": 0,
            "total_imported": 0,
            "total_duplicates": 0,
            "total_invalid": 0,
            "file_results": []
        }

        # 逐个处理文件
        for file_path in files:
            file_name = os.path.basename(file_path)
            file_result = {
                "file_name": file_name,
                "file_path": file_path,
                "success": False,
                "message": "",
                "imported": 0,
                "duplicates": 0,
                "invalid": 0
            }

            try:
                # 打开文件
                with open(file_path, 'rb') as f:
                    # 执行导入
                    result = self.import_service.import_from_file(
                        file=f,
                        filename=file_name,
                        field_mapping=field_mapping,
                        skip_duplicates=skip_duplicates
                    )

                    # 记录结果（转换为 Python 原生类型以避免序列化问题）
                    file_result["success"] = True
                    file_result["message"] = "导入成功"
                    file_result["imported"] = int(result.get("imported", 0))
                    file_result["duplicates"] = int(result.get("duplicates", 0))
                    file_result["invalid"] = int(result.get("invalid_rows", 0))

                    # 累加统计
                    stats["processed_files"] += 1
                    stats["total_imported"] += file_result["imported"]
                    stats["total_duplicates"] += file_result["duplicates"]
                    stats["total_invalid"] += file_result["invalid"]

            except Exception as e:
                # 记录失败
                file_result["success"] = False
                file_result["message"] = f"导入失败: {str(e)}"
                stats["failed_files"] += 1

            # 添加到结果列表
            stats["file_results"].append(file_result)

        # 更新总体状态
        if stats["failed_files"] > 0:
            stats["success"] = False
            stats["message"] = f"批量导入完成，{stats['failed_files']} 个文件失败"

        return stats

    def get_folder_files(self, folder_path: str, file_pattern: str = "*.xlsx") -> List[Dict]:
        """
        获取文件夹中的文件列表

        Args:
            folder_path: 文件夹路径
            file_pattern: 文件匹配模式

        Returns:
            List[Dict]: 文件信息列表
        """
        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"文件夹路径不存在: {folder_path}")

        if not os.path.isdir(folder_path):
            raise ValueError(f"路径不是文件夹: {folder_path}")

        # 获取匹配的文件
        pattern = os.path.join(folder_path, file_pattern)
        files = glob.glob(pattern)

        # 获取文件信息
        file_list = []
        for file_path in files:
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            file_list.append({
                "name": file_name,
                "path": file_path,
                "size": file_size,
                "size_mb": round(file_size / 1024 / 1024, 2)
            })

        return file_list

    def validate_folder_path(self, folder_path: str) -> Dict:
        """
        验证文件夹路径

        Args:
            folder_path: 文件夹路径

        Returns:
            Dict: 验证结果
        """
        result = {
            "valid": False,
            "exists": False,
            "is_directory": False,
            "readable": False,
            "message": ""
        }

        # 检查路径是否存在
        if not os.path.exists(folder_path):
            result["message"] = "路径不存在"
            return result

        result["exists"] = True

        # 检查是否是文件夹
        if not os.path.isdir(folder_path):
            result["message"] = "路径不是文件夹"
            return result

        result["is_directory"] = True

        # 检查是否可读
        if not os.access(folder_path, os.R_OK):
            result["message"] = "没有读取权限"
            return result

        result["readable"] = True
        result["valid"] = True
        result["message"] = "路径有效"

        return result

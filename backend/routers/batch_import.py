"""
批量导入功能 - API 路由
支持从文件夹路径批量导入多个文件
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.services.batch_import_service import BatchImportService
from typing import Dict, List
from pydantic import BaseModel

router = APIRouter(prefix="/api/batch-import", tags=["batch-import"])


class BatchImportRequest(BaseModel):
    """批量导入请求模型"""
    folder_path: str
    platform: str = "etsy"
    field_mapping: Dict[str, int] = {}
    skip_duplicates: bool = True
    file_pattern: str = "*.xlsx"  # 文件匹配模式，如 *.xlsx, *.csv, *.xls


class BatchImportResponse(BaseModel):
    """批量导入响应模型"""
    success: bool
    message: str
    total_files: int
    processed_files: int
    failed_files: int
    total_imported: int
    total_duplicates: int
    total_invalid: int
    file_results: List[Dict]


@router.post("/", response_model=BatchImportResponse)
async def batch_import_from_folder(
    request: BatchImportRequest,
    db: Session = Depends(get_db)
):
    """
    批量导入文件夹中的所有文件

    Args:
        request: 批量导入请求
            - folder_path: 文件夹路径
            - platform: 平台标识（etsy/gumroad/amazon）
            - field_mapping: 字段映射 {字段名: 列索引}
            - skip_duplicates: 是否跳过重复数据
            - file_pattern: 文件匹配模式（*.xlsx, *.csv, *.xls）

    Returns:
        BatchImportResponse: 批量导入结果
    """
    try:
        # 创建批量导入服务
        batch_service = BatchImportService(db)

        # 执行批量导入
        result = batch_service.batch_import_from_folder(
            folder_path=request.folder_path,
            platform=request.platform,
            field_mapping=request.field_mapping,
            skip_duplicates=request.skip_duplicates,
            file_pattern=request.file_pattern
        )

        return BatchImportResponse(
            success=result["success"],
            message=result["message"],
            total_files=result["total_files"],
            processed_files=result["processed_files"],
            failed_files=result["failed_files"],
            total_imported=result["total_imported"],
            total_duplicates=result["total_duplicates"],
            total_invalid=result["total_invalid"],
            file_results=result["file_results"]
        )

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=f"权限不足: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量导入失败: {str(e)}")


@router.post("/preview")
async def preview_folder_files(
    folder_path: str = Body(..., embed=True),
    file_pattern: str = Body("*.xlsx", embed=True)
):
    """
    预览文件夹中的文件列表

    Args:
        folder_path: 文件夹路径
        file_pattern: 文件匹配模式

    Returns:
        Dict: 文件列表和统计信息
    """
    try:
        import os
        import glob

        # 验证路径存在
        if not os.path.exists(folder_path):
            raise HTTPException(status_code=404, detail="文件夹路径不存在")

        if not os.path.isdir(folder_path):
            raise HTTPException(status_code=400, detail="路径不是文件夹")

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

        return {
            "success": True,
            "folder_path": folder_path,
            "file_pattern": file_pattern,
            "total_files": len(file_list),
            "files": file_list
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预览失败: {str(e)}")


@router.get("/status/{task_id}")
async def get_batch_import_status(task_id: str):
    """
    获取批量导入任务状态（预留接口，用于异步批量导入）

    Args:
        task_id: 任务ID

    Returns:
        Dict: 任务状态信息
    """
    # TODO: 实现异步任务状态查询
    return {
        "success": True,
        "task_id": task_id,
        "status": "pending",
        "message": "异步批量导入功能待实现"
    }

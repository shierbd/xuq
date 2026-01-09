# Reddit板块分析与标注系统 - API设计文档

**版本**: v1.0
**创建日期**: 2026-01-09
**作者**: Claude Code
**状态**: 设计完成

---

## 目录

1. [概述](#概述)
2. [核心模块](#核心模块)
3. [数据导入API](#数据导入api)
4. [AI分析API](#ai分析api)
5. [数据查询API](#数据查询api)
6. [配置管理API](#配置管理api)
7. [导出功能API](#导出功能api)
8. [错误处理](#错误处理)

---

## 概述

### API设计原则

本系统基于Streamlit构建，不提供REST API，而是提供内部Python函数接口。所有函数遵循以下原则：

- **类型注解**: 所有函数使用Python类型注解
- **文档字符串**: 提供详细的docstring
- **错误处理**: 统一的异常处理机制
- **返回格式**: 统一的返回格式（Dict[str, Any]）
- **日志记录**: 关键操作记录日志

### 返回格式规范

所有API函数返回统一格式：

```python
{
    "success": bool,          # 操作是否成功
    "data": Any,              # 返回的数据
    "message": str,           # 操作消息
    "errors": List[str]       # 错误列表（如有）
}
```

---

## 核心模块

### 模块结构

```
core/
└── reddit_analyzer.py        # Reddit分析核心逻辑

storage/
├── models.py                 # 数据模型（新增2个模型）
└── reddit_repository.py      # Reddit数据访问层

ui/
└── pages/
    └── phase6_reddit.py      # Reddit分析UI页面
```

---

## 数据导入API

### 1. import_reddit_data

导入Reddit板块数据（CSV或Excel格式）

**函数签名**:
```python
def import_reddit_data(
    file_path: str,
    file_type: str,
    batch_id: Optional[str] = None,
    skip_duplicates: bool = True
) -> Dict[str, Any]:
    """
    导入Reddit板块数据

    Args:
        file_path: 文件路径
        file_type: 文件类型 ('csv' 或 'excel')
        batch_id: 导入批次ID（可选，默认自动生成）
        skip_duplicates: 是否跳过重复记录（默认True）

    Returns:
        {
            'success': True/False,
            'data': {
                'imported_count': int,      # 成功导入数量
                'skipped_count': int,       # 跳过数量
                'error_count': int,         # 错误数量
                'batch_id': str             # 批次ID
            },
            'message': str,
            'errors': List[str]
        }
    """
```

**业务逻辑**:
```
1. 验证文件路径和类型
   ↓
2. 读取文件（pandas）
   - CSV: pd.read_csv(file_path, header=None, names=['name', 'description', 'subscribers'])
   - Excel: pd.read_excel(file_path, header=None, names=['name', 'description', 'subscribers'])
   ↓
3. 数据验证
   - name字段非空
   - subscribers >= 0
   - description为空时标记为skipped
   ↓
4. 去重处理（如果skip_duplicates=True）
   - 按name字段去重
   - 保留subscribers最大的记录
   ↓
5. 生成batch_id（如果未提供）
   - 格式：reddit_YYYYMMDD_HHMMSS
   ↓
6. 批量插入数据库
   - 使用bulk_insert_mappings
   - 每批1000条
   ↓
7. 返回导入统计
```

**代码示例**:
```python
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional, List
from storage.reddit_repository import RedditSubredditRepository

def import_reddit_data(
    file_path: str,
    file_type: str,
    batch_id: Optional[str] = None,
    skip_duplicates: bool = True
) -> Dict[str, Any]:
    try:
        # 1. 读取文件
        if file_type == 'csv':
            df = pd.read_csv(file_path, header=None, names=['name', 'description', 'subscribers'])
        elif file_type == 'excel':
            df = pd.read_excel(file_path, header=None, names=['name', 'description', 'subscribers'])
        else:
            return {
                'success': False,
                'data': None,
                'message': f'不支持的文件类型: {file_type}',
                'errors': [f'file_type must be csv or excel, got {file_type}']
            }

        # 2. 数据验证
        df = df.dropna(subset=['name'])  # 移除name为空的行
        df['subscribers'] = df['subscribers'].fillna(0).astype(int)
        df = df[df['subscribers'] >= 0]  # 移除subscribers < 0的行

        # 3. 标记描述为空的记录
        df['ai_analysis_status'] = df['description'].apply(
            lambda x: 'skipped' if pd.isna(x) or str(x).strip() == '' else 'pending'
        )

        # 4. 去重
        if skip_duplicates:
            df = df.sort_values('subscribers', ascending=False)
            df = df.drop_duplicates(subset=['name'], keep='first')

        # 5. 生成batch_id
        if not batch_id:
            batch_id = f"reddit_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        df['import_batch_id'] = batch_id

        # 6. 转换为字典列表
        records = df.to_dict('records')

        # 7. 批量插入
        with RedditSubredditRepository() as repo:
            imported_count = repo.bulk_insert(records)

        skipped_count = len(df[df['ai_analysis_status'] == 'skipped'])

        return {
            'success': True,
            'data': {
                'imported_count': imported_count,
                'skipped_count': skipped_count,
                'error_count': 0,
                'batch_id': batch_id
            },
            'message': f'成功导入 {imported_count} 条记录',
            'errors': []
        }

    except Exception as e:
        return {
            'success': False,
            'data': None,
            'message': f'导入失败: {str(e)}',
            'errors': [str(e)]
        }
```

---

## AI分析API

### 2. analyze_subreddits

批量分析Reddit板块

**函数签名**:
```python
def analyze_subreddits(
    subreddit_ids: Optional[List[int]] = None,
    config_id: Optional[int] = None,
    batch_size: int = 10,
    status_filter: str = 'pending'
) -> Dict[str, Any]:
    """
    批量分析Reddit板块

    Args:
        subreddit_ids: 板块ID列表（可选，默认分析所有pending状态的板块）
        config_id: AI配置ID（可选，默认使用默认配置）
        batch_size: 批次大小（默认10）
        status_filter: 状态筛选（默认'pending'）

    Returns:
        {
            'success': True/False,
            'data': {
                'analyzed_count': int,      # 成功分析数量
                'failed_count': int,        # 失败数量
                'skipped_count': int,       # 跳过数量
                'results': List[Dict]       # 分析结果列表
            },
            'message': str,
            'errors': List[str]
        }
    """
```

**业务逻辑**:
```
1. 获取待分析的板块列表
   - 如果提供subreddit_ids，按ID查询
   - 否则按status_filter查询
   ↓
2. 获取AI配置
   - 如果提供config_id，按ID查询
   - 否则获取默认配置
   ↓
3. 批量处理（每批batch_size条）
   ↓
4. 对每个板块：
   a. 更新状态为'processing'
   b. 调用LLM API
   c. 解析JSON响应
   d. 更新数据库记录
   e. 记录分析时间和模型信息
   ↓
5. 返回分析统计
```

**代码示例**:
```python
from typing import Dict, Any, Optional, List
from ai.client import LLMClient
from storage.reddit_repository import RedditSubredditRepository, AIPromptConfigRepository
import json
from datetime import datetime

def analyze_subreddits(
    subreddit_ids: Optional[List[int]] = None,
    config_id: Optional[int] = None,
    batch_size: int = 10,
    status_filter: str = 'pending'
) -> Dict[str, Any]:
    try:
        # 1. 获取待分析的板块
        with RedditSubredditRepository() as repo:
            if subreddit_ids:
                subreddits = repo.get_by_ids(subreddit_ids)
            else:
                subreddits = repo.get_by_status(status_filter, limit=1000)

        if not subreddits:
            return {
                'success': True,
                'data': {
                    'analyzed_count': 0,
                    'failed_count': 0,
                    'skipped_count': 0,
                    'results': []
                },
                'message': '没有待分析的板块',
                'errors': []
            }

        # 2. 获取AI配置
        with AIPromptConfigRepository() as config_repo:
            if config_id:
                config = config_repo.get_by_id(config_id)
            else:
                config = config_repo.get_default_config('reddit_analysis')

        if not config:
            return {
                'success': False,
                'data': None,
                'message': 'AI配置不存在',
                'errors': ['Config not found']
            }

        # 3. 初始化LLM客户端
        llm_client = LLMClient()

        # 4. 批量处理
        analyzed_count = 0
        failed_count = 0
        skipped_count = 0
        results = []
        errors = []

        for i in range(0, len(subreddits), batch_size):
            batch = subreddits[i:i+batch_size]

            for subreddit in batch:
                try:
                    # 更新状态为processing
                    with RedditSubredditRepository() as repo:
                        repo.update_status(subreddit['subreddit_id'], 'processing')

                    # 构建提示词
                    prompt = config['prompt_template'].format(
                        name=subreddit['name'],
                        description=subreddit['description'] or '',
                        subscribers=subreddit['subscribers']
                    )

                    # 调用LLM
                    response = llm_client.chat(
                        messages=[
                            {"role": "system", "content": config['system_message']},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=float(config['temperature']),
                        max_tokens=config['max_tokens']
                    )

                    # 解析响应
                    result = json.loads(response)

                    # 更新数据库
                    with RedditSubredditRepository() as repo:
                        repo.update(subreddit['subreddit_id'], {
                            'tag1': result.get('tag1'),
                            'tag2': result.get('tag2'),
                            'tag3': result.get('tag3'),
                            'importance_score': result.get('importance_score'),
                            'ai_confidence': result.get('confidence'),
                            'ai_analysis_status': 'completed',
                            'ai_analysis_timestamp': datetime.now(),
                            'ai_model_used': llm_client.model
                        })

                    analyzed_count += 1
                    results.append({
                        'subreddit_id': subreddit['subreddit_id'],
                        'name': subreddit['name'],
                        'status': 'completed',
                        'tags': [result.get('tag1'), result.get('tag2'), result.get('tag3')],
                        'importance_score': result.get('importance_score')
                    })

                except Exception as e:
                    # 标记为失败
                    with RedditSubredditRepository() as repo:
                        repo.update_status(subreddit['subreddit_id'], 'failed')

                    failed_count += 1
                    errors.append(f"{subreddit['name']}: {str(e)}")

        return {
            'success': True,
            'data': {
                'analyzed_count': analyzed_count,
                'failed_count': failed_count,
                'skipped_count': skipped_count,
                'results': results
            },
            'message': f'成功分析 {analyzed_count} 个板块，失败 {failed_count} 个',
            'errors': errors
        }

    except Exception as e:
        return {
            'success': False,
            'data': None,
            'message': f'分析失败: {str(e)}',
            'errors': [str(e)]
        }
```

---

## 数据查询API

### 3. query_subreddits

查询Reddit板块列表（支持筛选、排序、分页）

**函数签名**:
```python
def query_subreddits(
    filters: Optional[Dict[str, Any]] = None,
    sort_by: str = 'created_at',
    sort_order: str = 'desc',
    limit: int = 100,
    offset: int = 0
) -> Dict[str, Any]:
    """
    查询Reddit板块列表

    Args:
        filters: 筛选条件字典
            {
                'status': List[str],              # 状态列表
                'tags': List[str],                # 标签列表（OR查询）
                'importance_score_min': int,      # 最小评分
                'importance_score_max': int,      # 最大评分
                'subscribers_min': int,           # 最小订阅数
                'subscribers_max': int,           # 最大订阅数
                'batch_id': str,                  # 批次ID
                'search_text': str                # 搜索文本（名称或描述）
            }
        sort_by: 排序字段（默认'created_at'）
        sort_order: 排序方向（'asc'或'desc'，默认'desc'）
        limit: 返回数量限制（默认100）
        offset: 偏移量（默认0）

    Returns:
        {
            'success': True/False,
            'data': {
                'total': int,               # 总数量
                'data': List[Dict],         # 数据列表
                'page': int,                # 当前页
                'page_size': int,           # 每页大小
                'has_more': bool            # 是否有更多数据
            },
            'message': str,
            'errors': List[str]
        }
    """
```

**代码示例**:
```python
from typing import Dict, Any, Optional, List
from storage.reddit_repository import RedditSubredditRepository

def query_subreddits(
    filters: Optional[Dict[str, Any]] = None,
    sort_by: str = 'created_at',
    sort_order: str = 'desc',
    limit: int = 100,
    offset: int = 0
) -> Dict[str, Any]:
    try:
        with RedditSubredditRepository() as repo:
            # 查询数据
            result = repo.query(
                filters=filters,
                sort_by=sort_by,
                sort_order=sort_order,
                limit=limit,
                offset=offset
            )

            total = result['total']
            data = result['data']

            return {
                'success': True,
                'data': {
                    'total': total,
                    'data': data,
                    'page': offset // limit + 1,
                    'page_size': limit,
                    'has_more': offset + limit < total
                },
                'message': f'查询成功，共 {total} 条记录',
                'errors': []
            }

    except Exception as e:
        return {
            'success': False,
            'data': None,
            'message': f'查询失败: {str(e)}',
            'errors': [str(e)]
        }
```

---

### 4. get_tag_statistics

获取标签统计信息

**函数签名**:
```python
def get_tag_statistics() -> Dict[str, Any]:
    """
    获取标签统计信息

    Returns:
        {
            'success': True/False,
            'data': {
                'tag_counts': Dict[str, int],     # 标签计数
                'tag_groups': Dict[str, List],    # 标签分组
                'total_tags': int                 # 总标签数
            },
            'message': str,
            'errors': List[str]
        }
    """
```

---

## 配置管理API

### 5. get_prompt_configs

获取AI提示词配置列表

**函数签名**:
```python
def get_prompt_configs(
    config_type: str = 'reddit_analysis',
    active_only: bool = True
) -> Dict[str, Any]:
    """
    获取AI提示词配置列表

    Args:
        config_type: 配置类型（默认'reddit_analysis'）
        active_only: 仅返回启用的配置（默认True）

    Returns:
        {
            'success': True/False,
            'data': List[Dict],
            'message': str,
            'errors': List[str]
        }
    """
```

---

### 6. save_prompt_config

保存AI提示词配置

**函数签名**:
```python
def save_prompt_config(
    config_data: Dict[str, Any],
    config_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    保存AI提示词配置

    Args:
        config_data: 配置数据字典
        config_id: 配置ID（可选，提供则更新，否则创建）

    Returns:
        {
            'success': True/False,
            'data': Dict,           # 保存后的配置
            'message': str,
            'errors': List[str]
        }
    """
```

---

## 导出功能API

### 7. export_to_csv

导出数据为CSV格式

**函数签名**:
```python
def export_to_csv(
    subreddit_ids: Optional[List[int]] = None,
    filters: Optional[Dict[str, Any]] = None,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    导出Reddit板块数据为CSV

    Args:
        subreddit_ids: 板块ID列表（可选）
        filters: 筛选条件（可选）
        output_path: 输出路径（可选，默认自动生成）

    Returns:
        {
            'success': True/False,
            'data': {
                'file_path': str,       # 文件路径
                'record_count': int     # 记录数量
            },
            'message': str,
            'errors': List[str]
        }
    """
```

---

## 错误处理

### 错误类型

```python
class RedditAnalyzerError(Exception):
    """Reddit分析器基础异常"""
    pass

class FileImportError(RedditAnalyzerError):
    """文件导入异常"""
    pass

class AIAnalysisError(RedditAnalyzerError):
    """AI分析异常"""
    pass

class ConfigNotFoundError(RedditAnalyzerError):
    """配置不存在异常"""
    pass

class ValidationError(RedditAnalyzerError):
    """数据验证异常"""
    pass
```

### 错误处理示例

```python
try:
    result = import_reddit_data(file_path, file_type)
    if not result['success']:
        st.error(result['message'])
        for error in result['errors']:
            st.error(f"- {error}")
except FileImportError as e:
    st.error(f"文件导入失败: {str(e)}")
except Exception as e:
    st.error(f"未知错误: {str(e)}")
```

---

**文档版本**: v1.0
**最后更新**: 2026-01-09

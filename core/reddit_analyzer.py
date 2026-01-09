"""
Reddit板块分析功能 - 核心业务逻辑层

提供Reddit板块分析的核心功能：
1. 数据导入（CSV/Excel）
2. AI分析（批量分析板块）
3. 标签管理（统计、搜索）
4. 数据导出（CSV/Excel）
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import pandas as pd
import json
from pathlib import Path

from ai.client import LLMClient
from storage.reddit_repository import (
    RedditSubredditRepository,
    AIPromptConfigRepository
)


class RedditAnalyzer:
    """Reddit板块分析器"""

    def __init__(self):
        """初始化分析器"""
        self.llm_client = LLMClient()

    # ==================== 文件导入方法 ====================

    def import_from_csv(
        self,
        file_path: str,
        batch_id: Optional[str] = None,
        skip_duplicates: bool = True
    ) -> Dict[str, Any]:
        """
        从CSV导入数据

        Args:
            file_path: CSV文件路径
            batch_id: 导入批次ID（可选，默认自动生成）
            skip_duplicates: 是否跳过重复记录（默认True）

        Returns:
            {
                'success': True/False,
                'data': {
                    'imported_count': int,
                    'skipped_count': int,
                    'error_count': int,
                    'batch_id': str
                },
                'message': str,
                'errors': List[str]
            }
        """
        try:
            # 读取CSV文件（无列名，按列顺序）
            df = pd.read_csv(
                file_path,
                header=None,
                names=['name', 'description', 'subscribers']
            )

            return self._process_import(df, batch_id, skip_duplicates)

        except Exception as e:
            return {
                'success': False,
                'data': None,
                'message': f'导入失败: {str(e)}',
                'errors': [str(e)]
            }

    def import_from_excel(
        self,
        file_path: str,
        batch_id: Optional[str] = None,
        skip_duplicates: bool = True
    ) -> Dict[str, Any]:
        """
        从Excel导入数据

        Args:
            file_path: Excel文件路径
            batch_id: 导入批次ID（可选，默认自动生成）
            skip_duplicates: 是否跳过重复记录（默认True）

        Returns:
            同import_from_csv
        """
        try:
            # 读取Excel文件（无列名，按列顺序）
            df = pd.read_excel(
                file_path,
                header=None,
                names=['name', 'description', 'subscribers']
            )

            return self._process_import(df, batch_id, skip_duplicates)

        except Exception as e:
            return {
                'success': False,
                'data': None,
                'message': f'导入失败: {str(e)}',
                'errors': [str(e)]
            }

    def _process_import(
        self,
        df: pd.DataFrame,
        batch_id: Optional[str],
        skip_duplicates: bool
    ) -> Dict[str, Any]:
        """
        处理导入数据（内部方法）

        Args:
            df: DataFrame
            batch_id: 批次ID
            skip_duplicates: 是否跳过重复

        Returns:
            导入结果
        """
        try:
            # 1. 数据验证
            df = df.dropna(subset=['name'])  # 移除name为空的行

            # 处理subscribers字段：将NaN转换为0
            df['subscribers'] = df['subscribers'].fillna(0)
            # 确保是整数类型
            df['subscribers'] = pd.to_numeric(df['subscribers'], errors='coerce').fillna(0).astype(int)
            df = df[df['subscribers'] >= 0]  # 移除subscribers < 0的行

            # 处理description字段：将NaN转换为None
            df['description'] = df['description'].replace({pd.NA: None, float('nan'): None})
            df['description'] = df['description'].apply(lambda x: None if pd.isna(x) else str(x))

            # 2. 标记描述为空的记录
            df['ai_analysis_status'] = df['description'].apply(
                lambda x: 'skipped' if x is None or str(x).strip() == '' or str(x) == 'None' else 'pending'
            )

            # 3. 去重
            if skip_duplicates:
                df = df.sort_values('subscribers', ascending=False)
                df = df.drop_duplicates(subset=['name'], keep='first')

            # 4. 生成batch_id
            if not batch_id:
                batch_id = f"reddit_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            df['import_batch_id'] = batch_id

            # 5. 转换为字典列表
            records = df.to_dict('records')

            # 6. 批量插入
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
                'message': f'处理导入数据失败: {str(e)}',
                'errors': [str(e)]
            }

    # ==================== AI分析方法 ====================

    def analyze_subreddits(
        self,
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
                    'analyzed_count': int,
                    'failed_count': int,
                    'skipped_count': int,
                    'results': List[Dict]
                },
                'message': str,
                'errors': List[str]
            }
        """
        try:
            # 1. 获取待分析的板块
            with RedditSubredditRepository() as repo:
                if subreddit_ids:
                    # 按ID查询
                    subreddits = []
                    for sid in subreddit_ids:
                        s = repo.get_by_id(sid)
                        if s:
                            subreddits.append(s)
                else:
                    # 按状态查询
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

            # 3. 批量处理
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
                        response = self.llm_client._call_llm(
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
                                'ai_model_used': self.llm_client.config['model']
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

    # ==================== 标签管理方法 ====================

    def get_all_tags(self) -> List[str]:
        """
        获取所有标签

        Returns:
            标签列表（去重排序）
        """
        with RedditSubredditRepository() as repo:
            tag_stats = repo.get_tag_statistics()

        return sorted(tag_stats.keys())

    def get_tag_statistics(self) -> Dict[str, Any]:
        """
        获取标签统计

        Returns:
            {
                'success': True/False,
                'data': {
                    'tag_counts': Dict[str, int],
                    'total_tags': int
                },
                'message': str,
                'errors': List[str]
            }
        """
        try:
            with RedditSubredditRepository() as repo:
                tag_counts = repo.get_tag_statistics()

            return {
                'success': True,
                'data': {
                    'tag_counts': tag_counts,
                    'total_tags': len(tag_counts)
                },
                'message': f'共 {len(tag_counts)} 个标签',
                'errors': []
            }

        except Exception as e:
            return {
                'success': False,
                'data': None,
                'message': f'获取标签统计失败: {str(e)}',
                'errors': [str(e)]
            }

    # ==================== 数据查询方法 ====================

    def query_subreddits(
        self,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = 'created_at',
        sort_order: str = 'desc',
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        查询Reddit板块列表

        Args:
            filters: 筛选条件
            sort_by: 排序字段
            sort_order: 排序方向
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            {
                'success': True/False,
                'data': {
                    'total': int,
                    'data': List[Dict],
                    'page': int,
                    'page_size': int,
                    'has_more': bool
                },
                'message': str,
                'errors': List[str]
            }
        """
        try:
            with RedditSubredditRepository() as repo:
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

    # ==================== 配置管理方法 ====================

    def get_prompt_configs(
        self,
        config_type: str = 'reddit_analysis',
        active_only: bool = True
    ) -> Dict[str, Any]:
        """
        获取AI提示词配置列表

        Args:
            config_type: 配置类型
            active_only: 仅返回启用的配置

        Returns:
            {
                'success': True/False,
                'data': List[Dict],
                'message': str,
                'errors': List[str]
            }
        """
        try:
            with AIPromptConfigRepository() as repo:
                if active_only:
                    configs = repo.get_active_configs(config_type)
                else:
                    configs = repo.get_all_configs()

            return {
                'success': True,
                'data': configs,
                'message': f'共 {len(configs)} 个配置',
                'errors': []
            }

        except Exception as e:
            return {
                'success': False,
                'data': None,
                'message': f'获取配置失败: {str(e)}',
                'errors': [str(e)]
            }

    def save_prompt_config(
        self,
        config_data: Dict[str, Any],
        config_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        保存AI提示词配置

        Args:
            config_data: 配置数据
            config_id: 配置ID（可选，提供则更新，否则创建）

        Returns:
            {
                'success': True/False,
                'data': Dict,
                'message': str,
                'errors': List[str]
            }
        """
        try:
            with AIPromptConfigRepository() as repo:
                if config_id:
                    # 更新
                    success = repo.update(config_id, config_data)
                    if success:
                        config = repo.get_by_id(config_id)
                        return {
                            'success': True,
                            'data': config,
                            'message': '配置更新成功',
                            'errors': []
                        }
                    else:
                        return {
                            'success': False,
                            'data': None,
                            'message': '配置更新失败',
                            'errors': ['Update failed']
                        }
                else:
                    # 创建
                    new_id = repo.create(config_data)
                    config = repo.get_by_id(new_id)
                    return {
                        'success': True,
                        'data': config,
                        'message': '配置创建成功',
                        'errors': []
                    }

        except Exception as e:
            return {
                'success': False,
                'data': None,
                'message': f'保存配置失败: {str(e)}',
                'errors': [str(e)]
            }

    # ==================== 导出方法 ====================

    def export_to_csv(
        self,
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
                    'file_path': str,
                    'record_count': int
                },
                'message': str,
                'errors': List[str]
            }
        """
        try:
            # 1. 查询数据
            if subreddit_ids:
                with RedditSubredditRepository() as repo:
                    data = []
                    for sid in subreddit_ids:
                        s = repo.get_by_id(sid)
                        if s:
                            data.append(s)
            else:
                result = self.query_subreddits(filters=filters, limit=10000)
                if not result['success']:
                    return result
                data = result['data']['data']

            if not data:
                return {
                    'success': False,
                    'data': None,
                    'message': '没有数据可导出',
                    'errors': ['No data to export']
                }

            # 2. 转换为DataFrame
            df = pd.DataFrame(data)

            # 3. 生成输出路径
            if not output_path:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_path = f"reddit_export_{timestamp}.csv"

            # 4. 导出CSV
            df.to_csv(output_path, index=False, encoding='utf-8-sig')

            return {
                'success': True,
                'data': {
                    'file_path': output_path,
                    'record_count': len(data)
                },
                'message': f'成功导出 {len(data)} 条记录',
                'errors': []
            }

        except Exception as e:
            return {
                'success': False,
                'data': None,
                'message': f'导出失败: {str(e)}',
                'errors': [str(e)]
            }


# ==================== 便捷导入 ====================
__all__ = ['RedditAnalyzer']

"""
用户偏好设置管理模块
保存和加载用户在Phase 0中的操作配置
"""
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


class UserPreferences:
    """用户偏好设置管理器"""

    def __init__(self, config_file: str = "phase0_preferences.json"):
        """
        初始化用户偏好设置管理器

        Args:
            config_file: 配置文件名（保存在config目录下）
        """
        self.config_dir = Path(__file__).parent.parent / "config"
        self.config_dir.mkdir(exist_ok=True)
        self.config_file = self.config_dir / config_file

    def load_preferences(self) -> Dict[str, Any]:
        """
        加载用户偏好设置

        Returns:
            配置字典，如果文件不存在则返回默认配置
        """
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载配置文件失败: {e}")
                return self._get_default_preferences()
        else:
            return self._get_default_preferences()

    def save_preferences(self, preferences: Dict[str, Any]) -> bool:
        """
        保存用户偏好设置

        Args:
            preferences: 配置字典

        Returns:
            是否保存成功
        """
        try:
            # 添加最后更新时间
            preferences['last_updated'] = datetime.now().isoformat()

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(preferences, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False

    def update_preference(self, key: str, value: Any) -> bool:
        """
        更新单个配置项

        Args:
            key: 配置项名称
            value: 配置项值

        Returns:
            是否更新成功
        """
        preferences = self.load_preferences()
        preferences[key] = value
        return self.save_preferences(preferences)

    def get_preference(self, key: str, default: Any = None) -> Any:
        """
        获取单个配置项

        Args:
            key: 配置项名称
            default: 默认值

        Returns:
            配置项值
        """
        preferences = self.load_preferences()
        return preferences.get(key, default)

    def reset_to_defaults(self) -> bool:
        """
        重置为默认配置

        Returns:
            是否重置成功
        """
        return self.save_preferences(self._get_default_preferences())

    def _get_default_preferences(self) -> Dict[str, Any]:
        """
        获取默认配置

        Returns:
            默认配置字典
        """
        return {
            # 分词配置
            'segmentation': {
                'min_frequency': 2,              # 单词最小频次
                'min_ngram_frequency': 3,        # 短语最小频次
                'sort_by': 'frequency',          # 排序方式
                'enable_pos_tagging': True,      # 启用词性标注
                'extract_ngrams': True,          # 提取短语
            },

            # 筛选配置
            'filtering': {
                'freq_range': None,              # 频次范围（动态，不保存）
                'selected_word_counts': None,    # 选中的词数（动态，不保存）
                'selected_pos': [],              # 选中的词性
                'exclude_seeds': False,          # 排除词根
            },

            # 翻译配置
            'translation': {
                'translate_enabled': False,      # 是否启用翻译
            },

            # 导出配置
            'export': {
                'export_selected_only': False,   # 仅导出选中项
            },

            # 元数据
            'last_updated': None,
        }


# 全局单例
_preferences_instance: Optional[UserPreferences] = None


def get_preferences_manager() -> UserPreferences:
    """
    获取用户偏好设置管理器单例

    Returns:
        UserPreferences实例
    """
    global _preferences_instance
    if _preferences_instance is None:
        _preferences_instance = UserPreferences()
    return _preferences_instance


def load_phase0_preferences() -> Dict[str, Any]:
    """
    加载Phase 0的用户偏好设置

    Returns:
        配置字典
    """
    manager = get_preferences_manager()
    return manager.load_preferences()


def save_phase0_preferences(preferences: Dict[str, Any]) -> bool:
    """
    保存Phase 0的用户偏好设置

    Args:
        preferences: 配置字典

    Returns:
        是否保存成功
    """
    manager = get_preferences_manager()
    return manager.save_preferences(preferences)


def update_phase0_preference(category: str, key: str, value: Any) -> bool:
    """
    更新Phase 0的单个配置项

    Args:
        category: 配置分类（segmentation/filtering/translation/export）
        key: 配置项名称
        value: 配置项值

    Returns:
        是否更新成功
    """
    manager = get_preferences_manager()
    preferences = manager.load_preferences()

    if category not in preferences:
        preferences[category] = {}

    preferences[category][key] = value
    return manager.save_preferences(preferences)


# 测试代码
if __name__ == "__main__":
    # 测试保存和加载
    manager = get_preferences_manager()

    # 加载默认配置
    prefs = manager.load_preferences()
    print("默认配置:")
    print(json.dumps(prefs, ensure_ascii=False, indent=2))

    # 更新配置
    print("\n更新配置...")
    update_phase0_preference('segmentation', 'min_frequency', 10)
    update_phase0_preference('segmentation', 'min_ngram_frequency', 6)

    # 重新加载
    prefs = manager.load_preferences()
    print("\n更新后的配置:")
    print(json.dumps(prefs, ensure_ascii=False, indent=2))

    # 重置配置
    print("\n重置配置...")
    manager.reset_to_defaults()

    prefs = manager.load_preferences()
    print("\n重置后的配置:")
    print(json.dumps(prefs, ensure_ascii=False, indent=2))

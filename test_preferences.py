"""
测试用户偏好设置保存功能
"""
from utils.user_preferences import get_preferences_manager, load_phase0_preferences, update_phase0_preference
import json

print("=" * 70)
print("测试用户偏好设置功能")
print("=" * 70)

# 1. 加载默认配置
print("\n【测试1】加载默认配置")
prefs = load_phase0_preferences()
print(json.dumps(prefs, ensure_ascii=False, indent=2))

# 2. 模拟用户修改参数
print("\n【测试2】模拟用户修改参数")
print("修改最小频次为10...")
update_phase0_preference('segmentation', 'min_frequency', 10)

print("修改短语最小频次为6...")
update_phase0_preference('segmentation', 'min_ngram_frequency', 6)

print("启用翻译...")
update_phase0_preference('translation', 'translate_enabled', True)

print("启用排除词根...")
update_phase0_preference('filtering', 'exclude_seeds', True)

# 3. 重新加载配置，验证保存
print("\n【测试3】重新加载配置，验证保存")
prefs = load_phase0_preferences()
print(json.dumps(prefs, ensure_ascii=False, indent=2))

# 4. 验证关键配置项
print("\n【测试4】验证关键配置项")
print(f"✓ 最小频次: {prefs['segmentation']['min_frequency']} (期望: 10)")
print(f"✓ 短语最小频次: {prefs['segmentation']['min_ngram_frequency']} (期望: 6)")
print(f"✓ 启用翻译: {prefs['translation']['translate_enabled']} (期望: True)")
print(f"✓ 排除词根: {prefs['filtering']['exclude_seeds']} (期望: True)")

assert prefs['segmentation']['min_frequency'] == 10, "最小频次保存失败"
assert prefs['segmentation']['min_ngram_frequency'] == 6, "短语最小频次保存失败"
assert prefs['translation']['translate_enabled'] == True, "翻译配置保存失败"
assert prefs['filtering']['exclude_seeds'] == True, "排除词根配置保存失败"

print("\n✅ 所有测试通过！")

# 5. 重置为默认配置
print("\n【测试5】重置为默认配置")
manager = get_preferences_manager()
manager.reset_to_defaults()
prefs = load_phase0_preferences()
print(f"✓ 最小频次: {prefs['segmentation']['min_frequency']} (期望: 2)")
print(f"✓ 翻译启用: {prefs['translation']['translate_enabled']} (期望: False)")

print("\n" + "=" * 70)
print("测试完成！配置文件位置: config/phase0_preferences.json")
print("=" * 70)

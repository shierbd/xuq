"""
英译中翻译服务模块
支持批量翻译，使用deep-translator库（无依赖冲突）

deep-translator支持多种翻译服务:
- Google Translate (免费)
- DeepL (需要API key)
- 百度翻译 (需要API key)
- 有道翻译 (需要API key)
等等

本模块使用Google Translate（免费，无需API key）
"""
import time
from typing import List, Dict

# 尝试导入翻译库，如果失败则标记为不可用
try:
    from deep_translator import GoogleTranslator
    TRANSLATION_AVAILABLE = True
except ImportError:
    TRANSLATION_AVAILABLE = False
    GoogleTranslator = None


def translate_words_batch(words: List[str],
                          batch_size: int = 100,
                          delay: float = 0.3) -> Dict[str, str]:
    """
    批量将英文词汇翻译为中文（优化版：真正的批量翻译）

    策略：将多个词用换行符连接，一次性翻译，再拆分结果
    这样大大减少网络请求次数，速度提升10倍以上

    Args:
        words: 英文词汇列表
        batch_size: 批次大小（默认100个词一批）
        delay: 批次间延迟（秒，默认0.3秒）

    Returns:
        翻译字典 {英文: 中文}

    Example:
        >>> words = ["calculator", "dashboard", "simulator"]
        >>> translations = translate_words_batch(words)
        >>> translations
        {'calculator': '计算器', 'dashboard': '仪表盘', 'simulator': '模拟器'}
    """
    if not TRANSLATION_AVAILABLE:
        print("⚠️  翻译功能不可用：deep-translator未安装")
        print("提示：运行 pip install deep-translator 安装翻译库")
        return {word: word for word in words}  # 返回原文

    translator = GoogleTranslator(source='en', target='zh-CN')
    translations = {}

    # 去重
    unique_words = list(dict.fromkeys(words))  # 保持顺序去重
    total_batches = (len(unique_words) + batch_size - 1) // batch_size

    print(f"开始翻译 {len(unique_words)} 个词，共 {total_batches} 批...")

    # 分批处理
    for batch_idx in range(0, len(unique_words), batch_size):
        batch = unique_words[batch_idx:batch_idx + batch_size]
        current_batch = batch_idx // batch_size + 1

        try:
            # 关键优化：将多个词用换行符连接成一个文本
            # 这样只需要一次网络请求就能翻译整批词
            text_to_translate = '\n'.join(batch)

            # 一次性翻译整批
            translated_text = translator.translate(text_to_translate)

            # 拆分翻译结果
            translated_words = translated_text.split('\n')

            # 建立映射
            for i, word in enumerate(batch):
                if i < len(translated_words):
                    translations[word] = translated_words[i].strip()
                else:
                    translations[word] = word  # 如果拆分失败，保留原文

            print(f"[OK] 完成第 {current_batch}/{total_batches} 批 ({len(batch)} 个词)")

            # 批次间延迟，避免触发限流
            if batch_idx + batch_size < len(unique_words):
                time.sleep(delay)

        except Exception as e:
            print(f"[警告] 批量翻译失败 (第{current_batch}批): {str(e)}")
            print("   尝试逐个翻译此批次...")

            # 失败时回退到逐个翻译（仅针对失败的批次）
            for word in batch:
                try:
                    result = translator.translate(word)
                    translations[word] = result
                    time.sleep(0.1)  # 逐个翻译时添加短暂延迟
                except Exception as word_error:
                    print(f"   [警告] 翻译失败: {word} - {str(word_error)}")
                    translations[word] = word  # 保留原文

    print(f"[OK] 翻译完成！成功翻译 {len(translations)} 个词")
    return translations


def translate_single_word(word: str, retry: int = 3) -> str:
    """
    翻译单个英文词汇为中文

    Args:
        word: 英文词汇
        retry: 重试次数

    Returns:
        中文翻译（失败时返回原文）

    Example:
        >>> translate_single_word("calculator")
        '计算器'
    """
    if not TRANSLATION_AVAILABLE:
        return word  # 翻译不可用时返回原文

    translator = GoogleTranslator(source='en', target='zh-CN')

    for attempt in range(retry):
        try:
            result = translator.translate(word)
            return result
        except Exception as e:
            if attempt == retry - 1:
                print(f"⚠️  翻译失败 ({retry}次尝试): {word} - {str(e)}")
                return word  # 失败时返回原文
            time.sleep(0.5)  # 短暂延迟后重试

    return word


def get_supported_languages() -> Dict[str, str]:
    """
    获取支持的语言列表

    Returns:
        语言代码与名称的字典

    Example:
        >>> languages = get_supported_languages()
        >>> 'zh-CN' in languages
        True
    """
    if not TRANSLATION_AVAILABLE:
        return {}

    try:
        # deep-translator支持的语言
        from deep_translator import GoogleTranslator
        return GoogleTranslator.get_supported_languages(as_dict=True)
    except Exception:
        return {}


# 测试代码
if __name__ == "__main__":
    print("=== 翻译服务测试 ===\n")

    if not TRANSLATION_AVAILABLE:
        print("❌ deep-translator不可用")
        print("请运行: pip install deep-translator")
        exit(1)

    # 1. 测试单词翻译
    print("【测试1】单词翻译")
    test_word = "calculator"
    translation = translate_single_word(test_word)
    print(f"  {test_word} → {translation}\n")

    # 2. 测试批量翻译
    print("【测试2】批量翻译")
    test_words = [
        "calculator",
        "dashboard",
        "simulator",
        "downloader",
        "editor"
    ]

    translations = translate_words_batch(test_words, batch_size=10, delay=0.2)
    print("  翻译结果:")
    for en, cn in translations.items():
        print(f"    {en} → {cn}")

    # 3. 测试支持的语言
    print("\n【测试3】支持的语言")
    languages = get_supported_languages()
    print(f"  共支持 {len(languages)} 种语言")
    print(f"  英语: {languages.get('english', 'N/A')}")
    print(f"  简体中文: {languages.get('chinese (simplified)', 'N/A')}")

    print("\n✅ 所有测试完成！")

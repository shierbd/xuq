#!/usr/bin/env python3
"""测试预处理函数是否正确工作"""

import re

def preprocess_text(text: str) -> str:
    """
    预处理商品名称文本（复制自 clustering_service.py）
    """
    if not text:
        return ""

    # 1. 转小写
    text = text.lower()

    # 2. 去除特殊字符(保留字母、数字、空格)
    text = re.sub(r'[|/\\()\[\]{}<>]', ' ', text)

    # 3. 去除尺寸信息
    text = re.sub(r'\d+x\d+', '', text)  # 8x10, 5x7
    text = re.sub(r'\d+\s*(mm|cm|inch|in|ft|px)', '', text)  # 50mm, 8in

    # 4. 去除常见停用词（只移除真正的噪音词，保留产品类型标识符）
    # 保留: template, digital, printable, editable（这些是重要的产品类型词）
    stop_words = [
        'instant', 'download',  # 时效性词汇
        'file', 'files',  # 格式词汇
    ]
    for word in stop_words:
        text = re.sub(rf'\b{word}\b', '', text, flags=re.IGNORECASE)

    # 5. 清理多余空格
    text = ' '.join(text.split())

    return text.strip()

# 测试用例
test_cases = [
    "Digital Wedding Template Instant Download",
    "Printable Birthday Card Editable PDF File",
    "Canva Template Bundle Pack Set Design",
    "Wedding Invitation Template Digital Download",
]

print("=" * 60)
print("预处理函数测试")
print("=" * 60)

for text in test_cases:
    processed = preprocess_text(text)
    print(f"\n原始文本: {text}")
    print(f"处理后:   {processed}")

print("\n" + "=" * 60)
print("预期行为:")
print("- 应该保留: template, digital, printable, editable, pdf, canva, bundle, pack, set, design")
print("- 应该移除: instant, download, file, files")
print("=" * 60)

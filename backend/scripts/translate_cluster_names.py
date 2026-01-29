"""
批量翻译类别名称（英文 -> 中文）
使用 DeepSeek API 翻译所有 cluster_name 到 cluster_name_cn
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

from datetime import datetime
from sqlalchemy import distinct
from backend.database import SessionLocal
from backend.models.product import Product

def call_ai_api(prompt: str) -> str:
    """调用AI API进行翻译"""
    api_key = os.getenv('DEEPSEEK_API_KEY') or os.getenv('CLAUDE_API_KEY')
    use_claude = bool(os.getenv('CLAUDE_API_KEY'))

    if not api_key:
        raise Exception("未找到API密钥")

    try:
        if use_claude:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            message = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=100,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text.strip()
        else:
            import requests
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 100
                }
            )
            return response.json()['choices'][0]['message']['content'].strip()
    except Exception as e:
        raise Exception(f"AI API调用失败: {e}")

def translate_cluster_names():
    """批量翻译所有类别名称"""
    db = SessionLocal()

    try:
        # 获取所有不同的英文类别名称
        print("正在获取所有类别名称...")
        cluster_names = db.query(distinct(Product.cluster_name)).filter(
            Product.cluster_name.isnot(None),
            Product.cluster_name != ""
        ).all()

        cluster_names = [name[0] for name in cluster_names]
        total = len(cluster_names)
        print(f"找到 {total} 个不同的类别名称")

        if total == 0:
            print("没有需要翻译的类别名称")
            return

        # 批量翻译
        print("\n开始批量翻译...")
        start_time = datetime.now()
        success_count = 0
        failed_count = 0

        for i, en_name in enumerate(cluster_names, 1):
            try:
                print(f"\n[{i}/{total}] 翻译: {en_name}")

                # 构建翻译提示词
                prompt = f"""请将以下英文类别名称翻译成简洁的中文（不超过10个字）：

英文名称: {en_name}

要求：
1. 翻译要准确、简洁
2. 保持专业术语的准确性
3. 只返回中文翻译，不要其他内容

中文翻译："""

                # 调用 AI 翻译
                cn_name = call_ai_api(prompt)
                cn_name = cn_name.strip()

                print(f"   -> {cn_name}")

                # 更新数据库中所有该类别的商品
                updated = db.query(Product).filter(
                    Product.cluster_name == en_name
                ).update({
                    "cluster_name_cn": cn_name
                })

                db.commit()
                print(f"   更新了 {updated} 个商品")

                success_count += 1

            except Exception as e:
                print(f"   [错误] {str(e)}")
                failed_count += 1
                continue

        # 统计结果
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        print("\n" + "="*60)
        print("翻译完成！")
        print("="*60)
        print(f"总数: {total}")
        print(f"成功: {success_count}")
        print(f"失败: {failed_count}")
        print(f"耗时: {duration:.2f} 秒")
        print("="*60)

    except Exception as e:
        print(f"[错误] {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    translate_cluster_names()

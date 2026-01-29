"""
测试翻译功能 - 翻译前5个类别名称
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import distinct
from backend.database import SessionLocal
from backend.models.product import Product
import requests

def test_translation():
    """测试翻译前5个类别名称"""
    db = SessionLocal()

    try:
        # 获取前5个不同的英文类别名称
        cluster_names = db.query(distinct(Product.cluster_name)).filter(
            Product.cluster_name.isnot(None),
            Product.cluster_name != ""
        ).limit(5).all()

        cluster_names = [name[0] for name in cluster_names]
        print(f"找到 {len(cluster_names)} 个类别名称进行测试")

        api_key = os.getenv('DEEPSEEK_API_KEY')
        print(f"API Key: {api_key[:10]}..." if api_key else "未找到API密钥")

        for i, en_name in enumerate(cluster_names, 1):
            print(f"\n[{i}/5] 翻译: {en_name}")

            prompt = f"请将以下英文类别名称翻译成简洁的中文（不超过10个字），只返回中文翻译：\n\n{en_name}\n\n中文翻译："

            try:
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
                    },
                    timeout=30
                )

                if response.status_code == 200:
                    cn_name = response.json()['choices'][0]['message']['content'].strip()
                    print(f"   -> {cn_name}")

                    # 更新数据库
                    updated = db.query(Product).filter(
                        Product.cluster_name == en_name
                    ).update({"cluster_name_cn": cn_name})
                    db.commit()
                    print(f"   更新了 {updated} 个商品")
                else:
                    print(f"   [错误] HTTP {response.status_code}: {response.text}")

            except Exception as e:
                print(f"   [错误] {str(e)}")

    finally:
        db.close()

if __name__ == "__main__":
    test_translation()

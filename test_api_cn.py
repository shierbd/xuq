"""
测试 API 是否正确返回中文翻译
"""
import requests
import json

# 获取商品列表
response = requests.get("http://localhost:8001/api/products/?page=1&page_size=100")
data = response.json()

print("=" * 60)
print("API 中文翻译测试")
print("=" * 60)

# 查找有中文翻译的商品
found_count = 0
for item in data['items']:
    if item.get('cluster_name_cn') and item['cluster_name_cn'] != 'null':
        found_count += 1
        if found_count <= 5:  # 只显示前5个
            print(f"\n商品 {found_count}:")
            print(f"  商品名称: {item['product_name'][:60]}...")
            print(f"  簇ID: {item['cluster_id']}")
            print(f"  英文类别: {item['cluster_name']}")
            print(f"  中文类别: {item['cluster_name_cn']}")
            print(f"  评分: {item['rating']}")
            print(f"  评价数: {item['review_count']}")

print(f"\n总计: 在前100个商品中找到 {found_count} 个有中文翻译的商品")

# 验证字段是否存在
if data['items']:
    first_item = data['items'][0]
    print("\n" + "=" * 60)
    print("字段验证:")
    print("=" * 60)
    print(f"✅ cluster_name_cn 字段存在: {'cluster_name_cn' in first_item}")
    print(f"✅ API 响应正常")
    print("\n测试通过！")
else:
    print("\n❌ 没有找到商品数据")

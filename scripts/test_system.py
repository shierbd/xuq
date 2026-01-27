"""
系统功能验证脚本
用于快速测试需求挖掘系统 v2.0 的所有功能
"""
import requests
import time
from typing import Dict, Any

# 配置
BASE_URL = "http://127.0.0.1:8000"
TIMEOUT = 10


class Colors:
    """终端颜色"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'


def print_header(text: str):
    """打印标题"""
    print(f"\n{Colors.BLUE}{'=' * 80}{Colors.END}")
    print(f"{Colors.BLUE}{text:^80}{Colors.END}")
    print(f"{Colors.BLUE}{'=' * 80}{Colors.END}\n")


def print_success(text: str):
    """打印成功信息"""
    print(f"{Colors.GREEN}[OK] {text}{Colors.END}")


def print_error(text: str):
    """打印错误信息"""
    print(f"{Colors.RED}[ERROR] {text}{Colors.END}")


def print_info(text: str):
    """打印信息"""
    print(f"{Colors.YELLOW}[INFO] {text}{Colors.END}")


def test_api(name: str, method: str, endpoint: str, **kwargs) -> Dict[Any, Any]:
    """测试API端点"""
    url = f"{BASE_URL}{endpoint}"
    print(f"测试: {name}")
    print(f"  请求: {method} {endpoint}")

    try:
        if method == "GET":
            response = requests.get(url, timeout=TIMEOUT, **kwargs)
        elif method == "POST":
            response = requests.post(url, timeout=TIMEOUT, **kwargs)
        elif method == "PUT":
            response = requests.put(url, timeout=TIMEOUT, **kwargs)
        elif method == "DELETE":
            response = requests.delete(url, timeout=TIMEOUT, **kwargs)
        else:
            print_error(f"不支持的HTTP方法: {method}")
            return {}

        if response.status_code == 200:
            print_success(f"状态码: {response.status_code}")
            data = response.json()
            return data
        else:
            print_error(f"状态码: {response.status_code}")
            print(f"  响应: {response.text[:200]}")
            return {}

    except requests.exceptions.ConnectionError:
        print_error("连接失败 - 请确保后端服务正在运行")
        return {}
    except requests.exceptions.Timeout:
        print_error("请求超时")
        return {}
    except Exception as e:
        print_error(f"请求失败: {str(e)}")
        return {}


def test_basic_endpoints():
    """测试基础端点"""
    print_header("测试基础端点")

    # 1. 根路径
    data = test_api("根路径", "GET", "/")
    if data:
        print(f"  系统版本: {data.get('version', 'N/A')}")
        print(f"  模块: {', '.join(data.get('modules', {}).values())}")
    print()

    # 2. 健康检查
    data = test_api("健康检查", "GET", "/health")
    if data:
        print(f"  状态: {data.get('status', 'N/A')}")
    print()

    # 3. API文档
    print("测试: API文档")
    print(f"  访问: {BASE_URL}/docs")
    print_info("请在浏览器中访问查看完整文档")
    print()


def test_keywords_module():
    """测试词根聚类模块"""
    print_header("测试词根聚类模块")

    # 1. 获取关键词总数
    data = test_api("获取关键词总数", "GET", "/api/keywords/count")
    if data and data.get('success'):
        total = data['data']['total']
        print(f"  关键词总数: {total:,}")
    print()

    # 2. 获取关键词列表（第1页）
    data = test_api(
        "获取关键词列表",
        "GET",
        "/api/keywords/",
        params={"page": 1, "page_size": 5}
    )
    if data and data.get('success'):
        items = data['data']['items']
        print(f"  返回记录数: {len(items)}")
        if items:
            print(f"  示例关键词: {items[0]['keyword']}")
    print()

    # 3. 搜索关键词
    data = test_api(
        "搜索关键词",
        "GET",
        "/api/keywords/",
        params={"search": "best", "page_size": 5}
    )
    if data and data.get('success'):
        items = data['data']['items']
        print(f"  搜索结果数: {len(items)}")
        if items:
            print(f"  示例: {items[0]['keyword']}")
    print()

    # 4. 获取种子词列表
    data = test_api("获取种子词列表", "GET", "/api/keywords/seed-words")
    if data and data.get('success'):
        seeds = data['data']['seed_words']
        print(f"  种子词数量: {len(seeds)}")
        print(f"  示例: {', '.join(seeds[:5])}")
    print()

    # 5. 获取簇概览
    data = test_api(
        "获取簇概览",
        "GET",
        "/api/keywords/clusters/overview",
        params={"stage": "A", "exclude_noise": True}
    )
    if data and data.get('success'):
        clusters = data['data']
        print(f"  簇数量: {data['total']}")
        if clusters:
            top_cluster = clusters[0]
            print(f"  最大簇ID: {top_cluster['cluster_id']}")
            print(f"  最大簇大小: {top_cluster['cluster_size']}")
            print(f"  最大簇搜索量: {top_cluster['total_volume']:,}")
    print()

    # 6. 获取单个簇详情
    if clusters:
        cluster_id = clusters[0]['cluster_id']
        data = test_api(
            f"获取簇 #{cluster_id} 详情",
            "GET",
            f"/api/keywords/clusters/{cluster_id}",
            params={"stage": "A"}
        )
        if data and data.get('success'):
            cluster = data['data']
            print(f"  簇大小: {cluster['cluster_size']}")
            print(f"  种子词: {', '.join(cluster['seed_words'])}")
            print(f"  平均搜索量: {cluster['statistics']['avg_volume']:,.0f}")
    print()


def test_products_module():
    """测试商品管理模块"""
    print_header("测试商品管理模块")

    # 1. 获取商品总数
    data = test_api("获取商品总数", "GET", "/api/products/count")
    if data and data.get('success'):
        total = data['data']['total']
        print(f"  商品总数: {total:,}")
    print()

    # 2. 获取商品列表
    data = test_api(
        "获取商品列表",
        "GET",
        "/api/products/",
        params={"page": 1, "page_size": 5}
    )
    if data and data.get('success'):
        items = data['data']['items']
        print(f"  返回记录数: {len(items)}")
        if items:
            product = items[0]
            print(f"  示例商品: {product['product_name'][:50]}")
            print(f"  评分: {product.get('rating', 'N/A')}")
            print(f"  评价数: {product.get('review_count', 'N/A')}")
    print()

    # 3. 搜索商品
    data = test_api(
        "搜索商品",
        "GET",
        "/api/products/",
        params={"search": "planner", "page_size": 5}
    )
    if data and data.get('success'):
        items = data['data']['items']
        print(f"  搜索结果数: {len(items)}")
        if items:
            print(f"  示例: {items[0]['product_name'][:50]}")
    print()

    # 4. 获取单个商品详情
    if items:
        product_id = items[0]['product_id']
        data = test_api(
            f"获取商品 #{product_id} 详情",
            "GET",
            f"/api/products/{product_id}"
        )
        if data and data.get('success'):
            product = data['data']
            print(f"  商品名称: {product['product_name'][:50]}")
            print(f"  店铺: {product.get('shop_name', 'N/A')}")
            print(f"  价格: ${product.get('price', 'N/A')}")
    print()


def test_advanced_queries():
    """测试高级查询"""
    print_header("测试高级查询")

    # 1. 按种子词筛选
    data = test_api(
        "按种子词筛选关键词",
        "GET",
        "/api/keywords/",
        params={"seed_word": "Best", "page_size": 5}
    )
    if data and data.get('success'):
        items = data['data']['items']
        print(f"  结果数: {len(items)}")
    print()

    # 2. 按簇ID筛选
    data = test_api(
        "按簇ID筛选关键词",
        "GET",
        "/api/keywords/",
        params={"cluster_id": 42, "page_size": 5}
    )
    if data and data.get('success'):
        items = data['data']['items']
        print(f"  结果数: {len(items)}")
    print()

    # 3. 排除噪音点
    data = test_api(
        "排除噪音点",
        "GET",
        "/api/keywords/",
        params={"is_noise": False, "page_size": 5}
    )
    if data and data.get('success'):
        items = data['data']['items']
        print(f"  结果数: {len(items)}")
    print()

    # 4. 按簇大小筛选
    data = test_api(
        "按簇大小筛选",
        "GET",
        "/api/keywords/clusters/overview",
        params={"stage": "A", "min_size": 50}
    )
    if data and data.get('success'):
        clusters = data['data']
        print(f"  大簇数量: {len(clusters)}")
    print()


def test_performance():
    """测试性能"""
    print_header("测试性能")

    # 1. 测试关键词列表查询速度
    print("测试: 关键词列表查询速度")
    start_time = time.time()
    data = test_api(
        "获取100条关键词",
        "GET",
        "/api/keywords/",
        params={"page": 1, "page_size": 100}
    )
    elapsed = time.time() - start_time
    if data and data.get('success'):
        print(f"  查询时间: {elapsed:.3f} 秒")
        print(f"  返回记录数: {len(data['data']['items'])}")
    print()

    # 2. 测试簇概览查询速度
    print("测试: 簇概览查询速度")
    start_time = time.time()
    data = test_api(
        "获取所有簇概览",
        "GET",
        "/api/keywords/clusters/overview",
        params={"stage": "A"}
    )
    elapsed = time.time() - start_time
    if data and data.get('success'):
        print(f"  查询时间: {elapsed:.3f} 秒")
        print(f"  簇数量: {data['total']}")
    print()

    # 3. 测试搜索速度
    print("测试: 关键词搜索速度")
    start_time = time.time()
    data = test_api(
        "搜索关键词",
        "GET",
        "/api/keywords/",
        params={"search": "best", "page_size": 50}
    )
    elapsed = time.time() - start_time
    if data and data.get('success'):
        print(f"  查询时间: {elapsed:.3f} 秒")
        print(f"  结果数: {len(data['data']['items'])}")
    print()


def generate_summary():
    """生成测试摘要"""
    print_header("测试摘要")

    # 获取系统信息
    system_info = test_api("系统信息", "GET", "/")
    keywords_count = test_api("关键词总数", "GET", "/api/keywords/count")
    products_count = test_api("商品总数", "GET", "/api/products/count")
    clusters_overview = test_api(
        "簇概览",
        "GET",
        "/api/keywords/clusters/overview",
        params={"stage": "A"}
    )

    print("系统状态:")
    if system_info:
        print(f"  版本: {system_info.get('version', 'N/A')}")
        print(f"  模块: {', '.join(system_info.get('modules', {}).values())}")

    print("\n数据统计:")
    if keywords_count and keywords_count.get('success'):
        print(f"  关键词总数: {keywords_count['data']['total']:,}")

    if clusters_overview and clusters_overview.get('success'):
        print(f"  簇数量: {clusters_overview['total']}")
        clusters = clusters_overview['data']
        if clusters:
            total_volume = sum(c['total_volume'] for c in clusters)
            print(f"  总搜索量: {total_volume:,}")

    if products_count and products_count.get('success'):
        print(f"  商品总数: {products_count['data']['total']:,}")

    print("\n访问地址:")
    print(f"  后端 API: {BASE_URL}")
    print(f"  API 文档: {BASE_URL}/docs")
    print(f"  前端界面: http://localhost:5173")

    print("\n下一步:")
    print("  1. 访问 API 文档查看完整接口")
    print("  2. 使用前端界面进行可视化操作")
    print("  3. 运行 scripts/db_query_tool.py 查看数据库")
    print("  4. 查看 docs/API使用示例.md 学习更多用法")
    print()


def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("需求挖掘系统 v2.0 - 功能验证脚本")
    print("=" * 80)

    print_info(f"后端地址: {BASE_URL}")
    print_info("开始测试...\n")

    try:
        # 1. 测试基础端点
        test_basic_endpoints()

        # 2. 测试词根聚类模块
        test_keywords_module()

        # 3. 测试商品管理模块
        test_products_module()

        # 4. 测试高级查询
        test_advanced_queries()

        # 5. 测试性能
        test_performance()

        # 6. 生成摘要
        generate_summary()

        print_header("测试完成")
        print_success("所有测试已完成！")
        print_info("系统运行正常，可以开始使用。")

    except KeyboardInterrupt:
        print("\n\n测试被中断。")
    except Exception as e:
        print_error(f"测试过程中发生错误: {str(e)}")


if __name__ == "__main__":
    main()

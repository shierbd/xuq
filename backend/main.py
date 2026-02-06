"""
需求挖掘系统 - FastAPI 主应用
统一的后端服务，包含词根聚类和商品管理两大模块
Updated: 2026-01-29 - Added cluster_name_cn field support
Updated: 2026-01-31 - Added three-stage clustering support
Updated: 2026-01-31 - Added debug logging for API key issues
"""
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import init_db
from backend.routers import products, keywords, batch_import, clusters, demand_analysis, delivery_identification, attribute_extraction, top_product_analysis, ai_config, tasks

# 加载环境变量
load_dotenv()

# 创建 FastAPI 应用
app = FastAPI(
    title="需求挖掘系统 API",
    description="统一的需求挖掘与分析平台，包含词根聚类和商品管理功能",
    version="2.0.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(keywords.router)  # 词根聚类模块
app.include_router(products.router)  # 商品管理模块
app.include_router(batch_import.router)  # 批量导入模块
app.include_router(clusters.router)  # 聚类增强模块
app.include_router(demand_analysis.router)  # 需求分析模块
app.include_router(delivery_identification.router)  # 交付产品识别模块
app.include_router(attribute_extraction.router)  # 商品属性提取模块
app.include_router(top_product_analysis.router)  # Top商品AI深度分析模块
app.include_router(ai_config.router)  # AI配置管理模块
app.include_router(tasks.router)  # background tasks

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化数据库"""
    init_db()
    print("Database initialized successfully")
    print("Application started successfully")
    print("=" * 50)
    print("需求挖掘系统 v2.0")
    print("包含模块：")
    print("  - 词根聚类模块: /api/keywords/*")
    print("  - 商品管理模块: /api/products/*")
    print("  - 聚类增强模块: /api/clusters/*")
    print("  - 需求分析模块: /api/demand-analysis/*")
    print("  - 交付产品识别模块: /api/delivery-identification/*")
    print("  - 商品属性提取模块: /api/attribute-extraction/*")
    print("  - Top商品AI深度分析模块: /api/top-product-analysis/*")
    print("  - AI配置管理模块: /api/ai-config/*")
    print("=" * 50)

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "需求挖掘系统 API",
        "version": "2.0.0",
        "modules": {
            "keywords": "词根聚类模块",
            "products": "商品管理模块",
            "clusters": "聚类增强模块",
            "demand_analysis": "需求分析模块",
            "delivery_identification": "交付产品识别模块",
            "attribute_extraction": "商品属性提取模块",
            "top_product_analysis": "Top商品AI深度分析模块",
            "ai_config": "AI配置管理模块"
        },
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}

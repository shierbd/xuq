"""
需求挖掘系统 - FastAPI 主应用
统一的后端服务，包含词根聚类和商品管理两大模块
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import init_db
from backend.routers import products, keywords, batch_import

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
    print("=" * 50)

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "需求挖掘系统 API",
        "version": "2.0.0",
        "modules": {
            "keywords": "词根聚类模块",
            "products": "商品管理模块"
        },
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}

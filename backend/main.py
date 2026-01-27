"""
[REQ-001] 数据导入功能 - FastAPI 主应用
应用入口，配置路由和中间件
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import init_db
from backend.routers import products

# 创建 FastAPI 应用
app = FastAPI(
    title="需求挖掘系统 API",
    description="基于 Etsy 商品数据的需求挖掘与分析平台",
    version="1.0.0"
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
app.include_router(products.router)

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化数据库"""
    init_db()
    print("Application started successfully")

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "需求挖掘系统 API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}

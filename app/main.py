"""
FastAPI + HTMX 应用主入口
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

# 导入路由
from app.routers import products
from app.database import init_db

# 创建FastAPI应用
app = FastAPI(
    title="词根聚类需求挖掘系统",
    description="基于FastAPI + HTMX的轻量级需求挖掘系统",
    version="2.0.0"
)

# 初始化数据库
init_db()

# 配置静态文件
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# 配置模板
templates = Jinja2Templates(directory="app/templates")

# 注册路由
app.include_router(products.router)

# 首页路由
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """首页"""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "title": "词根聚类需求挖掘系统"
    })

# 健康检查
@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "ok", "version": "2.0.0"}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

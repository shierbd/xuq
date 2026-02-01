"""
商品管理路由
"""
from fastapi import APIRouter, Request, Query, Depends, Form, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import Optional
import csv
import io

from app.database import get_db, Product

router = APIRouter(prefix="/products", tags=["products"])
templates = Jinja2Templates(directory="app/templates")

@router.get("", response_class=HTMLResponse)
async def products_page(request: Request):
    """商品管理页面"""
    return templates.TemplateResponse("products.html", {
        "request": request,
        "title": "商品管理"
    })

@router.get("/list", response_class=HTMLResponse)
async def products_list(
    request: Request,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None
):
    """获取商品列表（HTMX）"""

    # 构建查询
    query = db.query(Product)

    # 搜索
    if search:
        query = query.filter(Product.name.contains(search))

    # 分类筛选
    if category:
        query = query.filter(Product.category == category)

    # 价格筛选
    if min_price is not None:
        query = query.filter(Product.price >= min_price)

    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    # 总数
    total = query.count()

    # 分页
    total_pages = (total + per_page - 1) // per_page
    products = query.offset((page - 1) * per_page).limit(per_page).all()

    return templates.TemplateResponse("products_table.html", {
        "request": request,
        "products": products,
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages
    })

@router.delete("/{product_id}", response_class=HTMLResponse)
async def delete_product(product_id: int, db: Session = Depends(get_db)):
    """删除商品（HTMX）"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if product:
        db.delete(product)
        db.commit()
    return ""

@router.get("/{product_id}/edit", response_class=HTMLResponse)
async def edit_product_form(request: Request, product_id: int, db: Session = Depends(get_db)):
    """编辑商品表单（HTMX）"""
    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        return "<div class='text-red-600'>商品不存在</div>"

    return templates.TemplateResponse("product_edit_modal.html", {
        "request": request,
        "product": product
    })

@router.put("/{product_id}", response_class=HTMLResponse)
async def update_product(
    request: Request,
    product_id: int,
    db: Session = Depends(get_db),
    name: str = Form(...),
    category: str = Form(...),
    price: float = Form(...),
    status: str = Form(...),
    description: Optional[str] = Form(None)
):
    """更新商品（HTMX）"""
    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        return "<div class='text-red-600'>商品不存在</div>"

    # 更新字段
    product.name = name
    product.category = category
    product.price = price
    product.status = status
    product.description = description

    db.commit()
    db.refresh(product)

    # 返回更新后的行
    return templates.TemplateResponse("product_row.html", {
        "request": request,
        "product": product
    })

@router.get("/new", response_class=HTMLResponse)
async def new_product_form(request: Request):
    """新建商品表单（HTMX）"""
    return templates.TemplateResponse("product_new_modal.html", {
        "request": request
    })

@router.post("", response_class=HTMLResponse)
async def create_product(
    request: Request,
    db: Session = Depends(get_db),
    name: str = Form(...),
    category: str = Form(...),
    price: float = Form(...),
    status: str = Form("active"),
    description: Optional[str] = Form(None)
):
    """创建商品（HTMX）"""
    product = Product(
        name=name,
        category=category,
        price=price,
        status=status,
        description=description
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    # 返回新行
    return templates.TemplateResponse("product_row.html", {
        "request": request,
        "product": product
    })

@router.get("/import", response_class=HTMLResponse)
async def import_modal(request: Request):
    """导入数据模态框（HTMX）"""
    return templates.TemplateResponse("product_import_modal.html", {
        "request": request
    })

@router.post("/import", response_class=HTMLResponse)
async def import_products(
    request: Request,
    db: Session = Depends(get_db),
    file: UploadFile = File(...)
):
    """导入商品数据（HTMX）"""
    try:
        # 读取CSV文件
        contents = await file.read()
        csv_file = io.StringIO(contents.decode('utf-8'))
        reader = csv.DictReader(csv_file)

        imported_count = 0
        for row in reader:
            product = Product(
                name=row.get('name', ''),
                category=row.get('category', ''),
                price=float(row.get('price', 0)),
                status=row.get('status', 'active'),
                description=row.get('description', '')
            )
            db.add(product)
            imported_count += 1

        db.commit()

        return f"""
        <div class="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded">
            成功导入 {imported_count} 条商品数据
        </div>
        """
    except Exception as e:
        return f"""
        <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            导入失败: {str(e)}
        </div>
        """

@router.get("/stats", response_class=HTMLResponse)
async def products_stats(request: Request, db: Session = Depends(get_db)):
    """商品统计信息（HTMX）"""
    total = db.query(Product).count()
    active = db.query(Product).filter(Product.status == "active").count()

    # 按分类统计
    categories = db.query(Product.category, db.func.count(Product.id))\
        .group_by(Product.category)\
        .all()

    return templates.TemplateResponse("product_stats.html", {
        "request": request,
        "total": total,
        "active": active,
        "categories": categories
    })

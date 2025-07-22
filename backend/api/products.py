from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from models.product import Product
from schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductOut,
    ProductSearch,
    ProductFilter,
)
from core.security import require_role
from core.database import get_db
from datetime import datetime
from models.audit import AuditLog
from typing import List
from fastapi.responses import FileResponse
import os
from core.pagination import paginate_query, get_pagination_params, PaginatedResponse
from sqlalchemy import or_, and_

product_router = APIRouter(prefix="/products", tags=["products"])

STATIC_IMAGE_DIR = os.path.join(os.path.dirname(__file__), "../static/images")
os.makedirs(STATIC_IMAGE_DIR, exist_ok=True)


@product_router.get("/", response_model=List[ProductOut])
def list_products(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    return (
        db.query(Product)
        .filter(Product.is_deleted == False)
        .offset(skip)
        .limit(limit)
        .all()
    )


@product_router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = (
        db.query(Product)
        .filter(Product.id == product_id, Product.is_deleted == False)
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@product_router.post(
    "/", response_model=ProductOut, status_code=status.HTTP_201_CREATED
)
def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role("admin")),
):
    db_product = Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    db.add(
        AuditLog(
            user_id=user.id,
            action="create",
            target_type="product",
            target_id=db_product.id,
            details=product.dict(),
        )
    )
    db.commit()
    return db_product


@product_router.put("/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int,
    product: ProductUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_role("admin")),
):
    db_product = (
        db.query(Product)
        .filter(Product.id == product_id, Product.is_deleted == False)
        .first()
    )
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    for key, value in product.dict(exclude_unset=True).items():
        setattr(db_product, key, value)
    db.commit()
    db.add(
        AuditLog(
            user_id=user.id,
            action="update",
            target_type="product",
            target_id=db_product.id,
            details=product.dict(exclude_unset=True),
        )
    )
    db.commit()
    return db_product


@product_router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int, db: Session = Depends(get_db), user=Depends(require_role("admin"))
):
    db_product = (
        db.query(Product)
        .filter(Product.id == product_id, Product.is_deleted == False)
        .first()
    )
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    object.__setattr__(db_product, "is_deleted", True)
    object.__setattr__(db_product, "deleted_at", datetime.utcnow())
    db.commit()
    db.add(
        AuditLog(
            user_id=user.id,
            action="delete",
            target_type="product",
            target_id=db_product.id,
            details={},
        )
    )
    db.commit()
    return None


@product_router.post(
    "/{product_id}/upload-image",
    response_model=ProductOut,
    dependencies=[Depends(require_role("admin"))],
)
def upload_product_image(
    product_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)
):
    product: Product = (
        db.query(Product)
        .filter(Product.id == product_id, Product.is_deleted == False)
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    ext = os.path.splitext(file.filename)[1]
    filename = f"product_{product_id}{ext}"
    file_path = os.path.join(STATIC_IMAGE_DIR, filename)
    with open(file_path, "wb") as image_file:
        image_file.write(file.file.read())
    product.image_url = f"/static/images/{filename}"
    db.commit()
    db.refresh(product)
    return product


@product_router.get("/images/{filename}")
def get_product_image(filename: str):
    file_path = os.path.join(STATIC_IMAGE_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(file_path)


@product_router.get(
    "/inventory",
    response_model=List[ProductOut],
    dependencies=[Depends(require_role("admin"))],
)
def list_inventory(db: Session = Depends(get_db)):
    return db.query(Product).filter(Product.is_deleted == False).all()


@product_router.patch(
    "/{product_id}/stock",
    response_model=ProductOut,
    dependencies=[Depends(require_role("admin"))],
)
def update_product_stock(product_id: int, stock: int, db: Session = Depends(get_db)):
    product = (
        db.query(Product)
        .filter(Product.id == product_id, Product.is_deleted == False)
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if stock < 0:
        raise HTTPException(status_code=400, detail="Stock cannot be negative")
    product.stock = stock
    db.commit()
    db.refresh(product)
    return product


@product_router.get(
    "/low-stock",
    response_model=List[ProductOut],
    dependencies=[Depends(require_role("admin"))],
)
def list_low_stock_products(threshold: int = 5, db: Session = Depends(get_db)):
    return (
        db.query(Product)
        .filter(Product.stock <= threshold, Product.is_deleted == False)
        .all()
    )


@product_router.get("/search", response_model=PaginatedResponse[ProductOut])
def search_products(
    search: ProductSearch = Depends(),
    filter: ProductFilter = Depends(),
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
):
    query = db.query(Product).filter(Product.is_deleted == False)

    # Search by query
    if search.query:
        search_term = f"%{search.query}%"
        query = query.filter(
            or_(Product.name.ilike(search_term), Product.description.ilike(search_term))
        )

    # Price filtering
    if search.min_price is not None:
        query = query.filter(Product.price >= search.min_price)
    if search.max_price is not None:
        query = query.filter(Product.price <= search.max_price)

    # Stock filtering
    if search.in_stock is not None:
        if search.in_stock:
            query = query.filter(Product.stock > 0)
        else:
            query = query.filter(Product.stock == 0)

    # Sorting
    if search.sort_by:
        sort_column = getattr(Product, search.sort_by)
        if search.sort_order == "desc":
            sort_column = sort_column.desc()
        query = query.order_by(sort_column)
    else:
        query = query.order_by(Product.created_at.desc())

    return paginate_query(query, page, size)


@product_router.get("/filter", response_model=PaginatedResponse[ProductOut])
def filter_products(
    filter: ProductFilter = Depends(),
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
):
    query = db.query(Product).filter(Product.is_deleted == False)

    # Apply filters (placeholder for category, brand, tags)
    # These would need corresponding fields in the Product model
    # For now, we'll return all products with pagination

    return paginate_query(query, page, size)

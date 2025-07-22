from typing import TypeVar, Generic, List, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Query
from fastapi import Query as FastAPIQuery

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int
    pages: int
    has_next: bool
    has_prev: bool


def paginate_query(query: Query, page: int = 1, size: int = 20) -> PaginatedResponse:
    """Paginate a SQLAlchemy query"""
    if page < 1:
        page = 1
    if size < 1 or size > 100:
        size = 20

    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()

    pages = (total + size - 1) // size  # Ceiling division

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages,
        has_next=page < pages,
        has_prev=page > 1,
    )


def get_pagination_params(
    page: int = FastAPIQuery(1, ge=1, description="Page number"),
    size: int = FastAPIQuery(20, ge=1, le=100, description="Items per page"),
) -> tuple[int, int]:
    """Get pagination parameters from request"""
    return page, size

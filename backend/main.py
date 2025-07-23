from fastapi import FastAPI, Depends, Request, HTTPException, Response
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models import Base
import os
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import secrets
from starlette.middleware.base import BaseHTTPMiddleware
from core.logging import logger
from api import api_version_one
from fastapi.staticfiles import StaticFiles



DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ecommerce.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables (for dev/demo; use Alembic for production)
Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, set to your frontend domain
    allow_credentials=False, # must be True in production
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_version_one)


app.mount(
    "/static/images", StaticFiles(directory="static/images"), name="product_images"
)

CSRF_COOKIE_NAME = "csrftoken"
CSRF_HEADER_NAME = "x-csrf-token"


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def read_root():
    return {"message": "Welcome to the E-commerce API!"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(f"HTTP error: {exc.detail}")
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.middleware("http")
async def log_requests(request, call_next):
    user = request.cookies.get("access_token", "anonymous")
    logger.info(f"Request: {request.method} {request.url.path} user={user}")
    response = await call_next(request)
    logger.info(
        f"Response: {request.method} {request.url.path} status={response.status_code} user={user}"
    )
    return response

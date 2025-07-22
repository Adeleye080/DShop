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
from api.profile import router as profile_router


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
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_version_one)
app.include_router(profile_router)


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
async def csrf_protect(request, call_next):
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        csrf_token_cookie = request.cookies.get(CSRF_COOKIE_NAME)
        csrf_token_header = request.headers.get(CSRF_HEADER_NAME)
        if (
            not csrf_token_cookie
            or not csrf_token_header
            or csrf_token_cookie != csrf_token_header
        ):
            return JSONResponse(
                status_code=403, content={"detail": "CSRF token missing or invalid"}
            )
    response = await call_next(request)
    if not request.cookies.get(CSRF_COOKIE_NAME):
        token = secrets.token_urlsafe(32)
        response.set_cookie(CSRF_COOKIE_NAME, token, httponly=False, secure=True)
    return response


@app.middleware("http")
async def log_requests(request, call_next):
    user = request.cookies.get("access_token", "anonymous")
    logger.info(f"Request: {request.method} {request.url.path} user={user}")
    response = await call_next(request)
    logger.info(
        f"Response: {request.method} {request.url.path} status={response.status_code} user={user}"
    )
    return response

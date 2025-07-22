from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session
from models.user import User
from models.audit import AuditLog
from schemas.user import UserCreate, UserLogin, Token
from core.security import (
    get_current_user,
    require_role,
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from core.database import get_db
from core.email_utils import send_email, render_template
import pyotp
import secrets
from datetime import datetime, timedelta
from collections import defaultdict
import time

router = APIRouter(prefix="/auth", tags=["auth"])

# In-memory rate limiting store
RATE_LIMIT = 5  # max attempts
RATE_PERIOD = 60  # seconds
register_attempts = defaultdict(list)
login_attempts = defaultdict(list)
revoked_refresh_tokens = set()


def is_strong_password(password: str) -> bool:
    import re

    pattern = r"""^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]).{8,}$"""
    return bool(re.match(pattern, password))


def check_rate_limit(ip: str, attempts_dict: dict):
    now = time.time()
    attempts = attempts_dict[ip]
    attempts = [t for t in attempts if now - t < RATE_PERIOD]
    attempts_dict[ip] = attempts
    if len(attempts) >= RATE_LIMIT:
        return False
    attempts.append(now)
    return True


@router.post("/register", response_model=Token)
def register(
    user: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    response: Response = None,
):
    ip = request.client.host if request else "unknown"
    if not check_rate_limit(ip, register_attempts):
        raise HTTPException(
            status_code=429,
            detail="Too many registration attempts. Please try again later.",
        )
    if not is_strong_password(user.password):
        raise HTTPException(
            status_code=400,
            detail="Password too weak. Must be 8+ chars, include upper/lowercase, digit, special char.",
        )
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(user.password)
    verification_token = secrets.token_urlsafe(32)
    new_user = User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name,
        verification_token=verification_token,
        email_verified=False,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    verify_url = f"http://localhost:8000/auth/verify-email?token={verification_token}"
    html_body = render_template(
        "verification_email.html",
        full_name=new_user.full_name,
        email=new_user.email,
        verify_url=verify_url,
    )
    send_email(
        new_user.email,
        "Verify your email",
        f"Verify your email: {verify_url}",
        html_body=html_body,
    )
    access_token = create_access_token(data={"sub": new_user.email})
    refresh_token = create_refresh_token(data={"sub": new_user.email})
    if response:
        response.set_cookie(
            key="access_token", value=access_token, httponly=True, secure=True
        )
        response.set_cookie(
            key="refresh_token", value=refresh_token, httponly=True, secure=True
        )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.get("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.verification_token == token).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid verification token")
    user.email_verified = True
    user.verification_token = None
    db.commit()
    return {"message": "Email verified. You can now log in."}


@router.post("/login", response_model=Token)
def login(
    user: UserLogin,
    db: Session = Depends(get_db),
    request: Request = None,
    response: Response = None,
    otp_token: str = None,
):
    ip = request.client.host if request else "unknown"
    if not check_rate_limit(ip, login_attempts):
        raise HTTPException(
            status_code=429, detail="Too many login attempts. Please try again later."
        )
    db_user = (
        db.query(User)
        .filter(User.email == user.email, User.is_deleted == False)
        .first()
    )
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not db_user.email_verified:
        raise HTTPException(status_code=403, detail="Email not verified")
    if db_user.otp_secret:
        if not otp_token:
            raise HTTPException(status_code=401, detail="2FA token required")
        totp = pyotp.TOTP(db_user.otp_secret)
        if not totp.verify(otp_token):
            raise HTTPException(status_code=401, detail="Invalid 2FA token")
    access_token = create_access_token(data={"sub": db_user.email})
    refresh_token = create_refresh_token(data={"sub": db_user.email})
    if response:
        response.set_cookie(
            key="access_token", value=access_token, httponly=True, secure=True
        )
        response.set_cookie(
            key="refresh_token", value=refresh_token, httponly=True, secure=True
        )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh")
def refresh_token_endpoint(
    response: Response, refresh_token: str = Depends(lambda: None)
):
    payload = decode_token(refresh_token)
    if (
        not payload
        or payload.get("type") != "refresh"
        or refresh_token in revoked_refresh_tokens
    ):
        raise HTTPException(status_code=401, detail="Invalid or revoked refresh token")
    email = payload.get("sub")
    access_token = create_access_token(data={"sub": email})
    new_refresh_token = create_refresh_token(data={"sub": email})
    revoked_refresh_tokens.add(refresh_token)
    response.set_cookie(
        key="access_token", value=access_token, httponly=True, secure=True
    )
    response.set_cookie(
        key="refresh_token", value=new_refresh_token, httponly=True, secure=True
    )
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


@router.post("/request-password-reset")
def request_password_reset(email: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return {"message": "If the email exists, a reset link will be sent."}
    token = secrets.token_urlsafe(32)
    user.password_reset_token = token
    user.password_reset_expiry = datetime.utcnow() + timedelta(hours=1)
    db.commit()
    reset_url = f"http://localhost:8000/auth/reset-password?token={token}"
    html_body = render_template(
        "password_reset_email.html",
        full_name=user.full_name,
        email=user.email,
        reset_url=reset_url,
    )
    send_email(
        user.email,
        "Password Reset",
        f"Reset your password: {reset_url}",
        html_body=html_body,
    )
    return {"message": "If the email exists, a reset link will be sent."}


@router.post("/reset-password")
def reset_password(token: str, new_password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.password_reset_token == token).first()
    if (
        not user
        or not user.password_reset_expiry
        or user.password_reset_expiry < datetime.utcnow()
    ):
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    if not is_strong_password(new_password):
        raise HTTPException(status_code=400, detail="Password too weak.")
    user.hashed_password = get_password_hash(new_password)
    user.password_reset_token = None
    user.password_reset_expiry = None
    db.commit()
    db.add(
        AuditLog(
            user_id=user.id,
            action="reset_password",
            target_type="user",
            target_id=user.id,
            details={},
        )
    )
    db.commit()
    return {"message": "Password reset successful. You can now log in."}


@router.delete("/user/{user_id}", status_code=204)
def delete_user(
    user_id: int, db: Session = Depends(get_db), user=Depends(require_role("admin"))
):
    user_obj = (
        db.query(User).filter(User.id == user_id, User.is_deleted == False).first()
    )
    if not user_obj:
        raise HTTPException(status_code=404, detail="User not found")
    object.__setattr__(user_obj, "is_deleted", True)
    object.__setattr__(user_obj, "deleted_at", datetime.utcnow())
    db.commit()
    db.add(
        AuditLog(
            user_id=user.id,
            action="delete",
            target_type="user",
            target_id=user_obj.id,
            details={},
        )
    )
    db.commit()
    return None


@router.post("/enable-2fa")
def enable_2fa(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.otp_secret:
        raise HTTPException(status_code=400, detail="2FA already enabled")
    secret = pyotp.random_base32()
    user.otp_secret = secret
    db.commit()
    otp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=user.email, issuer_name="EcommerceApp"
    )
    return {"otp_secret": secret, "otp_uri": otp_uri}


@router.post("/disable-2fa")
def disable_2fa(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not user.otp_secret:
        raise HTTPException(status_code=400, detail="2FA not enabled")
    user.otp_secret = None
    db.commit()
    return {"message": "2FA disabled"}


@router.post("/verify-2fa")
def verify_2fa(
    token: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    if not user.otp_secret:
        raise HTTPException(status_code=400, detail="2FA not enabled")
    totp = pyotp.TOTP(user.otp_secret)
    if not totp.verify(token):
        raise HTTPException(status_code=401, detail="Invalid 2FA token")
    return {"message": "2FA verified"}

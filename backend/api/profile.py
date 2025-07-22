from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.user import User
from schemas.user import UserProfileOut, UserProfileUpdate
from core.security import get_current_user
from core.database import get_db

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("/", response_model=UserProfileOut)
def get_profile(user: User = Depends(get_current_user)):
    return user


@router.put("/", response_model=UserProfileOut)
def update_profile(
    profile_update: UserProfileUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    update_data = profile_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


@router.get("/me", response_model=UserProfileOut)
def get_my_profile(user: User = Depends(get_current_user)):
    """Alias for get_profile for consistency"""
    return user

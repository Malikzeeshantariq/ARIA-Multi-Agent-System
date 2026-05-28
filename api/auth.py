import os
from datetime import datetime, timedelta

import bcrypt as _bcrypt

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import User

# ── Config ─────────────────────────────────────────────────────
JWT_SECRET      = os.getenv("JWT_SECRET", "change-this-in-production-use-random-string")
JWT_ALGORITHM   = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# ── Helpers ────────────────────────────────────────────────────
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)
router        = APIRouter(prefix="/auth", tags=["auth"])


# ── Pydantic schemas ───────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str = ""


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserOut(BaseModel):
    id: str
    email: str
    full_name: str | None
    created_at: datetime


# ── Password helpers ───────────────────────────────────────────

def hash_password(plain: str) -> str:
    return _bcrypt.hashpw(plain.encode(), _bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return _bcrypt.checkpw(plain.encode(), hashed.encode())


# ── JWT helpers ────────────────────────────────────────────────

def create_access_token(user_id: str, email: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": user_id, "email": email, "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ── FastAPI dependency — get current user from token ───────────

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_token(token)
    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def get_optional_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    """Same as get_current_user but returns None instead of raising."""
    if not token:
        return None
    try:
        payload = decode_token(token)
        return db.query(User).filter(User.id == payload["sub"]).first()
    except HTTPException:
        return None


# ── Routes ─────────────────────────────────────────────────────

@router.post("/register", response_model=LoginResponse, status_code=201)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """Create a new account and return an access token."""
    if len(req.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email           = req.email,
        hashed_password = hash_password(req.password),
        full_name       = req.full_name or None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id, user.email)
    return LoginResponse(
        access_token = token,
        user = {
            "id":        user.id,
            "email":     user.email,
            "full_name": user.full_name or "",
        },
    )


@router.post("/login", response_model=LoginResponse)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db:   Session                   = Depends(get_db),
):
    """
    Login with email + password.
    Returns a JWT access token valid for ACCESS_TOKEN_EXPIRE_MINUTES minutes.
    """
    user = db.query(User).filter(User.email == form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    # Update last login timestamp
    user.last_login = datetime.utcnow()
    db.commit()

    token = create_access_token(user.id, user.email)
    return LoginResponse(
        access_token = token,
        user = {
            "id":        user.id,
            "email":     user.email,
            "full_name": user.full_name or "",
        },
    )


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    """Return the currently authenticated user's profile."""
    return UserOut(
        id         = current_user.id,
        email      = current_user.email,
        full_name  = current_user.full_name,
        created_at = current_user.created_at,
    )


@router.post("/logout")
def logout():
    """
    Client-side logout — just clear the token from session_state.
    (Stateless JWT: no server-side invalidation unless you add a blocklist.)
    """
    return {"message": "Logged out successfully"}

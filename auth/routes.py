from fastapi import APIRouter, Depends, HTTPException, status, Form, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from .database import get_db
from .models import User, TokenBlacklist, UserSession, UserCreate, UserResponse, Token
from .auth_utils import verify_password, get_password_hash, create_access_token, validate_password_strength
from .dependencies import get_current_user
from datetime import timedelta
import re

router = APIRouter(prefix="/auth", tags=["authentication"])

def is_valid_email(email: str) -> bool:
    """Validar formato de email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def is_valid_username(username: str) -> bool:
    """Validar formato de username (alfanumérico, guiones y guiones bajos)"""
    pattern = r'^[a-zA-Z0-9_-]{3,20}$'
    return re.match(pattern, username) is not None

@router.post("/register", response_model=dict)
async def register_user(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Registrar nuevo usuario"""
    
    # Validaciones básicas
    if password != confirm_password:
        raise HTTPException(
            status_code=400,
            detail="Passwords do not match"
        )
    
    if not validate_password_strength(password):
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 6 characters long"
        )
    
    if not is_valid_email(email):
        raise HTTPException(
            status_code=400,
            detail="Invalid email format"
        )
    
    if not is_valid_username(username):
        raise HTTPException(
            status_code=400,
            detail="Username must be 3-20 characters, only letters, numbers, _ and -"
        )
    
    # Verificar si el usuario ya existe
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(
            status_code=400,
            detail="Username already registered"
        )
    
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    # Crear usuario
    hashed_password = get_password_hash(password)
    
    # Primer usuario registrado es admin
    is_first_user = db.query(User).count() == 0
    
    user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        is_admin=is_first_user
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return {
        "success": True,
        "message": "User created successfully" + (" (Admin privileges granted)" if is_first_user else ""),
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_admin": user.is_admin
        }
    }

@router.post("/login")
async def login_user(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Login de usuario y generar token JWT"""
    
    # Buscar usuario por username o email
    user = db.query(User).filter(
        (User.username == username) | (User.email == username)
    ).first()
    
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user"
        )
    
    # Crear token JWT
    access_token_expires = timedelta(minutes=1440)  # 24 horas
    access_token = create_access_token(
        data={"sub": user.username}, 
        expires_delta=access_token_expires
    )
    
    return {
        "success": True,
        "access_token": access_token,
        "token_type": "bearer",
        "message": "Login successful",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_admin": user.is_admin
        }
    }

@router.post("/logout")
async def logout_user(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Logout - agregar token a blacklist"""
    
    # Obtener token del header
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        
        # Agregar a blacklist
        blacklist_entry = TokenBlacklist(token=token)
        db.add(blacklist_entry)
        db.commit()
    
    return {"success": True, "message": "Logged out successfully"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Obtener información del usuario actual"""
    return UserResponse.from_orm(current_user)

@router.get("/profile")
async def get_user_profile(
    current_user: User = Depends(get_current_user)
):
    """Obtener perfil del usuario (endpoint alternativo para compatibilidad)"""
    return {
        "success": True,
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "is_admin": current_user.is_admin,
            "is_active": current_user.is_active,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None
        }
    }

@router.get("/validate")
async def validate_token_endpoint(
    current_user: User = Depends(get_current_user)
):
    """Endpoint para validar si un token es válido"""
    return {
        "valid": True,
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "is_admin": current_user.is_admin
        }
    }

@router.get("/sessions")
async def get_user_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener sesiones del usuario actual"""
    sessions = db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.is_active == True
    ).all()
    
    return {
        "success": True,
        "sessions": [
            {
                "id": session.id,
                "name": session.session_name,
                "created_at": session.created_at
            }
            for session in sessions
        ]
    }

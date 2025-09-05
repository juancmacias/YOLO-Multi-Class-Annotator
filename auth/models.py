from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relación con sesiones
    sessions = relationship("UserSession", back_populates="user")

class UserSession(Base):
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_name = Column(String(100), nullable=False)
    session_hash = Column(String(64), unique=True, nullable=False, index=True)  # Hash único para acceso privado
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    user = relationship("User", back_populates="sessions")

class TokenBlacklist(Base):
    __tablename__ = "token_blacklist"
    
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(500), unique=True, index=True)
    blacklisted_at = Column(DateTime, default=datetime.utcnow)

class AnnotationClass(Base):
    __tablename__ = "annotation_classes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    color = Column(String(7), nullable=False, default="#ff0000")  # Color hex
    user_id = Column(Integer, ForeignKey("users.id"))
    session_name = Column(String(100), nullable=True)  # Si es específica para una sesión
    session_hash = Column(String(64), nullable=True, index=True)  # Hash de sesión para acceso privado
    is_global = Column(Boolean, default=False)  # Si es global (para admin)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User")

# Schemas Pydantic para validación
from pydantic import BaseModel, EmailStr
from typing import Optional, List

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    is_admin: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class TokenData(BaseModel):
    username: Optional[str] = None

class AnnotationClassCreate(BaseModel):
    name: str
    color: str = "#ff0000"
    session_name: Optional[str] = None
    session_hash: Optional[str] = None  # Hash de sesión para acceso privado
    is_global: bool = False

class AnnotationClassUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None
    is_active: Optional[bool] = None

class AnnotationClassResponse(BaseModel):
    id: int
    name: str
    color: str
    user_id: int
    session_name: Optional[str]
    session_hash: Optional[str]  # Incluir hash en respuesta
    is_global: bool
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Esquemas para manejo de sesiones con hash
class SessionCreate(BaseModel):
    session_name: str

class SessionResponse(BaseModel):
    id: int
    session_name: str
    session_hash: str  # Hash único para acceso
    user_id: int
    created_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True

class SessionAccess(BaseModel):
    session_hash: str

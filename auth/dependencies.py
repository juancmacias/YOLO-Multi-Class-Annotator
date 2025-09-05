from fastapi import Depends, HTTPException, status, Request, Path
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from .database import get_db
from .models import User, TokenBlacklist, UserSession
from .auth_utils import verify_token
from .session_utils import verify_session_access as verify_hash_access, get_session_by_hash
from typing import Optional

# Security scheme
security = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Dependency para obtener usuario actual autenticado"""
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not credentials:
        raise credentials_exception
    
    token = credentials.credentials
    
    # Verificar si el token está en blacklist
    blacklisted = db.query(TokenBlacklist).filter(
        TokenBlacklist.token == token
    ).first()
    if blacklisted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verificar token JWT
    username = verify_token(token)
    if username is None:
        raise credentials_exception
    
    # Buscar usuario en base de datos
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user"
        )
    
    return user

async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Dependency opcional - devuelve usuario si está autenticado, None si no"""
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None

async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Dependency para verificar que el usuario actual es admin"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

def verify_session_access(user: User, session_name: str, db: Session) -> bool:
    """Verificar si el usuario tiene acceso a una sesión específica"""
    from .models import UserSession
    
    # Los admins tienen acceso a todo
    if user.is_admin:
        return True
    
    # Verificar si el usuario tiene una sesión con ese nombre
    user_session = db.query(UserSession).filter(
        UserSession.user_id == user.id,
        UserSession.session_name == session_name,
        UserSession.is_active == True
    ).first()
    
    return user_session is not None

async def require_session_access(
    session_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> User:
    """Dependency que requiere acceso específico a una sesión"""
    if not verify_session_access(current_user, session_name, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"No access to session '{session_name}'"
        )
    return current_user

# =====================================
# NUEVAS DEPENDENCIAS PARA HASH SESSIONS
# =====================================

async def get_session_by_hash_dep(
    session_hash: str = Path(..., description="Hash único de la sesión"),
    db: Session = Depends(get_db)
) -> UserSession:
    """
    Dependency para obtener una sesión por su hash.
    No requiere autenticación - cualquiera con el hash puede acceder.
    """
    session = get_session_by_hash(db, session_hash)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or inactive"
        )
    return session

async def verify_session_owner(
    session_hash: str = Path(..., description="Hash único de la sesión"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> UserSession:
    """
    Dependency para verificar que el usuario actual es propietario de la sesión.
    Solo el propietario puede modificar/eliminar la sesión.
    """
    session = get_session_by_hash(db, session_hash)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or inactive"
        )
    
    # Verificar propiedad (los admins también pueden acceder)
    if session.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this session"
        )
    
    return session

async def get_session_with_optional_auth(
    session_hash: str = Path(..., description="Hash único de la sesión"),
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
) -> tuple[UserSession, Optional[User]]:
    """
    Dependency que obtiene la sesión y el usuario (si está autenticado).
    Útil para endpoints que pueden funcionar con o sin autenticación.
    """
    session = get_session_by_hash(db, session_hash)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or inactive"
        )
    
    return session, current_user

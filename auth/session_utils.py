import hashlib
import secrets
import time
from typing import Optional
from sqlalchemy.orm import Session
from .models import UserSession, User

def generate_session_hash(user_id: int, session_name: str) -> str:
    """
    Genera un hash único para una sesión basado en:
    - ID del usuario
    - Nombre de la sesión
    - Timestamp actual
    - Salt aleatorio
    """
    # Crear un salt aleatorio
    salt = secrets.token_hex(16)
    
    # Crear string único combinando datos
    unique_string = f"{user_id}:{session_name}:{time.time()}:{salt}"
    
    # Generar hash SHA-256
    session_hash = hashlib.sha256(unique_string.encode()).hexdigest()
    
    return session_hash

def create_private_session(
    db: Session, 
    user_id: int, 
    session_name: str
) -> UserSession:
    """
    Crea una nueva sesión privada con hash único
    """
    # Generar hash único
    session_hash = generate_session_hash(user_id, session_name)
    
    # Verificar que el hash sea único (muy improbable que se repita, pero por seguridad)
    while db.query(UserSession).filter(UserSession.session_hash == session_hash).first():
        session_hash = generate_session_hash(user_id, session_name)
    
    # Crear la sesión
    new_session = UserSession(
        session_name=session_name,
        session_hash=session_hash,
        user_id=user_id,
        is_active=True
    )
    
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    
    return new_session

def verify_session_access(
    db: Session, 
    session_hash: str, 
    user_id: Optional[int] = None
) -> Optional[UserSession]:
    """
    Verifica el acceso a una sesión mediante hash.
    
    Args:
        db: Sesión de base de datos
        session_hash: Hash de la sesión
        user_id: ID del usuario (opcional, para verificación adicional)
    
    Returns:
        UserSession si el acceso es válido, None si no
    """
    query = db.query(UserSession).filter(
        UserSession.session_hash == session_hash,
        UserSession.is_active == True
    )
    
    # Si se proporciona user_id, verificar que coincida
    if user_id is not None:
        query = query.filter(UserSession.user_id == user_id)
    
    return query.first()

def get_session_by_hash(db: Session, session_hash: str) -> Optional[UserSession]:
    """
    Obtiene una sesión por su hash
    """
    return db.query(UserSession).filter(
        UserSession.session_hash == session_hash,
        UserSession.is_active == True
    ).first()

def get_user_sessions(db: Session, user_id: int) -> list[UserSession]:
    """
    Obtiene todas las sesiones activas de un usuario
    """
    return db.query(UserSession).filter(
        UserSession.user_id == user_id,
        UserSession.is_active == True
    ).all()

def deactivate_session(db: Session, session_hash: str, user_id: int) -> bool:
    """
    Desactiva una sesión (solo el propietario puede hacerlo)
    """
    session = db.query(UserSession).filter(
        UserSession.session_hash == session_hash,
        UserSession.user_id == user_id,
        UserSession.is_active == True
    ).first()
    
    if session:
        session.is_active = False
        db.commit()
        return True
    
    return False

def is_session_owner(db: Session, session_hash: str, user_id: int) -> bool:
    """
    Verifica si un usuario es propietario de una sesión
    """
    session = db.query(UserSession).filter(
        UserSession.session_hash == session_hash,
        UserSession.user_id == user_id,
        UserSession.is_active == True
    ).first()
    
    return session is not None

def generate_session_url(session_hash: str, base_url: str = "http://localhost:8002") -> str:
    """
    Genera una URL para acceder a una sesión específica
    """
    return f"{base_url}/session/{session_hash}"

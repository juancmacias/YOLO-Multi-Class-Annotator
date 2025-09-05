from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from .database import get_db
from .models import (
    UserSession, AnnotationClass, User,
    SessionCreate, SessionResponse, SessionAccess,
    AnnotationClassResponse
)
from .dependencies import (
    get_current_user, get_session_by_hash_dep, 
    verify_session_owner, get_session_with_optional_auth
)
from .session_utils import (
    create_private_session, get_user_sessions, 
    deactivate_session, generate_session_url
)

router = APIRouter(prefix="/api/sessions", tags=["Private Sessions"])

@router.post("/create", response_model=SessionResponse)
async def create_session(
    session_data: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Crear una nueva sesión privada con hash único.
    Solo el creador tendrá acceso inicial.
    """
    # Verificar que no exista ya una sesión con el mismo nombre para este usuario
    existing = db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.session_name == session_data.session_name,
        UserSession.is_active == True
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Session '{session_data.session_name}' already exists"
        )
    
    # Crear la sesión privada
    new_session = create_private_session(
        db=db,
        user_id=current_user.id,
        session_name=session_data.session_name
    )
    
    return new_session

@router.get("/my-sessions", response_model=List[SessionResponse])
async def get_my_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener todas las sesiones del usuario actual con información completa
    """
    from app_auth import get_user_sessions_with_info
    sessions = get_user_sessions_with_info(current_user, db)
    
    # Convertir a formato SessionResponse
    session_responses = []
    for session_info in sessions:
        # Buscar la sesión en la base de datos para obtener todos los datos
        session_obj = db.query(UserSession).filter(
            UserSession.session_name == session_info['name'],
            UserSession.is_active == True
        ).first()
        
        if session_obj:
            session_responses.append(session_obj)
    
    return session_responses

@router.get("/{session_hash}", response_model=SessionResponse)
async def get_session_info(
    session: UserSession = Depends(get_session_by_hash_dep)
):
    """
    Obtener información de una sesión por su hash.
    Acceso público - cualquiera con el hash puede ver la info básica.
    """
    return session

@router.get("/{session_hash}/url")
async def get_session_url(
    session: UserSession = Depends(get_session_by_hash_dep)
):
    """
    Obtener la URL de acceso a una sesión
    """
    url = generate_session_url(session.session_hash)
    return {
        "session_hash": session.session_hash,
        "session_name": session.session_name,
        "access_url": url,
        "created_by": session.user.username
    }

@router.delete("/{session_hash}")
async def deactivate_session_endpoint(
    session: UserSession = Depends(verify_session_owner),
    db: Session = Depends(get_db)
):
    """
    Desactivar una sesión (solo el propietario)
    """
    success = deactivate_session(db, session.session_hash, session.user_id)
    if success:
        return {"message": f"Session '{session.session_name}' deactivated successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate session"
        )

@router.get("/{session_hash}/annotations", response_model=List[AnnotationClassResponse])
async def get_session_annotations(
    session_and_user: tuple = Depends(get_session_with_optional_auth),
    db: Session = Depends(get_db)
):
    """
    Obtener todas las clases de anotación de una sesión específica.
    Acceso por hash - no requiere autenticación.
    """
    session, current_user = session_and_user
    
    # Obtener anotaciones de esta sesión específica
    annotations = db.query(AnnotationClass).filter(
        AnnotationClass.session_hash == session.session_hash,
        AnnotationClass.is_active == True
    ).all()
    
    return annotations

@router.post("/{session_hash}/annotations", response_model=AnnotationClassResponse)
async def create_session_annotation(
    annotation_data: dict,
    session_and_user: tuple = Depends(get_session_with_optional_auth),
    db: Session = Depends(get_db)
):
    """
    Crear una nueva clase de anotación en una sesión específica.
    Cualquiera con el hash puede agregar anotaciones.
    """
    session, current_user = session_and_user
    
    # Si el usuario está autenticado, usar su ID, sino usar el ID del propietario de la sesión
    user_id = current_user.id if current_user else session.user_id
    
    new_annotation = AnnotationClass(
        name=annotation_data.get("name"),
        color=annotation_data.get("color", "#ff0000"),
        user_id=user_id,
        session_name=session.session_name,
        session_hash=session.session_hash,
        is_global=False,
        is_active=True
    )
    
    db.add(new_annotation)
    db.commit()
    db.refresh(new_annotation)
    
    return new_annotation

@router.get("/{session_hash}/stats")
async def get_session_stats(
    session: UserSession = Depends(get_session_by_hash_dep),
    db: Session = Depends(get_db)
):
    """
    Obtener estadísticas de una sesión
    """
    # Contar anotaciones
    annotation_count = db.query(AnnotationClass).filter(
        AnnotationClass.session_hash == session.session_hash,
        AnnotationClass.is_active == True
    ).count()
    
    return {
        "session_name": session.session_name,
        "session_hash": session.session_hash,
        "created_by": session.user.username,
        "created_at": session.created_at,
        "annotation_classes_count": annotation_count,
        "is_active": session.is_active
    }

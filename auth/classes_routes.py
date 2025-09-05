from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from .database import get_db
from .models import AnnotationClass, AnnotationClassCreate, AnnotationClassUpdate, AnnotationClassResponse, User
from .dependencies import get_current_user

router = APIRouter(prefix="/api/classes", tags=["annotation_classes"])

# Clases por defecto para usuarios nuevos
DEFAULT_CLASSES = [
    {"name": "Persona", "color": "#ff0000"},
    {"name": "Vehículo", "color": "#00ff00"},
    {"name": "Animal", "color": "#0000ff"},
    {"name": "Edificio", "color": "#ffff00"},
    {"name": "Objeto", "color": "#ff00ff"},
    {"name": "Naturaleza", "color": "#00ffff"}
]

@router.get("/", response_model=List[AnnotationClassResponse])
async def get_user_classes(
    session_name: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener todas las clases del usuario para una sesión específica o globales"""
    
    query = db.query(AnnotationClass).filter(
        AnnotationClass.is_active == True
    )
    
    # Filtrar por usuario y incluir clases globales
    query = query.filter(
        (AnnotationClass.user_id == current_user.id) | 
        (AnnotationClass.is_global == True)
    )
    
    # Si se especifica una sesión, incluir clases específicas de esa sesión
    if session_name:
        query = query.filter(
            (AnnotationClass.session_name == session_name) |
            (AnnotationClass.session_name.is_(None))
        )
    else:
        # Solo clases globales/generales (sin sesión específica)
        query = query.filter(AnnotationClass.session_name.is_(None))
    
    classes = query.order_by(AnnotationClass.created_at).all()
    
    # Si no tiene clases, crear las por defecto
    if not classes and not session_name:
        classes = await create_default_classes(current_user.id, db)
    
    return classes

@router.post("/", response_model=AnnotationClassResponse)
async def create_annotation_class(
    class_data: AnnotationClassCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crear una nueva clase de anotación"""
    
    # Validar que el nombre no esté duplicado para este usuario/sesión
    existing = db.query(AnnotationClass).filter(
        AnnotationClass.user_id == current_user.id,
        AnnotationClass.name == class_data.name,
        AnnotationClass.session_name == class_data.session_name,
        AnnotationClass.is_active == True
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe una clase con el nombre '{class_data.name}'"
        )
    
    # Solo admin puede crear clases globales
    if class_data.is_global and not current_user.is_admin:
        class_data.is_global = False
    
    # Validar formato de color
    if not class_data.color.startswith('#') or len(class_data.color) != 7:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Color debe estar en formato hexadecimal #RRGGBB"
        )
    
    new_class = AnnotationClass(
        name=class_data.name,
        color=class_data.color,
        user_id=current_user.id,
        session_name=class_data.session_name,
        is_global=class_data.is_global
    )
    
    db.add(new_class)
    db.commit()
    db.refresh(new_class)
    
    return new_class

@router.put("/{class_id}", response_model=AnnotationClassResponse)
async def update_annotation_class(
    class_id: int,
    class_data: AnnotationClassUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualizar una clase de anotación"""
    
    annotation_class = db.query(AnnotationClass).filter(
        AnnotationClass.id == class_id
    ).first()
    
    if not annotation_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clase no encontrada"
        )
    
    # Verificar permisos
    if annotation_class.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para editar esta clase"
        )
    
    # Actualizar campos
    if class_data.name is not None:
        # Verificar duplicados
        existing = db.query(AnnotationClass).filter(
            AnnotationClass.user_id == annotation_class.user_id,
            AnnotationClass.name == class_data.name,
            AnnotationClass.session_name == annotation_class.session_name,
            AnnotationClass.id != class_id,
            AnnotationClass.is_active == True
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe una clase con el nombre '{class_data.name}'"
            )
        
        annotation_class.name = class_data.name
    
    if class_data.color is not None:
        if not class_data.color.startswith('#') or len(class_data.color) != 7:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Color debe estar en formato hexadecimal #RRGGBB"
            )
        annotation_class.color = class_data.color
    
    if class_data.is_active is not None:
        annotation_class.is_active = class_data.is_active
    
    db.commit()
    db.refresh(annotation_class)
    
    return annotation_class

@router.delete("/{class_id}")
async def delete_annotation_class(
    class_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Eliminar (desactivar) una clase de anotación"""
    
    annotation_class = db.query(AnnotationClass).filter(
        AnnotationClass.id == class_id
    ).first()
    
    if not annotation_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clase no encontrada"
        )
    
    # Verificar permisos
    if annotation_class.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para eliminar esta clase"
        )
    
    # Soft delete
    annotation_class.is_active = False
    db.commit()
    
    return {"detail": "Clase eliminada correctamente"}

@router.post("/reset-to-default")
async def reset_to_default_classes(
    session_name: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Restablecer a clases por defecto"""
    
    # Desactivar clases existentes
    existing_classes = db.query(AnnotationClass).filter(
        AnnotationClass.user_id == current_user.id,
        AnnotationClass.session_name == session_name,
        AnnotationClass.is_active == True
    ).all()
    
    for cls in existing_classes:
        cls.is_active = False
    
    # Crear clases por defecto
    new_classes = []
    for default_class in DEFAULT_CLASSES:
        new_class = AnnotationClass(
            name=default_class["name"],
            color=default_class["color"],
            user_id=current_user.id,
            session_name=session_name,
            is_global=False
        )
        db.add(new_class)
        new_classes.append(new_class)
    
    db.commit()
    
    # Refrescar objetos
    for cls in new_classes:
        db.refresh(cls)
    
    return {"detail": f"Se han creado {len(new_classes)} clases por defecto", "classes": new_classes}

@router.get("/available-colors")
async def get_available_colors():
    """Obtener colores predefinidos para clases"""
    
    colors = [
        {"name": "Rojo", "value": "#ff0000"},
        {"name": "Verde", "value": "#00ff00"},
        {"name": "Azul", "value": "#0000ff"},
        {"name": "Amarillo", "value": "#ffff00"},
        {"name": "Magenta", "value": "#ff00ff"},
        {"name": "Cian", "value": "#00ffff"},
        {"name": "Naranja", "value": "#ff8800"},
        {"name": "Rosa", "value": "#ff0088"},
        {"name": "Púrpura", "value": "#8800ff"},
        {"name": "Verde Lima", "value": "#88ff00"},
        {"name": "Azul Cielo", "value": "#0088ff"},
        {"name": "Turquesa", "value": "#00ff88"},
        {"name": "Rojo Oscuro", "value": "#800000"},
        {"name": "Verde Oscuro", "value": "#008000"},
        {"name": "Azul Oscuro", "value": "#000080"},
        {"name": "Marrón", "value": "#8B4513"},
        {"name": "Gris", "value": "#808080"},
        {"name": "Negro", "value": "#000000"}
    ]
    
    return colors

async def create_default_classes(user_id: int, db: Session) -> List[AnnotationClass]:
    """Crear clases por defecto para un usuario nuevo"""
    
    classes = []
    for default_class in DEFAULT_CLASSES:
        new_class = AnnotationClass(
            name=default_class["name"],
            color=default_class["color"],
            user_id=user_id,
            session_name=None,  # Clases globales del usuario
            is_global=False
        )
        db.add(new_class)
        classes.append(new_class)
    
    db.commit()
    
    # Refrescar objetos
    for cls in classes:
        db.refresh(cls)
    
    return classes

@router.post("/import")
async def import_classes_from_annotations(
    session_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Importar clases automáticamente desde anotaciones existentes"""
    
    # Leer archivos de anotaciones de la sesión
    import os
    
    session_path = os.path.join("annotations", session_name, "labels")
    if not os.path.exists(session_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sesión no encontrada"
        )
    
    # Encontrar todas las clases usadas
    used_class_ids = set()
    
    for filename in os.listdir(session_path):
        if filename.endswith('.txt'):
            filepath = os.path.join(session_path, filename)
            try:
                with open(filepath, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            parts = line.split()
                            if len(parts) >= 5:
                                class_id = int(parts[0])
                                used_class_ids.add(class_id)
            except:
                continue
    
    # Crear clases automáticamente
    created_classes = []
    existing_classes = db.query(AnnotationClass).filter(
        AnnotationClass.user_id == current_user.id,
        AnnotationClass.session_name == session_name,
        AnnotationClass.is_active == True
    ).all()
    
    existing_ids = {cls.id - 1 for cls in existing_classes}  # Ajustar para índice 0
    
    colors = ["#ff0000", "#00ff00", "#0000ff", "#ffff00", "#ff00ff", "#00ffff", 
              "#ff8800", "#ff0088", "#8800ff", "#88ff00", "#0088ff", "#00ff88"]
    
    for class_id in sorted(used_class_ids):
        if class_id not in existing_ids:
            color = colors[class_id % len(colors)]
            new_class = AnnotationClass(
                name=f"Clase {class_id}",
                color=color,
                user_id=current_user.id,
                session_name=session_name,
                is_global=False
            )
            db.add(new_class)
            created_classes.append(new_class)
    
    if created_classes:
        db.commit()
        for cls in created_classes:
            db.refresh(cls)
    
    return {
        "detail": f"Se importaron {len(created_classes)} clases nuevas",
        "created_classes": created_classes,
        "found_class_ids": list(used_class_ids)
    }

from fastapi import FastAPI, File, UploadFile, Form, Request, BackgroundTasks, Depends, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from augment_dataset import augment_session, get_session_stats, AVAILABLE_VARIANTS
from PIL import Image, ImageDraw
import numpy as np
import random
import io
import base64
import json
import zipfile
from datetime import datetime
import shutil
from sqlalchemy.orm import Session

# Importar módulos de autenticación
from auth.database import create_tables, get_db
from auth.models import User, UserSession
from auth.routes import router as auth_router
from auth.classes_routes import router as classes_router
from auth.session_routes import router as hash_sessions_router
from auth.dependencies import get_current_user, get_optional_user, verify_session_access

# Crear aplicación FastAPI
app = FastAPI(
    title="YOLO Multi-Class Annotator & Visualizer (JWT Auth)",
    description="Sistema de anotación YOLO con autenticación JWT",
    version="2.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar templates y archivos estáticos
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Incluir router de autenticación
app.include_router(auth_router)
app.include_router(classes_router)
app.include_router(hash_sessions_router)

# Crear carpetas necesarias
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)
os.makedirs("annotations", exist_ok=True)
os.makedirs("temp", exist_ok=True)

# Crear tablas de base de datos
create_tables()

# Funciones auxiliares (copiadas del original)
def create_session_structure(session_name, user_id=None, db=None):
    """Crear estructura de sesión y asociarla con usuario"""
    session_path = f"annotations/{session_name}"
    os.makedirs(f"{session_path}/images", exist_ok=True)
    os.makedirs(f"{session_path}/labels", exist_ok=True)
    
    # Si se proporciona user_id, crear relación en base de datos
    if user_id and db:
        existing_session = db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.session_name == session_name
        ).first()
        
        if not existing_session:
            user_session = UserSession(
                session_name=session_name,
                user_id=user_id
            )
            db.add(user_session)
            db.commit()
    
    return session_path

def random_color():
    return tuple(random.randint(0, 255) for _ in range(3))

def create_canvas_with_image(image_bytes, size, x, y, change_bg=True, max_size=800):
    """Crear canvas con imagen redimensionada automáticamente"""
    bg_color = random_color() if change_bg else (200, 200, 200)
    canvas = Image.new('RGB', size, bg_color)
    
    # Cargar imagen subida (soporta múltiples formatos incluyendo WebP)
    img = Image.open(io.BytesIO(image_bytes))
    
    # Convertir a RGB si es necesario (para WebP con transparencia, etc.)
    if img.mode in ('RGBA', 'LA', 'P'):
        # Crear fondo blanco para transparencias
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
        img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Redimensionar imagen si es muy grande manteniendo aspecto
    original_width, original_height = img.size
    
    # Calcular nuevo tamaño manteniendo proporción
    if original_width > max_size or original_height > max_size:
        ratio = min(max_size / original_width, max_size / original_height)
        new_width = int(original_width * ratio)
        new_height = int(original_height * ratio)
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Centrar imagen si es menor que el canvas
    canvas_width, canvas_height = size
    img_width, img_height = img.size
    
    # Calcular posición centrada o usar coordenadas proporcionadas
    if x == 0 and y == 0:  # Auto-centrar
        paste_x = (canvas_width - img_width) // 2
        paste_y = (canvas_height - img_height) // 2
    else:
        # Usar coordenadas proporcionadas pero asegurar que la imagen esté dentro
        paste_x = min(x, canvas_width - img_width)
        paste_y = min(y, canvas_height - img_height)
    
    paste_x = max(0, paste_x)
    paste_y = max(0, paste_y)
    
    # Pegar imagen en canvas
    canvas.paste(img, (paste_x, paste_y))
    
    return canvas

def image_to_base64(pil_image):
    buffer = io.BytesIO()
    pil_image.save(buffer, format='JPEG', quality=90)
    img_data = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/jpeg;base64,{img_data}"

def get_user_sessions_list(user: User, db: Session):
    """Obtener lista de nombres de sesiones del usuario (para compatibilidad)"""
    if user and user.is_admin:
        # Los admins pueden ver todas las sesiones
        sessions_dir = "annotations"
        all_sessions = []
        if os.path.exists(sessions_dir):
            for session_name in os.listdir(sessions_dir):
                session_path = os.path.join(sessions_dir, session_name)
                if os.path.isdir(session_path):
                    all_sessions.append(session_name)
        return all_sessions
    elif user:
        # Usuarios normales solo ven sus sesiones
        user_sessions = db.query(UserSession).filter(
            UserSession.user_id == user.id,
            UserSession.is_active == True
        ).all()
        return [session.session_name for session in user_sessions]
    else:
        # Usuario no autenticado: mostrar todas las sesiones disponibles (modo invitado)
        sessions_dir = "annotations"
        all_sessions = []
        if os.path.exists(sessions_dir):
            for session_name in os.listdir(sessions_dir):
                session_path = os.path.join(sessions_dir, session_name)
                if os.path.isdir(session_path):
                    all_sessions.append(session_name)
        return all_sessions


def get_user_sessions_with_info(user: User, db: Session):
    """Obtener lista de sesiones del usuario con información completa (para API)"""
    if user and user.is_admin:
        # Los admins pueden ver todas las sesiones activas de la base de datos
        user_sessions = db.query(UserSession).filter(
            UserSession.is_active == True
        ).all()
        
        sessions_list = []
        for session in user_sessions:
            session_info = {
                'name': session.session_name,
                'session_hash': session.session_hash,
                'is_private': bool(session.session_hash)
            }
            sessions_list.append(session_info)
        
        return sessions_list
    elif user:
        # Usuarios normales solo ven sus sesiones
        user_sessions = db.query(UserSession).filter(
            UserSession.user_id == user.id,
            UserSession.is_active == True
        ).all()
        
        sessions_list = []
        for session in user_sessions:
            session_info = {
                'name': session.session_name,
                'session_hash': session.session_hash,
                'is_private': bool(session.session_hash)
            }
            sessions_list.append(session_info)
        
        return sessions_list
    else:
        # Usuario no autenticado: mostrar sesiones disponibles con directorios físicos
        sessions_dir = "annotations"
        all_sessions = []
        if os.path.exists(sessions_dir):
            for session_name in os.listdir(sessions_dir):
                session_path = os.path.join(sessions_dir, session_name)
                if os.path.isdir(session_path):
                    # Para usuarios no autenticados, no mostrar información de hash
                    session_info = {
                        'name': session_name,
                        'session_hash': None,
                        'is_private': False
                    }
                    all_sessions.append(session_info)
        return all_sessions

# ============================================================================
# MIDDLEWARE DE AUTENTICACIÓN
# ============================================================================
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """Middleware para manejar autenticación en rutas protegidas"""
    
    # Rutas públicas que no requieren autenticación
    public_paths = [
        "/",
        "/login", 
        "/register", 
        "/auth/", 
        "/static/", 
        "/docs", 
        "/redoc", 
        "/openapi.json"
    ]
    
    # Verificar si la ruta es pública
    is_public = any(request.url.path.startswith(path) for path in public_paths)
    
    if is_public:
        response = await call_next(request)
        return response
    
    # Para rutas protegidas, verificar autenticación en el navegador
    # (Las rutas API manejan su propia autenticación con dependencies)
    if not request.url.path.startswith("/api/"):
        # Verificar si hay token en headers (para navegador)
        auth_header = request.headers.get("authorization")
        if not auth_header:
            # Redireccionar a login si no está autenticado
            return RedirectResponse(url="/login", status_code=302)
    
    response = await call_next(request)
    return response

# ============================================================================
# ENDPOINTS PRINCIPALES
# ============================================================================
@app.get("/", response_class=HTMLResponse)
async def main(request: Request):
    """Página principal - pública"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Página de login"""
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Página de registro"""
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request, 
    current_user: User = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Dashboard principal - verificación de autenticación en frontend"""
    if current_user:
        user_sessions = get_user_sessions_list(current_user, db)
    else:
        user_sessions = []
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": current_user,
        "sessions": user_sessions
    })

@app.get("/sessions", response_class=HTMLResponse) 
async def sessions_page(
    request: Request, 
    current_user: User = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Página de gestión de sesiones - autenticación opcional"""
    try:
        sessions_dir = "annotations"
        sessions = []
        
        # Obtener sesiones del usuario
        user_sessions = get_user_sessions_list(current_user, db)
        
        for session_name in user_sessions:
            session_path = os.path.join(sessions_dir, session_name)
            if os.path.isdir(session_path):
                images_path = os.path.join(session_path, "images")
                labels_path = os.path.join(session_path, "labels")
                
                image_count = 0
                label_count = 0
                
                if os.path.exists(images_path):
                    image_count = len([f for f in os.listdir(images_path) 
                                     if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
                
                if os.path.exists(labels_path):
                    label_count = len([f for f in os.listdir(labels_path) 
                                     if f.lower().endswith('.txt')])
                
                sessions.append({
                    'name': session_name,
                    'images': image_count,
                    'labels': label_count,
                    'path': session_path
                })
        
        return templates.TemplateResponse("sessions.html", {
            "request": request,
            "sessions": sessions,
            "current_user": current_user
        })
        
    except Exception as e:
        return HTMLResponse(content=f"<h1>Error</h1><p>Error: {str(e)}</p><a href='/dashboard'>← Volver</a>")

@app.get("/annotator", response_class=HTMLResponse)
async def annotator_page(
    request: Request, 
    current_user: User = Depends(get_optional_user)
):
    """Anotador clásico para crear datasets - verificación de autenticación en frontend"""
    return templates.TemplateResponse("annotator.html", {
        "request": request,
        "user": current_user
    })

@app.get("/visualizer", response_class=HTMLResponse)
async def visualizer_page(
    request: Request, 
    session: str = None,
    current_user: User = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Visualizador de datasets con anotaciones - verificación de autenticación en frontend"""
    try:
        # Obtener sesiones del usuario si está autenticado
        if current_user:
            user_sessions = get_user_sessions_list(current_user, db)
            
            # Verificar acceso a sesión específica si se proporciona
            if session and not verify_session_access(current_user, session, db):
                raise HTTPException(status_code=403, detail="No access to this session")
        else:
            user_sessions = []
        
        return templates.TemplateResponse("visualizer.html", {
            "request": request,
            "sessions": user_sessions,
            "current_session": session,
            "user": current_user
        })
        
    except HTTPException:
        raise
    except Exception as e:
        return HTMLResponse(content=f"<h1>Error</h1><p>Error en visualizador: {str(e)}</p><a href='/dashboard'>← Volver</a>")

# ============================================================================
# API ENDPOINTS CON AUTENTICACIÓN
# ============================================================================

# ============================================================================
# NUEVOS ENDPOINTS PARA ACCESO POR HASH
# ============================================================================

@app.get("/session/{session_hash}", response_class=HTMLResponse)
async def session_by_hash_page(
    request: Request,
    session_hash: str,
    db: Session = Depends(get_db)
):
    """
    Página de acceso a una sesión específica por hash.
    NO requiere autenticación - acceso público con hash.
    """
    from auth.session_utils import get_session_by_hash
    
    # Verificar que la sesión existe
    session = get_session_by_hash(db, session_hash)
    if not session:
        return HTMLResponse(
            content=f"""
            <h1>🔍 Sesión no encontrada</h1>
            <p>La sesión con hash <code>{session_hash}</code> no existe o está inactiva.</p>
            <a href="/">← Ir al inicio</a>
            """,
            status_code=404
        )
    
    return templates.TemplateResponse("session_access.html", {
        "request": request,
        "session": session,
        "session_hash": session_hash,
        "annotator_url": f"/session/{session_hash}/annotator",
        "visualizer_url": f"/session/{session_hash}/visualizer"
    })

@app.get("/session/{session_hash}/annotator", response_class=HTMLResponse)
async def session_annotator_by_hash(
    request: Request,
    session_hash: str,
    db: Session = Depends(get_db)
):
    """
    Anotador para una sesión específica accesible por hash.
    NO requiere autenticación.
    """
    from auth.session_utils import get_session_by_hash
    
    session = get_session_by_hash(db, session_hash)
    if not session:
        return HTMLResponse(content="Sesión no encontrada", status_code=404)
    
    return templates.TemplateResponse("annotator.html", {
        "request": request,
        "session_hash": session_hash,
        "session_name": session.session_name,
        "public_access": True,
        "user": None  # Sin usuario autenticado
    })

@app.get("/session/{session_hash}/visualizer", response_class=HTMLResponse)
async def session_visualizer_by_hash(
    request: Request,
    session_hash: str,
    db: Session = Depends(get_db)
):
    """
    Visualizador para una sesión específica accesible por hash.
    NO requiere autenticación.
    """
    from auth.session_utils import get_session_by_hash
    
    session = get_session_by_hash(db, session_hash)
    if not session:
        return HTMLResponse(content="Sesión no encontrada", status_code=404)
    
    return templates.TemplateResponse("visualizer.html", {
        "request": request,
        "session_hash": session_hash,
        "session_name": session.session_name,
        "current_session": session.session_name,
        "public_access": True,
        "sessions": [session],  # Solo esta sesión
        "user": None  # Sin usuario autenticado
    })
@app.get("/api/sessions")
async def list_sessions_api(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Listar sesiones del usuario actual"""
    try:
        sessions_dir = "annotations"
        sessions = []
        
        # Obtener sesiones del usuario con información de hash
        user_sessions = get_user_sessions_list(current_user, db)
        
        for session_info in user_sessions:
            # Manejar tanto el formato nuevo (dict) como el viejo (string)
            if isinstance(session_info, dict):
                session_name = session_info['name']
                session_hash = session_info.get('session_hash')
                is_private = session_info.get('is_private', False)
            else:
                session_name = session_info
                session_hash = None
                is_private = False
                
            session_path = os.path.join(sessions_dir, session_name)
            
            # Contar archivos si el directorio existe
            images_count = 0
            labels_count = 0
            
            if os.path.isdir(session_path):
                images_path = os.path.join(session_path, "images")
                labels_path = os.path.join(session_path, "labels")
                
                if os.path.exists(images_path):
                    images_count = len([f for f in os.listdir(images_path) 
                                      if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'))])
                
                if os.path.exists(labels_path):
                    labels_count = len([f for f in os.listdir(labels_path) 
                                      if f.lower().endswith('.txt')])
            
            session_data = {
                'name': session_name,
                'images_count': images_count,
                'labels_count': labels_count,
                'is_private': is_private
            }
            
            # Agregar información de hash solo si existe
            if session_hash:
                session_data['session_hash'] = session_hash
                session_data['share_url'] = f"{request.base_url}session/{session_hash}"
            
            sessions.append(session_data)
        
        # Ordenar sesiones por nombre
        sessions.sort(key=lambda x: x['name'])
        
        return {
            "success": True,
            "sessions": sessions,
            "user": {
                "username": current_user.username,
                "is_admin": current_user.is_admin
            }
        }
    except Exception as e:
        return {"success": False, "message": f"Error al listar sesiones: {str(e)}"}

@app.get("/api/session/{session_name}/visualize")
async def get_session_visualize_data(
    session_name: str, 
    limit: int = None, 
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """API endpoint para obtener datos de visualización de una sesión"""
    try:
        # Verificar acceso a la sesión
        if not verify_session_access(current_user, session_name, db):
            return {"success": False, "message": "No tienes acceso a esta sesión"}
        
        session_path = os.path.join("annotations", session_name)
        images_path = os.path.join(session_path, "images")
        labels_path = os.path.join(session_path, "labels")
        
        if not os.path.exists(session_path):
            return {"success": False, "message": f"Sesión '{session_name}' no encontrada"}
        
        images_data = []
        total_labels = 0
        
        if os.path.exists(images_path):
            for filename in os.listdir(images_path):
                if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                    # Obtener dimensiones de la imagen
                    from PIL import Image as PILImage
                    image_path = os.path.join(images_path, filename)
                    
                    try:
                        with PILImage.open(image_path) as img:
                            width, height = img.size
                    except:
                        width, height = 640, 640  # Default si hay error
                    
                    # Leer etiquetas para esta imagen
                    label_filename = os.path.splitext(filename)[0] + '.txt'
                    label_path = os.path.join(labels_path, label_filename)
                    
                    annotations = []
                    if os.path.exists(label_path):
                        with open(label_path, 'r') as f:
                            for line_num, line in enumerate(f):
                                line = line.strip()
                                if line:
                                    try:
                                        parts = line.split()
                                        if len(parts) >= 5:
                                            class_id = int(parts[0])
                                            x_center = float(parts[1])
                                            y_center = float(parts[2])
                                            bbox_width = float(parts[3])
                                            bbox_height = float(parts[4])
                                            
                                            # Convertir de formato YOLO normalizado a píxeles
                                            x1 = int((x_center - bbox_width/2) * width)
                                            y1 = int((y_center - bbox_height/2) * height)
                                            x2 = int((x_center + bbox_width/2) * width)
                                            y2 = int((y_center + bbox_height/2) * height)
                                            
                                            annotations.append({
                                                'class_id': class_id,
                                                'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
                                                'x_center': x_center, 'y_center': y_center,
                                                'width': bbox_width, 'height': bbox_height
                                            })
                                    except (ValueError, IndexError) as e:
                                        print(f"Error procesando línea {line_num} en {label_filename}: {e}")
                                        continue
                    
                    total_labels += len(annotations)
                    
                    images_data.append({
                        'name': filename,
                        'labels': len(annotations),
                        'annotations': annotations,
                        'width': width,
                        'height': height
                    })
        
        # Aplicar paginación si se especifica
        images_to_return = images_data
        if limit is not None and limit > 0:
            end_index = offset + limit
            images_to_return = images_data[offset:end_index]
        
        return {
            "success": True,
            "session_name": session_name,
            "total_images": len(images_data),
            "total_labels": total_labels,
            "returned_images": len(images_to_return),
            "offset": offset,
            "has_more": limit is not None and limit > 0 and offset + limit < len(images_data),
            "images": images_to_return
        }
        
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}

@app.post("/api/session/{session_name}/create")
async def create_session_api(
    session_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crear nueva sesión para el usuario"""
    try:
        # Verificar que el nombre de sesión sea válido
        if not session_name or session_name.strip() == '':
            return {"success": False, "message": "Nombre de sesión inválido"}
        
        # Limpiar nombre de sesión
        safe_session_name = "".join(c for c in session_name if c.isalnum() or c in ('_', '-')).strip()
        if not safe_session_name:
            return {"success": False, "message": "Nombre de sesión contiene caracteres inválidos"}
        
        # Verificar si la sesión ya existe para este usuario
        existing_session = db.query(UserSession).filter(
            UserSession.user_id == current_user.id,
            UserSession.session_name == safe_session_name
        ).first()
        
        if existing_session:
            return {"success": False, "message": "Ya tienes una sesión con este nombre"}
        
        # Crear estructura de sesión
        session_path = create_session_structure(safe_session_name, current_user.id, db)
        
        return {
            "success": True, 
            "message": f"Sesión '{safe_session_name}' creada exitosamente",
            "session_name": safe_session_name
        }
        
    except Exception as e:
        return {"success": False, "message": f"Error al crear sesión: {str(e)}"}

@app.post("/api/upload")
async def upload_image(
    session: str = Form(...),
    canvas_width: int = Form(640),
    canvas_height: int = Form(640),
    x: int = Form(0),
    y: int = Form(0),
    change_bg: bool = Form(True),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Subir imagen a sesión del usuario"""
    try:
        # Verificar acceso a la sesión
        if not verify_session_access(current_user, session, db):
            return {"success": False, "message": "No tienes acceso a esta sesión"}
        
        # Leer archivo
        image_bytes = await file.read()
        
        # Crear imagen con canvas
        canvas_image = create_canvas_with_image(
            image_bytes, (canvas_width, canvas_height), x, y, change_bg
        )
        
        # Generar nombre único de archivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_filename = f"{session}_{timestamp}_{file.filename}"
        
        # Guardar imagen
        session_path = os.path.join("annotations", session)
        image_path = os.path.join(session_path, "images", image_filename)
        
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        
        canvas_image.save(image_path)
        
        # Convertir a base64 para vista previa
        preview_b64 = image_to_base64(canvas_image)
        
        return {
            "success": True,
            "filename": image_filename,
            "preview": preview_b64,
            "message": f"Imagen subida a sesión '{session}'"
        }
        
    except Exception as e:
        return {"success": False, "message": f"Error al subir imagen: {str(e)}"}

@app.post("/api/save_annotations")
async def save_annotations(
    session: str = Form(...),
    filename: str = Form(...),
    annotations: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Guardar anotaciones de una imagen"""
    try:
        # Verificar acceso a la sesión
        if not verify_session_access(current_user, session, db):
            return {"success": False, "message": "No tienes acceso a esta sesión"}
        
        # Procesar anotaciones JSON
        try:
            annotations_data = json.loads(annotations)
        except json.JSONDecodeError:
            return {"success": False, "message": "Formato de anotaciones inválido"}
        
        # Preparar contenido del archivo de etiquetas
        label_content = []
        for ann in annotations_data:
            if all(key in ann for key in ['class_id', 'x_center', 'y_center', 'width', 'height']):
                label_line = f"{ann['class_id']} {ann['x_center']} {ann['y_center']} {ann['width']} {ann['height']}"
                label_content.append(label_line)
        
        # Guardar archivo de etiquetas
        session_path = os.path.join("annotations", session)
        label_filename = os.path.splitext(filename)[0] + '.txt'
        label_path = os.path.join(session_path, "labels", label_filename)
        
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(label_path), exist_ok=True)
        
        with open(label_path, 'w') as f:
            f.write('\n'.join(label_content))
        
        return {
            "success": True,
            "message": f"Anotaciones guardadas para {filename}",
            "annotations_count": len(label_content)
        }
        
    except Exception as e:
        return {"success": False, "message": f"Error al guardar anotaciones: {str(e)}"}

@app.post("/api/augment")
async def augment_dataset_api(
    background_tasks: BackgroundTasks,
    session: str = Form(...),
    variants: list = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Aumentar dataset en background - requiere autenticación"""
    try:
        # Verificar acceso a la sesión
        if not verify_session_access(current_user, session, db):
            return {"success": False, "message": "No tienes acceso a esta sesión"}
        
        session_path = os.path.join("annotations", session)
        
        if not os.path.exists(session_path):
            return {"success": False, "message": f"Sesión '{session}' no encontrada"}
        
        # Verificar que la sesión tenga imágenes
        images_path = os.path.join(session_path, "images")
        if not os.path.exists(images_path) or not os.listdir(images_path):
            return {"success": False, "message": f"No hay imágenes en la sesión '{session}'"}
        
        # Usar variantes especificadas o todas si no se especifican
        selected_variants = variants if variants else list(AVAILABLE_VARIANTS.keys())
        
        # Verificar que las variantes sean válidas
        invalid_variants = [v for v in selected_variants if v not in AVAILABLE_VARIANTS]
        if invalid_variants:
            return {"success": False, "message": f"Variantes inválidas: {invalid_variants}"}
        
        # Ejecutar augmentación en background con variantes seleccionadas
        background_tasks.add_task(augment_session, session, selected_variants)
        
        return {
            "success": True,
            "message": f"Aumentación iniciada para sesión '{session}' con {len(selected_variants)} variantes",
            "session": session,
            "selected_variants": selected_variants,
            "available_variants": AVAILABLE_VARIANTS
        }
        
    except Exception as e:
        return {"success": False, "message": f"Error al iniciar augmentación: {str(e)}"}

@app.get("/api/augment/progress/{session}")
async def get_augment_progress(
    session: str,
    current_user: User = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Obtener progreso de augmentación"""
    try:
        # Verificar acceso a la sesión solo si hay usuario autenticado
        if current_user and not verify_session_access(current_user, session, db):
            return {"success": False, "message": "No tienes acceso a esta sesión"}
        
        progress_file = f"temp/progress_{session}.json"
        
        if not os.path.exists(progress_file):
            return {
                "success": False,
                "message": "No hay proceso de augmentación activo"
            }
        
        with open(progress_file, 'r') as f:
            progress_data = json.load(f)
        
        return {
            "success": True,
            **progress_data  # Expandir las propiedades directamente
        }
        
    except Exception as e:
        return {"success": False, "message": f"Error al obtener progreso: {str(e)}"}

@app.get("/api/stats/{session}")
async def get_session_stats_api(
    session: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener estadísticas de una sesión"""
    try:
        # Verificar acceso a la sesión
        if not verify_session_access(current_user, session, db):
            return {"success": False, "message": "No tienes acceso a esta sesión"}
        
        stats = get_session_stats(session)
        return {
            "success": True,
            "session": session,
            "stats": stats
        }
        
    except Exception as e:
        return {"success": False, "message": f"Error al obtener estadísticas: {str(e)}"}

@app.get("/api/download/{session}")
async def download_session(
    session: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Descargar sesión como archivo ZIP"""
    try:
        # Verificar acceso a la sesión
        if not verify_session_access(current_user, session, db):
            raise HTTPException(status_code=403, detail="No tienes acceso a esta sesión")
        
        session_path = os.path.join("annotations", session)
        
        if not os.path.exists(session_path):
            raise HTTPException(status_code=404, detail=f"Sesión '{session}' no encontrada")
        
        # Crear archivo ZIP temporal
        zip_filename = f"{session}_dataset.zip"
        zip_path = os.path.join("temp", zip_filename)
        
        os.makedirs("temp", exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for root, dirs, files in os.walk(session_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, session_path)
                    zipf.write(file_path, arcname)
        
        return FileResponse(
            path=zip_path,
            media_type='application/zip',
            filename=zip_filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al descargar: {str(e)}")

@app.delete("/api/session/{session_name}")
async def delete_session_api(
    session_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Eliminar sesión del usuario"""
    try:
        # Verificar acceso a la sesión
        if not verify_session_access(current_user, session_name, db):
            return {"success": False, "message": "No tienes acceso a esta sesión"}
        
        # Eliminar entrada de base de datos
        user_session = db.query(UserSession).filter(
            UserSession.user_id == current_user.id,
            UserSession.session_name == session_name
        ).first()
        
        if user_session:
            db.delete(user_session)
            db.commit()
        
        # Eliminar archivos físicos
        session_path = os.path.join("annotations", session_name)
        if os.path.exists(session_path):
            shutil.rmtree(session_path)
        
        return {
            "success": True,
            "message": f"Sesión '{session_name}' eliminada exitosamente"
        }
        
    except Exception as e:
        return {"success": False, "message": f"Error al eliminar sesión: {str(e)}"}

# ============================================================================
# ADMIN ENDPOINTS
# ============================================================================
@app.get("/api/admin/users")
async def list_all_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Listar todos los usuarios (solo admins)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    users = db.query(User).all()
    return {
        "success": True,
        "users": [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_admin": user.is_admin,
                "created_at": user.created_at.isoformat() if user.created_at else None
            }
            for user in users
        ]
    }

@app.get("/api/admin/sessions")
async def list_all_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Listar todas las sesiones del sistema (solo admins)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    sessions = db.query(UserSession).all()
    return {
        "success": True,
        "sessions": [
            {
                "session_name": session.session_name,
                "user_id": session.user_id,
                "created_at": session.created_at.isoformat() if session.created_at else None,
                "is_active": session.is_active
            }
            for session in sessions
        ]
    }

# ============================================================================
# ENDPOINT PARA SERVIR IMÁGENES DE SESIONES
# ============================================================================
@app.get("/image/{session_name}/{image_name}")
async def serve_session_image(
    session_name: str, 
    image_name: str,
    current_user: User = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Servir imágenes de las sesiones con control de acceso"""
    try:
        # Por ahora, permitir acceso a todas las imágenes para debugging
        # TODO: Restaurar control de acceso después de resolver el problema
        # if current_user and not verify_session_access(current_user, session_name, db):
        #     raise HTTPException(status_code=403, detail="No access to this session")
        
        image_path = os.path.join("annotations", session_name, "images", image_name)
        print(f"🔍 Buscando imagen en: {image_path}")  # Debug
        print(f"🔍 Existe archivo: {os.path.exists(image_path)}")  # Debug
        
        if os.path.exists(image_path):
            print(f"✅ Sirviendo imagen: {image_path}")  # Debug
            return FileResponse(image_path)
        else:
            # Crear imagen placeholder SVG si no existe
            svg_content = f"""
            <svg width="300" height="200" xmlns="http://www.w3.org/2000/svg">
                <rect width="300" height="200" fill="#f8f9fa" stroke="#dee2e6"/>
                <text x="150" y="90" text-anchor="middle" fill="#6c757d" font-family="Arial" font-size="14">
                    📷 Imagen no encontrada
                </text>
                <text x="150" y="110" text-anchor="middle" fill="#adb5bd" font-family="Arial" font-size="12">
                    {image_name}
                </text>
                <text x="150" y="130" text-anchor="middle" fill="#adb5bd" font-family="Arial" font-size="10">
                    Sesión: {session_name}
                </text>
            </svg>
            """
            return HTMLResponse(content=svg_content, media_type="image/svg+xml")
    except HTTPException:
        raise
    except Exception as e:
        # SVG de error
        svg_error = f"""
        <svg width="300" height="200" xmlns="http://www.w3.org/2000/svg">
            <rect width="300" height="200" fill="#f8d7da" stroke="#f5c6cb"/>
            <text x="150" y="100" text-anchor="middle" fill="#721c24" font-family="Arial" font-size="12">
                ❌ Error: {str(e)[:30]}
            </text>
        </svg>
        """
        return HTMLResponse(content=svg_error, media_type="image/svg+xml")

if __name__ == "__main__":
    print("🚀 Iniciando YOLO Image Annotator con JWT Auth")
    print("📍 Abre tu navegador en: http://localhost:8002")
    print("🔐 Primera cuenta registrada será ADMIN")
    uvicorn.run("app_auth:app", host="127.0.0.1", port=8002, reload=False)

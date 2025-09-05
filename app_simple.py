from fastapi import FastAPI, File, UploadFile, Form, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
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

# Crear aplicación FastAPI
app = FastAPI(title="YOLO Multi-Class Annotator & Visualizer")

# Configurar templates y archivos estáticos
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Crear carpetas necesarias
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)
os.makedirs("annotations", exist_ok=True)
os.makedirs("temp", exist_ok=True)

# Funciones auxiliares
def create_session_structure(session_name):
    session_path = f"annotations/{session_name}"
    os.makedirs(f"{session_path}/images", exist_ok=True)
    os.makedirs(f"{session_path}/labels", exist_ok=True)
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

# ============================================================================
# ENDPOINT PRINCIPAL - Página de inicio con herramientas
# ============================================================================
@app.get("/", response_class=HTMLResponse)
async def main(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# ============================================================================
# ENDPOINT DE AUGMENTACIÓN - Funcional
# ============================================================================
@app.get("/real-sessions", response_class=HTMLResponse)
async def real_sessions_page(request: Request):
    try:
        sessions_dir = "annotations"
        sessions = []
        
        if os.path.exists(sessions_dir):
            for session_name in os.listdir(sessions_dir):
                session_path = os.path.join(sessions_dir, session_name)
                if os.path.isdir(session_path):
                    images_path = os.path.join(session_path, "images")
                    labels_path = os.path.join(session_path, "labels")
                    
                    image_count = 0
                    label_count = 0
                    
                    if os.path.exists(images_path):
                        image_count = len([f for f in os.listdir(images_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
                    
                    if os.path.exists(labels_path):
                        label_count = len([f for f in os.listdir(labels_path) if f.lower().endswith('.txt')])
                    
                    sessions.append({
                        'name': session_name,
                        'images': image_count,
                        'labels': label_count
                    })
        
        sessions_html = ""
        if sessions:
            for session in sessions:
                sessions_html += f"""
                <div class="session-card" data-session="{session['name']}">
                    <div class="session-info">
                        <h3>📁 {session['name']}</h3>
                        <p>🖼️ Imágenes: {session['images']} | 🏷️ Labels: {session['labels']}</p>
                    </div>
                    <div class="session-actions">
                        <button onclick="openAugmentationModal('{session['name']}')" class="augment-btn">
                            🔄 Augmentar Dataset
                        </button>
                    </div>
                </div>
                """
        else:
            sessions_html = """
            <div style="grid-column: 1 / -1; text-align: center; padding: 40px;">
                <h3>📂 No hay sesiones disponibles</h3>
                <p>Crea una sesión primero subiendo imágenes a la carpeta <code>annotations/tu_sesion/images/</code></p>
            </div>
            """
        
        variants_options = ""
        for key, variant in AVAILABLE_VARIANTS.items():
            variants_options += f"""
            <label class="variant-option">
                <input type="checkbox" name="variants" value="{key}">
                <span class="variant-info">
                    <strong>{variant['icon']} {variant['name']}</strong>
                    <small>{variant['description']}</small>
                </span>
            </label>
            """

        html_content = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <title>Augmentación de Dataset - YOLO Annotator</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 20px;
                    box-shadow: 0 20px 40px rgba(0,0,0,0.2);
                    padding: 40px;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 40px;
                }}
                .header h1 {{
                    color: #333;
                    font-size: 2.5em;
                    margin-bottom: 10px;
                }}
                .header p {{
                    color: #666;
                    font-size: 1.1em;
                }}
                .sessions-panel {{
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                    gap: 20px;
                    margin-bottom: 40px;
                }}
                .session-card {{
                    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                    color: white;
                    padding: 25px;
                    border-radius: 15px;
                    transition: all 0.3s ease;
                }}
                .session-card:hover {{
                    transform: translateY(-5px);
                    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                }}
                .session-info h3 {{
                    margin: 0 0 10px 0;
                    font-size: 1.3em;
                }}
                .session-info p {{
                    margin: 0 0 15px 0;
                    opacity: 0.9;
                }}
                .augment-btn {{
                    background: rgba(255,255,255,0.2);
                    color: white;
                    border: 2px solid rgba(255,255,255,0.3);
                    padding: 10px 20px;
                    border-radius: 10px;
                    cursor: pointer;
                    font-weight: bold;
                    transition: all 0.3s ease;
                    width: 100%;
                }}
                .augment-btn:hover {{
                    background: rgba(255,255,255,0.3);
                    border-color: rgba(255,255,255,0.5);
                }}
                
                /* Modal Styles */
                .modal {{
                    display: none;
                    position: fixed;
                    z-index: 1000;
                    left: 0;
                    top: 0;
                    width: 100%;
                    height: 100%;
                    background-color: rgba(0,0,0,0.8);
                    animation: fadeIn 0.3s;
                }}
                .modal-content {{
                    background-color: #fefefe;
                    margin: 5% auto;
                    padding: 0;
                    border-radius: 20px;
                    width: 90%;
                    max-width: 600px;
                    max-height: 80vh;
                    overflow-y: auto;
                    position: relative;
                    animation: slideIn 0.3s;
                }}
                @keyframes fadeIn {{
                    from {{ opacity: 0; }}
                    to {{ opacity: 1; }}
                }}
                @keyframes slideIn {{
                    from {{ transform: translateY(-50px); opacity: 0; }}
                    to {{ transform: translateY(0); opacity: 1; }}
                }}
                .modal-header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 25px;
                    border-radius: 20px 20px 0 0;
                    text-align: center;
                }}
                .modal-body {{
                    padding: 30px;
                }}
                .close {{
                    position: absolute;
                    top: 15px;
                    right: 20px;
                    color: white;
                    font-size: 28px;
                    font-weight: bold;
                    cursor: pointer;
                    z-index: 1001;
                }}
                .close:hover {{
                    opacity: 0.7;
                }}
                .variant-option {{
                    display: block;
                    background: #f8f9fa;
                    margin: 10px 0;
                    padding: 15px;
                    border-radius: 10px;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    border: 2px solid transparent;
                }}
                .variant-option:hover {{
                    background: #e9ecef;
                    border-color: #007bff;
                }}
                .variant-option input[type="checkbox"] {{
                    margin-right: 12px;
                    transform: scale(1.2);
                }}
                .variant-info strong {{
                    display: block;
                    color: #333;
                    margin-bottom: 5px;
                }}
                .variant-info small {{
                    color: #666;
                    font-size: 0.9em;
                }}
                .execute-btn {{
                    background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
                    color: white;
                    border: none;
                    padding: 15px 30px;
                    border-radius: 10px;
                    font-size: 16px;
                    font-weight: bold;
                    cursor: pointer;
                    width: 100%;
                    margin-top: 20px;
                    transition: all 0.3s ease;
                }}
                .execute-btn:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 5px 15px rgba(40, 167, 69, 0.4);
                }}
                .execute-btn:disabled {{
                    background: #6c757d;
                    cursor: not-allowed;
                    transform: none;
                    box-shadow: none;
                }}
                .progress-container {{
                    display: none;
                    margin-top: 20px;
                }}
                .progress-bar {{
                    width: 100%;
                    height: 20px;
                    background: #e9ecef;
                    border-radius: 10px;
                    overflow: hidden;
                }}
                .progress-fill {{
                    height: 100%;
                    background: linear-gradient(90deg, #28a745, #20c997);
                    width: 0%;
                    transition: width 0.3s ease;
                }}
                .progress-text {{
                    text-align: center;
                    margin-top: 10px;
                    font-weight: bold;
                    color: #333;
                }}
                .back-btn {{
                    background: #6c757d;
                    color: white;
                    padding: 10px 20px;
                    border: none;
                    border-radius: 10px;
                    text-decoration: none;
                    display: inline-block;
                    margin-bottom: 20px;
                    transition: all 0.3s ease;
                }}
                .back-btn:hover {{
                    background: #5a6268;
                    transform: translateY(-2px);
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔄 Augmentación de Dataset</h1>
                    <p>Multiplica tu dataset aplicando transformaciones automáticas</p>
                    <a href="/" class="back-btn">← Volver al inicio</a>
                </div>
                
                <div class="sessions-panel">
                    {sessions_html}
                </div>
            </div>
            
            <!-- Modal de Augmentación -->
            <div id="augmentationModal" class="modal">
                <div class="modal-content">
                    <div class="modal-header">
                        <span class="close">&times;</span>
                        <h2>🔄 Configurar Augmentación</h2>
                        <p id="sessionTitle">Sesión: </p>
                    </div>
                    <div class="modal-body">
                        <h3>Selecciona las variantes a aplicar:</h3>
                        <form id="augmentationForm">
                            {variants_options}
                            <button type="button" onclick="executeAugmentation()" class="execute-btn" id="executeBtn">
                                🚀 Ejecutar Augmentación
                            </button>
                        </form>
                        
                        <div class="progress-container" id="progressContainer">
                            <div class="progress-bar">
                                <div class="progress-fill" id="progressFill"></div>
                            </div>
                            <div class="progress-text" id="progressText">Iniciando...</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <script>
                let currentSession = null;
                let augmentationInProgress = false;
                
                function openAugmentationModal(sessionName) {{
                    currentSession = sessionName;
                    document.getElementById('sessionTitle').textContent = 'Sesión: ' + sessionName;
                    document.getElementById('augmentationModal').style.display = 'block';
                    document.body.style.overflow = 'hidden';
                }}
                
                function closeModal() {{
                    document.getElementById('augmentationModal').style.display = 'none';
                    document.body.style.overflow = 'auto';
                    resetForm();
                }}
                
                function resetForm() {{
                    document.getElementById('augmentationForm').reset();
                    document.getElementById('progressContainer').style.display = 'none';
                    document.getElementById('executeBtn').disabled = false;
                    document.getElementById('executeBtn').textContent = '🚀 Ejecutar Augmentación';
                    document.getElementById('progressFill').style.width = '0%';
                    augmentationInProgress = false;
                }}
                
                async function executeAugmentation() {{
                    if (augmentationInProgress) return;
                    
                    const selectedVariants = Array.from(document.querySelectorAll('input[name="variants"]:checked'))
                        .map(cb => cb.value);
                    
                    if (selectedVariants.length === 0) {{
                        alert('⚠️ Selecciona al menos una variante para continuar');
                        return;
                    }}
                    
                    augmentationInProgress = true;
                    document.getElementById('executeBtn').disabled = true;
                    document.getElementById('executeBtn').textContent = '🔄 Procesando...';
                    document.getElementById('progressContainer').style.display = 'block';
                    
                    try {{
                        // Iniciar augmentación
                        const response = await fetch(`/api/session/${{currentSession}}/augmentation/start`, {{
                            method: 'POST',
                            headers: {{
                                'Content-Type': 'application/json',
                            }},
                            body: JSON.stringify({{
                                variants: selectedVariants
                            }})
                        }});
                        
                        const result = await response.json();
                        
                        if (result.success) {{
                            // Monitorear progreso
                            monitorProgress();
                        }} else {{
                            throw new Error(result.message || 'Error desconocido');
                        }}
                        
                    }} catch (error) {{
                        alert('❌ Error: ' + error.message);
                        resetForm();
                    }}
                }}
                
                async function monitorProgress() {{
                    try {{
                        const response = await fetch(`/api/session/${{currentSession}}/augmentation/progress`);
                        const progress = await response.json();
                        
                        if (progress.success) {{
                            const percent = Math.round((progress.current / progress.total) * 100);
                            document.getElementById('progressFill').style.width = percent + '%';
                            document.getElementById('progressText').textContent = 
                                `Procesando: ${{progress.current}}/${{progress.total}} imágenes (${{percent}}%)`;
                            
                            if (progress.completed) {{
                                document.getElementById('progressText').textContent = 
                                    `✅ ¡Completado! ${{progress.total}} imágenes procesadas`;
                                document.getElementById('executeBtn').textContent = '✅ Augmentación Completada';
                                
                                setTimeout(() => {{
                                    alert('🎉 ¡Augmentación completada con éxito!\\n\\n📊 Revisa tu sesión para ver las nuevas imágenes generadas.');
                                    closeModal();
                                }}, 1000);
                            }} else {{
                                setTimeout(monitorProgress, 1000);
                            }}
                        }}
                    }} catch (error) {{
                        console.error('Error monitoring progress:', error);
                        setTimeout(monitorProgress, 2000);
                    }}
                }}
                
                // Event listeners
                document.querySelector('.close').onclick = closeModal;
                
                window.onclick = function(event) {{
                    const modal = document.getElementById('augmentationModal');
                    if (event.target == modal) {{
                        closeModal();
                    }}
                }};
            </script>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
    
    except Exception as e:
        return HTMLResponse(content=f"<h1>Error</h1><p>Error cargando sesiones: {str(e)}</p>")

# ============================================================================
# OTROS ENDPOINTS NECESARIOS
# ============================================================================
@app.get("/sessions", response_class=HTMLResponse) 
async def sessions_page(request: Request):
    """Página de gestión de sesiones"""
    try:
        sessions_dir = "annotations"
        sessions = []
        
        if os.path.exists(sessions_dir):
            for session_name in os.listdir(sessions_dir):
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
            "sessions": sessions
        })
        
    except Exception as e:
        return HTMLResponse(content=f"<h1>Error</h1><p>Error: {str(e)}</p><a href='/'>← Volver</a>")

@app.get("/annotator", response_class=HTMLResponse)
async def annotator_page(request: Request):
    """Anotador clásico para crear datasets"""
    return templates.TemplateResponse("annotator.html", {"request": request})

@app.get("/visualizer", response_class=HTMLResponse)
async def visualizer_page(request: Request, session: str = None):
    """Visualizador de datasets con anotaciones"""
    try:
        sessions_dir = "annotations"
        sessions = []
        
        if os.path.exists(sessions_dir):
            for session_name in os.listdir(sessions_dir):
                session_path = os.path.join(sessions_dir, session_name)
                if os.path.isdir(session_path):
                    sessions.append(session_name)
        
        sessions_options = ""
        for s in sessions:
            selected = "selected" if s == session else ""
            sessions_options += f'<option value="{s}" {selected}>{s}</option>'
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <title>Visualizador - YOLO Annotator</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                }}
                .container {{
                    max-width: 1400px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 20px;
                    box-shadow: 0 20px 40px rgba(0,0,0,0.2);
                    padding: 40px;
                }}
                .header {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 30px;
                }}
                .controls {{
                    display: flex;
                    gap: 15px;
                    align-items: center;
                    margin-bottom: 30px;
                    padding: 20px;
                    background: #f8f9fa;
                    border-radius: 10px;
                }}
                .controls select, .controls button {{
                    padding: 10px 15px;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    font-size: 14px;
                }}
                .controls button {{
                    background: #007bff;
                    color: white;
                    border: none;
                    cursor: pointer;
                }}
                .gallery {{
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                    gap: 20px;
                }}
                .image-card {{
                    border: 2px solid #ddd;
                    border-radius: 10px;
                    overflow: hidden;
                    background: white;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                    transition: all 0.3s ease;
                }}
                .image-card:hover {{
                    transform: translateY(-5px);
                    box-shadow: 0 8px 16px rgba(0,0,0,0.2);
                }}
                .image-container {{
                    position: relative;
                    width: 100%;
                    height: 250px;
                    overflow: hidden;
                }}
                .image-container img {{
                    width: 100%;
                    height: 100%;
                    object-fit: cover;
                }}
                .image-info {{
                    padding: 15px;
                }}
                .image-info h4 {{
                    margin: 0 0 10px 0;
                    color: #333;
                    font-size: 14px;
                }}
                .image-info p {{
                    margin: 5px 0;
                    font-size: 13px;
                    color: #666;
                }}
                .no-session {{
                    text-align: center;
                    padding: 60px;
                    color: #666;
                }}
                .back-btn {{
                    background: #6c757d;
                    color: white;
                    padding: 10px 20px;
                    border: none;
                    border-radius: 10px;
                    text-decoration: none;
                }}
                .loading {{
                    text-align: center;
                    padding: 40px;
                    color: #666;
                }}
                .stats {{
                    display: flex;
                    gap: 20px;
                    margin-bottom: 20px;
                }}
                .stat-card {{
                    background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
                    color: white;
                    padding: 15px;
                    border-radius: 10px;
                    text-align: center;
                    flex: 1;
                }}
                .stat-number {{
                    font-size: 24px;
                    font-weight: bold;
                    display: block;
                }}
                .stat-label {{
                    font-size: 12px;
                    opacity: 0.9;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>👁️ Visualizador de Datasets</h1>
                    <a href="/" class="back-btn">← Volver al inicio</a>
                </div>
                
                <div class="controls">
                    <label>📂 Seleccionar sesión:</label>
                    <select id="sessionSelect" onchange="loadSession()">
                        <option value="">Selecciona una sesión...</option>
                        {sessions_options}
                    </select>
                    <button onclick="refreshData()">🔄 Actualizar</button>
                </div>
                
                <div id="statsContainer" style="display: none;">
                    <div class="stats">
                        <div class="stat-card">
                            <span class="stat-number" id="totalImages">0</span>
                            <span class="stat-label">Imágenes</span>
                        </div>
                        <div class="stat-card">
                            <span class="stat-number" id="totalLabels">0</span>
                            <span class="stat-label">Labels</span>
                        </div>
                        <div class="stat-card">
                            <span class="stat-number" id="avgLabels">0</span>
                            <span class="stat-label">Promedio Labels/Imagen</span>
                        </div>
                    </div>
                </div>
                
                <div id="contentContainer">
                    {'''
                    <div class="no-session">
                        <h3>📂 Selecciona una sesión para visualizar</h3>
                        <p>Usa el selector de arriba para elegir qué dataset explorar</p>
                    </div>
                    ''' if not session else '''
                    <div class="loading">
                        <h3>⏳ Cargando imágenes...</h3>
                        <p>Procesando dataset de ''' + session + '''</p>
                    </div>
                    '''}
                </div>
            </div>
            
            <script>
                let currentSession = "{session or ''}";
                
                function loadSession() {{
                    const select = document.getElementById('sessionSelect');
                    const selectedSession = select.value;
                    
                    if (selectedSession) {{
                        window.location.href = '/visualizer?session=' + selectedSession;
                    }} else {{
                        window.location.href = '/visualizer';
                    }}
                }}
                
                function refreshData() {{
                    if (currentSession) {{
                        loadSession();
                    }}
                }}
                
                // Cargar datos si hay sesión seleccionada
                if (currentSession) {{
                    loadSessionData(currentSession);
                }}
                
                async function loadSessionData(sessionName) {{
                    try {{
                        const response = await fetch('/api/session/' + sessionName + '/visualize');
                        const data = await response.json();
                        
                        if (data.success) {{
                            displaySessionData(data);
                        }} else {{
                            showError('Error cargando sesión: ' + data.message);
                        }}
                    }} catch (error) {{
                        showError('Error de conexión: ' + error.message);
                    }}
                }}
                
                function displaySessionData(data) {{
                    // Mostrar estadísticas
                    document.getElementById('totalImages').textContent = data.total_images;
                    document.getElementById('totalLabels').textContent = data.total_labels;
                    const avgLabels = data.total_images > 0 ? (data.total_labels / data.total_images).toFixed(1) : '0.0';
                    document.getElementById('avgLabels').textContent = avgLabels;
                    document.getElementById('statsContainer').style.display = 'block';
                    
                    // Mostrar galería de imágenes
                    let galleryHTML = '<div class="gallery">';
                    
                    if (data.images && data.images.length > 0) {{
                        data.images.forEach((image, index) => {{
                            galleryHTML += `
                                <div class="image-card">
                                    <div class="image-container">
                                        <canvas id="canvas_${{index}}" width="${{image.width}}" height="${{image.height}}" 
                                                style="max-width: 100%; height: 250px; object-fit: contain; border: 1px solid #ddd;">
                                        </canvas>
                                    </div>
                                    <div class="image-info">
                                        <h4>📄 ${{image.name}}</h4>
                                        <p>🏷️ Labels: ${{image.labels || 0}}</p>
                                        <p>📏 Resolución: ${{image.width}}x${{image.height}}</p>
                                    </div>
                                </div>
                            `;
                        }});
                    }} else {{
                        galleryHTML += '<div style="grid-column: 1 / -1; text-align: center; padding: 40px;"><h3>📷 No hay imágenes en esta sesión</h3></div>';
                    }}
                    
                    galleryHTML += '</div>';
                    document.getElementById('contentContainer').innerHTML = galleryHTML;
                    
                    // Dibujar las imágenes y las anotaciones en los canvas
                    if (data.images && data.images.length > 0) {{
                        data.images.forEach((image, index) => {{
                            drawImageWithAnnotations(image, index);
                        }});
                    }}
                }}
                
                function drawImageWithAnnotations(imageData, index) {{
                    const canvas = document.getElementById(`canvas_${{index}}`);
                    if (!canvas) return;
                    
                    const ctx = canvas.getContext('2d');
                    const img = new Image();
                    
                    img.onload = function() {{
                        // Dibujar la imagen
                        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                        
                        // Dibujar las anotaciones
                        if (imageData.annotations && imageData.annotations.length > 0) {{
                            imageData.annotations.forEach(annotation => {{
                                drawBoundingBox(ctx, annotation, canvas.width, canvas.height, imageData.width, imageData.height);
                            }});
                        }}
                    }};
                    
                    img.onerror = function() {{
                        // Si la imagen no se puede cargar, mostrar placeholder
                        ctx.fillStyle = '#f8f9fa';
                        ctx.fillRect(0, 0, canvas.width, canvas.height);
                        ctx.fillStyle = '#6c757d';
                        ctx.font = '16px Arial';
                        ctx.textAlign = 'center';
                        ctx.fillText('Imagen no encontrada', canvas.width/2, canvas.height/2);
                    }};
                    
                    img.src = `/image/${{currentSession}}/${{imageData.name}}`;
                }}
                
                function drawBoundingBox(ctx, annotation, canvasWidth, canvasHeight, imageWidth, imageHeight) {{
                    // Escalar las coordenadas al tamaño del canvas
                    const scaleX = canvasWidth / imageWidth;
                    const scaleY = canvasHeight / imageHeight;
                    
                    const x1 = annotation.x1 * scaleX;
                    const y1 = annotation.y1 * scaleY;
                    const x2 = annotation.x2 * scaleX;
                    const y2 = annotation.y2 * scaleY;
                    
                    // Colores por clase
                    const colors = ['#ff0000', '#00ff00', '#0000ff', '#ffff00', '#ff00ff', '#00ffff'];
                    const color = colors[annotation.class_id % colors.length] || '#ff0000';
                    
                    // Dibujar el rectángulo
                    ctx.strokeStyle = color;
                    ctx.lineWidth = 2;
                    ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);
                    
                    // Dibujar la etiqueta de clase
                    ctx.fillStyle = color;
                    ctx.font = '12px Arial';
                    ctx.fillText(`Clase ${{annotation.class_id}}`, x1, y1 - 5);
                    
                    // Fondo semi-transparente para el texto
                    ctx.globalAlpha = 0.7;
                    ctx.fillRect(x1, y1 - 20, 60, 15);
                    ctx.globalAlpha = 1.0;
                    ctx.fillStyle = 'white';
                    ctx.fillText(`Clase ${{annotation.class_id}}`, x1 + 2, y1 - 8);
                }}
                
                function showError(message) {{
                    document.getElementById('contentContainer').innerHTML = `
                        <div class="no-session">
                            <h3>❌ Error</h3>
                            <p>${{message}}</p>
                            <button onclick="refreshData()" class="controls button">🔄 Intentar de nuevo</button>
                        </div>
                    `;
                }}
            </script>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        return HTMLResponse(content=f"<h1>Error</h1><p>Error en visualizador: {str(e)}</p><a href='/'>← Volver</a>")

# ============================================================================
# API ENDPOINTS PARA AUGMENTACIÓN Y VISUALIZACIÓN
# ============================================================================
@app.get("/api/session/{session_name}/visualize")
async def get_session_visualize_data(session_name: str, limit: int = None, offset: int = 0):
    """API endpoint para obtener datos de visualización de una sesión con paginación opcional"""
    try:
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
        
        # Aplicar paginación si se especifica (por defecto mostrar todas)
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

@app.post("/api/session/{session_name}/augmentation/start")
async def start_augmentation(session_name: str, request: Request, background_tasks: BackgroundTasks):
    try:
        body = await request.json()
        selected_variants = body.get("variants", [])
        
        if not selected_variants:
            return {"success": False, "message": "No variants selected"}
        
        # Ejecutar augmentación en background
        background_tasks.add_task(augment_session, session_name, selected_variants)
        
        return {"success": True, "message": "Augmentation started"}
        
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}

@app.get("/api/session/{session_name}/augmentation/progress")
async def get_augmentation_progress(session_name: str):
    try:
        # Buscar archivo de progreso temporal
        progress_file = f"temp/progress_{session_name}.json"
        
        if os.path.exists(progress_file):
            with open(progress_file, 'r') as f:
                progress_data = json.load(f)
            return {"success": True, **progress_data}
        else:
            # Si no hay archivo de progreso, asumir que no hay augmentación en curso
            return {
                "success": True, 
                "current": 0, 
                "total": 0, 
                "completed": True,
                "message": "No hay augmentación en progreso"
            }
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}

# ============================================================================
# ENDPOINT DE INFORMACIÓN  
# ============================================================================
@app.get("/api/session/{session_name}/augmentation/info")
async def get_augmentation_info(session_name: str):
    try:
        return {
            "session_name": session_name,
            "available_variants": AVAILABLE_VARIANTS,
            "success": True
        }
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}

# ============================================================================
# ENDPOINT PARA LISTAR SESIONES (API)
# ============================================================================
@app.get("/api/sessions")
async def list_sessions_api():
    """Listar todas las sesiones disponibles para el anotador clásico"""
    try:
        sessions_dir = "annotations"
        sessions = []
        
        if os.path.exists(sessions_dir):
            for session_name in os.listdir(sessions_dir):
                session_path = os.path.join(sessions_dir, session_name)
                if os.path.isdir(session_path):
                    images_path = os.path.join(session_path, "images")
                    labels_path = os.path.join(session_path, "labels")
                    
                    images_count = 0
                    labels_count = 0
                    
                    if os.path.exists(images_path):
                        images_count = len([f for f in os.listdir(images_path) 
                                          if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'))])
                    
                    if os.path.exists(labels_path):
                        labels_count = len([f for f in os.listdir(labels_path) 
                                          if f.lower().endswith('.txt')])
                    
                    sessions.append({
                        'name': session_name,
                        'images_count': images_count,
                        'labels_count': labels_count
                    })
        
        # Ordenar sesiones por nombre
        sessions.sort(key=lambda x: x['name'])
        
        return {
            "success": True,
            "sessions": sessions
        }
    except Exception as e:
        return {"success": False, "message": f"Error al listar sesiones: {str(e)}"}

# ============================================================================
# ENDPOINT PARA SERVIR IMÁGENES DE SESIONES
# ============================================================================
@app.get("/image/{session_name}/{image_name}")
async def serve_session_image(session_name: str, image_name: str):
    """Servir imágenes de las sesiones desde annotations/session/images/"""
    try:
        image_path = os.path.join("annotations", session_name, "images", image_name)
        if os.path.exists(image_path):
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

# Endpoints para el anotador clásico

@app.post("/generate")
async def generate_image(
    image: UploadFile = File(...),
    size: int = Form(320),
    x: int = Form(0),
    y: int = Form(0),
    random_bg: bool = Form(True),
    session_name: str = Form("default")
):
    try:
        print(f"DEBUG: Recibiendo datos - size:{size}, x:{x}, y:{y}, random_bg:{random_bg}, session:{session_name}")
        print(f"DEBUG: Archivo imagen - filename:{image.filename}, content_type:{image.content_type}")
        
        # Crear estructura de sesión
        create_session_structure(session_name)
        
        # Leer imagen subida
        image_bytes = await image.read()
        print(f"DEBUG: Imagen leída - {len(image_bytes)} bytes")
        
        # Crear canvas con imagen
        canvas_size = (size, size)
        result_image = create_canvas_with_image(image_bytes, canvas_size, x, y, random_bg)
        
        # Convertir a base64
        base64_image = image_to_base64(result_image)
        
        return {"image": base64_image, "session_name": session_name}
        
    except Exception as e:
        print(f"ERROR en generate_image: {str(e)}")
        return {"error": str(e)}

@app.post("/save_annotations")
async def save_annotations(
    annotations: str = Form(...),
    filename: str = Form(...),
    session_name: str = Form(...),
    image_width: int = Form(...),
    image_height: int = Form(...),
    image_data: str = Form(...)
):
    """Guardar anotaciones en formato YOLO normalizado e imagen con sesiones"""
    try:
        annotations_data = json.loads(annotations)
        
        # Crear estructura de sesión
        session_path = create_session_structure(session_name)
        
        # Encontrar el siguiente número disponible en la sesión
        def get_next_filename(base_filename, session_path):
            # Verificar si existe el archivo base
            image_path = f"{session_path}/images/{base_filename}.jpg"
            labels_path = f"{session_path}/labels/{base_filename}.txt"
            
            if not os.path.exists(image_path) and not os.path.exists(labels_path):
                return base_filename
            
            # Buscar el siguiente número disponible
            counter = 1
            while True:
                numbered_filename = f"{base_filename}_{counter}"
                image_path = f"{session_path}/images/{numbered_filename}.jpg"
                labels_path = f"{session_path}/labels/{numbered_filename}.txt"
                
                if not os.path.exists(image_path) and not os.path.exists(labels_path):
                    return numbered_filename
                counter += 1
        
        # Obtener nombre único
        unique_filename = get_next_filename(filename, session_path)
        
        # Guardar en formato YOLO (.txt) - NORMALIZADO
        yolo_content = []
        for annotation in annotations_data:
            class_id = annotation['class_id']
            x = annotation['x']
            y = annotation['y']
            width = annotation['width']
            height = annotation['height']
            
            # Convertir a formato YOLO normalizado
            # x_center, y_center normalizados (0-1)
            x_center = (x + width/2) / image_width
            y_center = (y + height/2) / image_height
            norm_width = width / image_width
            norm_height = height / image_height
            
            # Formato: class_id x_center y_center width height
            yolo_line = f"{class_id} {x_center:.6f} {y_center:.6f} {norm_width:.6f} {norm_height:.6f}"
            yolo_content.append(yolo_line)
        
        # Guardar archivo de anotaciones YOLO en /labels/
        labels_file = f"{session_path}/labels/{unique_filename}.txt"
        with open(labels_file, "w") as f:
            f.write("\n".join(yolo_content))
            
        # Guardar imagen en /images/
        # Decodificar imagen base64
        if image_data.startswith('data:image'):
            image_data = image_data.split(',')[1]
        
        image_bytes = base64.b64decode(image_data)
        image_file = f"{session_path}/images/{unique_filename}.jpg"
        
        # Guardar imagen como JPG
        with open(image_file, "wb") as f:
            f.write(image_bytes)
            
        return {
            "success": True, 
            "message": f"Dataset guardado en sesión '{session_name}' como '{unique_filename}': {len(annotations_data)} objetos",
            "files": {
                "image": image_file,
                "labels": labels_file
            },
            "session_name": session_name,
            "original_name": filename,
            "unique_name": unique_filename,
            "yolo_format": yolo_content
        }
        
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}

@app.get("/download_session/{session_name}")
async def download_session(session_name: str):
    """Descargar sesión completa como archivo ZIP con imágenes y etiquetas en una sola carpeta"""
    try:
        session_path = f"annotations/{session_name}"
        
        if not os.path.exists(session_path):
            return {"success": False, "message": f"Sesión '{session_name}' no encontrada"}
        
        images_path = f"{session_path}/images"
        labels_path = f"{session_path}/labels"
        
        # Verificar que existan las carpetas
        if not os.path.exists(images_path) and not os.path.exists(labels_path):
            return {"success": False, "message": f"No hay archivos en la sesión '{session_name}'"}
        
        # Crear archivo ZIP temporal
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"dataset_{session_name}_{timestamp}.zip"
        zip_path = f"temp/{zip_filename}"
        
        # Crear ZIP con estructura de carpetas images/ y labels/
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Agregar todas las imágenes en la carpeta images/
            if os.path.exists(images_path):
                for file in os.listdir(images_path):
                    if file.endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp')):
                        file_path = os.path.join(images_path, file)
                        zipf.write(file_path, f"images/{file}")  # Mantener carpeta images/
            
            # Agregar todas las etiquetas en la carpeta labels/
            if os.path.exists(labels_path):
                for file in os.listdir(labels_path):
                    if file.endswith('.txt'):
                        file_path = os.path.join(labels_path, file)
                        zipf.write(file_path, f"labels/{file}")  # Mantener carpeta labels/
        
        # Devolver el archivo ZIP
        return FileResponse(
            path=zip_path,
            filename=zip_filename,
            media_type='application/zip'
        )
        
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}

@app.delete("/delete_session/{session_name}")
async def delete_session(session_name: str):
    """Eliminar sesión completa con todas sus imágenes y etiquetas"""
    try:
        session_path = f"annotations/{session_name}"
        
        if not os.path.exists(session_path):
            return {"success": False, "message": f"Sesión '{session_name}' no encontrada"}
        
        # Verificar que no sea la sesión por defecto para evitar problemas
        if session_name == "default":
            return {"success": False, "message": "No se puede eliminar la sesión por defecto"}
        
        # Eliminar toda la carpeta de la sesión
        shutil.rmtree(session_path)
        
        return {
            "success": True, 
            "message": f"Sesión '{session_name}' eliminada correctamente"
        }
        
    except Exception as e:
        return {"success": False, "message": f"Error al eliminar sesión: {str(e)}"}

if __name__ == "__main__":
    print("🚀 Iniciando YOLO Image Annotator")
    print("📍 Abre tu navegador en: http://localhost:8001")
    uvicorn.run("app_simple:app", host="127.0.0.1", port=8001, reload=True)

# ============================================================================
# EJECUTAR SERVIDOR
# ============================================================================
# Configuración comentada - se usa la de arriba
# if __name__ == "__main__":
#     print("🚀 Iniciando YOLO Image Annotator")
#     print("📍 Abre tu navegador en: http://localhost:8001")
#     uvicorn.run(app, host="0.0.0.0", port=8001)

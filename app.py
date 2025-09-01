from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from PIL import Image, ImageDraw
import numpy as np
import random
import io
import base64
import os
import json
import zipfile
from datetime import datetime
import shutil

app = FastAPI(title="YOLO Multi-Class Annotator & Visualizer")

# Crear carpeta para archivos estáticos si no existe
os.makedirs("static", exist_ok=True)
os.makedirs("annotations", exist_ok=True)

# Función para crear estructura de sesión
def create_session_structure(session_name):
    session_path = f"annotations/{session_name}"
    os.makedirs(f"{session_path}/images", exist_ok=True)
    os.makedirs(f"{session_path}/labels", exist_ok=True)
    return session_path

# Clases predefinidas con colores
CLASSES = {
    0: {"name": "objeto 1", "color": "#ff0000"},
    1: {"name": "objeto 2", "color": "#00ff00"},
    2: {"name": "objeto 3", "color": "#0000ff"},
    3: {"name": "objeto 4", "color": "#ffff00"},
    4: {"name": "objeto 5", "color": "#ff00ff"},
    5: {"name": "objeto 6", "color": "#00ffff"}
}

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

def hex_to_rgb(hex_color):
    """Convertir color hex a RGB"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def draw_yolo_annotations(image_path, labels_path, max_display_size=800):
    """Dibujar anotaciones YOLO sobre la imagen con redimensionado automático"""
    try:
        # Cargar imagen (soporta WebP y otros formatos)
        image = Image.open(image_path)
        
        # Convertir a RGB si es necesario (para WebP con transparencia, etc.)
        if image.mode in ('RGBA', 'LA', 'P'):
            # Crear fondo blanco para transparencias
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
            image = background
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Obtener dimensiones originales
        original_width, original_height = image.size
        
        # Redimensionar para display si es muy grande (manteniendo proporciones para visualización)
        display_image = image.copy()
        scale_factor = 1.0
        
        if original_width > max_display_size or original_height > max_display_size:
            scale_factor = min(max_display_size / original_width, max_display_size / original_height)
            new_width = int(original_width * scale_factor)
            new_height = int(original_height * scale_factor)
            display_image = display_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        draw = ImageDraw.Draw(display_image)
        
        # Obtener dimensiones de la imagen de display
        display_width, display_height = display_image.size
        
        annotations = []
        
        # Leer archivo de etiquetas si existe
        if os.path.exists(labels_path):
            with open(labels_path, 'r') as f:
                for line_num, line in enumerate(f.readlines(), 1):
                    line = line.strip()
                    if line:
                        try:
                            parts = line.split()
                            if len(parts) == 5:
                                class_id = int(parts[0])
                                x_center = float(parts[1])
                                y_center = float(parts[2])
                                width = float(parts[3])
                                height = float(parts[4])
                                
                                # Convertir de coordenadas YOLO a píxeles usando las dimensiones de display
                                x_center_px = x_center * display_width
                                y_center_px = y_center * display_height
                                width_px = width * display_width
                                height_px = height * display_height
                                
                                # Calcular coordenadas del rectángulo
                                x1 = int(x_center_px - width_px / 2)
                                y1 = int(y_center_px - height_px / 2)
                                x2 = int(x_center_px + width_px / 2)
                                y2 = int(y_center_px + height_px / 2)
                                
                                # Obtener color de la clase
                                color = CLASSES.get(class_id, {"color": "#ffffff", "name": f"clase_{class_id}"})
                                rgb_color = hex_to_rgb(color["color"])
                                
                                # Dibujar rectángulo (más grueso para imágenes grandes)
                                line_width = max(2, int(3 * scale_factor))
                                draw.rectangle([x1, y1, x2, y2], outline=rgb_color, width=line_width)
                                
                                # Dibujar etiqueta
                                label_text = f"{color['name']} ({class_id})"
                                font_size = max(12, int(14 * scale_factor))
                                text_width = len(label_text) * int(font_size * 0.6)
                                text_height = int(font_size * 1.2)
                                
                                draw.rectangle([x1, y1-text_height, x1+text_width, y1], fill=rgb_color)
                                draw.text((x1+2, y1-text_height+2), label_text, fill=(255, 255, 255))
                                
                                # Guardar información de la anotación
                                annotations.append({
                                    "class_id": class_id,
                                    "class_name": color['name'],
                                    "bbox": [x1, y1, x2, y2],
                                    "yolo_coords": [x_center, y_center, width, height],
                                    "color": color["color"],
                                    "original_size": [original_width, original_height],
                                    "display_scale": scale_factor
                                })
                                
                        except (ValueError, IndexError) as e:
                            print(f"Error en línea {line_num} de {labels_path}: {e}")
                            continue
        
        return display_image, annotations
    
    except Exception as e:
        print(f"Error procesando {image_path}: {e}")
        return None, []

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

@app.get("/", response_class=HTMLResponse)
async def main():
    return """
<!DOCTYPE html>
<html>
<head>
    <title>YOLO Multi-Class Annotator</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .controls {
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
            flex-wrap: wrap;
            align-items: center;
        }
        .control-group {
            display: flex;
            flex-direction: column;
            gap: 5px;
        }
        label {
            font-weight: bold;
            color: #333;
        }
        input, select, button {
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
        }
        button {
            background: #007bff;
            color: white;
            border: none;
            cursor: pointer;
            transition: background 0.3s;
        }
        button:hover {
            background: #0056b3;
        }
        .save-btn {
            background: #28a745;
        }
        .save-btn:hover {
            background: #218838;
        }
        .clear-btn {
            background: #dc3545;
        }
        .clear-btn:hover {
            background: #c82333;
        }
        #imageCanvas {
            border: 2px solid #333;
            cursor: crosshair;
            max-width: 100%;
            margin: 20px 0;
        }
        .selection-box {
            position: absolute;
            border: 2px solid;
            background: rgba(255, 0, 0, 0.1);
            pointer-events: none;
            font-size: 12px;
            font-weight: bold;
            color: white;
            padding: 2px 5px;
        }
        .class-selector {
            display: flex;
            gap: 10px;
            margin: 20px 0;
            flex-wrap: wrap;
        }
        .class-btn {
            padding: 10px 15px;
            border: 2px solid;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s;
        }
        .class-btn.active {
            transform: scale(1.1);
            box-shadow: 0 0 10px rgba(0,0,0,0.3);
        }
        .annotations-panel {
            background: #e9ecef;
            padding: 15px;
            border-radius: 5px;
            margin-top: 20px;
            max-height: 400px;
            overflow-y: auto;
        }
        .annotation-item {
            background: white;
            padding: 10px;
            margin: 5px 0;
            border-radius: 5px;
            border-left: 4px solid;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .delete-annotation {
            background: #dc3545;
            color: white;
            border: none;
            padding: 5px 10px;
            border-radius: 3px;
            cursor: pointer;
            font-size: 12px;
        }
        .title {
            color: #333;
            margin-bottom: 20px;
            text-align: center;
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 15px;
        }
        .help-btn {
            background: #17a2b8;
            color: white;
            border: none;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            font-size: 16px;
            cursor: pointer;
            transition: all 0.3s;
        }
        .help-btn:hover {
            background: #138496;
            transform: scale(1.1);
        }
        
        /* Modal Styles */
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.5);
            animation: fadeIn 0.3s;
        }
        .modal-content {
            background-color: #fefefe;
            margin: 5% auto;
            padding: 0;
            border-radius: 10px;
            width: 80%;
            max-width: 700px;
            max-height: 80vh;
            overflow-y: auto;
            position: relative;
            animation: slideIn 0.3s;
        }
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        @keyframes slideIn {
            from { transform: translateY(-50px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
        .close {
            position: absolute;
            top: 15px;
            right: 20px;
            color: #aaa;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
            z-index: 1001;
        }
        .close:hover,
        .close:focus {
            color: #000;
            text-decoration: none;
        }
        .instructions-content {
            padding: 40px 30px 30px 30px;
        }
        .instructions-content h2 {
            color: #333;
            margin-bottom: 25px;
            text-align: center;
            border-bottom: 2px solid #007bff;
            padding-bottom: 10px;
        }
        .instructions-content h3 {
            color: #495057;
            margin-top: 25px;
            margin-bottom: 15px;
        }
        .instructions-content ol {
            padding-left: 20px;
        }
        .instructions-content ol li {
            margin-bottom: 10px;
            line-height: 1.5;
        }
        .instructions-content ul {
            padding-left: 20px;
        }
        .instructions-content ul li {
            margin-bottom: 8px;
            line-height: 1.5;
        }
        .classes-preview {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            margin: 15px 0;
        }
        .class-item {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 8px 12px;
            background: #f8f9fa;
            border-radius: 5px;
            font-size: 14px;
        }
        .class-item span {
            width: 20px;
            height: 20px;
            border-radius: 3px;
            display: inline-block;
        }
        .instructions-content kbd {
            background: #f8f9fa;
            border: 1px solid #ddd;
            border-radius: 3px;
            padding: 2px 6px;
            font-family: monospace;
            font-size: 12px;
            color: #333;
        }
        .two-column {
            display: grid;
            grid-template-columns: 1fr 350px;
            gap: 20px;
        }
        .sessions-panel {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            border: 1px solid #dee2e6;
        }
        .session-item {
            background: white;
            padding: 10px;
            margin: 5px 0;
            border-radius: 5px;
            border: 1px solid #ddd;
            cursor: pointer;
            transition: all 0.3s;
        }
        .session-item:hover {
            background: #e9ecef;
            border-color: #007bff;
        }
        .session-item.selected {
            background: #007bff;
            color: white;
            border-color: #007bff;
        }
        .session-stats {
            font-size: 12px;
            color: #666;
        }
        .download-btn {
            background: #17a2b8;
            font-size: 12px;
            padding: 5px 10px;
            margin-top: 5px;
            margin-right: 5px;
        }
        .download-btn:hover {
            background: #138496;
        }
        .visualize-btn {
            background: #28a745;
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 12px;
            padding: 5px 10px;
            margin-top: 5px;
            cursor: pointer;
        }
        .visualize-btn:hover {
            background: #218838;
        }
        .delete-btn {
            background: #dc3545;
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 12px;
            padding: 5px 10px;
            margin-top: 5px;
            margin-right: 5px;
            cursor: pointer;
        }
        .delete-btn:hover {
            background: #c82333;
        }
        .session-actions {
            margin-top: 10px;
            display: flex;
            gap: 5px;
            flex-wrap: wrap;
        }
        .main-panel {
            min-width: 0;
        }
        .side-panel {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="title">YOLO Multi-Class Annotator
            <button id="helpBtn" class="help-btn" title="Ver instrucciones">❓</button>
        </h1>
        
        <!-- Modal de Instrucciones -->
        <div id="instructionsModal" class="modal">
            <div class="modal-content">
                <span class="close">&times;</span>
                <h2>📚 Instrucciones de Uso</h2>
                <div class="instructions-content">
                    <h3>🚀 Pasos para anotar:</h3>
                    <ol>
                        <li><strong>📤 Sube tu imagen</strong> - Formatos soportados: JPG, PNG, WebP, GIF, BMP</li>
                        <li><strong>⚙️ Configura parámetros</strong> - Tamaño del canvas, posición, fondo</li>
                        <li><strong>🖼️ Genera el canvas</strong> - Click en "Generar" para crear el lienzo</li>
                        <li><strong>🎯 Selecciona una clase</strong> - Elige el tipo de objeto a anotar</li>
                        <li><strong>🖱️ Arrastra para anotar</strong> - Crea bounding boxes sobre los objetos</li>
                        <li><strong>🔄 Repite para múltiples objetos</strong> - Anota todos los objetos de la imagen</li>
                        <li><strong>💾 Guarda las anotaciones</strong> - Formato YOLO estándar para entrenamiento</li>
                    </ol>
                    
                    <h3>🎨 Clases disponibles:</h3>
                    <div class="classes-preview">
                        <div class="class-item"><span style="background: #ff0000;"></span> Objeto 1</div>
                        <div class="class-item"><span style="background: #00ff00;"></span> Objeto 2</div>
                        <div class="class-item"><span style="background: #0000ff;"></span> Objeto 3</div>
                        <div class="class-item"><span style="background: #ffff00;"></span> Objeto 4</div>
                        <div class="class-item"><span style="background: #ff00ff;"></span> Objeto 5</div>
                        <div class="class-item"><span style="background: #00ffff;"></span> Objeto 6</div>
                    </div>
                    
                    <h3>⚡ Atajos de teclado:</h3>
                    <ul>
                        <li><kbd>1-6</kbd> - Seleccionar clase rápida</li>
                        <li><kbd>Escape</kbd> - Cancelar anotación actual</li>
                        <li><kbd>Delete</kbd> - Eliminar anotación seleccionada</li>
                    </ul>
                    
                    <h3>📁 Gestión de sesiones:</h3>
                    <ul>
                        <li><strong>💾 Descargar:</strong> Obtén un ZIP con formato YOLO listo para entrenar</li>
                        <li><strong>👁️ Visualizar:</strong> Ve todas las anotaciones en galería</li>
                        <li><strong>🗑️ Eliminar:</strong> Borra sesión completa (irreversible)</li>
                    </ul>
                </div>
            </div>
        </div>

        <div class="two-column">
            <div class="main-panel">
                <form id="imageForm" enctype="multipart/form-data">
                    <div class="controls">
                        <div class="control-group">
                            <label for="sessionName">Sesión:</label>
                            <input type="text" id="sessionName" name="sessionName" placeholder="Nombre de sesión" value="default">
                            <button type="button" id="refreshSessions">🔄</button>
                        </div>
                        
                        <div class="control-group">
                            <label for="imageFile">Imagen:</label>
                            <input type="file" id="imageFile" name="imageFile" accept="image/*" required>
                            <small style="color: #666; font-size: 12px;">
                                Soporta: JPG, PNG, WebP, GIF, BMP (se redimensiona automáticamente)
                            </small>
                        </div>
                        
                        <div class="control-group">
                            <label for="size">Tamaño:</label>
                            <select id="size" name="size">
                                <option value="320">320x320</option>
                                <option value="640">640x640</option>
                            </select>
                        </div>
                        
                        <div class="control-group">
                            <label for="xPos">Pos X:</label>
                            <input type="range" id="xPos" name="xPos" min="0" max="640" value="0">
                            <span id="xValue">0</span>
                        </div>
                        
                        <div class="control-group">
                            <label for="yPos">Pos Y:</label>
                            <input type="range" id="yPos" name="yPos" min="0" max="640" value="0">
                            <span id="yValue">0</span>
                        </div>
                        
                        <div class="control-group">
                            <label>
                                <input type="checkbox" id="randomBg" name="randomBg" checked> Fondo aleatorio
                            </label>
                        </div>
                        
                        <button type="submit">🖼️ Generar</button>
                    </div>
                </form>

                <div class="class-selector">
                    <h3>Selecciona la clase:</h3>
                    <div id="classButtons"></div>
                </div>

                <div style="position: relative;">
                    <canvas id="imageCanvas" style="display: none;"></canvas>
                </div>
            </div>

            <div class="side-panel">
                <h3>📝 Anotaciones</h3>
                <div>
                    <input type="text" id="filename" placeholder="nombre_archivo" style="width: 100%; margin-bottom: 10px;">
                    <button onclick="saveAnnotations()" class="save-btn" style="width: 100%; margin-bottom: 10px;">💾 Guardar Anotaciones</button>
                    <button onclick="clearAnnotations()" class="clear-btn" style="width: 100%;">🗑️ Limpiar Todo</button>
                </div>
                
                <div class="annotations-panel" id="annotationsList">
                    <p>Sin anotaciones aún</p>
                </div>
            </div>
            
            <div class="sessions-panel">
                <h3>📁 Sesiones</h3>
                <div id="sessionsList">
                    <p>Cargando sesiones...</p>
                </div>
                <button onclick="refreshSessions()" class="save-btn" style="width: 100%; margin-top: 10px;">🔄 Actualizar</button>
            </div>
        </div>
    </div>

    <script>
        let isSelecting = false;
        let startX, startY, currentBox;
        let currentClass = 0;
        let annotations = [];
        let annotationCounter = 0;
        let originalImageData = null; // Para guardar la imagen original sin anotaciones
        
        const classes = {
            0: {name: "objeto 1", color: "#ff0000"},
            1: {name: "objeto 2", color: "#00ff00"},
            2: {name: "objeto 3", color: "#0000ff"},
            3: {name: "objeto 4", color: "#ffff00"},
            4: {name: "objeto 5", color: "#ff00ff"},
            5: {name: "objeto 6", color: "#00ffff"}
        };

        // Inicializar botones de clase
        function initializeClassButtons() {
            const container = document.getElementById('classButtons');
            Object.keys(classes).forEach(classId => {
                const btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'class-btn';
                btn.style.backgroundColor = classes[classId].color;
                btn.style.borderColor = classes[classId].color;
                btn.style.color = getContrastColor(classes[classId].color);
                btn.textContent = classes[classId].name;
                btn.onclick = () => selectClass(classId);
                container.appendChild(btn);
            });
            selectClass(0); // Seleccionar primera clase por defecto
        }

        function getContrastColor(hexColor) {
            const r = parseInt(hexColor.substr(1,2), 16);
            const g = parseInt(hexColor.substr(3,2), 16);
            const b = parseInt(hexColor.substr(5,2), 16);
            const brightness = ((r * 299) + (g * 587) + (b * 114)) / 1000;
            return brightness > 128 ? '#000000' : '#ffffff';
        }

        function selectClass(classId) {
            currentClass = parseInt(classId);
            document.querySelectorAll('.class-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.class-btn')[currentClass].classList.add('active');
        }

        // Resto del código JavaScript...
        document.getElementById('xPos').addEventListener('input', function() {
            document.getElementById('xValue').textContent = this.value;
        });
        
        document.getElementById('yPos').addEventListener('input', function() {
            document.getElementById('yValue').textContent = this.value;
        });

        document.getElementById('imageForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData();
            const imageFile = document.getElementById('imageFile').files[0];
            const sessionName = document.getElementById('sessionName').value || 'default';
            
            if (!imageFile) {
                alert('Por favor selecciona una imagen');
                return;
            }
            
            formData.append('image', imageFile);
            formData.append('size', document.getElementById('size').value);
            formData.append('x', document.getElementById('xPos').value);
            formData.append('y', document.getElementById('yPos').value);
            formData.append('random_bg', document.getElementById('randomBg').checked);
            formData.append('session_name', sessionName);
            
            try {
                const response = await fetch('/generate', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                displayImage(result.image);
                clearAnnotations();
                
                // Actualizar sesiones después de generar
                refreshSessions();
            } catch (error) {
                alert('Error al generar la imagen: ' + error.message);
            }
        });

        function displayImage(base64Image) {
            const canvas = document.getElementById('imageCanvas');
            const ctx = canvas.getContext('2d');
            
            const img = new Image();
            img.onload = function() {
                canvas.width = img.width;
                canvas.height = img.height;
                ctx.drawImage(img, 0, 0);
                canvas.style.display = 'block';
                
                // Guardar imagen original sin anotaciones
                originalImageData = canvas.toDataURL('image/jpeg', 0.9);
                
                setupSelection();
            };
            img.src = base64Image;
        }

        function setupSelection() {
            const canvas = document.getElementById('imageCanvas');
            
            canvas.addEventListener('mousedown', function(e) {
                const rect = canvas.getBoundingClientRect();
                startX = e.clientX - rect.left;
                startY = e.clientY - rect.top;
                isSelecting = true;
                
                if (currentBox) {
                    currentBox.remove();
                }
            });
            
            canvas.addEventListener('mousemove', function(e) {
                if (!isSelecting) return;
                
                const rect = canvas.getBoundingClientRect();
                const currentX = e.clientX - rect.left;
                const currentY = e.clientY - rect.top;
                
                if (currentBox) {
                    currentBox.remove();
                }
                
                currentBox = document.createElement('div');
                currentBox.className = 'selection-box';
                
                const left = Math.min(startX, currentX);
                const top = Math.min(startY, currentY);
                const width = Math.abs(currentX - startX);
                const height = Math.abs(currentY - startY);
                
                const classColor = classes[currentClass].color;
                currentBox.style.borderColor = classColor;
                currentBox.style.backgroundColor = classColor + '20';
                currentBox.style.left = (rect.left + left) + 'px';
                currentBox.style.top = (rect.top + top + window.scrollY) + 'px';
                currentBox.style.width = width + 'px';
                currentBox.style.height = height + 'px';
                currentBox.textContent = classes[currentClass].name;
                
                document.body.appendChild(currentBox);
            });
            
            canvas.addEventListener('mouseup', function(e) {
                if (isSelecting && currentBox) {
                    const rect = canvas.getBoundingClientRect();
                    const endX = e.clientX - rect.left;
                    const endY = e.clientY - rect.top;
                    
                    const left = Math.min(startX, endX);
                    const top = Math.min(startY, endY);
                    const width = Math.abs(endX - startX);
                    const height = Math.abs(endY - startY);
                    
                    if (width > 5 && height > 5) {
                        addAnnotation(left, top, width, height, currentClass);
                    }
                    
                    if (currentBox) {
                        currentBox.remove();
                        currentBox = null;
                    }
                }
                isSelecting = false;
            });
        }

        function addAnnotation(x, y, width, height, classId) {
            const annotation = {
                id: annotationCounter++,
                x: Math.round(x),
                y: Math.round(y),
                width: Math.round(width),
                height: Math.round(height),
                class_id: classId,
                class_name: classes[classId].name
            };
            
            annotations.push(annotation);
            updateAnnotationsList();
            redrawCanvas();
        }

        function removeAnnotation(id) {
            annotations = annotations.filter(ann => ann.id !== id);
            updateAnnotationsList();
            redrawCanvas();
        }

        function updateAnnotationsList() {
            const container = document.getElementById('annotationsList');
            if (annotations.length === 0) {
                container.innerHTML = '<p>Sin anotaciones aún</p>';
                return;
            }
            
            container.innerHTML = annotations.map(ann => `
                <div class="annotation-item" style="border-left-color: ${classes[ann.class_id].color}">
                    <div>
                        <strong>${ann.class_name}</strong><br>
                        <small>x:${ann.x}, y:${ann.y}, w:${ann.width}, h:${ann.height}</small>
                    </div>
                    <button class="delete-annotation" onclick="removeAnnotation(${ann.id})">❌</button>
                </div>
            `).join('');
        }

        function redrawCanvas() {
            const canvas = document.getElementById('imageCanvas');
            const ctx = canvas.getContext('2d');
            
            // Redibujar imagen base (asumimos que está en cache del navegador)
            const img = new Image();
            img.onload = function() {
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                ctx.drawImage(img, 0, 0);
                
                // Dibujar todas las anotaciones
                annotations.forEach(ann => {
                    ctx.strokeStyle = classes[ann.class_id].color;
                    ctx.lineWidth = 2;
                    ctx.strokeRect(ann.x, ann.y, ann.width, ann.height);
                    
                    // Etiqueta
                    ctx.fillStyle = classes[ann.class_id].color;
                    ctx.fillRect(ann.x, ann.y - 20, ctx.measureText(ann.class_name).width + 10, 20);
                    ctx.fillStyle = 'white';
                    ctx.font = '14px Arial';
                    ctx.fillText(ann.class_name, ann.x + 5, ann.y - 5);
                });
            };
            img.src = canvas.toDataURL();
        }

        async function saveAnnotations() {
            const filename = document.getElementById('filename').value;
            const sessionName = document.getElementById('sessionName').value || 'default';
            
            if (!filename) {
                alert('Por favor ingresa un nombre para el archivo');
                return;
            }
            
            if (annotations.length === 0) {
                alert('No hay anotaciones para guardar');
                return;
            }
            
            const canvas = document.getElementById('imageCanvas');
            
            if (!originalImageData) {
                alert('No hay imagen original para guardar');
                return;
            }
            
            const formData = new FormData();
            formData.append('annotations', JSON.stringify(annotations));
            formData.append('filename', filename);
            formData.append('session_name', sessionName);
            formData.append('image_width', canvas.width);
            formData.append('image_height', canvas.height);
            formData.append('image_data', originalImageData); // Usar imagen original sin marcas
            
            try {
                const response = await fetch('/save_annotations', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                if (result.success) {
                    alert(`✅ Dataset guardado correctamente!
                    
� Nombre solicitado: "${result.original_name}"
🔢 Nombre único generado: "${result.unique_name}"

📁 Archivos creados:
• Imagen: ${result.files.image}
• Etiquetas: ${result.files.labels}

📊 Objetos anotados: ${annotations.length}

🎯 Formato YOLO guardado:
${result.yolo_format.join('\\n')}

ℹ️  La imagen se guardó SIN las marcas de selección`);
                    
                    // Opcional: limpiar anotaciones después de guardar
                    // clearAnnotations();
                    
                    // Actualizar sesiones después de guardar
                    refreshSessions();
                } else {
                    alert(`❌ Error: ${result.message}`);
                }
            } catch (error) {
                alert('Error al guardar: ' + error.message);
            }
        }

        function clearAnnotations() {
            annotations = [];
            annotationCounter = 0;
            updateAnnotationsList();
            if (document.getElementById('imageCanvas').style.display !== 'none') {
                redrawCanvas();
            }
        }

        // Inicializar al cargar la página
        initializeClassButtons();
        
        // Funciones para manejo de sesiones
        async function refreshSessions() {
            try {
                const response = await fetch('/list_sessions');
                const result = await response.json();
                
                if (result.success) {
                    displaySessions(result.sessions);
                } else {
                    alert(`Error al cargar sesiones: ${result.message}`);
                }
            } catch (error) {
                alert('Error al cargar sesiones: ' + error.message);
            }
        }
        
        function displaySessions(sessions) {
            const sessionsList = document.getElementById('sessionsList');
            
            if (sessions.length === 0) {
                sessionsList.innerHTML = '<p>No hay sesiones disponibles</p>';
                return;
            }
            
            sessionsList.innerHTML = sessions.map(session => `
                <div class="session-item" onclick="selectSession('${session.name}')">
                    <div><strong>${session.name}</strong></div>
                    <div class="session-stats">
                        📷 ${session.images_count} imágenes | 📝 ${session.labels_count} etiquetas
                    </div>
                    <div class="session-actions">
                        <button class="download-btn" onclick="downloadSession('${session.name}'); event.stopPropagation();" title="Descargar sesión">
                            💾 Descargar
                        </button>
                        <button class="visualize-btn" onclick="visualizeSession('${session.name}'); event.stopPropagation();" title="Visualizar sesión">
                            👁️ Visualizar
                        </button>
                        <button class="delete-btn" onclick="deleteSession('${session.name}'); event.stopPropagation();" title="Eliminar sesión">
                            🗑️ Eliminar
                        </button>
                    </div>
                </div>
            `).join('');
        }
        
        function selectSession(sessionName) {
            document.getElementById('sessionName').value = sessionName;
            
            // Destacar sesión seleccionada
            document.querySelectorAll('.session-item').forEach(item => {
                item.classList.remove('selected');
            });
            event.target.closest('.session-item').classList.add('selected');
        }
        
        async function downloadSession(sessionName) {
            try {
                // Crear enlace de descarga temporal
                const downloadLink = document.createElement('a');
                downloadLink.href = `/download_session/${sessionName}`;
                downloadLink.download = `dataset_${sessionName}.zip`;
                
                // Agregar al DOM y hacer click automáticamente
                document.body.appendChild(downloadLink);
                downloadLink.click();
                
                // Remover del DOM
                document.body.removeChild(downloadLink);
                
                alert(`🎉 Descargando dataset '${sessionName}' como archivo ZIP
                
📦 Estructura YOLO estándar:
├── images/ (imágenes .jpg)
└── labels/ (etiquetas .txt)

📁 Archivo: dataset_${sessionName}_YYYYMMDD_HHMMSS.zip
🎯 Formato listo para entrenamiento YOLO`);
                
            } catch (error) {
                alert('Error al descargar sesión: ' + error.message);
            }
        }
        
        function visualizeSession(sessionName) {
            // Guardar sesión actual en localStorage
            localStorage.setItem('currentSession', sessionName);
            
            // Abrir visualizador en nueva pestaña/ventana
            window.open(`/visualizer?session=${sessionName}`, '_top');
        }
        
        async function deleteSession(sessionName) {
            // Confirmar eliminación
            const confirmation = confirm(`⚠️ ¿Estás seguro de que quieres eliminar la sesión "${sessionName}"?

🗑️ Esta acción eliminará permanentemente:
• Todas las imágenes de la sesión
• Todas las etiquetas/anotaciones 
• No se puede deshacer

¿Continuar con la eliminación?`);
            
            if (!confirmation) {
                return;
            }
            
            try {
                const response = await fetch(`/delete_session/${sessionName}`, {
                    method: 'DELETE'
                });
                
                const result = await response.json();
                
                if (result.success) {
                    alert(`✅ Sesión "${sessionName}" eliminada correctamente`);
                    refreshSessions(); // Actualizar lista
                    
                    // Si era la sesión seleccionada, limpiar selección
                    const currentSelected = document.getElementById('sessionName').value;
                    if (currentSelected === sessionName) {
                        document.getElementById('sessionName').value = 'default';
                    }
                } else {
                    alert(`❌ Error al eliminar sesión: ${result.message}`);
                }
            } catch (error) {
                alert('❌ Error de conexión al eliminar sesión: ' + error.message);
            }
        }
        
        // Cargar sesiones al inicializar
        document.addEventListener('DOMContentLoaded', function() {
            refreshSessions();
            initializeModal();
        });
        
        // Inicializar modal de instrucciones
        function initializeModal() {
            const modal = document.getElementById('instructionsModal');
            const helpBtn = document.getElementById('helpBtn');
            const closeBtn = document.querySelector('.close');
            
            // Abrir modal
            helpBtn.addEventListener('click', function() {
                modal.style.display = 'block';
                document.body.style.overflow = 'hidden'; // Prevenir scroll del body
            });
            
            // Cerrar modal con X
            closeBtn.addEventListener('click', function() {
                modal.style.display = 'none';
                document.body.style.overflow = 'auto';
            });
            
            // Cerrar modal clickeando fuera
            window.addEventListener('click', function(event) {
                if (event.target === modal) {
                    modal.style.display = 'none';
                    document.body.style.overflow = 'auto';
                }
            });
            
            // Cerrar con tecla ESC
            document.addEventListener('keydown', function(event) {
                if (event.key === 'Escape' && modal.style.display === 'block') {
                    modal.style.display = 'none';
                    document.body.style.overflow = 'auto';
                }
            });
        }
        
        // Agregar event listener al botón de refresh
        document.getElementById('refreshSessions')?.addEventListener('click', refreshSessions);
    </script>
</body>
</html>
"""

@app.post("/generate")
async def generate_image(
    image: UploadFile = File(...),
    size: int = Form(320),
    x: int = Form(0),
    y: int = Form(0),
    random_bg: bool = Form(True),
    session_name: str = Form("default")
):
    # Crear estructura de sesión
    create_session_structure(session_name)
    
    # Leer imagen subida
    image_bytes = await image.read()
    
    # Crear canvas con imagen
    canvas_size = (size, size)
    result_image = create_canvas_with_image(image_bytes, canvas_size, x, y, random_bg)
    
    # Convertir a base64
    base64_image = image_to_base64(result_image)
    
    return {"image": base64_image, "session_name": session_name}

@app.get("/list_sessions")
async def list_sessions():
    """Listar todas las sesiones disponibles"""
    try:
        sessions = []
        annotations_path = "annotations"
        
        if os.path.exists(annotations_path):
            for item in os.listdir(annotations_path):
                session_path = os.path.join(annotations_path, item)
                if os.path.isdir(session_path):
                    # Contar archivos en la sesión
                    images_count = 0
                    labels_count = 0
                    
                    images_path = os.path.join(session_path, "images")
                    labels_path = os.path.join(session_path, "labels")
                    
                    if os.path.exists(images_path):
                        images_count = len([f for f in os.listdir(images_path) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp'))])
                    
                    if os.path.exists(labels_path):
                        labels_count = len([f for f in os.listdir(labels_path) if f.endswith('.txt')])
                    
                    sessions.append({
                        "name": item,
                        "images_count": images_count,
                        "labels_count": labels_count,
                        "path": session_path
                    })
        
        return {"success": True, "sessions": sessions}
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
        
        # Crear carpeta temporal
        os.makedirs("temp", exist_ok=True)
        
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

@app.get("/visualizer", response_class=HTMLResponse)
async def visualizer_page():
    """Página del visualizador integrado"""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>🎯 Dataset Visualizer</title>
    <meta charset="utf-8">
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
        }
        .nav-buttons {
            margin-bottom: 20px;
            text-align: center;
        }
        .nav-btn {
            background: #007bff;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            margin: 0 10px;
            text-decoration: none;
            display: inline-block;
        }
        .nav-btn:hover {
            background: #0056b3;
        }
        .images-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
        }
        .image-card {
            background: white;
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .image-preview {
            width: 100%;
            max-width: 100%;
            height: auto;
            border-radius: 5px;
            margin-bottom: 10px;
        }
        .image-info {
            font-size: 14px;
            color: #333;
        }
        .annotations-list {
            margin-top: 10px;
            max-height: 150px;
            overflow-y: auto;
        }
        .annotation-item {
            padding: 5px;
            margin: 2px 0;
            border-left: 4px solid;
            background: #f8f9fa;
            border-radius: 3px;
            font-size: 12px;
        }
        .loading {
            text-align: center;
            padding: 40px;
            color: #666;
        }
        .legend {
            background: white;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .legend-title {
            font-weight: bold;
            margin-bottom: 10px;
        }
        .legend-items {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }
        .legend-item {
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 12px;
            color: white;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Dataset Visualizer</h1>
            <p>Visualizar las anotaciones YOLO de la sesión actual</p>
        </div>

        <div class="nav-buttons">
            <a href="/" class="nav-btn">← Volver al Anotador</a>
        </div>
        
        <div class="legend">
            <div class="legend-title">🎨 Leyenda de Clases:</div>
            <div class="legend-items" id="legendItems"></div>
        </div>
        
        <h2 id="sessionTitle">📷 Selecciona una sesión en el anotador principal</h2>
        <div class="images-grid" id="imagesGrid">
            <div class="loading">Usa el anotador principal para seleccionar una sesión a visualizar</div>
        </div>
    </div>

    <script>
        // Obtener parámetro de sesión de la URL
        const urlParams = new URLSearchParams(window.location.search);
        const sessionName = urlParams.get('session') || localStorage.getItem('currentSession');

        function createLegend() {
            const classes = {
                0: {"name": "objeto 1", "color": "#ff0000"},
                1: {"name": "objeto 2", "color": "#00ff00"},
                2: {"name": "objeto 3", "color": "#0000ff"},
                3: {"name": "objeto 4", "color": "#ffff00"},
                4: {"name": "objeto 5", "color": "#ff00ff"},
                5: {"name": "objeto 6", "color": "#00ffff"}
            };
            
            const legendItems = document.getElementById('legendItems');
            legendItems.innerHTML = Object.entries(classes).map(([id, cls]) => `
                <div class="legend-item" style="background-color: ${cls.color}">
                    ${id}: ${cls.name}
                </div>
            `).join('');
        }

        async function loadSessionImages(sessionName) {
            if (!sessionName) return;
            
            document.getElementById('sessionTitle').textContent = `📷 Imágenes de: ${sessionName}`;
            
            try {
                const response = await fetch(`/api/session/${sessionName}/visualize`);
                const data = await response.json();
                
                const grid = document.getElementById('imagesGrid');
                
                if (data.images.length === 0) {
                    grid.innerHTML = '<div class="loading">No hay imágenes en esta sesión</div>';
                    return;
                }
                
                grid.innerHTML = data.images.map(img => `
                    <div class="image-card">
                        <img src="${img.image_data}" alt="${img.filename}" class="image-preview">
                        <div class="image-info">
                            <strong>📄 ${img.filename}</strong><br>
                            ${img.has_labels ? '✅' : '❌'} ${img.annotations.length} anotaciones
                            ${img.annotations.length > 0 && img.annotations[0].original_size ? 
                                `<br>📏 Tamaño original: ${img.annotations[0].original_size[0]}×${img.annotations[0].original_size[1]}px` : ''}
                            ${img.annotations.length > 0 && img.annotations[0].display_scale && img.annotations[0].display_scale < 1 ? 
                                `<br>🔍 Escala: ${Math.round(img.annotations[0].display_scale * 100)}%` : ''}
                        </div>
                        ${img.annotations.length > 0 ? `
                            <div class="annotations-list">
                                ${img.annotations.map(ann => `
                                    <div class="annotation-item" style="border-left-color: ${ann.color}">
                                        ${ann.class_name} (ID: ${ann.class_id})
                                        <br>YOLO: [${ann.yolo_coords.map(c => c.toFixed(3)).join(', ')}]
                                    </div>
                                `).join('')}
                            </div>
                        ` : ''}
                    </div>
                `).join('');
                
            } catch (error) {
                document.getElementById('imagesGrid').innerHTML = 
                    '<div class="loading">Error cargando imágenes: ' + error.message + '</div>';
            }
        }

        // Inicializar
        document.addEventListener('DOMContentLoaded', function() {
            createLegend();
            if (sessionName) {
                loadSessionImages(sessionName);
            }
        });
    </script>
</body>
</html>
"""

@app.get("/api/session/{session_name}/visualize")
async def api_visualize_session(session_name: str):
    """API para visualizar una sesión específica"""
    try:
        session_path = f"annotations/{session_name}"
        if not os.path.exists(session_path):
            return {"error": "Sesión no encontrada", "images": []}

        images_path = f"{session_path}/images"
        labels_path = f"{session_path}/labels"
        
        if not os.path.exists(images_path):
            return {"session_name": session_name, "images": []}

        visualized_images = []
        
        # Obtener todas las imágenes
        for img_file in os.listdir(images_path):
            if img_file.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp')):
                img_path = os.path.join(images_path, img_file)
                
                # Buscar archivo de etiquetas correspondiente
                label_file = os.path.splitext(img_file)[0] + '.txt'
                label_file_path = os.path.join(labels_path, label_file)
                
                # Dibujar anotaciones sobre la imagen
                image_with_annotations, annotations = draw_yolo_annotations(img_path, label_file_path)
                
                if image_with_annotations:
                    # Convertir a base64
                    image_data = image_to_base64(image_with_annotations)
                    
                    visualized_images.append({
                        "filename": img_file,
                        "image_data": image_data,
                        "has_labels": os.path.exists(label_file_path),
                        "annotations": annotations
                    })
        
        return {"session_name": session_name, "images": visualized_images}
        
    except Exception as e:
        return {"error": f"Error: {str(e)}", "images": []}

@app.get("/cleanup_temp")
async def cleanup_temp():
    """Limpiar archivos temporales"""
    try:
        temp_path = "temp"
        if os.path.exists(temp_path):
            for file in os.listdir(temp_path):
                file_path = os.path.join(temp_path, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
        return {"success": True, "message": "Archivos temporales limpiados"}
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}

if __name__ == "__main__":
    print("🚀 Iniciando YOLO Image Annotator")
    print("📍 Abre tu navegador en: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)

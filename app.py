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

app = FastAPI(title="YOLO Multi-Class Annotator")

# Crear carpeta para archivos estáticos si no existe
os.makedirs("static", exist_ok=True)
os.makedirs("annotations", exist_ok=True)
os.makedirs("annotations/images", exist_ok=True)
os.makedirs("annotations/labels", exist_ok=True)

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

def create_canvas_with_image(image_bytes, size, x, y, change_bg=True):
    bg_color = random_color() if change_bg else (200, 200, 200)
    canvas = Image.new('RGB', size, bg_color)
    
    # Cargar imagen subida
    img = Image.open(io.BytesIO(image_bytes))
    img.thumbnail((size[0], size[1]))
    
    # Posicionar imagen
    max_x = size[0] - img.width
    max_y = size[1] - img.height
    x = min(max(0, x), max_x)
    y = min(max(0, y), max_y)
    canvas.paste(img, (x, y))
    
    return canvas

def image_to_base64(pil_image):
    buffer = io.BytesIO()
    pil_image.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

@app.post("/save_annotations")
async def save_annotations(
    annotations: str = Form(...),
    filename: str = Form(...),
    image_width: int = Form(...),
    image_height: int = Form(...),
    image_data: str = Form(...)
):
    """Guardar anotaciones en formato YOLO normalizado e imagen con numeración automática"""
    try:
        annotations_data = json.loads(annotations)
        
        # Encontrar el siguiente número disponible
        def get_next_filename(base_filename):
            # Verificar si existe el archivo base
            image_path = f"annotations/images/{base_filename}.jpg"
            labels_path = f"annotations/labels/{base_filename}.txt"
            
            if not os.path.exists(image_path) and not os.path.exists(labels_path):
                return base_filename
            
            # Buscar el siguiente número disponible
            counter = 1
            while True:
                numbered_filename = f"{base_filename}_{counter}"
                image_path = f"annotations/images/{numbered_filename}.jpg"
                labels_path = f"annotations/labels/{numbered_filename}.txt"
                
                if not os.path.exists(image_path) and not os.path.exists(labels_path):
                    return numbered_filename
                counter += 1
        
        # Obtener nombre único
        unique_filename = get_next_filename(filename)
        
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
        labels_file = f"annotations/labels/{unique_filename}.txt"
        with open(labels_file, "w") as f:
            f.write("\n".join(yolo_content))
            
        # Guardar imagen en /images/
        # Decodificar imagen base64
        if image_data.startswith('data:image'):
            image_data = image_data.split(',')[1]
        
        image_bytes = base64.b64decode(image_data)
        image_file = f"annotations/images/{unique_filename}.jpg"
        
        # Guardar imagen como JPG
        with open(image_file, "wb") as f:
            f.write(image_bytes)
            
        return {
            "success": True, 
            "message": f"Dataset guardado como '{unique_filename}': {len(annotations_data)} objetos",
            "files": {
                "image": image_file,
                "labels": labels_file
            },
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
        }
        .instructions {
            background: #d4edda;
            border: 1px solid #c3e6cb;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .two-column {
            display: grid;
            grid-template-columns: 1fr 300px;
            gap: 20px;
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
        <h1 class="title">🎯 YOLO Multi-Class Annotator</h1>
        
        <div class="instructions">
            <strong>Instrucciones:</strong>
            <ol>
                <li>Sube tu imagen y genera el fondo</li>
                <li>Selecciona una clase de objeto</li>
                <li>Arrastra sobre la imagen para crear una anotación</li>
                <li>Repite para múltiples objetos</li>
                <li>Guarda las anotaciones cuando termines</li>
            </ol>
        </div>

        <div class="two-column">
            <div class="main-panel">
                <form id="imageForm" enctype="multipart/form-data">
                    <div class="controls">
                        <div class="control-group">
                            <label for="imageFile">Imagen:</label>
                            <input type="file" id="imageFile" name="imageFile" accept="image/*" required>
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
            
            if (!imageFile) {
                alert('Por favor selecciona una imagen');
                return;
            }
            
            formData.append('image', imageFile);
            formData.append('size', document.getElementById('size').value);
            formData.append('x', document.getElementById('xPos').value);
            formData.append('y', document.getElementById('yPos').value);
            formData.append('random_bg', document.getElementById('randomBg').checked);
            
            try {
                const response = await fetch('/generate', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                displayImage(result.image);
                clearAnnotations();
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
    random_bg: bool = Form(True)
):
    # Leer imagen subida
    image_bytes = await image.read()
    
    # Crear canvas con imagen
    canvas_size = (size, size)
    result_image = create_canvas_with_image(image_bytes, canvas_size, x, y, random_bg)
    
    # Convertir a base64
    base64_image = image_to_base64(result_image)
    
    return {"image": base64_image}

if __name__ == "__main__":
    print("🚀 Iniciando YOLO Image Annotator")
    print("📍 Abre tu navegador en: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)

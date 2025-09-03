// ===== ANOTADOR YOLO - JAVASCRIPT PRINCIPAL =====

// Variables globales
let currentClass = 0;
let annotations = [];
let annotationCounter = 0;
let isSelecting = false;
let startX, startY;
let currentBox = null;
let originalImageData = null;

// Configuración de clases
const classes = {
    0: {"name": "objeto 1", "color": "#ff0000"},
    1: {"name": "objeto 2", "color": "#00ff00"},
    2: {"name": "objeto 3", "color": "#0000ff"},
    3: {"name": "objeto 4", "color": "#ffff00"},
    4: {"name": "objeto 5", "color": "#ff00ff"},
    5: {"name": "objeto 6", "color": "#00ffff"}
};

// ===== INICIALIZACIÓN =====
document.addEventListener('DOMContentLoaded', function() {
    // initializeModal(); // Modal de ayuda no implementado aún
    initializeClassButtons();
    refreshSessions();
    
    // Event listeners principales
    document.getElementById('imageForm').addEventListener('submit', handleImageUpload);
    document.getElementById('refreshSessions')?.addEventListener('click', refreshSessions);
    
    // Sliders de posición
    const xSlider = document.getElementById('xPos');
    const ySlider = document.getElementById('yPos');
    const xValue = document.getElementById('xValue');
    const yValue = document.getElementById('yValue');
    
    if (xSlider && xValue) {
        xSlider.addEventListener('input', function() {
            xValue.textContent = this.value;
        });
    }
    
    if (ySlider && yValue) {
        ySlider.addEventListener('input', function() {
            yValue.textContent = this.value;
        });
    }
});

// ===== MANEJO DE CLASES =====
function initializeClassButtons() {
    const container = document.getElementById('classButtons');
    if (!container) return;
    
    container.innerHTML = Object.entries(classes).map(([id, cls]) => `
        <button type="button" class="class-btn" data-class="${id}" style="background-color: ${cls.color};">
            ${cls.name}
        </button>
    `).join('');
    
    // Event listeners para botones de clase
    container.querySelectorAll('.class-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            currentClass = parseInt(this.dataset.class);
            
            // Actualizar botones activos
            container.querySelectorAll('.class-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
        });
    });
    
    // Seleccionar primera clase por defecto
    container.querySelector('.class-btn')?.classList.add('active');
}

// ===== MANEJO DE IMÁGENES =====
async function handleImageUpload(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    
    try {
        const response = await fetch('/generate', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.image) {
            displayImage(result.image);
            clearAnnotations();
        }
    } catch (error) {
        alert('Error al procesar imagen: ' + error.message);
    }
}

function displayImage(base64Image) {
    const canvas = document.getElementById('imageCanvas');
    const ctx = canvas.getContext('2d');
    
    const img = new Image();
    img.onload = function() {
        canvas.width = img.width;
        canvas.height = img.height;
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(img, 0, 0);
        
        // Guardar imagen original para exportación
        originalImageData = base64Image;
        
        // Mostrar controles de anotación
        document.getElementById('annotationControls').style.display = 'block';
        canvas.style.display = 'block';
        
        // Configurar eventos de canvas
        setupCanvasEvents();
    };
    img.src = base64Image;
}

// ===== EVENTOS DE CANVAS PARA ANOTACIONES =====
function setupCanvasEvents() {
    const canvas = document.getElementById('imageCanvas');
    
    // Limpiar eventos previos
    canvas.removeEventListener('mousedown', handleMouseDown);
    canvas.removeEventListener('mousemove', handleMouseMove);
    canvas.removeEventListener('mouseup', handleMouseUp);
    
    canvas.addEventListener('mousedown', handleMouseDown);
    canvas.addEventListener('mousemove', handleMouseMove);
    canvas.addEventListener('mouseup', handleMouseUp);
}

function handleMouseDown(e) {
    if (currentClass === undefined) return;
    
    const rect = e.target.getBoundingClientRect();
    startX = e.clientX - rect.left;
    startY = e.clientY - rect.top;
    isSelecting = true;
    
    // Crear caja de selección visual
    currentBox = document.createElement('div');
    currentBox.style.position = 'absolute';
    currentBox.style.border = '2px solid ' + classes[currentClass].color;
    currentBox.style.backgroundColor = classes[currentClass].color + '20';
    currentBox.style.pointerEvents = 'none';
    currentBox.style.fontSize = '12px';
    currentBox.style.color = classes[currentClass].color;
    currentBox.style.padding = '2px';
    currentBox.style.zIndex = '1000';
}

function handleMouseMove(e) {
    if (!isSelecting || !currentBox) return;
    
    const rect = e.target.getBoundingClientRect();
    const currentX = e.clientX - rect.left;
    const currentY = e.clientY - rect.top;
    
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
}

function handleMouseUp(e) {
    if (!isSelecting || !currentBox) return;
    
    const rect = e.target.getBoundingClientRect();
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
    
    isSelecting = false;
}

// ===== GESTIÓN DE ANOTACIONES =====
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
    if (!container) return;
    
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
    if (!canvas || !originalImageData) return;
    
    const ctx = canvas.getContext('2d');
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
    img.src = originalImageData;
}

function clearAnnotations() {
    annotations = [];
    annotationCounter = 0;
    updateAnnotationsList();
    if (document.getElementById('imageCanvas').style.display !== 'none') {
        redrawCanvas();
    }
}

// ===== GUARDAR ANOTACIONES =====
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
    formData.append('image_data', originalImageData);
    
    try {
        const response = await fetch('/save_annotations', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        if (result.success) {
            alert(`✅ Dataset guardado correctamente!
            
📄 Nombre solicitado: "${result.original_name}"
🔢 Nombre único generado: "${result.unique_name}"

📁 Archivos creados:
• Imagen: ${result.files.image}
• Etiquetas: ${result.files.labels}

📊 Objetos anotados: ${annotations.length}

🎯 Formato YOLO guardado:
${result.yolo_format.join('\\n')}

ℹ️  La imagen se guardó SIN las marcas de selección`);
            
            refreshSessions();
        } else {
            alert(`❌ Error: ${result.message}`);
        }
    } catch (error) {
        alert('Error al guardar: ' + error.message);
    }
}

// ===== GESTIÓN DE SESIONES =====
async function refreshSessions() {
    try {
        const response = await fetch('/api/sessions');
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
    if (!sessionsList) return;
    
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
    const sessionInput = document.getElementById('sessionName');
    if (sessionInput) {
        sessionInput.value = sessionName;
    }
    
    // Destacar sesión seleccionada
    document.querySelectorAll('.session-item').forEach(item => {
        item.classList.remove('selected');
    });
    event.target.closest('.session-item').classList.add('selected');
}

async function downloadSession(sessionName) {
    try {
        const downloadLink = document.createElement('a');
        downloadLink.href = `/download_session/${sessionName}`;
        downloadLink.download = `dataset_${sessionName}.zip`;
        
        document.body.appendChild(downloadLink);
        downloadLink.click();
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
    localStorage.setItem('currentSession', sessionName);
    window.open(`/visualizer?session=${sessionName}`, '_blank');
}

async function deleteSession(sessionName) {
    const confirmation = confirm(`⚠️ ¿Estás seguro de que quieres eliminar la sesión "${sessionName}"?

🗑️ Esta acción eliminará permanentemente:
• Todas las imágenes de la sesión
• Todas las etiquetas/anotaciones 
• No se puede deshacer

¿Continuar con la eliminación?`);
    
    if (!confirmation) return;
    
    try {
        const response = await fetch(`/delete_session/${sessionName}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(`✅ Sesión "${sessionName}" eliminada correctamente`);
            refreshSessions();
            
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

// ===== FUNCIONES GLOBALES (expuestas para HTML onclick) =====
window.removeAnnotation = removeAnnotation;
window.saveAnnotations = saveAnnotations;
window.clearAnnotations = clearAnnotations;
window.selectSession = selectSession;
window.downloadSession = downloadSession;
window.visualizeSession = visualizeSession;
window.deleteSession = deleteSession;

// JavaScript específico para el visualizador de datasets

let currentSession = "";

function loadSession() {
    const select = document.getElementById('sessionSelect');
    const selectedSession = select.value;
    
    if (selectedSession) {
        window.location.href = '/visualizer?session=' + selectedSession;
    } else {
        window.location.href = '/visualizer';
    }
}

function refreshData() {
    if (currentSession) {
        loadSession();
    }
}

// Función para inicializar el visualizador
function initializeVisualizer(session) {
    currentSession = session || '';
    
    // Cargar datos si hay sesión seleccionada
    if (currentSession) {
        loadSessionData(currentSession);
    }
}

async function loadSessionData(sessionName) {
    try {
        const response = await fetch('/api/session/' + sessionName + '/visualize');
        const data = await response.json();
        
        if (data.success) {
            displaySessionData(data);
        } else {
            showError('Error cargando sesión: ' + data.message);
        }
    } catch (error) {
        showError('Error de conexión: ' + error.message);
    }
}

function displaySessionData(data) {
    // Mostrar estadísticas
    document.getElementById('totalImages').textContent = data.total_images;
    document.getElementById('totalLabels').textContent = data.total_labels;
    const avgLabels = data.total_images > 0 ? (data.total_labels / data.total_images).toFixed(1) : '0.0';
    document.getElementById('avgLabels').textContent = avgLabels;
    document.getElementById('statsContainer').style.display = 'block';
    
    // Mostrar galería de imágenes
    let galleryHTML = '<div class="gallery">';
    
    if (data.images && data.images.length > 0) {
        data.images.forEach((image, index) => {
            galleryHTML += `
                <div class="image-card">
                    <div class="image-container">
                        <canvas id="canvas_${index}" width="${image.width}" height="${image.height}" 
                                style="max-width: 100%; height: 250px; object-fit: contain; border: 1px solid #ddd;">
                        </canvas>
                    </div>
                    <div class="image-info">
                        <h4>📄 ${image.name}</h4>
                        <p>🏷️ Labels: ${image.labels || 0}</p>
                        <p>📏 Resolución: ${image.width}x${image.height}</p>
                    </div>
                </div>
            `;
        });
    } else {
        galleryHTML += '<div style="grid-column: 1 / -1; text-align: center; padding: 40px;"><h3>📷 No hay imágenes en esta sesión</h3></div>';
    }
    
    galleryHTML += '</div>';
    document.getElementById('contentContainer').innerHTML = galleryHTML;
    
    // Dibujar las imágenes y las anotaciones en los canvas
    if (data.images && data.images.length > 0) {
        data.images.forEach((image, index) => {
            drawImageWithAnnotations(image, index);
        });
    }
}

function drawImageWithAnnotations(imageData, index) {
    const canvas = document.getElementById(`canvas_${index}`);
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const img = new Image();
    
    img.onload = function() {
        // Dibujar la imagen
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        
        // Dibujar las anotaciones
        if (imageData.annotations && imageData.annotations.length > 0) {
            imageData.annotations.forEach(annotation => {
                drawBoundingBox(ctx, annotation, canvas.width, canvas.height, imageData.width, imageData.height);
            });
        }
    };
    
    img.onerror = function() {
        // Si la imagen no se puede cargar, mostrar placeholder
        ctx.fillStyle = '#f8f9fa';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = '#6c757d';
        ctx.font = '16px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('Imagen no encontrada', canvas.width/2, canvas.height/2);
    };
    
    img.src = `/image/${currentSession}/${imageData.name}`;
}

function drawBoundingBox(ctx, annotation, canvasWidth, canvasHeight, imageWidth, imageHeight) {
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
    ctx.fillText(`Clase ${annotation.class_id}`, x1, y1 - 5);
    
    // Fondo semi-transparente para el texto
    ctx.globalAlpha = 0.7;
    ctx.fillRect(x1, y1 - 20, 60, 15);
    ctx.globalAlpha = 1.0;
    ctx.fillStyle = 'white';
    ctx.fillText(`Clase ${annotation.class_id}`, x1 + 2, y1 - 8);
}

function showError(message) {
    document.getElementById('contentContainer').innerHTML = `
        <div class="no-session">
            <h3>❌ Error</h3>
            <p>${message}</p>
            <button onclick="refreshData()" class="controls button">🔄 Intentar de nuevo</button>
        </div>
    `;
}

// ===== JAVASCRIPT PARA VISUALIZADOR DE ANOTACIONES =====

// Configuración global
const VISUALIZATION_CONFIG = {
    colors: {
        0: '#ff0000',  // Rojo - Persona
        1: '#00ff00',  // Verde - Vehículo
        2: '#0000ff',  // Azul - Animal
        3: '#ffff00',  // Amarillo - Objeto
        4: '#ff00ff',  // Magenta - Edificio
        5: '#00ffff'   // Cian - Otro
    },
    classNames: {
        0: 'Persona',
        1: 'Vehículo', 
        2: 'Animal',
        3: 'Objeto',
        4: 'Edificio',
        5: 'Otro'
    },
    boxThickness: 3,
    fontSize: 16,
    fontFamily: 'Arial, sans-serif'
};

// Variables globales
let sessionData = null;
let currentImages = [];

// ===== FUNCIONES DE CARGA Y PROCESAMIENTO =====

// Función principal para cargar datos de la sesión
async function loadSessionData(sessionId) {
    if (!sessionId) {
        console.error('Session ID is required');
        showError('ID de sesión requerido');
        return;
    }
    
    console.log('Cargando datos para sesión:', sessionId);
    
    try {
        showLoading(true);
        
        // Usar el endpoint existente que funciona
        const url = `/api/session/${sessionId}/visualize`;
        console.log('Haciendo fetch a:', url);
        
        const response = await fetch(url);
        console.log('Response status:', response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Datos recibidos:', data);
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        sessionData = data;
        currentImages = data.images || [];
        
        console.log('Número de imágenes:', currentImages.length);
        
        // Actualizar la interfaz
        updateSessionInfo(data);
        renderLegend();
        renderImages();
        
    } catch (error) {
        console.error('Error loading session data:', error);
        showError('Error al cargar los datos de la sesión: ' + error.message);
    } finally {
        showLoading(false);
    }
}

// Función para actualizar información de la sesión
function updateSessionInfo(data) {
    // Actualizar título
    const titleElement = document.getElementById('session-title');
    if (titleElement) {
        titleElement.textContent = `Visualizador - Sesión: ${data.session_name}`;
    }
    
    // Actualizar estadísticas si existen elementos
    const statsElement = document.getElementById('session-stats');
    if (statsElement) {
        const imageCount = data.images ? data.images.length : 0;
        const annotationCount = data.images ? data.images.reduce((sum, img) => sum + (img.annotations ? img.annotations.length : 0), 0) : 0;
        
        statsElement.innerHTML = `
            <div>Imágenes: <strong>${imageCount}</strong></div>
            <div>Anotaciones: <strong>${annotationCount}</strong></div>
        `;
    }
}

// ===== FUNCIONES DE RENDERIZADO =====

// Función para renderizar la leyenda de colores
function renderLegend() {
    const legendContainer = document.getElementById('legend-items');
    if (!legendContainer) return;
    
    legendContainer.innerHTML = '';
    
    Object.keys(VISUALIZATION_CONFIG.colors).forEach(classId => {
        const color = VISUALIZATION_CONFIG.colors[classId];
        const name = VISUALIZATION_CONFIG.classNames[classId];
        
        const legendItem = document.createElement('div');
        legendItem.className = 'legend-item';
        legendItem.innerHTML = `
            <span style="background-color: ${color}; width: 20px; height: 20px; display: inline-block; margin-right: 10px; border-radius: 3px;"></span>
            ${name}
        `;
        
        legendContainer.appendChild(legendItem);
    });
}

// Función para renderizar todas las imágenes con sus anotaciones
function renderImages() {
    const imagesContainer = document.getElementById('images-container');
    if (!imagesContainer) {
        console.error('No se encontró el contenedor de imágenes');
        return;
    }
    
    console.log('Renderizando imágenes, total:', currentImages.length);
    
    imagesContainer.innerHTML = '';
    
    if (!currentImages || currentImages.length === 0) {
        imagesContainer.innerHTML = '<div class="loading">No hay imágenes anotadas en esta sesión</div>';
        return;
    }
    
    currentImages.forEach((imageData, index) => {
        console.log(`Procesando imagen ${index + 1}:`, imageData.filename);
        const imageCard = createImageCard(imageData);
        imagesContainer.appendChild(imageCard);
    });
    
    console.log('Todas las imágenes han sido renderizadas');
}

// Función para crear una tarjeta de imagen
function createImageCard(imageData) {
    const card = document.createElement('div');
    card.className = 'image-card';
    
    const fileName = imageData.filename || 'imagen.jpg';
    const annotations = imageData.annotations || [];
    
    // Si la imagen ya tiene los datos en base64, usarlos directamente
    if (imageData.image_data) {
        const img = document.createElement('img');
        img.src = imageData.image_data;
        img.className = 'image-preview';
        img.alt = fileName;
        
        // Información de la imagen
        const imageInfo = document.createElement('div');
        imageInfo.className = 'image-info';
        imageInfo.innerHTML = `
            <strong>${fileName}</strong><br>
            <small>Anotaciones: ${annotations.length}</small>
            ${imageData.has_labels ? '<br>✅ Etiquetas encontradas' : '<br>❌ Sin etiquetas'}
        `;
        
        // Lista de anotaciones si existen
        if (annotations.length > 0) {
            const annotationsList = document.createElement('div');
            annotationsList.className = 'annotations-list';
            
            annotations.forEach(annotation => {
                const annotationItem = document.createElement('div');
                annotationItem.className = 'annotation-item';
                annotationItem.style.borderLeftColor = annotation.color || '#ccc';
                
                annotationItem.innerHTML = `
                    ${annotation.class_name || `Clase ${annotation.class_id}`} (ID: ${annotation.class_id})
                    <br><small>YOLO: [${annotation.yolo_coords ? annotation.yolo_coords.map(c => c.toFixed(3)).join(', ') : 'N/A'}]</small>
                `;
                
                annotationsList.appendChild(annotationItem);
            });
            
            card.appendChild(img);
            card.appendChild(imageInfo);
            card.appendChild(annotationsList);
        } else {
            card.appendChild(img);
            card.appendChild(imageInfo);
        }
    } else {
        // Si no hay datos de imagen, mostrar error
        card.innerHTML = `
            <div class="image-info">
                <strong>${fileName}</strong><br>
                <small style="color: red;">Error: No se pudo cargar la imagen</small>
            </div>
        `;
    }
    
    return card;
}

// ===== FUNCIONES DE UTILIDAD =====

// Función para mostrar estado de carga
function showLoading(show) {
    const loadingElement = document.getElementById('loading');
    const contentElement = document.getElementById('content');
    
    if (loadingElement) {
        loadingElement.style.display = show ? 'block' : 'none';
    }
    
    if (contentElement) {
        contentElement.style.display = show ? 'none' : 'block';
    }
}

// Función para mostrar errores
function showError(message) {
    console.error('Error:', message);
    
    const imagesContainer = document.getElementById('images-container');
    if (imagesContainer) {
        imagesContainer.innerHTML = `
            <div style="background: #f8d7da; color: #721c24; padding: 20px; border-radius: 5px; text-align: center;">
                <strong>Error:</strong> ${message}
                <br><br>
                <button onclick="reloadData()" style="background: #dc3545; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer;">
                    Intentar de nuevo
                </button>
            </div>
        `;
    }
}

// Función para obtener parámetro de URL
function getUrlParameter(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
}

// ===== INICIALIZACIÓN =====

// Función de inicialización
function initVisualizer() {
    console.log('Inicializando visualizador...');
    
    // Obtener session ID de la URL
    const sessionId = getUrlParameter('session');
    
    if (!sessionId) {
        showError('No se especificó una sesión para visualizar. Ve al anotador principal y selecciona una sesión.');
        return;
    }
    
    console.log('Cargando sesión:', sessionId);
    
    // Cargar datos de la sesión
    loadSessionData(sessionId);
}

// Función para recargar datos
function reloadData() {
    const sessionId = getUrlParameter('session');
    if (sessionId) {
        loadSessionData(sessionId);
    } else {
        showError('No se puede recargar: falta el ID de sesión');
    }
}

// ===== EVENT LISTENERS =====

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM cargado, inicializando visualizador...');
    
    // Crear leyenda inmediatamente
    renderLegend();
    
    // Inicializar visualizador
    initVisualizer();
    
    // Agregar event listener al botón de recarga (si existe)
    const reloadBtn = document.getElementById('reload-btn');
    if (reloadBtn) {
        reloadBtn.addEventListener('click', reloadData);
    }
    
    // Agregar event listener al botón de volver (si existe)
    const backBtn = document.getElementById('back-btn');
    if (backBtn) {
        backBtn.addEventListener('click', function() {
            window.location.href = '/';
        });
    }
});

// Manejar errores de imagen globalmente
window.addEventListener('error', function(e) {
    if (e.target.tagName === 'IMG') {
        console.error('Error loading image:', e.target.src);
        e.target.style.display = 'none';
        
        // Mostrar mensaje de error en lugar de la imagen
        const errorDiv = document.createElement('div');
        errorDiv.innerHTML = '⚠️ Error al cargar imagen';
        errorDiv.style.cssText = 'padding: 20px; background: #f8d7da; color: #721c24; text-align: center; border-radius: 5px;';
        e.target.parentNode.insertBefore(errorDiv, e.target);
    }
});

// Exportar funciones para uso global
window.visualizerUtils = {
    loadSessionData,
    reloadData,
    showError,
    showLoading,
    VISUALIZATION_CONFIG,
    initVisualizer
};

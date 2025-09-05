// sessions.js - Manejo de sesiones para YOLO Annotator

let currentSession = null;
let selectedVariants = new Set();
let augmentationInProgress = false;

// Cargar sesiones al inicializar la página
document.addEventListener('DOMContentLoaded', function() {
    loadSessions();
});

// Cargar y mostrar lista de sesiones
async function loadSessions() {
    try {
        const response = await fetch('/api/sessions');
        const data = await response.json();
        
        if (data.success) {
            displaySessions(data.sessions);
        } else {
            showError('Error al cargar sesiones: ' + data.message);
        }
    } catch (error) {
        showError('Error de conexión: ' + error.message);
    }
}

// Mostrar sesiones en la interfaz
function displaySessions(sessions) {
    const sessionsList = document.getElementById('sessionsList');
    
    if (!sessions || sessions.length === 0) {
        sessionsList.innerHTML = `
            <div class="no-sessions">
                <h3>📂 No hay sesiones disponibles</h3>
                <p>Para crear una sesión, sube imágenes a:</p>
                <code>annotations/nombre_sesion/images/</code>
                <br><br>
                <button onclick="createExampleSession()" class="btn-create">💡 Instrucciones</button>
            </div>
        `;
        return;
    }
    
    let html = '<div class="sessions-grid">';
    
    sessions.forEach(session => {
        html += `
            <div class="session-card">
                <h3>📁 ${session.name}</h3>
                <div class="session-stats">
                    <span>🖼️ ${session.images_count} imágenes</span>
                    <span>🏷️ ${session.labels_count} labels</span>
                </div>
                <div class="session-actions">
                    <a href="/visualizer?session=${session.name}" class="btn-visualize">👁️ Visualizar</a>
                    <button onclick="openAugmentationModal('${session.name}')" class="augment-btn">🔄 Augmentar</button>
                    <button onclick="deleteSession('${session.name}')" class="btn-delete">🗑️ Eliminar</button>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    sessionsList.innerHTML = html;
}

// Refrescar lista de sesiones
function refreshSessions() {
    loadSessions();
}

// Mostrar mensaje de error
function showError(message) {
    const sessionsList = document.getElementById('sessionsList');
    sessionsList.innerHTML = `
        <div class="error-message" style="text-align: center; padding: 40px; color: #dc3545;">
            <h3>❌ Error</h3>
            <p>${message}</p>
            <button onclick="refreshSessions()" class="btn-create">🔄 Reintentar</button>
        </div>
    `;
}

// Crear sesión de ejemplo (mostrar instrucciones)
function createExampleSession() {
    alert('💡 Para crear una sesión:\n\n' +
          '1. Crea la carpeta: annotations/mi_sesion/\n' +
          '2. Crea subcarpeta: annotations/mi_sesion/images/\n' +
          '3. Sube tus imágenes JPG/PNG\n' +
          '4. Recarga esta página\n\n' +
          '¡La sesión aparecerá automáticamente!');
}

// Eliminar sesión
async function deleteSession(sessionName) {
    if (!confirm(`¿Estás seguro de que quieres eliminar la sesión "${sessionName}"?\n\n` +
                'Esta acción NO se puede deshacer y eliminará todas las imágenes y anotaciones.')) {
        return;
    }
    
    try {
        const response = await fetch(`/delete_session/${sessionName}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('✅ Sesión eliminada correctamente');
            loadSessions(); // Recargar lista
        } else {
            alert('❌ Error: ' + result.message);
        }
    } catch (error) {
        alert('❌ Error de conexión: ' + error.message);
    }
}

// ====================================================================
// FUNCIONES DEL MODAL DE AUGMENTACIÓN
// ====================================================================

// Abrir modal de augmentación
async function openAugmentationModal(sessionName) {
    currentSession = sessionName;
    selectedVariants.clear();
    
    // Mostrar información de la sesión
    document.getElementById('sessionInfo').innerHTML = `
        <strong>📁 Sesión:</strong> ${sessionName}<br>
        <small>Se aplicarán las transformaciones seleccionadas a todas las imágenes de esta sesión</small>
    `;
    
    // Cargar variantes disponibles
    await loadVariants();
    
    // Mostrar modal
    document.getElementById('augmentationModal').style.display = 'block';
    document.body.style.overflow = 'hidden';
}

// Cerrar modal de augmentación
function closeAugmentationModal() {
    document.getElementById('augmentationModal').style.display = 'none';
    document.body.style.overflow = 'auto';
    resetAugmentationForm();
}

// Cargar variantes disponibles
async function loadVariants() {
    try {
        const response = await fetch(`/api/session/${currentSession}/augmentation/info`);
        const data = await response.json();
        
        if (data.success) {
            displayVariants(data.available_variants);
        } else {
            showModalError('Error al cargar variantes: ' + data.message);
        }
    } catch (error) {
        showModalError('Error de conexión: ' + error.message);
    }
}

// Mostrar variantes en el modal
function displayVariants(variants) {
    const variantGrid = document.getElementById('variantGrid');
    let html = '';
    
    for (const [key, variant] of Object.entries(variants)) {
        html += `
            <div class="variant-card" onclick="toggleVariant('${key}')" id="variant_${key}">
                <h4>${variant.icon} ${variant.name}</h4>
                <p>${variant.description}</p>
            </div>
        `;
    }
    
    variantGrid.innerHTML = html;
}

// Alternar selección de variante
function toggleVariant(variantKey) {
    const card = document.getElementById(`variant_${variantKey}`);
    
    if (selectedVariants.has(variantKey)) {
        selectedVariants.delete(variantKey);
        card.classList.remove('selected');
    } else {
        selectedVariants.add(variantKey);
        card.classList.add('selected');
    }
    
    updateButtons();
}

// Seleccionar todas las variantes
function selectAllVariants() {
    const cards = document.querySelectorAll('.variant-card');
    
    if (selectedVariants.size === cards.length) {
        // Deseleccionar todas
        selectedVariants.clear();
        cards.forEach(card => card.classList.remove('selected'));
        document.getElementById('selectAllBtn').textContent = 'Seleccionar Todo';
    } else {
        // Seleccionar todas
        cards.forEach(card => {
            const variantKey = card.id.replace('variant_', '');
            selectedVariants.add(variantKey);
            card.classList.add('selected');
        });
        document.getElementById('selectAllBtn').textContent = 'Deseleccionar Todo';
    }
    
    updateButtons();
}

// Actualizar estado de botones
function updateButtons() {
    const startBtn = document.getElementById('startAugmentationBtn');
    const selectAllBtn = document.getElementById('selectAllBtn');
    const totalVariants = document.querySelectorAll('.variant-card').length;
    
    startBtn.disabled = selectedVariants.size === 0 || augmentationInProgress;
    
    if (selectedVariants.size === totalVariants) {
        selectAllBtn.textContent = 'Deseleccionar Todo';
    } else {
        selectAllBtn.textContent = 'Seleccionar Todo';
    }
}

// Iniciar augmentación
async function startAugmentation() {
    if (selectedVariants.size === 0) {
        alert('⚠️ Selecciona al menos una variante para continuar');
        return;
    }
    
    if (augmentationInProgress) {
        return;
    }
    
    augmentationInProgress = true;
    
    // Deshabilitar botones
    document.getElementById('startAugmentationBtn').disabled = true;
    document.getElementById('startAugmentationBtn').textContent = '🔄 Procesando...';
    document.getElementById('selectAllBtn').disabled = true;
    
    // Mostrar barra de progreso
    document.getElementById('progressContainer').style.display = 'block';
    document.getElementById('progressText').textContent = 'Iniciando augmentación...';
    
    try {
        // Iniciar augmentación
        const response = await fetch(`/api/session/${currentSession}/augmentation/start`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                variants: Array.from(selectedVariants)
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Monitorear progreso
            monitorAugmentationProgress();
        } else {
            throw new Error(result.message || 'Error desconocido');
        }
        
    } catch (error) {
        alert('❌ Error: ' + error.message);
        resetAugmentationForm();
    }
}

// Monitorear progreso de augmentación
async function monitorAugmentationProgress() {
    try {
        const response = await fetch(`/api/session/${currentSession}/augmentation/progress`);
        const progress = await response.json();
        
        if (progress.success) {
            const percent = progress.total > 0 ? Math.round((progress.current / progress.total) * 100) : 0;
            
            document.getElementById('progressFill').style.width = percent + '%';
            document.getElementById('progressText').textContent = 
                `Procesando: ${progress.current}/${progress.total} imágenes (${percent}%)`;
            
            if (progress.completed) {
                document.getElementById('progressText').textContent = 
                    `✅ ¡Completado! ${progress.total} imágenes procesadas`;
                document.getElementById('startAugmentationBtn').textContent = '✅ Augmentación Completada';
                
                setTimeout(() => {
                    alert('🎉 ¡Augmentación completada con éxito!\n\n' +
                          '📊 Revisa tu sesión para ver las nuevas imágenes generadas.\n' +
                          '🔄 La lista de sesiones se actualizará automáticamente.');
                    closeAugmentationModal();
                    loadSessions(); // Recargar sesiones para mostrar nuevos datos
                }, 1000);
            } else {
                // Continuar monitoreando
                setTimeout(monitorAugmentationProgress, 1000);
            }
        }
    } catch (error) {
        console.error('Error monitoring progress:', error);
        // Reintentar en caso de error temporal
        setTimeout(monitorAugmentationProgress, 2000);
    }
}

// Resetear formulario de augmentación
function resetAugmentationForm() {
    selectedVariants.clear();
    augmentationInProgress = false;
    
    // Resetear botones
    document.getElementById('startAugmentationBtn').disabled = false;
    document.getElementById('startAugmentationBtn').textContent = 'Iniciar Augmentación';
    document.getElementById('selectAllBtn').disabled = false;
    document.getElementById('selectAllBtn').textContent = 'Seleccionar Todo';
    
    // Ocultar progreso
    document.getElementById('progressContainer').style.display = 'none';
    document.getElementById('progressFill').style.width = '0%';
    
    // Limpiar selecciones
    document.querySelectorAll('.variant-card').forEach(card => {
        card.classList.remove('selected');
    });
}

// Mostrar error en el modal
function showModalError(message) {
    document.getElementById('variantGrid').innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 20px; color: #dc3545;">
            <h4>❌ Error</h4>
            <p>${message}</p>
        </div>
    `;
}

// Cerrar modal al hacer clic fuera
window.onclick = function(event) {
    const modal = document.getElementById('augmentationModal');
    if (event.target === modal) {
        closeAugmentationModal();
    }
};

// Manejar tecla Escape para cerrar modal
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closeAugmentationModal();
    }
});

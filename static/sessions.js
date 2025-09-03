// JS para la gestión de sesiones

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
    // ===== JAVASCRIPT PARA GESTIÓN DE SESIONES =====

// Función para seleccionar una sesión
function selectSession(sessionId) {
    // Remover selección anterior
    const allItems = document.querySelectorAll('.session-item');
    allItems.forEach(item => item.classList.remove('selected'));
    
    // Agregar selección actual
    const selectedItem = document.querySelector(`[data-session-id="${sessionId}"]`);
    if (selectedItem) {
        selectedItem.classList.add('selected');
    }
    
    // Actualizar el input de sesión en el formulario principal (si existe)
    const sessionInput = document.getElementById('session');
    if (sessionInput) {
        sessionInput.value = sessionId;
    }
}

// Función para descargar una sesión
async function downloadSession(sessionId, event) {
    event.stopPropagation(); // Evitar que se seleccione la sesión
    
    try {
        const response = await fetch(`/download_session/${sessionId}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `${sessionId}.zip`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        
        // Mostrar mensaje de éxito
        showMessage('Sesión descargada exitosamente', 'success');
        
    } catch (error) {
        console.error('Error al descargar sesión:', error);
        showMessage('Error al descargar la sesión', 'error');
    }
}

// Función para visualizar una sesión
function visualizeSession(sessionId, event) {
    event.stopPropagation(); // Evitar que se seleccione la sesión
    
    // Abrir el visualizador en una nueva pestaña
    const url = `/visualizer?session=${sessionId}`;
    window.open(url, '_blank');
}

// Función para eliminar una sesión
async function deleteSession(sessionId, event) {
    event.stopPropagation(); // Evitar que se seleccione la sesión
    
    // Pedir confirmación
    const confirmed = confirm(`¿Estás seguro de que quieres eliminar la sesión "${sessionId}"? Esta acción no se puede deshacer.`);
    if (!confirmed) {
        return;
    }
    
    try {
        const response = await fetch(`/delete_session/${sessionId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        // Remover el elemento del DOM
        const sessionItem = document.querySelector(`[data-session-id="${sessionId}"]`);
        if (sessionItem) {
            sessionItem.remove();
        }
        
        // Mostrar mensaje de éxito
        showMessage('Sesión eliminada exitosamente', 'success');
        
        // Si era la sesión seleccionada, limpiar selección
        const sessionInput = document.getElementById('session');
        if (sessionInput && sessionInput.value === sessionId) {
            sessionInput.value = '';
        }
        
    } catch (error) {
        console.error('Error al eliminar sesión:', error);
        showMessage('Error al eliminar la sesión', 'error');
    }
}

// Función para mostrar mensajes al usuario
function showMessage(message, type = 'info') {
    // Crear elemento de mensaje si no existe
    let messageContainer = document.getElementById('message-container');
    if (!messageContainer) {
        messageContainer = document.createElement('div');
        messageContainer.id = 'message-container';
        messageContainer.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            display: flex;
            flex-direction: column;
            gap: 10px;
        `;
        document.body.appendChild(messageContainer);
    }
    
    // Crear mensaje
    const messageElement = document.createElement('div');
    messageElement.textContent = message;
    
    // Estilos según el tipo
    const baseStyle = `
        padding: 12px 20px;
        border-radius: 5px;
        color: white;
        font-weight: bold;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        opacity: 0;
        transform: translateX(100%);
        transition: all 0.3s ease;
    `;
    
    const typeStyles = {
        'success': 'background-color: #28a745;',
        'error': 'background-color: #dc3545;',
        'info': 'background-color: #17a2b8;',
        'warning': 'background-color: #ffc107; color: #333;'
    };
    
    messageElement.style.cssText = baseStyle + (typeStyles[type] || typeStyles['info']);
    
    // Agregar al contenedor
    messageContainer.appendChild(messageElement);
    
    // Mostrar con animación
    setTimeout(() => {
        messageElement.style.opacity = '1';
        messageElement.style.transform = 'translateX(0)';
    }, 100);
    
    // Ocultar después de 5 segundos
    setTimeout(() => {
        messageElement.style.opacity = '0';
        messageElement.style.transform = 'translateX(100%)';
        
        // Remover del DOM después de la animación
        setTimeout(() => {
            if (messageElement.parentNode) {
                messageElement.parentNode.removeChild(messageElement);
            }
        }, 300);
    }, 5000);
}

// Función para actualizar las estadísticas de una sesión
function updateSessionStats(sessionId) {
    const sessionItem = document.querySelector(`[data-session-id="${sessionId}"]`);
    if (!sessionItem) return;
    
    // Obtener información actualizada de la sesión
    fetch(`/api/session_info/${sessionId}`)
        .then(response => response.json())
        .then(data => {
            const statsElement = sessionItem.querySelector('.session-stats');
            if (statsElement && data.stats) {
                const stats = data.stats;
                statsElement.innerHTML = `
                    <div>Imágenes: ${stats.images}</div>
                    <div>Anotaciones: ${stats.annotations}</div>
                    <div>Modificado: ${stats.last_modified}</div>
                `;
            }
        })
        .catch(error => {
            console.error('Error al actualizar estadísticas:', error);
        });
}

// Función para crear una nueva sesión
function createNewSession() {
    const sessionName = prompt('Nombre para la nueva sesión (opcional):');
    
    // Si el usuario cancela, no hacer nada
    if (sessionName === null) {
        return;
    }
    
    // Crear la nueva sesión
    const formData = new FormData();
    if (sessionName && sessionName.trim()) {
        formData.append('session_name', sessionName.trim());
    }
    
    fetch('/create_session', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.session_id) {
            // Recargar la página para mostrar la nueva sesión
            window.location.reload();
        } else {
            showMessage('Error al crear la sesión', 'error');
        }
    })
    .catch(error => {
        console.error('Error al crear sesión:', error);
        showMessage('Error al crear la sesión', 'error');
    });
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    console.log('JavaScript de sesiones cargado correctamente');
    
    // Agregar event listeners a botones existentes
    const createBtn = document.getElementById('create-session-btn');
    if (createBtn) {
        createBtn.addEventListener('click', createNewSession);
    }
    
    // Agregar event listeners a items de sesión existentes
    const sessionItems = document.querySelectorAll('.session-item');
    sessionItems.forEach(item => {
        const sessionId = item.dataset.sessionId;
        
        // Click en el item para seleccionar
        item.addEventListener('click', () => selectSession(sessionId));
        
        // Botones de acción
        const downloadBtn = item.querySelector('.download-btn');
        if (downloadBtn) {
            downloadBtn.addEventListener('click', (e) => downloadSession(sessionId, e));
        }
        
        const visualizeBtn = item.querySelector('.visualize-btn');
        if (visualizeBtn) {
            visualizeBtn.addEventListener('click', (e) => visualizeSession(sessionId, e));
        }
        
        const deleteBtn = item.querySelector('.delete-btn');
        if (deleteBtn) {
            deleteBtn.addEventListener('click', (e) => deleteSession(sessionId, e));
        }
    });
});

// Exportar funciones para uso global
window.sessionUtils = {
    selectSession,
    downloadSession,
    visualizeSession,
    deleteSession,
    showMessage,
    updateSessionStats,
    createNewSession
};
    localStorage.setItem('currentSession', sessionName);
    alert(`Sesión seleccionada: ${sessionName}`);
}

async function downloadSession(sessionName) {
    try {
        const downloadLink = document.createElement('a');
        downloadLink.href = `/download_session/${sessionName}`;
        downloadLink.download = `dataset_${sessionName}.zip`;
        document.body.appendChild(downloadLink);
        downloadLink.click();
        document.body.removeChild(downloadLink);
    } catch (error) {
        alert('Error al descargar sesión: ' + error.message);
    }
}

function visualizeSession(sessionName) {
    localStorage.setItem('currentSession', sessionName);
    window.open(`/visualizer?session=${sessionName}`, '_blank');
}

async function deleteSession(sessionName) {
    const confirmation = confirm(`¿Seguro que quieres eliminar la sesión "${sessionName}"? Esta acción no se puede deshacer.`);
    if (!confirmation) return;
    try {
        const response = await fetch(`/delete_session/${sessionName}`, { method: 'DELETE' });
        const result = await response.json();
        if (result.success) {
            alert(`Sesión "${sessionName}" eliminada correctamente`);
            refreshSessions();
        } else {
            alert(`Error al eliminar sesión: ${result.message}`);
        }
    } catch (error) {
        alert('Error de conexión al eliminar sesión: ' + error.message);
    }
}

document.addEventListener('DOMContentLoaded', function() {
    refreshSessions();
});

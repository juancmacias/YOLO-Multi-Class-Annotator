// ===== MODAL DE INSTRUCCIONES =====

function initializeModal() {
    const modal = document.getElementById('instructionsModal');
    const helpBtn = document.getElementById('helpBtn');
    const closeBtn = document.querySelector('.close');
    
    if (!modal || !helpBtn || !closeBtn) return;
    
    // Abrir modal
    helpBtn.addEventListener('click', function() {
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden';
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

// Hacer función global para que pueda ser llamada desde otros JS
window.initializeModal = initializeModal;

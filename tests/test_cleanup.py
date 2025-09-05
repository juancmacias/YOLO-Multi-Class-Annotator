"""
Test de limpieza del proyecto

Verifica que archivos obsoletos hayan sido eliminados correctamente
"""

import pytest
import os
from pathlib import Path


class TestProjectCleanup:
    """Tests para verificar la limpieza del proyecto"""
    
    def test_obsolete_files_removed(self):
        """Verificar que archivos obsoletos han sido eliminados"""
        obsolete_files = [
            "app_simple.py",
        ]
        
        for file in obsolete_files:
            file_path = Path(file)
            assert not file_path.exists(), (
                f"Archivo obsoleto encontrado: {file}. "
                f"Este archivo debe ser eliminado para mantener el proyecto limpio."
            )
    
    def test_main_application_exists(self):
        """Verificar que la aplicación principal existe"""
        main_app = Path("app_auth.py")
        assert main_app.exists(), "app_auth.py debe existir como aplicación principal"
    
    def test_essential_files_exist(self):
        """Verificar que archivos esenciales existen"""
        essential_files = [
            "requirements.txt",
            "README.md",
            ".env.example",
            "augment_dataset.py"
        ]
        
        for file in essential_files:
            file_path = Path(file)
            assert file_path.exists(), f"Archivo esencial faltante: {file}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

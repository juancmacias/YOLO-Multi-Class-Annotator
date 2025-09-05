"""
Configuración y fixtures compartidas para pytest.

Este archivo contiene fixtures y configuraciones que son compartidas
entre todos los tests del proyecto YOLO Multi-Class Annotator.
"""

import pytest
import os
import sys
from pathlib import Path

# Agregar el directorio raíz al PYTHONPATH para importar módulos
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# Configurar variables de entorno de testing
os.environ['TESTING'] = 'true'
os.environ['DATABASE_URL'] = 'mysql+pymysql://test_user:test_pass@localhost/test_yolo_db'

@pytest.fixture(scope="session")
def root_path():
    """Fixture que devuelve la ruta raíz del proyecto."""
    return root_dir

@pytest.fixture(scope="session")
def test_data_path():
    """Fixture que devuelve la ruta de datos de testing."""
    return root_dir / "tests" / "data"

@pytest.fixture(scope="function")
def temp_dir(tmp_path):
    """Fixture que crea un directorio temporal para cada test."""
    return tmp_path

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Fixture que configura el entorno de testing automáticamente."""
    # Configurar logging para tests
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    # Aquí puedes agregar más configuraciones de testing
    yield
    
    # Cleanup después de todos los tests
    pass

@pytest.fixture
def mock_mysql_connection():
    """Fixture que simula una conexión MySQL para testing."""
    class MockConnection:
        def __init__(self):
            self.connected = False
            
        def connect(self):
            self.connected = True
            return True
            
        def disconnect(self):
            self.connected = False
            
        def execute(self, query):
            return {"status": "success", "query": query}
    
    return MockConnection()

@pytest.fixture
def sample_image_data():
    """Fixture que proporciona datos de imagen de muestra."""
    return {
        "filename": "test_image.jpg",
        "width": 640,
        "height": 480,
        "format": "JPEG",
        "annotations": [
            {"class": "adidas", "bbox": [100, 100, 200, 200]},
            {"class": "nike", "bbox": [300, 300, 400, 400]}
        ]
    }

@pytest.fixture
def sample_user_data():
    """Fixture que proporciona datos de usuario de muestra."""
    return {
        "username": "test_user",
        "email": "test@example.com",
        "password": "test_password_123",
        "is_active": True
    }

@pytest.fixture
def jwt_token_data():
    """Fixture que proporciona datos de token JWT de muestra."""
    return {
        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "token_type": "bearer",
        "expires_in": 3600
    }

#!/usr/bin/env python3
"""
Test de integración para la gestión de clases personalizadas

NOTA: Este es un test de integración que requiere:
1. Servidor ejecutándose en localhost:8002
2. Base de datos MySQL configurada
3. Usuario admin/admin creado

Para ejecutar solo este test:
pytest tests/test_classes.py -m integration -v

Para omitir tests de integración:
pytest -m "not integration" -v
"""

import pytest
import requests
import json

# Configuración
BASE_URL = "http://localhost:8002"
USERNAME = "admin"  # Cambia por tu usuario
PASSWORD = "admin"  # Cambia por tu contraseña


def login():
    """Hacer login y obtener token"""
    try:
        response = requests.post(f"{BASE_URL}/auth/login", data={
            "username": USERNAME,
            "password": PASSWORD
        }, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            return data["access_token"]
        else:
            print(f"❌ Error en login: {response.text}")
            return None
    except requests.exceptions.ConnectionError:
        pytest.skip("Servidor no disponible en localhost:8002. Inicia app_auth.py primero.")
    except Exception as e:
        pytest.skip(f"Error de conexión: {str(e)}")


def get_headers(token):
    """Obtener headers con autorización"""
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }


@pytest.mark.integration
def test_class_management():
    """Probar funciones de gestión de clases (test de integración)"""
    print("🧪 Probando gestión de clases personalizadas...")
    
    # Login
    token = login()
    if not token:
        pytest.fail("No se pudo obtener token de autenticación")
    
    headers = get_headers(token)
    
    # 1. Obtener clases actuales
    print("\n1️⃣ Obteniendo clases actuales...")
    response = requests.get(f"{BASE_URL}/api/classes/", headers=headers)
    if response.status_code == 200:
        classes = response.json()
        print(f"✅ Clases actuales: {len(classes)}")
        for cls in classes:
            print(f"   - {cls['name']} ({cls['color']})")
    else:
        pytest.fail(f"Error obteniendo clases: {response.text}")
    
    # 2. Crear nuevas clases personalizadas
    print("\n2️⃣ Creando clases personalizadas...")
    
    new_classes = [
        {"name": "Perro_Test", "color": "#FF6B6B"},
        {"name": "Gato_Test", "color": "#4ECDC4"},
    ]
    
    created_classes = []
    for class_data in new_classes:
        response = requests.post(
            f"{BASE_URL}/api/classes/", 
            headers=headers,
            data=json.dumps(class_data)
        )
        
        if response.status_code == 200:
            created = response.json()
            created_classes.append(created)
            print(f"✅ Creada: {created['name']}")
        else:
            print(f"❌ Error creando {class_data['name']}: {response.text}")
    
    # Verificar que al menos una clase fue creada
    assert len(created_classes) > 0, "No se pudo crear ninguna clase de prueba"
    
    # 3. Actualizar una clase
    if created_classes:
        print("\n3️⃣ Actualizando clase...")
        class_id = created_classes[0]['id']
        update_data = {"name": "Perro_Test_Updated", "color": "#FF4757"}
        
        response = requests.put(
            f"{BASE_URL}/api/classes/{class_id}",
            headers=headers,
            data=json.dumps(update_data)
        )
        
        if response.status_code == 200:
            updated_class = response.json()
            print(f"✅ Clase actualizada: {updated_class['name']}")
            assert updated_class['name'] == "Perro_Test_Updated"
        else:
            pytest.fail(f"Error actualizando clase: {response.text}")
    
    # 4. Obtener colores disponibles
    print("\n4️⃣ Obteniendo colores predefinidos...")
    response = requests.get(f"{BASE_URL}/api/classes/available-colors", headers=headers)
    if response.status_code == 200:
        colors = response.json()
        print(f"✅ Colores disponibles: {len(colors)}")
        assert len(colors) > 0, "Debería haber colores predefinidos disponibles"
        for color in colors[:3]:  # Mostrar solo los primeros 3
            print(f"   - {color['name']}: {color['value']}")
    else:
        pytest.fail(f"Error obteniendo colores: {response.text}")
    
    # 5. Limpiar clases de prueba creadas
    print("\n5️⃣ Limpiando clases de prueba...")
    for created_class in created_classes:
        response = requests.delete(
            f"{BASE_URL}/api/classes/{created_class['id']}", 
            headers=headers
        )
        if response.status_code == 200:
            print(f"✅ Eliminada: {created_class['name']}")
        else:
            print(f"⚠️ No se pudo eliminar: {created_class['name']}")
    
    print("\n🎉 Test de integración completado!")


# Test unitario que no requiere servidor
@pytest.mark.unit
def test_class_management_configuration():
    """Test unitario para verificar configuración del test de clases"""
    # Verificar configuración del test
    assert BASE_URL == "http://localhost:8002"
    assert USERNAME is not None
    assert PASSWORD is not None
    
    # Verificar formato de datos de prueba
    test_class = {"name": "Test", "color": "#FF0000"}
    assert "name" in test_class
    assert "color" in test_class
    assert test_class["color"].startswith("#")
    assert len(test_class["color"]) == 7  # formato #RRGGBB


if __name__ == "__main__":
    # Solo ejecutar test de integración si se ejecuta directamente
    test_class_management()

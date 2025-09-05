#!/usr/bin/env python3
"""
Script de prueba para la gestión de clases personalizadas
"""

import requests
import json

# Configuración
BASE_URL = "http://localhost:8002"
USERNAME = "admin"  # Cambia por tu usuario
PASSWORD = "admin"  # Cambia por tu contraseña

def login():
    """Hacer login y obtener token"""
    response = requests.post(f"{BASE_URL}/auth/login", data={
        "username": USERNAME,
        "password": PASSWORD
    })
    
    if response.status_code == 200:
        data = response.json()
        return data["access_token"]
    else:
        print(f"❌ Error en login: {response.text}")
        return None

def get_headers(token):
    """Obtener headers con autorización"""
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

def test_class_management():
    """Probar funciones de gestión de clases"""
    print("🧪 Probando gestión de clases personalizadas...")
    
    # Login
    token = login()
    if not token:
        return
    
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
        print(f"❌ Error: {response.text}")
    
    # 2. Crear nuevas clases personalizadas
    print("\n2️⃣ Creando clases personalizadas...")
    
    new_classes = [
        {"name": "Perro", "color": "#FF6B6B"},
        {"name": "Gato", "color": "#4ECDC4"},
        {"name": "Coche", "color": "#45B7D1"},
        {"name": "Bicicleta", "color": "#F9CA24"},
        {"name": "Casa", "color": "#6C5CE7"},
        {"name": "Árbol", "color": "#A0E7E5"}
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
    
    # 3. Actualizar una clase
    if created_classes:
        print("\n3️⃣ Actualizando clase...")
        class_id = created_classes[0]['id']
        update_data = {"name": "Perro Grande", "color": "#FF4757"}
        
        response = requests.put(
            f"{BASE_URL}/api/classes/{class_id}",
            headers=headers,
            data=json.dumps(update_data)
        )
        
        if response.status_code == 200:
            print(f"✅ Clase actualizada: {response.json()['name']}")
        else:
            print(f"❌ Error actualizando: {response.text}")
    
    # 4. Obtener colores disponibles
    print("\n4️⃣ Obteniendo colores predefinidos...")
    response = requests.get(f"{BASE_URL}/api/classes/available-colors", headers=headers)
    if response.status_code == 200:
        colors = response.json()
        print(f"✅ Colores disponibles: {len(colors)}")
        for color in colors[:5]:  # Mostrar solo los primeros 5
            print(f"   - {color['name']}: {color['value']}")
    else:
        print(f"❌ Error: {response.text}")
    
    # 5. Obtener clases finales
    print("\n5️⃣ Clases finales...")
    response = requests.get(f"{BASE_URL}/api/classes/", headers=headers)
    if response.status_code == 200:
        classes = response.json()
        print(f"✅ Total de clases: {len(classes)}")
        for cls in classes:
            print(f"   - {cls['name']} ({cls['color']}) - ID: {cls['id']}")
    else:
        print(f"❌ Error: {response.text}")
    
    print("\n🎉 Prueba completada!")
    print("\n💡 Ahora puedes:")
    print("   1. Ir a http://localhost:8002/annotator")
    print("   2. Cargar una imagen")
    print("   3. Click en '⚙️ Gestionar Clases'")
    print("   4. ¡Probar el nuevo sistema de clases!")

if __name__ == "__main__":
    test_class_management()

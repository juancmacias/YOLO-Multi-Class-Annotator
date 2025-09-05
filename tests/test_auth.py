#!/usr/bin/env python3
"""Script de prueba para registrar usuario admin"""

import requests
import json

# URL base de la API
BASE_URL = "http://localhost:8002"

def test_register():
    """Probar registro de usuario"""
    url = f"{BASE_URL}/auth/register"
    
    data = {
        "username": "admin",
        "email": "admin@example.com", 
        "password": "admin123",
        "confirm_password": "admin123"
    }
    
    try:
        response = requests.post(url, data=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Usuario registrado exitosamente!")
            if result.get("user", {}).get("is_admin"):
                print("🔑 Usuario tiene privilegios de administrador")
            return True
        else:
            print("❌ Error en el registro")
            return False
            
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

def test_login():
    """Probar login de usuario"""
    url = f"{BASE_URL}/auth/login"
    
    data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        response = requests.post(url, data=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Login exitoso!")
            token = result.get("access_token")
            if token:
                print(f"🔑 Token obtenido: {token[:20]}...")
                return token
        else:
            print("❌ Error en el login")
            return None
            
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return None

if __name__ == "__main__":
    print("🧪 Probando sistema de autenticación...")
    print("=" * 50)
    
    print("\n1. Probando registro...")
    success = test_register()
    
    if success:
        print("\n2. Probando login...")
        token = test_login()
        
        if token:
            print("\n✅ ¡Sistema funcionando correctamente!")
            print("Puedes usar las credenciales:")
            print("Usuario: admin")
            print("Contraseña: admin123")
        else:
            print("\n❌ Login falló")
    else:
        print("\n❌ Registro falló")

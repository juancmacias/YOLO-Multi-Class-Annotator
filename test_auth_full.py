#!/usr/bin/env python3
"""
Script para probar autenticación completa end-to-end
"""

import requests
import json

BASE_URL = "http://localhost:8002"

def test_auth_flow():
    """Probar flujo completo de autenticación"""
    print("=== Test de Autenticación End-to-End ===")
    
    # 1. Registrar usuario de prueba
    print("\n1. Registrando usuario de prueba...")
    register_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "test123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", data=register_data)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        
        if response.status_code == 200:
            print("   ✅ Registro exitoso")
        else:
            print("   ⚠️ Error en registro (posiblemente usuario ya existe)")
    except Exception as e:
        print(f"   ❌ Error en registro: {e}")
        return False
    
    # 2. Login
    print("\n2. Haciendo login...")
    login_data = {
        "username": "testuser",
        "password": "test123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", data=login_data)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            login_result = response.json()
            print(f"   ✅ Login exitoso")
            token = login_result.get("access_token")
            print(f"   Token: {token[:50] if token else 'No token'}...")
            
            if not token:
                print("   ❌ No se recibió token")
                return False
        else:
            print(f"   ❌ Error en login: {response.json()}")
            return False
    except Exception as e:
        print(f"   ❌ Error en login: {e}")
        return False
    
    # 3. Probar acceso al perfil con token
    print("\n3. Probando acceso al perfil...")
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/auth/profile", headers=headers)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            profile_data = response.json()
            print(f"   ✅ Acceso al perfil exitoso")
            print(f"   Usuario: {profile_data.get('user', {}).get('username', 'Unknown')}")
        else:
            print(f"   ❌ Error accediendo al perfil: {response.json()}")
            return False
    except Exception as e:
        print(f"   ❌ Error accediendo al perfil: {e}")
        return False
    
    # 4. Probar acceso al dashboard
    print("\n4. Probando acceso al dashboard...")
    try:
        response = requests.get(f"{BASE_URL}/dashboard", headers=headers)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"   ✅ Acceso al dashboard exitoso")
            # Verificar que el HTML contiene elementos esperados
            if "dashboard" in response.text.lower():
                print("   ✅ Dashboard HTML contiene contenido esperado")
            else:
                print("   ⚠️ Dashboard HTML no contiene contenido esperado")
        else:
            print(f"   ❌ Error accediendo al dashboard: status {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error accediendo al dashboard: {e}")
        return False
    
    # 5. Probar token inválido
    print("\n5. Probando token inválido...")
    invalid_headers = {
        "Authorization": "Bearer invalid-token-here"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/auth/profile", headers=invalid_headers)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 401:
            print(f"   ✅ Token inválido correctamente rechazado")
        else:
            print(f"   ❌ Token inválido no fue rechazado: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error probando token inválido: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_auth_flow()
    if success:
        print("\n🎉 Todos los tests de autenticación pasaron exitosamente")
        print("\nAhora puedes probar en tu navegador:")
        print("1. Ve a http://localhost:8002/login")
        print("2. Registra un nuevo usuario o usa testuser/test123")
        print("3. Después del login deberías poder acceder al dashboard")
    else:
        print("\n❌ Error en tests de autenticación")
        print("Revisa que el servidor esté funcionando en http://localhost:8002")

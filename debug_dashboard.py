#!/usr/bin/env python3
"""
Script para debuggear el problema específico del dashboard
"""

import requests
import json

BASE_URL = "http://localhost:8002"

def debug_dashboard_access():
    """Debuggear acceso al dashboard paso a paso"""
    print("=== Debug Dashboard Access ===")
    
    # 1. Login para obtener token
    print("\n1. Haciendo login...")
    login_data = {
        "username": "admin",  # Usar admin que debería existir
        "password": "admin123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", data=login_data)
        print(f"   Login Status: {response.status_code}")
        
        if response.status_code == 200:
            login_result = response.json()
            print(f"   ✅ Login exitoso")
            token = login_result.get("access_token")
            token_type = login_result.get("token_type", "bearer")
            print(f"   Token: {token[:50] if token else 'No token'}...")
            print(f"   Token Type: {token_type}")
            
            if not token:
                print("   ❌ No se recibió token")
                return False
        else:
            print(f"   ❌ Error en login: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Error en login: {e}")
        return False
    
    # 2. Probar endpoint /auth/profile con diferentes formatos
    print("\n2. Probando /auth/profile...")
    
    test_headers = [
        {"Authorization": f"Bearer {token}"},
        {"Authorization": f"bearer {token}"},
        {"Authorization": f"{token_type} {token}"},
        {"Authorization": f"{token_type.title()} {token}"},
    ]
    
    for i, headers in enumerate(test_headers):
        try:
            response = requests.get(f"{BASE_URL}/auth/profile", headers=headers)
            print(f"   Test {i+1} - Headers: {headers['Authorization'][:20]}...")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print("   ✅ Acceso exitoso")
                profile_correct_headers = headers
                break
            else:
                print(f"   ❌ Error: {response.text[:100]}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # 3. Probar endpoint /dashboard con headers correctos
    print("\n3. Probando /dashboard...")
    try:
        response = requests.get(f"{BASE_URL}/dashboard", headers=profile_correct_headers)
        print(f"   Dashboard Status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ Dashboard accesible")
            print(f"   Content Length: {len(response.text)}")
            if "dashboard" in response.text.lower():
                print("   ✅ Dashboard HTML válido")
            else:
                print("   ⚠️ Dashboard HTML no contiene 'dashboard'")
        else:
            print(f"   ❌ Error dashboard: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"   ❌ Error dashboard: {e}")
        return False
    
    # 4. Verificar detalles del token
    print("\n4. Analizando token...")
    import base64
    try:
        # Decodificar JWT header y payload (sin verificar firma)
        parts = token.split('.')
        if len(parts) == 3:
            header = parts[0]
            payload = parts[1]
            
            # Agregar padding si es necesario
            header += '=' * (4 - len(header) % 4)
            payload += '=' * (4 - len(payload) % 4)
            
            header_decoded = json.loads(base64.b64decode(header))
            payload_decoded = json.loads(base64.b64decode(payload))
            
            print(f"   Header: {json.dumps(header_decoded, indent=2)}")
            print(f"   Payload: {json.dumps(payload_decoded, indent=2)}")
            
            # Verificar campos importantes
            if "sub" in payload_decoded:
                print(f"   ✅ Subject (username): {payload_decoded['sub']}")
            else:
                print("   ❌ No hay 'sub' en payload")
                
            if "exp" in payload_decoded:
                import datetime
                exp_time = datetime.datetime.fromtimestamp(payload_decoded['exp'])
                now = datetime.datetime.now()
                print(f"   Expira: {exp_time}")
                print(f"   Ahora: {now}")
                if exp_time > now:
                    print("   ✅ Token no expirado")
                else:
                    print("   ❌ Token expirado")
        else:
            print("   ❌ Token JWT malformado")
    except Exception as e:
        print(f"   ❌ Error analizando token: {e}")
    
    return True

if __name__ == "__main__":
    debug_dashboard_access()

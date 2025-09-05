#!/usr/bin/env python3
"""
Script para probar la generación y verificación de tokens JWT
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from auth.auth_utils import create_access_token, verify_token, decode_token
from datetime import timedelta
import json

def test_token_creation():
    """Probar creación y verificación de tokens"""
    print("=== Test de Token JWT ===")
    
    # Datos del usuario de prueba
    test_username = "admin"
    
    # Crear token
    print(f"1. Creando token para usuario: {test_username}")
    token = create_access_token(
        data={"sub": test_username},
        expires_delta=timedelta(minutes=30)
    )
    print(f"   Token generado: {token[:50]}...")
    
    # Verificar token
    print(f"\n2. Verificando token...")
    verified_username = verify_token(token)
    print(f"   Username verificado: {verified_username}")
    
    if verified_username == test_username:
        print("   ✅ Token válido - verificación exitosa")
    else:
        print("   ❌ Token inválido - error en verificación")
        return False
    
    # Decodificar token completo
    print(f"\n3. Decodificando token completo...")
    try:
        payload = decode_token(token)
        print(f"   Payload completo: {json.dumps(payload, indent=2, default=str)}")
        print("   ✅ Decodificación exitosa")
    except Exception as e:
        print(f"   ❌ Error decodificando: {e}")
        return False
    
    # Probar token inválido
    print(f"\n4. Probando token inválido...")
    invalid_token = "invalid.token.here"
    invalid_result = verify_token(invalid_token)
    if invalid_result is None:
        print("   ✅ Token inválido correctamente rechazado")
    else:
        print(f"   ❌ Token inválido aceptado: {invalid_result}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_token_creation()
    if success:
        print("\n🎉 Todos los tests de token pasaron exitosamente")
        sys.exit(0)
    else:
        print("\n❌ Error en tests de token")
        sys.exit(1)

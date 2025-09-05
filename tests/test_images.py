#!/usr/bin/env python3
"""
Test rápido para verificar que el endpoint de imágenes funciona
"""

import requests

BASE_URL = "http://localhost:8002"
session_name = "inicial"
image_name = "inicial_20250905_094132_adidas2.png"

def test_image_endpoint():
    print("=== Test Endpoint de Imágenes ===")
    
    # Test 1: Acceso directo sin autenticación
    print(f"\n1. Probando acceso directo a imagen:")
    print(f"   URL: {BASE_URL}/image/{session_name}/{image_name}")
    
    try:
        response = requests.get(f"{BASE_URL}/image/{session_name}/{image_name}")
        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
        print(f"   Content-Length: {response.headers.get('content-length', 'N/A')}")
        
        if response.status_code == 200:
            print("   ✅ Imagen accesible")
        else:
            print(f"   ❌ Error: {response.text[:100]}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Imagen que no existe
    print(f"\n2. Probando imagen inexistente:")
    fake_image = "imagen_que_no_existe.jpg"
    try:
        response = requests.get(f"{BASE_URL}/image/{session_name}/{fake_image}")
        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
        
        if response.status_code == 200 and 'svg' in response.headers.get('content-type', ''):
            print("   ✅ Placeholder SVG generado correctamente")
        else:
            print(f"   ❌ Respuesta inesperada")
    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    test_image_endpoint()

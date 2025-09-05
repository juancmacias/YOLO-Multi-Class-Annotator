#!/usr/bin/env python3
"""
Script para ejecutar tests unitarios (sin servidor)

Este script ejecuta solo los tests que no requieren que el servidor esté ejecutándose.
Los tests de integración que requieren servidor deben ejecutarse por separado.
"""

import subprocess
import sys

def run_unit_tests():
    """Ejecuta solo los tests unitarios que no requieren servidor."""
    
    print("🧪 Ejecutando tests unitarios del proyecto YOLO Multi-Class Annotator...")
    print("=" * 70)
    
    # Tests que NO requieren servidor activo
    unit_tests = [
        "tests/test_environment.py",     # Tests de configuración del entorno
        "tests/test_mysql_script.py",    # Tests de validación del script MySQL
        "tests/test_token.py",           # Tests de JWT (no requiere servidor)
        "tests/test_mysql.py",           # Tests de conexión MySQL (no requiere servidor)
        "tests/test_auth.py",            # Tests básicos de auth (no requiere servidor)
        "tests/test_images.py"           # Tests de imágenes (no requiere servidor)
    ]
    
    # Tests que SÍ requieren servidor (comentados para referencia)
    integration_tests = [
        # "tests/test_auth_full.py",    # Requiere servidor activo
        # "tests/test_classes.py"       # Requiere servidor activo
    ]
    
    print("Tests unitarios a ejecutar:")
    for test in unit_tests:
        print(f"  ✓ {test}")
    
    print("\nTests de integración (requieren servidor activo):")
    for test in integration_tests:
        print(f"  ⚠️ {test}")
    
    print("\n" + "=" * 70)
    
    # Ejecutar tests unitarios
    try:
        cmd = ["pytest"] + unit_tests + ["-v", "--tb=short"]
        result = subprocess.run(cmd, check=True)
        
        print("\n🎉 ¡Todos los tests unitarios pasaron exitosamente!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Algunos tests fallaron. Código de salida: {e.returncode}")
        return False
    except FileNotFoundError:
        print("\n❌ Error: pytest no está instalado o no está en el PATH")
        print("Instala pytest con: pip install pytest")
        return False

def run_integration_tests():
    """Información sobre cómo ejecutar tests de integración."""
    
    print("\n" + "=" * 70)
    print("📋 Para ejecutar tests de integración:")
    print("=" * 70)
    
    print("\n1. Inicia el servidor de desarrollo:")
    print("   python app_auth.py")
    
    print("\n2. En otra terminal, ejecuta los tests de integración:")
    print("   pytest tests/test_auth_full.py -v")
    print("   pytest tests/test_classes.py -v")
    
    print("\n3. O ejecuta todos los tests (unitarios + integración):")
    print("   pytest tests/ -v")

if __name__ == "__main__":
    success = run_unit_tests()
    run_integration_tests()
    
    sys.exit(0 if success else 1)

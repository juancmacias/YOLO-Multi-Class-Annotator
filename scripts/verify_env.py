#!/usr/bin/env python3
"""
Script para verificar la configuración del archivo .env

Este script comprueba que todas las variables necesarias estén definidas
en el archivo .env y proporciona sugerencias para configuraciones faltantes.
"""

import os
from dotenv import load_dotenv
from pathlib import Path

def verify_env_config():
    """Verifica la configuración del archivo .env"""
    
    print("🔍 Verificando configuración del archivo .env...")
    print("=" * 60)
    
    # Cargar variables del .env
    env_path = Path(".env")  # Buscar en directorio actual
    
    if not env_path.exists():
        print("❌ Archivo .env no encontrado")
        print("📋 Crea el archivo .env copiando desde .env.example:")
        print("   copy .env.example .env")
        return False
    
    load_dotenv(env_path)
    
    # Variables requeridas para MySQL
    required_vars = {
        "DB_HOST": "Dirección del servidor MySQL",
        "DB_PORT": "Puerto del servidor MySQL",
        "DB_USER": "Usuario de MySQL", 
        "DB_PASSWORD": "Contraseña de MySQL",
        "DB_NAME": "Nombre de la base de datos",
        "SECRET_KEY": "Clave secreta para JWT",
        "JWT_ALGORITHM": "Algoritmo para JWT",
        "JWT_ACCESS_TOKEN_EXPIRE_MINUTES": "Tiempo de expiración del token",
        "HOST": "IP del servidor web",
        "PORT": "Puerto del servidor web",
        "DEBUG": "Modo debug"
    }
    
    # Variables opcionales
    optional_vars = {
        "MAX_FILE_SIZE_MB": "Tamaño máximo de archivos",
        "ALLOWED_IMAGE_EXTENSIONS": "Extensiones de imagen permitidas",
        "MAX_SESSIONS_PER_USER": "Máximo de sesiones por usuario",
        "DEFAULT_CANVAS_SIZE": "Tamaño por defecto del canvas",
        "TESTING": "Modo testing",
        "TEST_DATABASE_URL": "URL de base de datos para testing"
    }
    
    print("✅ Variables requeridas:")
    all_required_present = True
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value is not None:  # Permitir valores vacíos pero definidos
            # Mostrar valor censurado para variables sensibles
            if var in ["DB_PASSWORD", "SECRET_KEY"]:
                if value:  # Solo censurar si no está vacía
                    display_value = "*" * min(len(value), 8)
                else:
                    display_value = "(vacía - válido para MySQL sin contraseña)"
            else:
                display_value = value if value else "(vacía)"
            print(f"   ✓ {var:<35} = {display_value}")
        else:
            print(f"   ❌ {var:<35} = NO DEFINIDA ({description})")
            all_required_present = False
    
    print("\n📋 Variables opcionales:")
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value:
            print(f"   ✓ {var:<35} = {value}")
        else:
            print(f"   - {var:<35} = Por defecto ({description})")
    
    # Verificaciones específicas
    print("\n🔍 Verificaciones específicas:")
    
    # Verificar SECRET_KEY
    secret_key = os.getenv("SECRET_KEY")
    if secret_key:
        if len(secret_key) >= 32:
            print("   ✓ SECRET_KEY tiene longitud adecuada")
        else:
            print(f"   ⚠️ SECRET_KEY muy corta ({len(secret_key)} chars, recomendado: 32+)")
    
    # Verificar puerto
    port = os.getenv("PORT")
    if port and port.isdigit():
        port_num = int(port)
        if 1024 <= port_num <= 65535:
            print(f"   ✓ Puerto {port_num} está en rango válido")
        else:
            print(f"   ⚠️ Puerto {port_num} fuera de rango recomendado (1024-65535)")
    
    # Verificar configuración MySQL
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")
    if db_host and db_port:
        print(f"   ✓ MySQL configurado en {db_host}:{db_port}")
    
    print("\n" + "=" * 60)
    
    if all_required_present:
        print("🎉 ¡Configuración completa! Todas las variables requeridas están definidas.")
        print("\n📋 Próximos pasos:")
        print("   1. Verificar que MySQL esté ejecutándose")
        print("   2. Crear la base de datos: CREATE DATABASE yolo_annotator;")
        print("   3. Ejecutar la aplicación: python app_auth.py")
        return True
    else:
        print("❌ Configuración incompleta. Revisa las variables faltantes.")
        print("\n📋 Para solucionarlo:")
        print("   1. Edita el archivo .env")
        print("   2. Define todas las variables requeridas")
        print("   3. Ejecuta este script nuevamente para verificar")
        return False

def show_mysql_example():
    """Muestra un ejemplo de configuración MySQL"""
    
    print("\n" + "=" * 60)
    print("📋 Ejemplo de configuración MySQL para .env:")
    print("=" * 60)
    
    example_config = """
# Base de datos MySQL
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=tu_password_aqui
DB_NAME=yolo_annotator

# JWT Security (¡CAMBIAR EN PRODUCCIÓN!)
SECRET_KEY=mi-clave-super-secreta-jwt-para-produccion-12345678901234567890
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Servidor
HOST=127.0.0.1
PORT=8002
DEBUG=True
"""
    
    print(example_config)

if __name__ == "__main__":
    success = verify_env_config()
    
    if not success:
        show_mysql_example()
    
    print("\n🔧 Para más información consulta: manual/INSTALACION.md")

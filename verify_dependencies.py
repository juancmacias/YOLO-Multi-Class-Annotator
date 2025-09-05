#!/usr/bin/env python3
"""
Script de verificación de dependencias
Verifica que todas las dependencias estén correctamente instaladas
"""

def verify_imports():
    """Verificar que todas las dependencias se puedan importar"""
    dependencies = {
        # Framework Web
        'fastapi': 'FastAPI framework',
        'uvicorn': 'ASGI server',
        'jinja2': 'Template engine',
        
        # Procesamiento de imágenes
        'PIL': 'Python Imaging Library (Pillow)',
        'cv2': 'OpenCV computer vision',
        'numpy': 'Numerical operations',
        
        # Base de datos
        'sqlalchemy': 'SQL ORM',
        'pymysql': 'MySQL driver',
        'cryptography': 'Cryptographic operations',
        
        # Autenticación
        'jose': 'JWT tokens (python-jose)',
        'passlib': 'Password hashing',
        'pydantic': 'Data validation',
        
        # Utilidades
        'dotenv': 'Environment variables',
        'pandas': 'Data analysis',
    }
    
    print("🔍 Verificando dependencias...")
    print("=" * 50)
    
    success_count = 0
    total_count = len(dependencies)
    
    for module, description in dependencies.items():
        try:
            if module == 'PIL':
                import PIL
                from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
                version = PIL.__version__
            elif module == 'cv2':
                import cv2
                version = cv2.__version__
            elif module == 'jose':
                from jose import jwt
                import jose
                version = jose.__version__
            elif module == 'dotenv':
                from dotenv import load_dotenv
                import dotenv
                version = dotenv.__version__
            else:
                imported_module = __import__(module)
                version = getattr(imported_module, '__version__', 'N/A')
            
            print(f"✅ {module:<15} v{version:<10} - {description}")
            success_count += 1
            
        except ImportError as e:
            print(f"❌ {module:<15} {'ERROR':<10} - {description}")
            print(f"   Error: {e}")
        except Exception as e:
            print(f"⚠️  {module:<15} {'WARNING':<10} - {description}")
            print(f"   Warning: {e}")
    
    print("=" * 50)
    print(f"✅ Dependencias verificadas: {success_count}/{total_count}")
    
    if success_count == total_count:
        print("🎉 ¡Todas las dependencias están correctamente instaladas!")
        return True
    else:
        print("⚠️  Algunas dependencias faltan o tienen problemas")
        print("💡 Ejecuta: pip install -r requirements.txt")
        return False

def verify_optional_features():
    """Verificar características opcionales"""
    print("\n🔧 Verificando características adicionales...")
    print("=" * 50)
    
    # Verificar FastAPI features
    try:
        from fastapi import FastAPI, File, UploadFile
        from fastapi.responses import HTMLResponse, FileResponse
        from fastapi.templating import Jinja2Templates
        from fastapi.staticfiles import StaticFiles
        from fastapi.middleware.cors import CORSMiddleware
        print("✅ FastAPI completo - Todas las características disponibles")
    except ImportError:
        print("❌ FastAPI incompleto - Algunas características no disponibles")
    
    # Verificar OpenCV features
    try:
        import cv2
        import numpy as np
        # Crear imagen de prueba
        test_img = np.zeros((100, 100, 3), dtype=np.uint8)
        blurred = cv2.GaussianBlur(test_img, (5, 5), 0)
        print("✅ OpenCV completo - Augmentación de imágenes disponible")
    except Exception:
        print("❌ OpenCV incompleto - Problemas con augmentación")
    
    # Verificar MySQL connection
    try:
        import pymysql
        import sqlalchemy
        print("✅ MySQL driver - Conexión a base de datos disponible")
    except ImportError:
        print("❌ MySQL driver - Problemas de conexión a BD")

if __name__ == "__main__":
    print("🚀 YOLO Multi-Class Annotator - Verificación de Dependencias")
    print("=" * 60)
    
    # Verificar dependencias principales
    main_ok = verify_imports()
    
    # Verificar características opcionales
    verify_optional_features()
    
    print("\n" + "=" * 60)
    if main_ok:
        print("🎯 Sistema listo para ejecutar: python app_auth.py")
    else:
        print("🔧 Revisar instalación de dependencias antes de continuar")

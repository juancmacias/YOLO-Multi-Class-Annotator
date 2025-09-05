#!/usr/bin/env python3
"""
🚀 YOLO Multi-Class Annotator - Verificación de Supabase
========================================================
Script para verificar que la configuración de Supabase esté correcta
"""

import os
import sys
from pathlib import Path

def check_environment():
    """Verificar variables de entorno"""
    print("🔍 Verificando variables de entorno...")
    
    required_vars = [
        'SUPABASE_URL',
        'SUPABASE_ANON_KEY', 
        'DATABASE_URL',
        'SECRET_KEY'
    ]
    
    missing_vars = []
    configured_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        elif 'your-' in value or 'change-' in value:
            missing_vars.append(f"{var} (tiene valor de ejemplo)")
        else:
            configured_vars.append(var)
    
    if configured_vars:
        print(f"✅ Variables configuradas: {', '.join(configured_vars)}")
    
    if missing_vars:
        print(f"❌ Variables faltantes o con valores de ejemplo:")
        for var in missing_vars:
            print(f"   - {var}")
        return False
    
    print("✅ Todas las variables de entorno están configuradas")
    return True

def check_files():
    """Verificar que los archivos necesarios existen"""
    print("\n📁 Verificando archivos...")
    
    files_to_check = [
        'supabase_setup.sql',
        'app-jwt/auth/models.py',
        '.env.supabase.template'
    ]
    
    missing_files = []
    existing_files = []
    
    for file_path in files_to_check:
        if Path(file_path).exists():
            existing_files.append(file_path)
        else:
            missing_files.append(file_path)
    
    if existing_files:
        print(f"✅ Archivos encontrados: {', '.join(existing_files)}")
    
    if missing_files:
        print(f"❌ Archivos faltantes: {', '.join(missing_files)}")
        return False
    
    print("✅ Todos los archivos necesarios están presentes")
    return True

def check_dependencies():
    """Verificar dependencias Python"""
    print("\n📦 Verificando dependencias...")
    
    dependencies = {
        'sqlalchemy': 'SQLAlchemy',
        'psycopg2': 'psycopg2-binary', 
        'dotenv': 'python-dotenv',
        'fastapi': 'FastAPI',
        'uvicorn': 'Uvicorn'
    }
    
    installed = []
    missing = []
    
    for module, package in dependencies.items():
        try:
            __import__(module)
            installed.append(package)
        except ImportError:
            missing.append(package)
    
    if installed:
        print(f"✅ Dependencias instaladas: {', '.join(installed)}")
    
    if missing:
        print(f"❌ Dependencias faltantes: {', '.join(missing)}")
        print("   Instalar con: pip install " + " ".join(missing))
        return False
    
    print("✅ Todas las dependencias están instaladas")
    return True

def test_database_connection():
    """Probar conexión a la base de datos"""
    print("\n🔌 Probando conexión a Supabase...")
    
    try:
        from sqlalchemy import create_engine
        
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL no configurada")
            return False
        
        if 'your-' in database_url:
            print("❌ DATABASE_URL tiene valores de ejemplo")
            return False
        
        # Crear engine con timeout corto para prueba rápida
        engine = create_engine(
            database_url,
            pool_pre_ping=True,
            connect_args={'connect_timeout': 10}
        )
        
        # Probar conexión
        with engine.connect() as conn:
            result = conn.execute("SELECT 1").scalar()
            if result == 1:
                print("✅ Conexión a Supabase exitosa!")
                return True
        
        print("❌ Conexión fallida - respuesta inesperada")
        return False
        
    except ImportError as e:
        print(f"❌ Error importando dependencias: {e}")
        return False
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

def check_supabase_project():
    """Verificar configuración del proyecto Supabase"""
    print("\n🏗️ Verificando proyecto Supabase...")
    
    supabase_url = os.getenv('SUPABASE_URL')
    anon_key = os.getenv('SUPABASE_ANON_KEY')
    
    if not supabase_url or not anon_key:
        print("❌ URL o clave de Supabase no configuradas")
        return False
    
    if 'your-' in supabase_url or 'your-' in anon_key:
        print("❌ URL o clave tienen valores de ejemplo")
        return False
    
    try:
        import requests
        
        # Probar endpoint de health check
        response = requests.get(
            f"{supabase_url}/rest/v1/",
            headers={
                'apikey': anon_key,
                'Authorization': f'Bearer {anon_key}'
            },
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Proyecto Supabase accesible!")
            return True
        else:
            print(f"❌ Error HTTP {response.status_code} al acceder a Supabase")
            return False
            
    except ImportError:
        print("⚠️  requests no instalado - saltando verificación de API")
        print("   Instalar con: pip install requests")
        return True  # No falla la verificación completa
    except Exception as e:
        print(f"❌ Error verificando proyecto: {e}")
        return False

def show_next_steps():
    """Mostrar próximos pasos según el estado"""
    print("\n📋 PRÓXIMOS PASOS:")
    print("=" * 50)
    
    print("1. 📄 Ejecutar script SQL:")
    print("   - Ve a tu proyecto Supabase > SQL Editor")
    print("   - Copia y pega el contenido de 'supabase_setup.sql'")
    print("   - Ejecuta el script")
    
    print("\n2. 🔧 Configurar aplicación:")
    print("   - Copia '.env.supabase.template' a 'app-jwt/.env'")
    print("   - Reemplaza valores de ejemplo con tus credenciales")
    
    print("\n3. 🏃 Ejecutar aplicación:")
    print("   cd app-jwt")
    print("   python app_auth.py")
    
    print("\n4. 🧪 Probar funcionalidad:")
    print("   - Registrar usuario")
    print("   - Crear sesión")
    print("   - Verificar datos en Supabase dashboard")

def main():
    """Función principal"""
    print("🚀 YOLO Multi-Class Annotator - Verificación de Supabase")
    print("=" * 60)
    
    # Cargar variables de entorno si existe .env
    env_path = Path('app-jwt/.env')
    if env_path.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(env_path)
            print(f"📝 Cargando variables desde {env_path}")
        except ImportError:
            print("⚠️  python-dotenv no instalado - usando variables del sistema")
    else:
        print("📝 Archivo .env no encontrado - usando variables del sistema")
    
    # Ejecutar verificaciones
    checks = [
        ("Archivos", check_files),
        ("Variables de entorno", check_environment), 
        ("Dependencias Python", check_dependencies),
        ("Conexión a base de datos", test_database_connection),
        ("Proyecto Supabase", check_supabase_project)
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Error en verificación de {name}: {e}")
            results.append((name, False))
    
    # Resumen
    print("\n📊 RESUMEN DE VERIFICACIÓN:")
    print("=" * 30)
    
    passed = 0
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
        if result:
            passed += 1
    
    print(f"\nResultado: {passed}/{total} verificaciones pasadas")
    
    if passed == total:
        print("\n🎉 ¡Todo listo! Tu configuración de Supabase está completa.")
        print("   Puedes proceder a ejecutar la aplicación.")
    elif passed >= total - 1:
        print("\n⚠️  Casi listo. Revisa las verificaciones fallidas.")
    else:
        print("\n❌ Configuración incompleta. Revisa los errores arriba.")
        show_next_steps()
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

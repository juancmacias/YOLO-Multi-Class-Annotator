#!/usr/bin/env python3
"""
YOLO Multi-Class Annotator - Database Migration Setup Script
============================================================
Script automático para configurar dependencias y opciones de base de datos
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path

def print_header(text):
    """Imprimir header con formato"""
    print("\n" + "="*60)
    print(f"🚀 {text}")
    print("="*60)

def print_step(step, text):
    """Imprimir paso con formato"""
    print(f"\n📋 Paso {step}: {text}")

def run_command(command, description=""):
    """Ejecutar comando y manejar errores"""
    try:
        if description:
            print(f"   ⏳ {description}...")
        
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"   ✅ {description or 'Comando'} completado")
            return True
        else:
            print(f"   ❌ Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False

def check_python_version():
    """Verificar versión de Python"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ requerido")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True

def install_base_dependencies():
    """Instalar dependencias básicas"""
    print_step(1, "Instalando dependencias básicas")
    
    base_packages = [
        "sqlalchemy>=1.4.0",
        "python-multipart",
        "python-jose[cryptography]",
        "passlib[bcrypt]",
        "uvicorn[standard]",
        "fastapi",
        "jinja2"
    ]
    
    for package in base_packages:
        success = run_command(f"pip install {package}", f"Instalando {package}")
        if not success:
            return False
    
    return True

def install_postgresql_dependencies():
    """Instalar dependencias para PostgreSQL/Supabase"""
    print_step(2, "Instalando dependencias de PostgreSQL/Supabase")
    
    packages = [
        "psycopg2-binary",
        "supabase"
    ]
    
    for package in packages:
        success = run_command(f"pip install {package}", f"Instalando {package}")
        if not success:
            print(f"   ⚠️  Error instalando {package} - puede necesitar compilación manual")
            return False
    
    return True

def install_sqlserver_dependencies():
    """Instalar dependencias para SQL Server"""
    print_step(3, "Instalando dependencias de SQL Server")
    
    # Instalar pyodbc
    success = run_command("pip install pyodbc", "Instalando pyodbc")
    if not success:
        return False
    
    # Verificar/instalar ODBC Driver según el sistema
    system = platform.system().lower()
    
    if system == "windows":
        print("   💡 En Windows: Descargar ODBC Driver 17 desde Microsoft")
        print("   📁 URL: https://docs.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server")
        
    elif system == "linux":
        print("   💡 Para Ubuntu/Debian:")
        print("   📦 sudo apt-get update")
        print("   📦 sudo apt-get install msodbcsql17")
        
        # Intentar instalación automática en Ubuntu
        distro = subprocess.run("lsb_release -si", shell=True, capture_output=True, text=True)
        if "ubuntu" in distro.stdout.lower():
            print("   🔄 Intentando instalación automática...")
            commands = [
                "curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -",
                "curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list | sudo tee /etc/apt/sources.list.d/msprod.list",
                "sudo apt-get update",
                "sudo ACCEPT_EULA=Y apt-get install -y msodbcsql17"
            ]
            
            for cmd in commands:
                run_command(cmd, "Configurando repositorio Microsoft")
                
    elif system == "darwin":  # macOS
        print("   💡 Para macOS:")
        print("   🍺 brew install msodbcsql17")
        
        # Intentar instalación con Homebrew
        if shutil.which("brew"):
            run_command("brew install msodbcsql17", "Instalando ODBC Driver con Homebrew")
        else:
            print("   ⚠️  Homebrew no encontrado - instalar manualmente")
    
    return True

def create_config_templates():
    """Crear templates de configuración"""
    print_step(4, "Creando templates de configuración")
    
    # Template general
    env_template = """# YOLO Multi-Class Annotator Configuration
# ========================================

# JWT Configuration
SECRET_KEY=your-super-secret-jwt-key-here-change-this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database Selection (uncomment one)
# DATABASE_TYPE=sqlite    # Default - current setup
# DATABASE_TYPE=postgresql # For Supabase
# DATABASE_TYPE=sqlserver  # For SQL Server

# SQLite Configuration (current)
DATABASE_URL=sqlite:///./users.db

# ========================================
# PostgreSQL/Supabase Configuration
# ========================================
# SUPABASE_URL=https://your-project.supabase.co
# SUPABASE_KEY=your-anon-key-here
# SUPABASE_SERVICE_KEY=your-service-role-key-here

# ========================================
# SQL Server Configuration
# ========================================
# SQL_SERVER_HOST=localhost
# SQL_SERVER_PORT=1433
# SQL_SERVER_DATABASE=YOLOAnnotator
# SQL_SERVER_USERNAME=sa
# SQL_SERVER_PASSWORD=your-password-here

# For Azure SQL Database
# USE_AZURE_SQL=false
# AZURE_SQL_SERVER=your-server.database.windows.net
# AZURE_SQL_DATABASE=YOLOAnnotator
# AZURE_SQL_USERNAME=your-username
# AZURE_SQL_PASSWORD=your-password

# SQL Server Authentication
# USE_WINDOWS_AUTH=false
# SQL_SERVER_DRIVER=ODBC Driver 17 for SQL Server
"""
    
    with open(".env.template", "w") as f:
        f.write(env_template)
    
    print("   ✅ .env.template creado")
    
    # Crear .env si no existe
    if not os.path.exists(".env"):
        with open(".env", "w") as f:
            f.write(env_template)
        print("   ✅ .env creado (configurar antes de usar)")
    else:
        print("   ℹ️  .env ya existe - no sobreescribiendo")
    
    return True

def create_database_selector():
    """Crear script selector de base de datos"""
    print_step(5, "Creando script selector de base de datos")
    
    selector_script = '''#!/usr/bin/env python3
"""
Database Selector for YOLO Multi-Class Annotator
Utility script to switch between database configurations
"""

import os
import sys
from pathlib import Path

def select_database():
    """Interactive database selection"""
    print("🗄️  YOLO Annotator - Selector de Base de Datos")
    print("="*50)
    print("1. SQLite (actual - local)")
    print("2. PostgreSQL/Supabase (cloud)")
    print("3. SQL Server (enterprise)")
    print("4. Mostrar configuración actual")
    print("5. Salir")
    
    choice = input("\\nSelecciona una opción (1-5): ")
    
    if choice == "1":
        configure_sqlite()
    elif choice == "2":
        configure_postgresql()
    elif choice == "3":
        configure_sqlserver()
    elif choice == "4":
        show_current_config()
    elif choice == "5":
        print("👋 ¡Hasta luego!")
        sys.exit(0)
    else:
        print("❌ Opción inválida")
        select_database()

def configure_sqlite():
    """Configure SQLite"""
    print("\\n📁 Configurando SQLite...")
    update_env("DATABASE_TYPE", "sqlite")
    update_env("DATABASE_URL", "sqlite:///./users.db")
    print("✅ SQLite configurado")
    
    # Update app imports
    update_app_imports("sqlite")

def configure_postgresql():
    """Configure PostgreSQL/Supabase"""
    print("\\n🌐 Configurando PostgreSQL/Supabase...")
    
    url = input("Supabase URL: ")
    key = input("Supabase Anon Key: ")
    service_key = input("Supabase Service Key (opcional): ")
    
    update_env("DATABASE_TYPE", "postgresql")
    update_env("SUPABASE_URL", url)
    update_env("SUPABASE_KEY", key)
    if service_key:
        update_env("SUPABASE_SERVICE_KEY", service_key)
    
    print("✅ PostgreSQL/Supabase configurado")
    
    # Update app imports
    update_app_imports("postgresql")

def configure_sqlserver():
    """Configure SQL Server"""
    print("\\n🏢 Configurando SQL Server...")
    
    use_azure = input("¿Usar Azure SQL? (y/n): ").lower() == 'y'
    
    if use_azure:
        server = input("Azure SQL Server (sin .database.windows.net): ")
        database = input("Database name: ")
        username = input("Username: ")
        password = input("Password: ")
        
        update_env("DATABASE_TYPE", "sqlserver")
        update_env("USE_AZURE_SQL", "true")
        update_env("AZURE_SQL_SERVER", f"{server}.database.windows.net")
        update_env("AZURE_SQL_DATABASE", database)
        update_env("AZURE_SQL_USERNAME", username)
        update_env("AZURE_SQL_PASSWORD", password)
    else:
        host = input("SQL Server Host (localhost): ") or "localhost"
        database = input("Database name (YOLOAnnotator): ") or "YOLOAnnotator"
        username = input("Username (sa): ") or "sa"
        password = input("Password: ")
        
        update_env("DATABASE_TYPE", "sqlserver")
        update_env("USE_AZURE_SQL", "false")
        update_env("SQL_SERVER_HOST", host)
        update_env("SQL_SERVER_DATABASE", database)
        update_env("SQL_SERVER_USERNAME", username)
        update_env("SQL_SERVER_PASSWORD", password)
    
    print("✅ SQL Server configurado")
    
    # Update app imports
    update_app_imports("sqlserver")

def update_env(key, value):
    """Update .env file"""
    env_path = Path(".env")
    
    if not env_path.exists():
        with open(env_path, "w") as f:
            f.write(f"{key}={value}\\n")
        return
    
    lines = []
    updated = False
    
    with open(env_path, "r") as f:
        for line in f:
            if line.startswith(f"{key}=") or line.startswith(f"#{key}="):
                lines.append(f"{key}={value}\\n")
                updated = True
            else:
                lines.append(line)
    
    if not updated:
        lines.append(f"{key}={value}\\n")
    
    with open(env_path, "w") as f:
        f.writelines(lines)

def update_app_imports(db_type):
    """Update app imports based on database type"""
    
    import_map = {
        "sqlite": "from auth.database import get_db",
        "postgresql": "from auth.database_supabase import get_db", 
        "sqlserver": "from auth.database_sqlserver import get_db"
    }
    
    app_files = ["app_auth.py", "app_simple.py"]
    
    for app_file in app_files:
        if os.path.exists(app_file):
            print(f"   📝 Actualizando imports en {app_file}")
            
            with open(app_file, "r") as f:
                content = f.read()
            
            # Replace import lines
            for db, import_line in import_map.items():
                content = content.replace(import_map[db], import_map[db_type])
            
            with open(app_file, "w") as f:
                f.write(content)

def show_current_config():
    """Show current configuration"""
    print("\\n📋 Configuración Actual:")
    print("-" * 30)
    
    env_path = Path(".env")
    if not env_path.exists():
        print("❌ Archivo .env no encontrado")
        return
    
    relevant_keys = [
        "DATABASE_TYPE", "DATABASE_URL", "SUPABASE_URL", 
        "SQL_SERVER_HOST", "AZURE_SQL_SERVER", "USE_AZURE_SQL"
    ]
    
    with open(env_path, "r") as f:
        for line in f:
            for key in relevant_keys:
                if line.startswith(f"{key}="):
                    value = line.split("=", 1)[1].strip()
                    # Hide passwords
                    if "PASSWORD" in key and value:
                        value = "*" * len(value)
                    print(f"{key}: {value}")

if __name__ == "__main__":
    select_database()
'''
    
    with open("select_database.py", "w") as f:
        f.write(selector_script)
    
    # Make executable on Unix systems
    if os.name != 'nt':
        os.chmod("select_database.py", 0o755)
    
    print("   ✅ select_database.py creado")
    return True

def run_tests():
    """Ejecutar tests básicos"""
    print_step(6, "Ejecutando tests básicos")
    
    # Test basic imports
    try:
        import sqlalchemy
        print("   ✅ SQLAlchemy importado correctamente")
    except ImportError:
        print("   ❌ Error importando SQLAlchemy")
        return False
    
    # Test database connection (current)
    try:
        from auth.database import test_connection
        if test_connection():
            print("   ✅ Conexión a SQLite funcional")
        else:
            print("   ⚠️  Conexión a SQLite con problemas")
    except Exception as e:
        print(f"   ❌ Error probando SQLite: {e}")
    
    return True

def create_requirements_update():
    """Crear requirements.txt actualizado"""
    print_step(7, "Actualizando requirements.txt")
    
    requirements = """# YOLO Multi-Class Annotator - Database Migration Ready
# Core FastAPI dependencies
fastapi>=0.68.0
uvicorn[standard]>=0.15.0
python-multipart>=0.0.5
jinja2>=3.0.0

# Authentication
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4

# Database - Core
sqlalchemy>=1.4.0

# Database - PostgreSQL/Supabase
psycopg2-binary>=2.9.0
supabase>=1.0.0

# Database - SQL Server
pyodbc>=4.0.0

# Image processing and augmentation
opencv-python>=4.5.0
Pillow>=8.0.0
numpy>=1.21.0

# File handling
python-dotenv>=0.19.0

# Development (optional)
pytest>=6.0.0
black>=21.0.0
flake8>=3.9.0

# Notes:
# - psycopg2-binary: Para PostgreSQL/Supabase
# - pyodbc: Para SQL Server (requiere ODBC Driver instalado)
# - supabase: Cliente oficial de Supabase
# - Todas las dependencias de SQLite ya están incluidas en Python
"""
    
    with open("requirements_database.txt", "w") as f:
        f.write(requirements)
    
    print("   ✅ requirements_database.txt creado")
    
    # Backup current requirements if exists
    if os.path.exists("requirements.txt"):
        shutil.copy("requirements.txt", "requirements_backup.txt")
        print("   ✅ requirements.txt respaldado como requirements_backup.txt")
    
    # Ask if user wants to update current requirements
    update = input("   ❓ ¿Actualizar requirements.txt actual? (y/n): ")
    if update.lower() == 'y':
        shutil.copy("requirements_database.txt", "requirements.txt")
        print("   ✅ requirements.txt actualizado")
    
    return True

def main():
    """Main setup function"""
    print_header("YOLO Multi-Class Annotator - Database Migration Setup")
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    print("Este script configurará las dependencias para migración de base de datos.")
    print("Opciones disponibles:")
    print("  🗄️  SQLite (actual)")
    print("  🌐 PostgreSQL/Supabase (cloud)")
    print("  🏢 SQL Server (enterprise)")
    
    continue_setup = input("\n¿Continuar con la configuración? (y/n): ")
    if continue_setup.lower() != 'y':
        print("👋 Setup cancelado")
        sys.exit(0)
    
    # Select what to install
    print("\n📦 ¿Qué dependencias instalar?")
    print("1. Solo dependencias básicas")
    print("2. Básicas + PostgreSQL/Supabase")
    print("3. Básicas + SQL Server")
    print("4. Todas las dependencias")
    
    choice = input("Selecciona (1-4): ")
    
    # Install base dependencies
    if not install_base_dependencies():
        print("❌ Error en dependencias básicas")
        sys.exit(1)
    
    # Install specific dependencies
    if choice in ["2", "4"]:
        install_postgresql_dependencies()
    
    if choice in ["3", "4"]:
        install_sqlserver_dependencies()
    
    # Create configuration files
    create_config_templates()
    create_database_selector()
    create_requirements_update()
    
    # Run basic tests
    run_tests()
    
    # Final instructions
    print_header("Setup Completado")
    print("✅ Dependencias instaladas")
    print("✅ Templates de configuración creados")
    print("✅ Script selector de BD creado")
    print("✅ Requirements actualizados")
    
    print("\n📋 Próximos pasos:")
    print("1. Ejecutar: python select_database.py")
    print("2. Configurar credenciales en .env")
    print("3. Ejecutar scripts SQL según la BD elegida")
    print("4. Probar la aplicación: python app_auth.py")
    
    print("\n📚 Documentación:")
    print("   - MIGRACION_DATABASE.md")
    print("   - supabase_setup.sql (para Supabase)")
    print("   - sqlserver_setup.sql (para SQL Server)")
    
    print("\n🎉 ¡Listo para migrar!")

if __name__ == "__main__":
    main()

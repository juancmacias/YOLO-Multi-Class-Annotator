# ========================================================
# YOLO Multi-Class Annotator - Supabase Configuration
# ========================================================
# Archivo de configuración para migrar de SQLite a Supabase
# ========================================================

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

# ========================================================
# CONFIGURACIÓN DE SUPABASE
# ========================================================

# Variables de entorno necesarias para Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://your-project.supabase.co")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "your-anon-key")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "your-service-key")

# URL de conexión a PostgreSQL de Supabase
# Formato: postgresql://postgres:[password]@[host]:[port]/[database]
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:your-password@db.your-project.supabase.co:5432/postgres"
)

# Configuración alternativa usando componentes separados
DB_HOST = os.getenv("DB_HOST", "db.your-project.supabase.co")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "your-password")

# Construir URL si no se proporciona DATABASE_URL completa
if not os.getenv("DATABASE_URL"):
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# ========================================================
# CONFIGURACIÓN DE SQLALCHEMY PARA POSTGRESQL
# ========================================================

# Crear engine para PostgreSQL (diferente configuración que SQLite)
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verificar conexiones antes de usar
    pool_recycle=300,    # Reciclar conexiones cada 5 minutos
    pool_size=10,        # Número máximo de conexiones persistentes
    max_overflow=20,     # Conexiones adicionales permitidas
    echo=False           # Cambiar a True para debug SQL
)

# Crear SessionLocal
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ========================================================
# DEPENDENCY FUNCTIONS
# ========================================================

def get_db():
    """Dependency para obtener sesión de DB"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Crear todas las tablas (usar solo para desarrollo/testing)"""
    Base.metadata.create_all(bind=engine)

def test_connection():
    """Probar conexión a la base de datos"""
    try:
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            print("✅ Conexión a Supabase exitosa!")
            return True
    except Exception as e:
        print(f"❌ Error de conexión a Supabase: {e}")
        return False

# ========================================================
# CONFIGURACIÓN PARA SUPABASE CLIENT (OPCIONAL)
# ========================================================

try:
    from supabase import create_client, Client
    
    def get_supabase_client() -> Client:
        """Crear cliente de Supabase para operaciones adicionales"""
        return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    
    def get_supabase_admin_client() -> Client:
        """Crear cliente de Supabase con permisos de servicio"""
        return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    
except ImportError:
    print("⚠️  Supabase client no instalado. Instalar con: pip install supabase")
    
    def get_supabase_client():
        raise ImportError("Supabase client no disponible")
    
    def get_supabase_admin_client():
        raise ImportError("Supabase client no disponible")

# ========================================================
# FUNCIONES DE MIGRACIÓN
# ========================================================

def migrate_from_sqlite(sqlite_db_path="./users.db"):
    """
    Migrar datos desde SQLite a Supabase
    USAR CON PRECAUCIÓN - Esta función transfiere todos los datos
    """
    import sqlite3
    from sqlalchemy.orm import Session
    from .models import User, UserSession, TokenBlacklist
    
    try:
        # Conectar a SQLite
        sqlite_conn = sqlite3.connect(sqlite_db_path)
        sqlite_conn.row_factory = sqlite3.Row
        
        # Crear sesión de PostgreSQL
        db: Session = SessionLocal()
        
        print("🔄 Iniciando migración de datos...")
        
        # Migrar usuarios
        users_cursor = sqlite_conn.execute("SELECT * FROM users")
        users_migrated = 0
        
        for row in users_cursor:
            existing_user = db.query(User).filter(User.username == row['username']).first()
            if not existing_user:
                user = User(
                    username=row['username'],
                    email=row['email'],
                    hashed_password=row['hashed_password'],
                    is_active=row['is_active'],
                    is_admin=row['is_admin'],
                    created_at=row['created_at']
                )
                db.add(user)
                users_migrated += 1
        
        db.commit()
        print(f"✅ Usuarios migrados: {users_migrated}")
        
        # Migrar sesiones de usuario
        sessions_cursor = sqlite_conn.execute("SELECT * FROM user_sessions")
        sessions_migrated = 0
        
        for row in sessions_cursor:
            existing_session = db.query(UserSession).filter(
                UserSession.session_name == row['session_name'],
                UserSession.user_id == row['user_id']
            ).first()
            
            if not existing_session:
                session = UserSession(
                    session_name=row['session_name'],
                    user_id=row['user_id'],
                    created_at=row['created_at'],
                    is_active=row['is_active']
                )
                db.add(session)
                sessions_migrated += 1
        
        db.commit()
        print(f"✅ Sesiones migradas: {sessions_migrated}")
        
        # Migrar blacklist de tokens (opcional, pueden estar expirados)
        try:
            tokens_cursor = sqlite_conn.execute("SELECT * FROM token_blacklist")
            tokens_migrated = 0
            
            for row in tokens_cursor:
                existing_token = db.query(TokenBlacklist).filter(
                    TokenBlacklist.token == row['token']
                ).first()
                
                if not existing_token:
                    token = TokenBlacklist(
                        token=row['token'],
                        blacklisted_at=row['blacklisted_at']
                    )
                    db.add(token)
                    tokens_migrated += 1
            
            db.commit()
            print(f"✅ Tokens migrados: {tokens_migrated}")
            
        except Exception as e:
            print(f"⚠️  Error migrando tokens (puede ser normal): {e}")
        
        print("🎉 Migración completada exitosamente!")
        
    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
        db.rollback()
        raise
    
    finally:
        sqlite_conn.close()
        db.close()

# ========================================================
# CONFIGURACIÓN DE VARIABLES DE ENTORNO
# ========================================================

def setup_env_template():
    """Crear archivo .env template para Supabase"""
    env_template = """
# ========================================================
# SUPABASE CONFIGURATION
# ========================================================

# URL de tu proyecto Supabase
SUPABASE_URL=https://your-project-id.supabase.co

# Clave anónima de Supabase (public)
SUPABASE_ANON_KEY=your-anon-key-here

# Clave de servicio de Supabase (private - solo servidor)
SUPABASE_SERVICE_KEY=your-service-key-here

# URL completa de conexión PostgreSQL
DATABASE_URL=postgresql://postgres:your-password@db.your-project-id.supabase.co:5432/postgres

# O usar componentes separados:
DB_HOST=db.your-project-id.supabase.co
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your-password-here

# ========================================================
# JWT CONFIGURATION (mantener configuración actual)
# ========================================================

SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# ========================================================
# NOTAS:
# 1. Reemplaza 'your-project-id' con tu ID real de Supabase
# 2. Obtén las claves desde: Settings > API en tu dashboard de Supabase
# 3. La contraseña de DB está en: Settings > Database
# 4. Nunca commitees este archivo con credenciales reales
# ========================================================
"""
    
    with open(".env.supabase.template", "w") as f:
        f.write(env_template)
    
    print("📝 Archivo .env.supabase.template creado!")
    print("   1. Cópialo a .env")
    print("   2. Reemplaza los valores con tus credenciales reales de Supabase")

# ========================================================
# TESTING FUNCTIONS
# ========================================================

def run_database_tests():
    """Ejecutar tests básicos de la base de datos"""
    print("🧪 Ejecutando tests de base de datos...")
    
    # Test 1: Conexión
    if not test_connection():
        return False
    
    # Test 2: Crear tablas
    try:
        create_tables()
        print("✅ Tablas creadas/verificadas")
    except Exception as e:
        print(f"❌ Error creando tablas: {e}")
        return False
    
    # Test 3: CRUD básico
    try:
        db = SessionLocal()
        
        # Test INSERT
        test_user = User(
            username=f"test_user_{os.urandom(4).hex()}",
            email=f"test_{os.urandom(4).hex()}@test.com",
            hashed_password="test_hash",
            is_admin=False
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        # Test SELECT
        found_user = db.query(User).filter(User.id == test_user.id).first()
        assert found_user is not None
        
        # Test UPDATE
        found_user.is_active = False
        db.commit()
        
        # Test DELETE
        db.delete(found_user)
        db.commit()
        
        print("✅ CRUD operations funcionando")
        db.close()
        
    except Exception as e:
        print(f"❌ Error en CRUD tests: {e}")
        return False
    
    print("🎉 Todos los tests pasaron!")
    return True

if __name__ == "__main__":
    print("🚀 YOLO Annotator - Configuración de Supabase")
    print("="*50)
    
    # Crear template de variables de entorno
    setup_env_template()
    
    # Probar conexión si las variables están configuradas
    if os.getenv("DATABASE_URL") and "your-" not in os.getenv("DATABASE_URL", ""):
        print("\n🔍 Probando conexión...")
        if test_connection():
            print("\n🧪 Ejecutando tests...")
            run_database_tests()
    else:
        print("\n⚠️  Configura las variables de entorno antes de probar la conexión")
        print("   Usa el archivo .env.supabase.template como referencia")

# ========================================================
# YOLO Multi-Class Annotator - SQL Server Configuration
# ========================================================
# Archivo de configuración para usar SQL Server
# Compatible con: SQL Server 2019+, Azure SQL Database
# ========================================================

import os
import urllib.parse
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine
from .models import Base

# ========================================================
# CONFIGURACIÓN DE SQL SERVER
# ========================================================

# Variables de entorno para SQL Server
SQL_SERVER_HOST = os.getenv("SQL_SERVER_HOST", "localhost")
SQL_SERVER_PORT = os.getenv("SQL_SERVER_PORT", "1433")
SQL_SERVER_DATABASE = os.getenv("SQL_SERVER_DATABASE", "YOLOAnnotator")
SQL_SERVER_USERNAME = os.getenv("SQL_SERVER_USERNAME", "sa")
SQL_SERVER_PASSWORD = os.getenv("SQL_SERVER_PASSWORD", "")

# Configuración para Azure SQL Database
AZURE_SQL_SERVER = os.getenv("AZURE_SQL_SERVER", "")  # nombre.database.windows.net
AZURE_SQL_DATABASE = os.getenv("AZURE_SQL_DATABASE", "")
AZURE_SQL_USERNAME = os.getenv("AZURE_SQL_USERNAME", "")
AZURE_SQL_PASSWORD = os.getenv("AZURE_SQL_PASSWORD", "")

# Opciones de conexión
USE_AZURE_SQL = os.getenv("USE_AZURE_SQL", "false").lower() == "true"
USE_WINDOWS_AUTH = os.getenv("USE_WINDOWS_AUTH", "false").lower() == "true"
SQL_SERVER_DRIVER = os.getenv("SQL_SERVER_DRIVER", "ODBC Driver 17 for SQL Server")

# ========================================================
# CONSTRUCCIÓN DE CADENA DE CONEXIÓN
# ========================================================

def build_connection_string():
    """Construir cadena de conexión según configuración"""
    
    if USE_AZURE_SQL:
        # Configuración para Azure SQL Database
        if not all([AZURE_SQL_SERVER, AZURE_SQL_DATABASE, AZURE_SQL_USERNAME, AZURE_SQL_PASSWORD]):
            raise ValueError("Variables de Azure SQL Database incompletas")
        
        server = AZURE_SQL_SERVER
        database = AZURE_SQL_DATABASE
        username = AZURE_SQL_USERNAME
        password = AZURE_SQL_PASSWORD
        
        # Parámetros específicos para Azure SQL
        params = {
            'driver': SQL_SERVER_DRIVER,
            'Encrypt': 'yes',
            'TrustServerCertificate': 'no',
            'Connection Timeout': '30',
        }
        
    else:
        # Configuración para SQL Server on-premise
        server = f"{SQL_SERVER_HOST},{SQL_SERVER_PORT}" if SQL_SERVER_PORT != "1433" else SQL_SERVER_HOST
        database = SQL_SERVER_DATABASE
        
        if USE_WINDOWS_AUTH:
            # Autenticación Windows
            params = {
                'driver': SQL_SERVER_DRIVER,
                'Trusted_Connection': 'yes',
            }
            connection_string = f"mssql+pyodbc://{server}/{database}"
        else:
            # Autenticación SQL Server
            if not SQL_SERVER_PASSWORD:
                raise ValueError("SQL_SERVER_PASSWORD requerida para autenticación SQL")
                
            username = SQL_SERVER_USERNAME
            password = SQL_SERVER_PASSWORD
            
            params = {
                'driver': SQL_SERVER_DRIVER,
                'TrustServerCertificate': 'yes',
            }
    
    # Construir cadena de conexión
    if USE_WINDOWS_AUTH and not USE_AZURE_SQL:
        connection_string = f"mssql+pyodbc://{server}/{database}"
    else:
        # URL encode password para caracteres especiales
        encoded_password = urllib.parse.quote_plus(password)
        connection_string = f"mssql+pyodbc://{username}:{encoded_password}@{server}/{database}"
    
    # Agregar parámetros de conexión
    if params:
        params_string = urllib.parse.urlencode(params)
        connection_string += f"?{params_string}"
    
    return connection_string

# ========================================================
# CONFIGURACIÓN DE SQLALCHEMY
# ========================================================

# Obtener cadena de conexión
try:
    DATABASE_URL = build_connection_string()
except Exception as e:
    print(f"❌ Error construyendo cadena de conexión: {e}")
    DATABASE_URL = None

# Crear engine para SQL Server
if DATABASE_URL:
    engine = create_engine(
        DATABASE_URL,
        # Configuraciones específicas para SQL Server
        pool_pre_ping=True,          # Verificar conexiones antes de usar
        pool_recycle=3600,           # Reciclar conexiones cada hora
        pool_size=10,                # Número de conexiones en el pool
        max_overflow=20,             # Conexiones adicionales permitidas
        pool_timeout=30,             # Timeout para obtener conexión del pool
        echo=False,                  # Cambiar a True para debug SQL
        
        # Configuraciones específicas para SQL Server
        connect_args={
            "timeout": 30,
            "autocommit": False,
        }
    )
    
    # Event listener para configurar la sesión SQL Server
    @event.listens_for(Engine, "connect")
    def set_sql_server_settings(dbapi_connection, connection_record):
        """Configurar settings específicos de SQL Server al conectar"""
        with dbapi_connection.cursor() as cursor:
            # Configurar formato de fecha
            cursor.execute("SET DATEFORMAT ymd")
            # Configurar comportamiento de transacciones
            cursor.execute("SET IMPLICIT_TRANSACTIONS OFF")
            # Configurar configuración numérica
            cursor.execute("SET NUMERIC_ROUNDABORT OFF")
            # Configurar warnings
            cursor.execute("SET ANSI_WARNINGS ON")
else:
    engine = None

# Crear SessionLocal
if engine:
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
else:
    SessionLocal = None

# ========================================================
# DEPENDENCY FUNCTIONS
# ========================================================

def get_db():
    """Dependency para obtener sesión de DB"""
    if not SessionLocal:
        raise RuntimeError("Base de datos no configurada correctamente")
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Crear todas las tablas (usar solo para desarrollo/testing)"""
    if not engine:
        raise RuntimeError("Engine no configurado")
    Base.metadata.create_all(bind=engine)

def test_connection():
    """Probar conexión a la base de datos"""
    if not engine:
        print("❌ Engine no configurado")
        return False
    
    try:
        with engine.connect() as conn:
            result = conn.execute("SELECT 1 as test").scalar()
            if result == 1:
                print("✅ Conexión a SQL Server exitosa!")
                
                # Información adicional del servidor
                server_info = conn.execute("""
                    SELECT 
                        @@VERSION as Version,
                        @@SERVERNAME as ServerName,
                        DB_NAME() as DatabaseName,
                        GETDATE() as CurrentTime
                """).fetchone()
                
                print(f"📊 Servidor: {server_info.ServerName}")
                print(f"📊 Base de datos: {server_info.DatabaseName}")
                print(f"📊 Versión: {server_info.Version.split(' - ')[0]}")
                
                return True
        
    except Exception as e:
        print(f"❌ Error de conexión a SQL Server: {e}")
        return False

# ========================================================
# FUNCIONES ESPECÍFICAS DE SQL SERVER
# ========================================================

def execute_stored_procedure(proc_name, params=None):
    """Ejecutar stored procedure"""
    if not engine:
        raise RuntimeError("Engine no configurado")
    
    try:
        with engine.connect() as conn:
            if params:
                result = conn.execute(f"EXEC {proc_name} {', '.join(['?' for _ in params])}", params)
            else:
                result = conn.execute(f"EXEC {proc_name}")
            
            # Si el SP retorna datos, devolverlos
            try:
                return result.fetchall()
            except:
                return None
                
    except Exception as e:
        print(f"❌ Error ejecutando SP {proc_name}: {e}")
        raise

def cleanup_expired_tokens():
    """Limpiar tokens expirados usando SP"""
    try:
        result = execute_stored_procedure("sp_CleanupExpiredTokens")
        print("🧹 Limpieza de tokens completada")
        return True
    except Exception as e:
        print(f"❌ Error en limpieza de tokens: {e}")
        return False

def get_user_stats(user_id=None):
    """Obtener estadísticas de usuario usando SP"""
    try:
        params = [user_id] if user_id else []
        result = execute_stored_procedure("sp_GetUserStats", params)
        return result
    except Exception as e:
        print(f"❌ Error obteniendo estadísticas: {e}")
        return None

def get_database_size():
    """Obtener información de tamaño de la base de datos"""
    if not engine:
        return None
    
    try:
        with engine.connect() as conn:
            result = conn.execute("""
                SELECT 
                    DB_NAME() as DatabaseName,
                    ROUND(SUM(CAST(FILEPROPERTY(name, 'SpaceUsed') AS BIGINT) * 8.0 / 1024), 2) as SizeUsedMB,
                    ROUND(SUM(size * 8.0 / 1024), 2) as SizeAllocatedMB
                FROM sys.database_files
                WHERE type = 0 -- Data files only
            """).fetchone()
            
            return {
                'database_name': result.DatabaseName,
                'size_used_mb': result.SizeUsedMB,
                'size_allocated_mb': result.SizeAllocatedMB
            }
            
    except Exception as e:
        print(f"❌ Error obteniendo tamaño de BD: {e}")
        return None

# ========================================================
# FUNCIONES DE MIGRACIÓN
# ========================================================

def migrate_from_sqlite(sqlite_db_path="./users.db"):
    """
    Migrar datos desde SQLite a SQL Server
    USAR CON PRECAUCIÓN - Esta función transfiere todos los datos
    """
    import sqlite3
    from sqlalchemy.orm import Session
    from .models import User, UserSession, TokenBlacklist
    
    if not engine:
        raise RuntimeError("SQL Server no configurado")
    
    try:
        # Conectar a SQLite
        sqlite_conn = sqlite3.connect(sqlite_db_path)
        sqlite_conn.row_factory = sqlite3.Row
        
        # Crear sesión de SQL Server
        db: Session = SessionLocal()
        
        print("🔄 Iniciando migración de SQLite a SQL Server...")
        
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
                    is_active=bool(row['is_active']),
                    is_admin=bool(row['is_admin']),
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
                    is_active=bool(row['is_active'])
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
                        blacklisted_at=row['blacklisted_at'],
                        # Calcular expires_at si no existe en SQLite
                        expires_at=row.get('expires_at', row['blacklisted_at'])
                    )
                    db.add(token)
                    tokens_migrated += 1
            
            db.commit()
            print(f"✅ Tokens migrados: {tokens_migrated}")
            
        except Exception as e:
            print(f"⚠️  Error migrando tokens (puede ser normal): {e}")
        
        print("🎉 Migración completada exitosamente!")
        
        # Mostrar estadísticas finales
        stats = get_database_size()
        if stats:
            print(f"📊 Tamaño de BD: {stats['size_used_mb']} MB")
        
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
    """Crear archivo .env template para SQL Server"""
    env_template = """
# ========================================================
# SQL SERVER CONFIGURATION
# ========================================================

# Para SQL Server on-premise
SQL_SERVER_HOST=localhost
SQL_SERVER_PORT=1433
SQL_SERVER_DATABASE=YOLOAnnotator
SQL_SERVER_USERNAME=sa
SQL_SERVER_PASSWORD=tu-password-aqui

# Para autenticación Windows (on-premise)
USE_WINDOWS_AUTH=false

# Para Azure SQL Database
USE_AZURE_SQL=false
AZURE_SQL_SERVER=tu-servidor.database.windows.net
AZURE_SQL_DATABASE=YOLOAnnotator
AZURE_SQL_USERNAME=tu-usuario@tu-servidor
AZURE_SQL_PASSWORD=tu-password-azure

# Driver ODBC (verificar que esté instalado)
SQL_SERVER_DRIVER=ODBC Driver 17 for SQL Server

# ========================================================
# JWT CONFIGURATION (mantener configuración actual)
# ========================================================

SECRET_KEY=tu-clave-secreta-aqui
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# ========================================================
# NOTAS DE CONFIGURACIÓN:
# ========================================================
# 
# Para SQL Server on-premise:
# 1. Asegúrate de que SQL Server esté ejecutándose
# 2. Habilitar TCP/IP en SQL Server Configuration Manager
# 3. Configurar firewall para puerto 1433
# 4. Crear la base de datos: CREATE DATABASE YOLOAnnotator;
#
# Para Azure SQL Database:
# 1. Crear servidor Azure SQL desde el portal
# 2. Crear base de datos YOLOAnnotator
# 3. Configurar firewall para tu IP
# 4. Usar autenticación SQL (no Windows Auth)
#
# Para ODBC Driver:
# Windows: Descargar desde Microsoft
# Linux: sudo apt-get install msodbcsql17
# macOS: brew install msodbcsql17
#
# ========================================================
"""
    
    with open(".env.sqlserver.template", "w") as f:
        f.write(env_template)
    
    print("📝 Archivo .env.sqlserver.template creado!")
    print("   1. Cópialo a .env")
    print("   2. Configura tus credenciales de SQL Server")

# ========================================================
# TESTING FUNCTIONS
# ========================================================

def run_database_tests():
    """Ejecutar tests básicos de la base de datos"""
    print("🧪 Ejecutando tests de SQL Server...")
    
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
        from .models import User
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
    
    # Test 4: Stored Procedures
    try:
        cleanup_expired_tokens()
        print("✅ Stored procedures funcionando")
    except Exception as e:
        print(f"❌ Error en stored procedures: {e}")
        return False
    
    print("🎉 Todos los tests de SQL Server pasaron!")
    return True

if __name__ == "__main__":
    print("🚀 YOLO Annotator - Configuración de SQL Server")
    print("="*50)
    
    # Crear template de variables de entorno
    setup_env_template()
    
    # Probar conexión si las variables están configuradas
    if DATABASE_URL and "tu-" not in DATABASE_URL:
        print("\n🔍 Probando conexión...")
        if test_connection():
            print("\n🧪 Ejecutando tests...")
            run_database_tests()
    else:
        print("\n⚠️  Configura las variables de entorno antes de probar la conexión")
        print("   Usa el archivo .env.sqlserver.template como referencia")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de base de datos MySQL
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "yolo_annotator")

# URL de la base de datos MySQL (única opción)
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Crear motor de base de datos MySQL
try:
    engine = create_engine(DATABASE_URL, echo=False)
    # Test de conexión
    connection = engine.connect()
    connection.close()
    print(f"✅ Conectado a MySQL: {DB_HOST}:{DB_PORT}/{DB_NAME}")
except Exception as e:
    print(f"❌ Error conectando a MySQL: {e}")
    print("� Verifica que MySQL esté ejecutándose y las credenciales sean correctas.")
    raise e

# Crear SessionLocal
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency para obtener sesión de DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Crear todas las tablas
def create_tables():
    try:
        from sqlalchemy import inspect
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        if not existing_tables:
            # Si no hay tablas, crear todas
            Base.metadata.create_all(bind=engine)
            print("🆕 Tablas MySQL creadas por SQLAlchemy")
        else:
            print(f"✅ Usando tablas MySQL existentes: {len(existing_tables)} encontradas")
            # Verificar que las tablas necesarias existen
            required_tables = ['users', 'user_sessions', 'annotation_classes']
            missing_tables = [table for table in required_tables if table not in existing_tables]
            
            if missing_tables:
                print(f"⚠️ Tablas faltantes: {missing_tables}")
                # Crear solo las tablas faltantes
                Base.metadata.create_all(bind=engine, tables=[
                    Base.metadata.tables[table] for table in missing_tables 
                    if table in Base.metadata.tables
                ])
    except Exception as e:
        print(f"⚠️ Error al verificar/crear tablas MySQL: {e}")
        raise e

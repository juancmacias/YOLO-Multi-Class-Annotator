#!/usr/bin/env python3
"""
Script de prueba para verificar conexión MySQL y configuración de la aplicación
"""

import os
import sys
from dotenv import load_dotenv

def test_mysql_connection():
    """Prueba la conexión a MySQL"""
    print("🔍 Probando conexión a MySQL...")
    
    # Cargar variables de entorno
    load_dotenv()
    
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "yolo_annotator")
    
    print(f"📊 Configuración:")
    print(f"   Host: {DB_HOST}")
    print(f"   Puerto: {DB_PORT}")
    print(f"   Usuario: {DB_USER}")
    print(f"   Base de datos: {DB_NAME}")
    print(f"   Password: {'✅ Configurada' if DB_PASSWORD else '❌ Vacía'}")
    
    try:
        import pymysql
        print("✅ pymysql instalado correctamente")
    except ImportError:
        print("❌ Error: pymysql no está instalado")
        return False
    
    try:
        # Probar conexión básica
        connection = pymysql.connect(
            host=DB_HOST,
            port=int(DB_PORT),
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset='utf8mb4'
        )
        
        print("✅ Conexión a MySQL exitosa!")
        
        # Probar consultas básicas
        cursor = connection.cursor()
        
        # Verificar que las tablas existen
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        print(f"📋 Tablas encontradas ({len(tables)}):")
        for table in tables:
            print(f"   - {table[0]}")
        
        # Verificar tabla de clases específicamente
        if ('annotation_classes',) in tables:
            cursor.execute("SELECT COUNT(*) FROM annotation_classes")
            count = cursor.fetchone()[0]
            print(f"✅ Tabla annotation_classes: {count} registros")
        else:
            print("⚠️ Tabla annotation_classes no encontrada")
        
        # Verificar tabla de usuarios
        if ('users',) in tables:
            cursor.execute("SELECT COUNT(*) FROM users")
            count = cursor.fetchone()[0]
            print(f"✅ Tabla users: {count} usuarios")
        else:
            print("⚠️ Tabla users no encontrada")
        
        cursor.close()
        connection.close()
        print("✅ Conexión cerrada correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

def test_sqlalchemy_connection():
    """Prueba la conexión usando SQLAlchemy"""
    print("\n🔍 Probando conexión con SQLAlchemy...")
    
    try:
        from sqlalchemy import create_engine
        from dotenv import load_dotenv
        
        load_dotenv()
        
        DB_HOST = os.getenv("DB_HOST", "localhost")
        DB_PORT = os.getenv("DB_PORT", "3306")
        DB_USER = os.getenv("DB_USER", "root")
        DB_PASSWORD = os.getenv("DB_PASSWORD", "")
        DB_NAME = os.getenv("DB_NAME", "yolo_annotator")
        
        DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        
        engine = create_engine(DATABASE_URL, echo=False)
        connection = engine.connect()
        
        print("✅ SQLAlchemy conectado exitosamente!")
        
        # Probar una consulta simple
        from sqlalchemy import text
        result = connection.execute(text("SELECT 1 as test"))
        row = result.fetchone()
        print(f"✅ Consulta de prueba: {row[0]}")
        
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ Error con SQLAlchemy: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 YOLO Multi-Class Annotator - Prueba de Configuración MySQL")
    print("=" * 60)
    
    # Verificar archivo .env
    if os.path.exists('.env'):
        print("✅ Archivo .env encontrado")
    else:
        print("❌ Archivo .env no encontrado")
        return
    
    # Probar conexiones
    mysql_ok = test_mysql_connection()
    sqlalchemy_ok = test_sqlalchemy_connection()
    
    print("\n📊 Resumen:")
    print(f"   MySQL directo: {'✅' if mysql_ok else '❌'}")
    print(f"   SQLAlchemy: {'✅' if sqlalchemy_ok else '❌'}")
    
    if mysql_ok and sqlalchemy_ok:
        print("\n🎉 ¡Todo configurado correctamente!")
        print("💡 Puedes ejecutar la aplicación con:")
        print("   cd app-jwt && python app_auth.py")
    else:
        print("\n⚠️ Hay problemas de configuración que resolver")
        print("💡 Verifica:")
        print("   - Que MySQL esté ejecutándose")
        print("   - Que la base de datos 'yolo_annotator' exista")
        print("   - Que las credenciales en .env sean correctas")

if __name__ == "__main__":
    main()

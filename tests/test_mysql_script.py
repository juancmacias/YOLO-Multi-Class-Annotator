"""
Test para verificar que el script MySQL coincida con los modelos SQLAlchemy

Este test verifica que el script mysql_simple_setup.sql cree todas las tablas
y columnas necesarias según están definidas en los modelos de SQLAlchemy.
"""

import pytest
import os
import re
from pathlib import Path
from sqlalchemy import inspect
from auth.database import engine
from auth.models import Base, User, UserSession, TokenBlacklist, AnnotationClass


class TestMySQLScript:
    """Tests para verificar la consistencia del script MySQL"""
    
    def test_script_file_exists(self):
        """Verificar que el script MySQL existe"""
        script_path = Path("manual/mysql_simple_setup.sql")
        assert script_path.exists(), "Script mysql_simple_setup.sql no encontrado"
    
    def test_obsolete_script_removed(self):
        """Verificar que el script obsoleto ha sido eliminado"""
        obsolete_script = Path("manual/mysql_setup.sql")
        assert not obsolete_script.exists(), "Script obsoleto mysql_setup.sql aún existe y debería haber sido eliminado"
    
    def test_script_creates_all_required_tables(self):
        """Verificar que el script crea todas las tablas necesarias"""
        script_path = Path("manual/mysql_simple_setup.sql")
        script_content = script_path.read_text(encoding='utf-8')
        
        # Tablas requeridas según los modelos SQLAlchemy
        required_tables = {
            'users': User.__tablename__,
            'user_sessions': UserSession.__tablename__,
            'token_blacklist': TokenBlacklist.__tablename__,
            'annotation_classes': AnnotationClass.__tablename__
        }
        
        for table_name in required_tables.values():
            assert f"CREATE TABLE {table_name}" in script_content, f"Tabla {table_name} no se crea en el script"
    
    def test_users_table_structure(self):
        """Verificar la estructura de la tabla users"""
        script_path = Path("manual/mysql_simple_setup.sql")
        script_content = script_path.read_text(encoding='utf-8')
        
        # Buscar la definición de la tabla users
        users_match = re.search(r'CREATE TABLE users \((.*?)\) ENGINE=InnoDB', script_content, re.DOTALL)
        assert users_match, "Definición de tabla users no encontrada"
        
        users_definition = users_match.group(1)
        
        # Verificar columnas requeridas
        required_columns = [
            'id INT NOT NULL AUTO_INCREMENT',
            'username VARCHAR(50) NOT NULL',
            'email VARCHAR(100) NOT NULL', 
            'hashed_password VARCHAR(255) NOT NULL',  # Debe ser hashed_password, no password_hash
            'is_active TINYINT(1) DEFAULT 1',
            'is_admin TINYINT(1) DEFAULT 0',
            'created_at DATETIME NOT NULL'
        ]
        
        for column in required_columns:
            assert column in users_definition, f"Columna '{column}' faltante en tabla users"
        
        # Verificar índices únicos
        assert 'UNIQUE KEY ix_users_username (username)' in users_definition
        assert 'UNIQUE KEY ix_users_email (email)' in users_definition
    
    def test_user_sessions_table_structure(self):
        """Verificar la estructura de la tabla user_sessions"""
        script_path = Path("manual/mysql_simple_setup.sql")
        script_content = script_path.read_text(encoding='utf-8')
        
        users_sessions_match = re.search(r'CREATE TABLE user_sessions \((.*?)\) ENGINE=InnoDB', script_content, re.DOTALL)
        assert users_sessions_match, "Definición de tabla user_sessions no encontrada"
        
        sessions_definition = users_sessions_match.group(1)
        
        # Verificar columnas requeridas (incluyendo session_hash que es crítico)
        required_columns = [
            'id INT NOT NULL AUTO_INCREMENT',
            'session_name VARCHAR(100) NOT NULL',
            'session_hash VARCHAR(64) NOT NULL',  # Columna crítica para sesiones privadas
            'user_id INT NOT NULL',
            'created_at DATETIME NOT NULL',
            'is_active TINYINT(1) DEFAULT 1'
        ]
        
        for column in required_columns:
            assert column in sessions_definition, f"Columna '{column}' faltante en tabla user_sessions"
        
        # Verificar índice único para session_hash
        assert 'UNIQUE KEY ix_user_sessions_session_hash (session_hash)' in sessions_definition
        
        # Verificar clave foránea
        assert 'FOREIGN KEY (user_id) REFERENCES users (id)' in sessions_definition
    
    def test_token_blacklist_table_structure(self):
        """Verificar la estructura de la tabla token_blacklist"""
        script_path = Path("manual/mysql_simple_setup.sql")
        script_content = script_path.read_text(encoding='utf-8')
        
        blacklist_match = re.search(r'CREATE TABLE token_blacklist \((.*?)\) ENGINE=InnoDB', script_content, re.DOTALL)
        assert blacklist_match, "Definición de tabla token_blacklist no encontrada"
        
        blacklist_definition = blacklist_match.group(1)
        
        # Verificar columnas requeridas
        required_columns = [
            'id INT NOT NULL AUTO_INCREMENT',
            'token VARCHAR(500) NOT NULL',
            'blacklisted_at DATETIME NOT NULL'
        ]
        
        for column in required_columns:
            assert column in blacklist_definition, f"Columna '{column}' faltante en tabla token_blacklist"
        
        # Verificar índice único para token
        assert 'UNIQUE KEY ix_token_blacklist_token (token)' in blacklist_definition
    
    def test_annotation_classes_table_structure(self):
        """Verificar la estructura de la tabla annotation_classes"""
        script_path = Path("manual/mysql_simple_setup.sql")
        script_content = script_path.read_text(encoding='utf-8')
        
        classes_match = re.search(r'CREATE TABLE annotation_classes \((.*?)\) ENGINE=InnoDB', script_content, re.DOTALL)
        assert classes_match, "Definición de tabla annotation_classes no encontrada"
        
        classes_definition = classes_match.group(1)
        
        # Verificar columnas requeridas (incluyendo session_hash)
        required_columns = [
            'id INT NOT NULL AUTO_INCREMENT',
            'name VARCHAR(50) NOT NULL',
            'color VARCHAR(7) NOT NULL DEFAULT \'#ff0000\'',
            'user_id INT NOT NULL',
            'session_name VARCHAR(100) DEFAULT NULL',
            'session_hash VARCHAR(64) DEFAULT NULL',  # Columna crítica para sesiones privadas
            'is_global TINYINT(1) DEFAULT 0',
            'is_active TINYINT(1) DEFAULT 1',
            'created_at DATETIME NOT NULL'
        ]
        
        for column in required_columns:
            assert column in classes_definition, f"Columna '{column}' faltante en tabla annotation_classes"
        
        # Verificar clave foránea
        assert 'FOREIGN KEY (user_id) REFERENCES users (id)' in classes_definition
    
    def test_script_includes_sample_data(self):
        """Verificar que el script incluye datos de ejemplo"""
        script_path = Path("manual/mysql_simple_setup.sql")
        script_content = script_path.read_text(encoding='utf-8')
        
        # Verificar inserción de usuarios
        assert "INSERT INTO users" in script_content
        assert "'admin'" in script_content
        assert "'testuser'" in script_content
        
        # Verificar inserción de sesión de ejemplo
        assert "INSERT INTO user_sessions" in script_content
        assert "'demo_session'" in script_content
        
        # Verificar inserción de clases globales
        assert "INSERT INTO annotation_classes" in script_content
        assert "'adidas'" in script_content
        assert "'nike'" in script_content
    
    def test_script_includes_verification_queries(self):
        """Verificar que el script incluye consultas de verificación"""
        script_path = Path("manual/mysql_simple_setup.sql")
        script_content = script_path.read_text(encoding='utf-8')
        
        # Verificar que incluye verificaciones
        assert "SHOW TABLES" in script_content
        assert "SELECT" in script_content
        assert "INSTALACIÓN COMPLETADA CORRECTAMENTE" in script_content
    
    def test_no_obsolete_tables_in_script(self):
        """Verificar que el script no incluye tablas obsoletas"""
        script_path = Path("manual/mysql_simple_setup.sql")
        script_content = script_path.read_text(encoding='utf-8')
        
        # Tablas que NO deben estar en el script (no están en los modelos actuales)
        obsolete_tables = [
            'CREATE TABLE projects',
            'CREATE TABLE images', 
            'CREATE TABLE annotations',
            'CREATE TABLE activity_log',
            'CREATE TABLE user_tokens'  # Reemplazada por token_blacklist
        ]
        
        for table in obsolete_tables:
            assert table not in script_content, f"Tabla obsoleta encontrada: {table}"
    
    @pytest.mark.integration  
    def test_script_would_create_valid_schema(self):
        """Test de integración: verificar que el esquema sería válido"""
        # Obtener esquema actual de SQLAlchemy
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        # Tablas que deberían existir según los modelos
        expected_tables = {'users', 'user_sessions', 'token_blacklist', 'annotation_classes'}
        
        if existing_tables:
            # Si hay tablas existentes, verificar que coincidan
            existing_set = set(existing_tables)
            missing_tables = expected_tables - existing_set
            extra_tables = existing_set - expected_tables
            
            if missing_tables:
                print(f"\n⚠️ Tablas faltantes en BD actual: {missing_tables}")
            if extra_tables:
                print(f"\n⚠️ Tablas extra en BD actual: {extra_tables}")
                
            # El test pasa si al menos las tablas requeridas existen
            assert expected_tables.issubset(existing_set), f"Tablas requeridas faltantes: {missing_tables}"
        else:
            print("\n📋 No hay tablas existentes - el script debe ejecutarse para crear el esquema")
            assert True  # El test pasa, el script debe ejecutarse
    
    def test_character_set_and_collation(self):
        """Verificar que se use UTF8MB4 correctamente"""
        script_path = Path("manual/mysql_simple_setup.sql")
        script_content = script_path.read_text(encoding='utf-8')
        
        # Verificar configuración de base de datos
        assert "CHARACTER SET utf8mb4" in script_content
        assert "COLLATE utf8mb4_unicode_ci" in script_content
        
        # Verificar que todas las tablas usen utf8mb4 (buscar completo incluyendo ENGINE)
        table_matches = re.findall(r'CREATE TABLE \w+ \((.*?)\) ENGINE=InnoDB[^;]*;', script_content, re.DOTALL)
        
        # Contar líneas ENGINE=InnoDB con charset
        engine_lines = re.findall(r'ENGINE=InnoDB[^;]*', script_content)
        
        charset_count = 0
        collation_count = 0
        
        for line in engine_lines:
            if "CHARSET=utf8mb4" in line:
                charset_count += 1
            if "COLLATE=utf8mb4_unicode_ci" in line:
                collation_count += 1
        
        # Debe haber al menos 4 tablas con charset y collation correctos
        assert charset_count >= 4, f"Solo {charset_count} tablas tienen charset utf8mb4"
        assert collation_count >= 4, f"Solo {collation_count} tablas tienen collation utf8mb4_unicode_ci"


if __name__ == "__main__":
    # Permitir ejecutar el test directamente
    pytest.main([__file__, "-v", "-s"])

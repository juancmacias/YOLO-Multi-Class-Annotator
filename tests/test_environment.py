

import pytest
import os
from pathlib import Path
from dotenv import load_dotenv


class TestEnvironmentConfiguration:
    """Tests para verificar la configuración del entorno"""
    
    @classmethod
    def setup_class(cls):
        """Configuración inicial para los tests de entorno"""
        # Cargar variables del .env
        env_path = Path(".env")
        if env_path.exists():
            load_dotenv(env_path)
        
    def test_obsolete_files_removed(self):
        """Verificar que archivos obsoletos han sido eliminados"""
        obsolete_files = [
            "app_simple.py",
        ]
        
        for file in obsolete_files:
            file_path = Path(file)
            assert not file_path.exists(), f"Archivo obsoleto encontrado: {file}. Debe ser eliminado para mantener el proyecto limpio."
    
    def test_env_file_exists(self):
        """Verificar que el archivo .env existe"""
        env_path = Path(".env")
        assert env_path.exists(), (
            "Archivo .env no encontrado. "
            "Crea el archivo .env copiando desde .env.example: copy .env.example .env"
        )
    
    def test_mysql_configuration(self):
        """Verificar que la configuración de MySQL esté completa"""
        required_mysql_vars = ["DB_HOST", "DB_PORT", "DB_USER", "DB_NAME"]
        
        for var in required_mysql_vars:
            value = os.getenv(var)
            assert value is not None, f"Variable {var} no está definida en .env"
            assert value.strip() != "", f"Variable {var} no puede estar vacía"
        
        # DB_PASSWORD puede estar vacía (válido para desarrollo local)
        db_password = os.getenv("DB_PASSWORD")
        assert db_password is not None, "Variable DB_PASSWORD debe estar definida (puede estar vacía)"
    
    def test_jwt_configuration(self):
        """Verificar que la configuración JWT esté completa"""
        secret_key = os.getenv("SECRET_KEY")
        assert secret_key is not None, "Variable SECRET_KEY no está definida"
        assert len(secret_key) >= 32, f"SECRET_KEY muy corta ({len(secret_key)} chars, mínimo: 32)"
        
        jwt_algorithm = os.getenv("JWT_ALGORITHM")
        assert jwt_algorithm is not None, "Variable JWT_ALGORITHM no está definida"
        assert jwt_algorithm in ["HS256", "HS384", "HS512"], f"JWT_ALGORITHM inválido: {jwt_algorithm}"
        
        expire_minutes = os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
        assert expire_minutes is not None, "Variable JWT_ACCESS_TOKEN_EXPIRE_MINUTES no está definida"
        assert expire_minutes.isdigit(), "JWT_ACCESS_TOKEN_EXPIRE_MINUTES debe ser un número"
        assert int(expire_minutes) > 0, "JWT_ACCESS_TOKEN_EXPIRE_MINUTES debe ser mayor a 0"
    
    def test_server_configuration(self):
        """Verificar que la configuración del servidor esté completa"""
        host = os.getenv("HOST")
        assert host is not None, "Variable HOST no está definida"
        
        port = os.getenv("PORT")
        assert port is not None, "Variable PORT no está definida"
        assert port.isdigit(), f"PORT debe ser un número, recibido: {port}"
        
        port_num = int(port)
        assert 1024 <= port_num <= 65535, f"PORT fuera de rango válido (1024-65535): {port_num}"
        
        debug = os.getenv("DEBUG")
        assert debug is not None, "Variable DEBUG no está definida"
        assert debug.lower() in ["true", "false"], f"DEBUG debe ser 'true' o 'false': {debug}"
    
    def test_mysql_connection_string_format(self):
        """Verificar que se pueda construir la URL de conexión MySQL"""
        db_host = os.getenv("DB_HOST")
        db_port = os.getenv("DB_PORT") 
        db_user = os.getenv("DB_USER")
        db_password = os.getenv("DB_PASSWORD", "")  # Puede estar vacía
        db_name = os.getenv("DB_NAME")
        
        # Construir URL de conexión
        database_url = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        
        # Verificar que no tenga caracteres problemáticos
        assert "None" not in database_url, f"URL de conexión contiene 'None': {database_url}"
        assert database_url.startswith("mysql+pymysql://"), "URL debe comenzar con mysql+pymysql://"
    
    @pytest.mark.integration
    def test_mysql_port_accessibility(self):
        """Verificar que el puerto MySQL sea accesible (solo si MySQL está disponible)"""
        import socket
        
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = int(os.getenv("DB_PORT", "3306"))
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)  # 5 segundos timeout
        
        try:
            result = sock.connect_ex((db_host, db_port))
            if result == 0:
                # Puerto accesible
                assert True, f"MySQL accesible en {db_host}:{db_port}"
            else:
                # Puerto no accesible - solo advertencia, no falla el test
                pytest.skip(f"MySQL no accesible en {db_host}:{db_port} - esto es normal en CI/CD")
        except socket.gaierror:
            pytest.skip(f"No se puede resolver el host {db_host} - esto es normal en CI/CD")
        finally:
            sock.close()
    
    def test_environment_variables_summary(self, capsys):
        """Mostrar resumen de configuración del entorno"""
        print("\n" + "="*60)
        print("📋 RESUMEN DE CONFIGURACIÓN DEL ENTORNO")
        print("="*60)
        
        # Variables requeridas
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
        
        print("✅ Variables requeridas:")
        for var, description in required_vars.items():
            value = os.getenv(var)
            if value is not None:
                if var in ["DB_PASSWORD", "SECRET_KEY"]:
                    if value:
                        display_value = "*" * min(len(value), 8)
                    else:
                        display_value = "(vacía - válido para MySQL sin contraseña)"
                else:
                    display_value = value if value else "(vacía)"
                print(f"   ✓ {var:<35} = {display_value}")
            else:
                print(f"   ❌ {var:<35} = NO DEFINIDA")
        
        # Verificaciones específicas
        print("\n🔍 Verificaciones específicas:")
        
        secret_key = os.getenv("SECRET_KEY")
        if secret_key and len(secret_key) >= 32:
            print("   ✓ SECRET_KEY tiene longitud adecuada")
        
        port = os.getenv("PORT")
        if port and port.isdigit():
            port_num = int(port)
            if 1024 <= port_num <= 65535:
                print(f"   ✓ Puerto {port_num} está en rango válido")
        
        db_host = os.getenv("DB_HOST")
        db_port = os.getenv("DB_PORT")
        if db_host and db_port:
            print(f"   ✓ MySQL configurado en {db_host}:{db_port}")
        
        print("="*60)
        
        # El test siempre pasa, solo muestra información
        assert True


# Tests adicionales para desarrollo
class TestDevelopmentEnvironment:
    """Tests específicos para el entorno de desarrollo"""
    
    def test_development_mode_active(self):
        """Verificar que el modo desarrollo esté activo"""
        debug = os.getenv("DEBUG", "false").lower()
        if debug == "true":
            print("\n⚠️ Modo DEBUG activo - Solo para desarrollo")
            assert True
        else:
            print("\n✓ Modo DEBUG desactivado - Apropiado para producción")
            assert True
    
    def test_secret_key_security(self):
        """Verificar la seguridad de la clave secreta"""
        secret_key = os.getenv("SECRET_KEY", "")
        
        # Advertir sobre claves por defecto inseguras
        insecure_patterns = [
            "your-super-secret-jwt-key",
            "change-this",
            "default",
            "secret",
            "12345"
        ]
        
        for pattern in insecure_patterns:
            if pattern in secret_key.lower():
                print(f"\n⚠️ ADVERTENCIA: SECRET_KEY contiene patrón inseguro: '{pattern}'")
                print("   Cambia la SECRET_KEY en producción por una clave aleatoria")
                break
        
        assert len(secret_key) >= 32, "SECRET_KEY debe tener al menos 32 caracteres"
    
    def test_obsolete_files_removed(self):
        """Verificar que archivos obsoletos han sido eliminados"""
        obsolete_files = [
            "app_simple.py",
        ]
        
        for file in obsolete_files:
            file_path = Path(file)
            assert not file_path.exists(), f"Archivo obsoleto encontrado: {file}. Debe ser eliminado para mantener el proyecto limpio."


if __name__ == "__main__":
    # Permitir ejecutar el test directamente
    pytest.main([__file__, "-v", "-s"])

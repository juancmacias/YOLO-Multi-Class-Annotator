# Tests - YOLO Multi-Class Annotator

Este directorio contiene todos los tests para el sistema de anotación YOLO con autenticación JWT.

## Estructura de Tests

```
tests/
├── __init__.py              # Configuración del paquete de tests
├── conftest.py              # Fixtures compartidas de pytest
├── test_environment.py      # Tests de configuración del entorno (.env)
├── test_mysql_script.py     # Tests de validación del script MySQL
├── test_auth.py             # Tests básicos de autenticación
├── test_auth_full.py        # Tests completos de autenticación end-to-end
├── test_classes.py          # Tests de gestión de clases personalizadas
├── test_images.py           # Tests de procesamiento de imágenes
├── test_mysql.py            # Tests de conexión y operaciones MySQL
├── test_token.py            # Tests de generación y verificación JWT
└── verify_dependencies.py   # Verificación de dependencias del sistema
```

## Ejecución de Tests

### Instalar dependencias de testing
```bash
pip install pytest pytest-asyncio pytest-cov
```

### Ejecutar todos los tests
```bash
pytest tests/
```

### Ejecutar tests específicos
```bash
# Test individual
pytest tests/test_auth.py

# Test con verbose
pytest tests/test_mysql.py -v

# Tests con coverage
pytest tests/ --cov=auth --cov-report=html
```

### Filtrar tests por marcadores
```bash
# Solo tests de autenticación
pytest -m auth

# Solo tests de MySQL
pytest -m mysql

# Solo tests de configuración del entorno
pytest -m environment

# Excluir tests lentos
pytest -m "not slow"

# Solo tests de integración
pytest -m integration
```

## Configuración

La configuración de pytest está en `pyproject.toml` en la raíz del proyecto:

- **testpaths**: `tests/` - Directorio de tests
- **python_files**: `test_*.py` - Archivos de test
- **python_functions**: `test_*` - Funciones de test
- **markers**: Etiquetas para categorizar tests

## Fixtures Disponibles

Las fixtures compartidas están en `conftest.py`:

- `root_path`: Ruta raíz del proyecto
- `test_data_path`: Ruta de datos de testing
- `temp_dir`: Directorio temporal por test
- `mock_mysql_connection`: Conexión MySQL simulada
- `sample_image_data`: Datos de imagen de muestra
- `sample_user_data`: Datos de usuario de muestra
- `jwt_token_data`: Datos de token JWT de muestra

## Tests Disponibles

### test_environment.py
- Verificación del archivo .env
- Validación de variables de entorno MySQL
- Configuración JWT y servidor
- Verificación de conectividad de puertos
- Advertencias de seguridad para desarrollo

### test_mysql_script.py
- Validación del script mysql_simple_setup.sql
- Verificación de consistencia con modelos SQLAlchemy
- Comprobación de estructura de tablas
- Validación de datos de ejemplo
- Verificación de charset UTF8MB4

### test_auth.py
- Registro de usuarios
- Login y autenticación básica

### test_auth_full.py
- Flujo completo de autenticación end-to-end
- Integración con base de datos

### test_classes.py
- Gestión de clases personalizadas
- CRUD de clases de anotación

### test_images.py
- Endpoints de imágenes
- Procesamiento y validación

### test_mysql.py
- Conexión a base de datos MySQL
- Operaciones SQLAlchemy
- Configuración de tablas

### test_token.py
- Generación de tokens JWT
- Verificación y validación
- Expiración de tokens

### verify_dependencies.py
- Verificación de dependencias instaladas
- Validación de versiones
- Diagnóstico del entorno

## Variables de Entorno para Testing

```bash
TESTING=true
DATABASE_URL=mysql+pymysql://test_user:test_pass@localhost/test_yolo_db
```

## Tips para Desarrollo

1. **Escribir nuevos tests**: Sigue el patrón `test_*.py`
2. **Usar fixtures**: Aprovecha las fixtures de `conftest.py`
3. **Marcadores**: Usa marcadores para categorizar tests
4. **Coverage**: Ejecuta con `--cov` para ver cobertura de código
5. **Debug**: Usa `-s` para ver prints en tests
6. **Paralelo**: Usa `-n auto` con pytest-xdist para tests paralelos

## Ejemplos de Comandos Útiles

```bash
# Ejecutar tests con output detallado
pytest tests/ -v -s

# Solo tests que fallan
pytest tests/ --lf

# Tests con timeout
pytest tests/ --timeout=30

# Generar reporte de coverage
pytest tests/ --cov=auth --cov-report=html --cov-report=term

# Ejecutar tests específicos
pytest tests/test_auth.py::test_register -v
```

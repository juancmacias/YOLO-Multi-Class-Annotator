# 🧪 Guía de Testing - YOLO Multi-Class Annotator

## 🎯 Tipos de Tests

### 📋 Tests Unitarios (Unit Tests)
Verifican componentes individuales sin dependencias externas:
- ✅ Configuración del entorno
- ✅ Funcionalidad de tokens JWT
- ✅ Validación de scripts SQL
- ✅ Estructura del proyecto

### 🔗 Tests de Integración (Integration Tests)  
Requieren servidor ejecutándose y base de datos configurada:
- 🔄 Gestión de clases personalizadas
- 🔐 Flujo completo de autenticación
- 📸 Subida y procesamiento de imágenes

## 🚀 Comandos de Testing

### Ejecutar TODOS los tests unitarios (recomendado)
```bash
pytest tests/ -m "not integration" -v
```

### Ejecutar tests específicos
```bash
# Test de limpieza del proyecto
pytest tests/test_cleanup.py -v

# Test de configuración del entorno
pytest tests/test_environment.py -v

# Test de scripts MySQL
pytest tests/test_mysql_script.py -v

# Test de autenticación (unitario)
pytest tests/test_auth.py -v
```

### Ejecutar tests de integración (requiere servidor)
```bash
# Primero iniciar el servidor:
python app_auth.py

# En otra terminal:
pytest tests/ -m "integration" -v
```

### Ejecutar test específico de integración
```bash
# Test de gestión de clases (requiere servidor)
pytest tests/test_classes.py::test_class_management -v
```

## 📊 Resultados de Tests

### ✅ Estado Actual (32/32 tests unitarios pasando)
- `test_auth.py`: 2/2 ✅
- `test_auth_full.py`: 1/1 ✅
- `test_classes.py`: 1/1 ✅ (unitario)
- `test_cleanup.py`: 3/3 ✅
- `test_environment.py`: 9/9 ✅
- `test_images.py`: 1/1 ✅
- `test_mysql.py`: 2/2 ✅
- `test_mysql_script.py`: 12/12 ✅
- `test_token.py`: 1/1 ✅

### 🔄 Tests de Integración (requieren servidor)
- `test_class_management`: Se omite si no hay servidor disponible

## 🎛️ Configuración de Markers

Los tests están organizados por categorías:

```toml
# pyproject.toml
[tool.pytest.ini_options]
markers = [
    "unit: tests unitarios",
    "integration: tests de integración",
    "auth: tests de autenticación",
    "mysql: tests de MySQL",
    "images: tests de imágenes",
    "environment: tests de entorno",
]
```

### Filtrar por markers
```bash
# Solo tests unitarios
pytest -m "unit" -v

# Solo tests de MySQL
pytest -m "mysql" -v

# Excluir tests de integración
pytest -m "not integration" -v
```

## 🔧 Troubleshooting

### Error: "Servidor no disponible en localhost:8002"
**Solución**: El test de integración se omite automáticamente. Esto es normal.

### Error: "No se puede establecer conexión MySQL"
**Solución**: 
1. Verificar que MySQL esté ejecutándose
2. Revisar configuración en `.env`
3. Ejecutar solo tests unitarios: `pytest -m "not integration"`

### Error: "archivo .env no encontrado"
**Solución**: 
```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

## 📈 Cobertura de Tests

Los tests cubren:
- ✅ **Configuración**: Variables de entorno, MySQL, JWT
- ✅ **Autenticación**: Registro, login, tokens
- ✅ **Base de datos**: Scripts SQL, estructuras de tablas
- ✅ **Proyecto**: Limpieza, archivos esenciales
- ✅ **Integración**: API completa (con servidor)

## 🎯 Tests Recomendados

### Para desarrollo diario:
```bash
pytest tests/ -m "not integration" -v
```

### Para validación completa (con servidor):
```bash
# Terminal 1:
python app_auth.py

# Terminal 2:
pytest tests/ -v
```

### Para CI/CD:
```bash
pytest tests/ -m "not integration" --tb=short
```

## 📝 Crear Nuevos Tests

### Test unitario:
```python
@pytest.mark.unit
def test_nueva_funcionalidad():
    # Tu test aquí
    assert True
```

### Test de integración:
```python
@pytest.mark.integration  
def test_api_endpoint():
    # Verificar servidor disponible
    try:
        response = requests.get("http://localhost:8002/")
    except requests.exceptions.ConnectionError:
        pytest.skip("Servidor no disponible")
    
    # Tu test aquí
```

¡Los tests están listos para garantizar la calidad del código! 🚀

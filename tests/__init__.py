# Tests para YOLO Multi-Class Annotator
"""
Suite de tests para el sistema de anotación YOLO con autenticación JWT.

Estructura de tests:
- test_auth.py: Tests básicos de autenticación
- test_auth_full.py: Tests completos de autenticación
- test_classes.py: Tests de clases de anotación
- test_images.py: Tests de procesamiento de imágenes
- test_mysql.py: Tests de base de datos MySQL
- test_token.py: Tests de tokens JWT
- verify_dependencies.py: Verificación de dependencias

Para ejecutar todos los tests:
    pytest tests/

Para ejecutar tests específicos:
    pytest tests/test_auth.py
    pytest tests/test_mysql.py -v
"""

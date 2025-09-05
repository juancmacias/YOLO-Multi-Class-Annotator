# Scripts - YOLO Multi-Class Annotator

Esta carpeta contiene scripts utilitarios para el proyecto.

## Scripts Disponibles

### verify_env.py
Script independiente para verificar la configuración del archivo `.env`.

**Uso:**
```bash
python scripts/verify_env.py
```

**Funcionalidad:**
- Verifica que todas las variables de entorno estén definidas
- Valida configuración de MySQL
- Comprueba configuración JWT
- Muestra resumen de configuración
- Proporciona ejemplos de configuración

**Nota:** Esta funcionalidad también está disponible como test en `tests/test_environment.py`. 
Se recomienda usar los tests para validación automática:
```bash
pytest tests/test_environment.py -v -s
```

## Propósito

Los scripts en esta carpeta son herramientas auxiliares que pueden ejecutarse 
independientemente para tareas de mantenimiento, diagnóstico o configuración 
del proyecto.

Para funcionalidades de testing, preferir usar la suite de tests en `tests/`.

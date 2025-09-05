# Script MySQL para YOLO Multi-Class Annotator

Este directorio contiene el script SQL para configurar la base de datos MySQL del proyecto.

## 📋 Archivo de Configuración

### `mysql_simple_setup.sql` 
**✅ Script de Base de Datos MySQL**

- **Estado**: ✅ Actualizado y validado
- **Propósito**: Script optimizado y sincronizado con el código actual
- **Compatibilidad**: 100% compatible con modelos SQLAlchemy
- **Validación**: Verificado con tests automatizados

**Características**:
- 4 tablas necesarias para el proyecto
- Estructura exacta según models.py
- Incluye session_hash para sesiones privadas
- Incluye token_blacklist para JWT
- Datos de ejemplo apropiados
- Configuración UTF8MB4 completa

## 📋 Instrucciones de Uso

### Para Nueva Instalación

1. **Abrir phpMyAdmin**
2. **Ir a la pestaña SQL**
3. **Copiar y pegar el contenido de `mysql_simple_setup.sql`**
4. **Ejecutar el script**
5. **Verificar que se crearon las 4 tablas**

### Verificación Rápida

Después de ejecutar el script, deberías ver estas tablas:
- ✅ `users` - Usuarios del sistema
- ✅ `user_sessions` - Sesiones privadas con hash
- ✅ `token_blacklist` - Tokens JWT revocados  
- ✅ `annotation_classes` - Clases de anotación

## 🧪 Validación Automatizada

El script está validado con tests automatizados:

```bash
# Ejecutar tests de validación del script
pytest tests/test_mysql_script.py -v

# Incluido en suite de tests unitarios
python tests/run_unit_tests.py
```

## 🗃️ Estructura de Base de Datos

El script crea exactamente las tablas necesarias según los modelos SQLAlchemy:

```sql
users                 -- Autenticación de usuarios
├── id (PK)
├── username (UNIQUE)
├── email (UNIQUE)
├── hashed_password
├── is_active
├── is_admin
└── created_at

user_sessions         -- Sesiones privadas
├── id (PK)
├── session_name
├── session_hash (UNIQUE) -- Para acceso privado
├── user_id (FK)
├── created_at
└── is_active

token_blacklist       -- Gestión JWT
├── id (PK)
├── token (UNIQUE)
└── blacklisted_at

annotation_classes    -- Clases personalizadas
├── id (PK)
├── name
├── color
├── user_id (FK)
├── session_name
├── session_hash      -- Vinculación con sesiones
├── is_global
├── is_active
└── created_at
```

## 📊 Datos de Ejemplo

El script incluye datos listos para usar:

- **Usuario admin**: `admin@yolo-annotator.local` (contraseña: admin123)
- **Usuario test**: `test@yolo-annotator.local` (contraseña: test123)
- **Sesión demo**: Con hash único para pruebas
- **6 clases globales**: adidas, nike, puma, reebok, converse, vans

## 🔧 Configuración Técnica

- **Engine**: InnoDB para transacciones
- **Charset**: UTF8MB4 para soporte completo Unicode
- **Collation**: utf8mb4_unicode_ci
- **Claves foráneas**: Configuradas correctamente
- **Índices**: Optimizados para rendimiento

## ⚡ Características Avanzadas

- **Session Hash**: Sistema de sesiones privadas con SHA-256
- **Token Blacklist**: Gestión segura de JWT revocados
- **Clases Flexibles**: Soporte para clases globales y por sesión
- **Integridad Referencial**: Claves foráneas y constraints

## � Próximos Pasos

Después de ejecutar el script:

1. **Configurar el archivo .env** con los datos de conexión
2. **Ejecutar la aplicación**: `python app_auth.py`
3. **Acceder a**: `http://localhost:8002`
4. **Login inicial**: Usar credenciales de admin o test

## 📞 Soporte

Si tienes problemas con la instalación:
- Consulta `manual/MYSQL_ERROR_FIX.md`
- Ejecuta los tests de validación
- Verifica la configuración en `.env`

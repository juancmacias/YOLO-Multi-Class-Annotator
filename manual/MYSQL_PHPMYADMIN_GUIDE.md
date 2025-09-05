# 🚀 Guía de Instalación MySQL en phpMyAdmin

## 📋 Pasos para Ejecutar el Script en phpMyAdmin

### 1. **Preparar phpMyAdmin**
1. Abre tu navegador y ve a phpMyAdmin
2. Inicia sesión con tus credenciales de MySQL
3. Asegúrate de tener permisos de administrador

### 2. **Ejecutar el Script de Instalación**

#### Opción A: Importar el Archivo Completo
1. En phpMyAdmin, haz clic en **"Importar"** en el menú superior
2. Selecciona **"Elegir archivo"** 
3. Busca y selecciona el archivo `mysql_simple_setup.sql`
4. Asegúrate de que el formato esté en **"SQL"**
5. Haz clic en **"Continuar"**

#### Opción B: Ejecutar Manualmente
1. Haz clic en **"SQL"** en el menú superior
2. Copia todo el contenido del archivo `mysql_simple_setup.sql`
3. Pégalo en el área de texto
4. Haz clic en **"Continuar"**

### 3. **Verificar la Instalación**

Después de ejecutar el script, deberías ver:
- ✅ Base de datos `yolo_annotator` creada
- ✅ 9+ tablas creadas incluyendo `annotation_classes`
- ✅ Múltiples índices y constraints
- ✅ 4 stored procedures
- ✅ 6 vistas para reportes
- ✅ Datos de ejemplo insertados

### 4. **Configurar la Aplicación**

Actualiza tu archivo de configuración con la nueva cadena de conexión MySQL:

```python
# En tu archivo de configuración (.env o config.py)
DATABASE_URL = "mysql+pymysql://usuario:password@localhost:3306/yolo_annotator"

# O usando configuración separada
DB_HOST = "localhost"
DB_PORT = 3306
DB_USER = "tu_usuario"
DB_PASSWORD = "tu_password"
DB_NAME = "yolo_annotator"
```

## 🔧 Configuración de Seguridad (Recomendado)

### Crear Usuario Específico para la Aplicación

Ejecuta estos comandos en la pestaña SQL de phpMyAdmin:

```sql
-- Crear usuario específico para la aplicación
CREATE USER 'yolo_app'@'localhost' IDENTIFIED BY 'tu_password_seguro';

-- Otorgar permisos específicos
GRANT SELECT, INSERT, UPDATE, DELETE ON yolo_annotator.* TO 'yolo_app'@'localhost';
GRANT EXECUTE ON yolo_annotator.* TO 'yolo_app'@'localhost';

-- Aplicar cambios
FLUSH PRIVILEGES;
```

Luego usa estas credenciales en tu aplicación:
```python
DATABASE_URL = "mysql+pymysql://yolo_app:tu_password_seguro@localhost:3306/yolo_annotator"
```

## 🧪 Probar la Instalación

### 1. Verificar Tablas Creadas
```sql
USE yolo_annotator;
SHOW TABLES;
```

### 2. Verificar Datos de Ejemplo
```sql
-- Ver usuarios creados
SELECT * FROM users;

-- Ver clases por defecto
SELECT * FROM annotation_classes;

-- Ver colores predefinidos
SELECT * FROM color_presets;
```

### 3. Probar Stored Procedures
```sql
-- Crear clases por defecto para un usuario
CALL sp_CreateDefaultClasses(1, 'test_session');

-- Ver clases de un usuario
CALL sp_GetUserClasses(1, 'test_session', 1);

-- Ver estadísticas
CALL sp_GetClassStatistics(1);
```

### 4. Probar Vistas
```sql
-- Ver estadísticas de usuarios
SELECT * FROM vw_user_statistics;

-- Ver clases más populares
SELECT * FROM vw_popular_classes;

-- Ver resumen de gestión de clases
SELECT * FROM vw_class_management_summary;
```

## 🔍 Resolución de Problemas Comunes

### Error: "Base de datos ya existe"
- **Solución**: El script está diseñado para manejar esto. Si quieres empezar limpio, elimina la base de datos primero:
```sql
DROP DATABASE IF EXISTS yolo_annotator;
```

### Error: "Permisos insuficientes"
- **Solución**: Asegúrate de estar conectado como usuario root o con permisos de administrador.

### Error: "Event scheduler deshabilitado"
- **Solución**: Los eventos para mantenimiento automático requieren permisos especiales. Puedes ignorar este error si no tienes permisos de SUPER.

### Error: "Sintaxis no reconocida"
- **Solución**: Asegúrate de estar usando MySQL 5.7+ o MariaDB 10.2+.

## 📊 Funcionalidades Incluidas

### ✅ **Sistema de Gestión de Clases**
- Clases personalizadas por usuario
- Clases globales para toda la organización
- Clases específicas por sesión
- Colores hexadecimales personalizados
- Validación automática de datos

### ✅ **Autenticación Completa**
- Registro y login de usuarios
- Tokens JWT con expiración
- Roles de administrador
- Log de actividades

### ✅ **Gestión de Proyectos**
- Múltiples proyectos por usuario
- Sesiones organizadas por proyecto
- Estadísticas detalladas

### ✅ **Sistema de Anotaciones**
- Coordenadas YOLO normalizadas
- Múltiples clases por imagen
- Historial de cambios
- Validación de datos

### ✅ **Reportes y Estadísticas**
- Vistas predefinidas para análisis
- Stored procedures optimizados
- Mantenimiento automático

## 🎯 Credenciales por Defecto

**⚠️ IMPORTANTE: Cambiar en producción**

- **Usuario Administrador**: 
  - Username: `admin`
  - Email: `admin@yolo-annotator.com`
  - Password: `password`

- **Usuario de Prueba**:
  - Username: `testuser`
  - Email: `test@yolo-annotator.com`
  - Password: `password`

## 🔄 Migración desde Otras Bases de Datos

Si ya tienes datos en SQLite o PostgreSQL, el script incluye la estructura compatible para migrar. Las tablas tienen la misma estructura lógica, solo cambian los tipos de datos específicos de cada motor.

## 📞 Soporte

Si encuentras problemas:

1. **Verifica la versión de MySQL**: Debe ser 5.7+ o MariaDB 10.2+
2. **Revisa los logs de phpMyAdmin**: Busca errores específicos
3. **Verifica permisos**: El usuario debe tener permisos de CREATE, ALTER, INSERT
4. **Consulta la documentación**: Revisa `CLASE_MANAGEMENT_GUIDE.md` para más detalles

---

¡Tu sistema YOLO Multi-Class Annotator con gestión personalizada de clases está listo para usar en MySQL! 🎉

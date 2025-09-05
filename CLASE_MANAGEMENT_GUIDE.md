# Guía de Gestión de Clases Personalizada - YOLO Multi-Class Annotator

## 🎯 Visión General

El sistema de gestión de clases personalizada permite a cada usuario crear, editar y organizar sus propias clases de anotación, tanto a nivel global como específico por sesión. Esta funcionalidad proporciona flexibilidad total para adaptar el anotador a diferentes proyectos y necesidades.

## ✨ Características Principales

### 🔧 Gestión Completa de Clases
- **Crear nuevas clases** con nombres y colores personalizados
- **Editar clases existentes** (nombre y color)
- **Eliminar clases** no utilizadas
- **Activar/Desactivar** clases temporalmente
- **Reset a configuración por defecto** con clases estándar

### 🌍 Tipos de Clases
1. **Clases Globales**: Disponibles para todos los usuarios (solo administradores)
2. **Clases Generales**: Específicas del usuario, disponibles en todas sus sesiones
3. **Clases de Sesión**: Específicas para una sesión particular

### 🎨 Personalización Visual
- **Colores hexadecimales** personalizados (#RRGGBB)
- **Previsualización en tiempo real** de los colores
- **Validación automática** de formatos de color
- **Interfaz modal intuitiva** integrada en el anotador

## 🚀 Cómo Usar el Sistema

### 1. Acceder a la Gestión de Clases

En la interfaz del anotador, busca el botón **"Gestionar Clases"** en la barra de herramientas. Este abrirá la ventana modal de gestión.

### 2. Crear una Nueva Clase

1. Click en **"Nueva Clase"**
2. Introduce el **nombre** de la clase
3. Selecciona un **color** usando el selector de color
4. Especifica el **ámbito**:
   - **General**: Disponible en todas tus sesiones
   - **Esta Sesión**: Solo para la sesión actual
5. Click en **"Guardar"**

### 3. Editar Clase Existente

1. Localiza la clase en la lista
2. Click en el icono de **"Editar"** (lápiz)
3. Modifica nombre y/o color
4. Click en **"Actualizar"**

### 4. Eliminar Clase

1. Localiza la clase en la lista
2. Click en el icono de **"Eliminar"** (papelera)
3. Confirma la eliminación

### 5. Reset a Configuración por Defecto

1. Click en **"Resetear Clases"**
2. Confirma la acción
3. Se crearán las clases estándar: person, car, bicycle, dog, cat, etc.

## 🗃️ Estructura de Base de Datos

### Tabla: `annotation_classes` (PostgreSQL) / `AnnotationClasses` (SQL Server)

```sql
-- Campos principales
id              -- ID único de la clase
user_id         -- ID del usuario propietario
name            -- Nombre de la clase
color           -- Color en formato hexadecimal (#RRGGBB)
session_name    -- Nombre de sesión (NULL para clases generales)
is_global       -- TRUE si es clase global (solo admin)
is_active       -- TRUE si la clase está activa
created_at      -- Timestamp de creación
updated_at      -- Timestamp de última actualización
```

### Índices y Constrains
- **Índice único**: (user_id, session_name, name) - Evita duplicados
- **Validación de color**: Formato hexadecimal válido
- **Validación de nombre**: No vacío, longitud mínima
- **Foreign keys**: Integridad referencial con usuarios y proyectos

## 🔌 API Endpoints

### Obtener Clases del Usuario
```http
GET /api/classes?session_name={session_name}&include_global={boolean}
```

### Crear Nueva Clase
```http
POST /api/classes
Content-Type: application/json

{
    "name": "nombre_clase",
    "color": "#FF5733",
    "session_name": "session_opcional",
    "is_global": false
}
```

### Actualizar Clase
```http
PUT /api/classes/{class_id}
Content-Type: application/json

{
    "name": "nuevo_nombre",
    "color": "#33FF57",
    "is_active": true
}
```

### Eliminar Clase
```http
DELETE /api/classes/{class_id}
```

### Reset a Clases por Defecto
```http
POST /api/classes/reset-default?session_name={session_name}
```

## 📊 Vistas y Estadísticas

### Estadísticas por Usuario
```sql
-- PostgreSQL
SELECT * FROM user_class_statistics WHERE user_id = $1;

-- SQL Server  
SELECT * FROM vw_ClassStatsByUser WHERE UserId = @user_id;
```

### Clases Más Populares
```sql
-- PostgreSQL
SELECT * FROM popular_classes_view ORDER BY used_by_users DESC;

-- SQL Server
SELECT * FROM vw_PopularClasses ORDER BY UsedByUsers DESC;
```

### Resumen de Gestión
```sql
-- SQL Server
SELECT * FROM vw_ClassManagementSummary WHERE CreatedBy = @username;
```

## 🔧 Configuración de Despliegue

### 1. Base de Datos PostgreSQL/Supabase
```bash
# Ejecutar script de migración
psql -h tu-host -U tu-usuario -d tu-db -f supabase_setup.sql
```

### 2. Base de Datos SQL Server
```bash
# Ejecutar script de migración
sqlcmd -S tu-servidor -d tu-db -i sqlserver_setup.sql
```

### 3. Configuración de la Aplicación
```python
# En el archivo de configuración
DATABASE_URL = "postgresql://user:password@host/db"
# o
DATABASE_URL = "mssql+pyodbc://user:password@host/db?driver=ODBC+Driver+17+for+SQL+Server"
```

## 🛠️ Stored Procedures (SQL Server)

### Crear Clases por Defecto
```sql
EXEC sp_CreateDefaultClasses @UserId = 1, @SessionName = 'mi_session';
```

### Obtener Clases de Usuario
```sql
EXEC sp_GetUserClasses @UserId = 1, @SessionName = 'mi_session', @IncludeGlobal = 1;
```

### Estadísticas de Clases
```sql
EXEC sp_GetClassStatistics @UserId = 1;
```

## 📝 Funciones PostgreSQL

### Crear Clases por Defecto
```sql
SELECT create_default_annotation_classes(1, 'mi_session');
```

### Obtener Clases de Usuario  
```sql
SELECT * FROM get_user_annotation_classes(1, 'mi_session', true);
```

### Estadísticas de Usuario
```sql
SELECT * FROM get_user_class_statistics(1);
```

## 🎯 Mejores Prácticas

### 1. Nomenclatura de Clases
- Usa nombres descriptivos y únicos
- Evita caracteres especiales
- Considera la consistencia entre proyectos

### 2. Gestión de Colores
- Usa colores contrastantes para mejor visibilidad
- Mantén coherencia cromática en proyectos relacionados
- Evita colores muy similares entre clases

### 3. Organización por Sesiones
- Crea clases específicas para proyectos especializados
- Usa clases generales para categorías comunes
- Aprovecha las clases globales para estándares organizacionales

### 4. Mantenimiento
- Elimina clases no utilizadas regularmente
- Usa la función de reset cuando cambies de proyecto
- Mantén activas solo las clases necesarias

## 🔍 Troubleshooting

### Problema: No puedo crear clases duplicadas
**Solución**: El sistema previene duplicados por diseño. Usa nombres únicos por sesión.

### Problema: El color no se guarda correctamente
**Solución**: Verifica que el formato sea hexadecimal válido (#RRGGBB).

### Problema: Las clases no aparecen en el anotador
**Solución**: Verifica que las clases estén activas (is_active = true).

### Problema: Error de permisos al crear clases globales
**Solución**: Solo usuarios administradores pueden crear clases globales.

## 📞 Soporte

Para problemas adicionales o consultas específicas:
1. Revisa los logs de la aplicación
2. Verifica la configuración de base de datos
3. Consulta la documentación de la API
4. Contacta al equipo de desarrollo

---

*Esta guía cubre el sistema completo de gestión de clases personalizada. El sistema está diseñado para ser intuitivo y flexible, adaptándose a las necesidades específicas de cada usuario y proyecto.*

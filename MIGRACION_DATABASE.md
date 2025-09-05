# 🚀 YOLO Multi-Class Annotator - Guía de Migración a Bases de Datos

## 📋 Índice

1. [Preparación General](#preparación-general)
2. [Migración a Supabase (PostgreSQL)](#migración-a-supabase-postgresql)
3. [Migración a SQL Server](#migración-a-sql-server)
4. [Comparación de Opciones](#comparación-de-opciones)
5. [Solución de Problemas](#solución-de-problemas)
6. [Mantenimiento](#mantenimiento)

---

## 📚 Preparación General

### Requisitos Previos

```bash
# Instalar dependencias adicionales
pip install sqlalchemy psycopg2-binary pyodbc supabase

# Para SQL Server en Linux/Mac
# Linux: sudo apt-get install msodbcsql17
# Mac: brew install msodbcsql17
```

### Backup de Datos Actuales

```bash
# Crear backup de SQLite actual
cp users.db users_backup_$(date +%Y%m%d_%H%M%S).db

# Exportar datos en formato SQL (opcional)
sqlite3 users.db .dump > backup_dump.sql
```

---

## 🌐 Migración a Supabase (PostgreSQL)

### 1. Configuración en Supabase

1. **Crear Proyecto en Supabase:**
   - Ve a https://supabase.com
   - Crear nuevo proyecto
   - Anota la URL y API Key

2. **Ejecutar Script de Setup:**
   ```sql
   -- Ejecutar supabase_setup.sql en el SQL Editor de Supabase
   -- El script creará todas las tablas, políticas RLS, triggers, etc.
   ```

3. **Configurar Variables de Entorno:**
   ```bash
   # Copiar template
   cp .env.supabase.template .env
   
   # Editar .env con tus credenciales de Supabase
   SUPABASE_URL=https://tu-proyecto.supabase.co
   SUPABASE_KEY=tu-anon-key
   SUPABASE_SERVICE_KEY=tu-service-role-key
   ```

### 2. Actualizar Aplicación

```python
# En app_auth.py, cambiar import
from auth.database_supabase import get_db, test_connection, migrate_from_sqlite

# Probar conexión
python -c "from auth.database_supabase import test_connection; test_connection()"

# Migrar datos (OPCIONAL - solo si tienes datos en SQLite)
python -c "from auth.database_supabase import migrate_from_sqlite; migrate_from_sqlite()"
```

### 3. Verificación

```python
# Verificar migración
python -c "
from auth.database_supabase import run_database_tests
run_database_tests()
"
```

### 4. Características Supabase

✅ **Incluidas:**
- Row Level Security (RLS) automática
- API REST automática
- Autenticación integrada (opcional)
- Dashboard web
- Backups automáticos
- Edge Functions
- Real-time subscriptions

📊 **Monitoring:**
```sql
-- Ver estadísticas de uso
SELECT * FROM vw_UserStats;

-- Ver actividad reciente
SELECT * FROM vw_RecentSessions;

-- Limpiar datos
SELECT cleanup_expired_data();
```

---

## 🏢 Migración a SQL Server

### 1. Configuración de SQL Server

#### Opción A: SQL Server On-Premise

```sql
-- 1. Crear base de datos
CREATE DATABASE YOLOAnnotator;
GO

-- 2. Usar la base de datos
USE YOLOAnnotator;
GO

-- 3. Ejecutar sqlserver_setup.sql
-- (Copiar y pegar el contenido del archivo)
```

#### Opción B: Azure SQL Database

1. **Crear en Azure Portal:**
   - Crear SQL Server
   - Crear Base de Datos
   - Configurar firewall

2. **Ejecutar Setup:**
   ```sql
   -- Conectar con SQL Server Management Studio o Azure Data Studio
   -- Ejecutar sqlserver_setup.sql
   ```

### 2. Configurar Variables de Entorno

```bash
# Copiar template
cp .env.sqlserver.template .env

# Para SQL Server on-premise
SQL_SERVER_HOST=localhost
SQL_SERVER_DATABASE=YOLOAnnotator
SQL_SERVER_USERNAME=sa
SQL_SERVER_PASSWORD=tu-password

# Para Azure SQL
USE_AZURE_SQL=true
AZURE_SQL_SERVER=tu-servidor.database.windows.net
AZURE_SQL_DATABASE=YOLOAnnotator
AZURE_SQL_USERNAME=tu-usuario
AZURE_SQL_PASSWORD=tu-password
```

### 3. Actualizar Aplicación

```python
# En app_auth.py, cambiar import
from auth.database_sqlserver import get_db, test_connection, migrate_from_sqlite

# Probar conexión
python -c "from auth.database_sqlserver import test_connection; test_connection()"

# Migrar datos
python -c "from auth.database_sqlserver import migrate_from_sqlite; migrate_from_sqlite()"
```

### 4. Características SQL Server

✅ **Incluidas:**
- Stored procedures optimizados
- Triggers para auditoría
- Índices avanzados
- Vistas especializadas
- Jobs de mantenimiento automático
- Compresión de datos
- Particionamiento (Enterprise)

📊 **Monitoring:**
```sql
-- Ejecutar stored procedures
EXEC sp_GetUserStats;
EXEC sp_GetDatabaseHealth;
EXEC sp_CleanupExpiredTokens;

-- Ver performance
SELECT * FROM vw_PerformanceMetrics;
```

---

## ⚖️ Comparación de Opciones

| Característica | SQLite (Actual) | Supabase | SQL Server |
|---|---|---|---|
| **Hosting** | Local | Cloud | Local/Azure |
| **Escalabilidad** | Limitada | Alta | Muy Alta |
| **Concurrencia** | Baja | Alta | Muy Alta |
| **Costo** | Gratis | Freemium | Licencia/Azure |
| **Complejidad Setup** | Baja | Media | Alta |
| **Features Avanzadas** | Básicas | Muchas | Completas |
| **Backup** | Manual | Automático | Configurable |
| **Monitoring** | Básico | Dashboard | Completo |

### Recomendaciones por Escenario

🏠 **Desarrollo/Testing:** SQLite (actual)
🌐 **Startup/Small Team:** Supabase
🏢 **Enterprise:** SQL Server

---

## 🔧 Solución de Problemas

### Problemas Comunes con Supabase

```bash
# Error de conexión
❌ Error: connection to server failed
✅ Verificar URL y API keys
✅ Verificar firewall/network

# Error de RLS
❌ Error: new row violates row-level security
✅ Verificar políticas RLS en dashboard
✅ Usar service role key para admin operations
```

### Problemas Comunes con SQL Server

```bash
# Error de driver
❌ Error: ODBC Driver 17 not found
✅ Instalar driver ODBC
✅ Verificar nombre exacto del driver

# Error de conexión
❌ Error: Login failed
✅ Verificar credenciales
✅ Verificar SQL Server Authentication habilitado
✅ Verificar firewall (puerto 1433)

# Error de Azure SQL
❌ Error: Server not found
✅ Verificar nombre completo del servidor
✅ Verificar firewall rules en Azure
```

### Testing de Conexiones

```python
# Test rápido Supabase
python -c "
import os
os.environ['SUPABASE_URL'] = 'tu-url'
os.environ['SUPABASE_KEY'] = 'tu-key'
from auth.database_supabase import test_connection
test_connection()
"

# Test rápido SQL Server
python -c "
import os
os.environ['SQL_SERVER_HOST'] = 'localhost'
os.environ['SQL_SERVER_PASSWORD'] = 'tu-password'
from auth.database_sqlserver import test_connection
test_connection()
"
```

---

## 🛠️ Mantenimiento

### Tareas Regulares

#### Supabase
```sql
-- Ejecutar semanalmente
SELECT cleanup_expired_data();

-- Monitorear uso
SELECT * FROM vw_UserStats;
```

#### SQL Server
```sql
-- Los jobs automáticos se encargan de:
-- - Cleanup diario de tokens expirados
-- - Rebuild de índices semanal
-- - Update de estadísticas diario
-- - Backup automático

-- Monitoreo manual:
EXEC sp_GetDatabaseHealth;
```

### Backup y Restore

#### Supabase
```bash
# Backup automático incluido
# Export manual desde dashboard si necesario
```

#### SQL Server
```sql
-- Backup manual
BACKUP DATABASE YOLOAnnotator 
TO DISK = 'C:\backup\YOLOAnnotator.bak'

-- Restore
RESTORE DATABASE YOLOAnnotator 
FROM DISK = 'C:\backup\YOLOAnnotator.bak'
```

### Monitoring de Performance

```python
# Script de monitoreo automático
import schedule
import time

def monitor_database():
    """Función para monitorear BD automáticamente"""
    try:
        # Para Supabase
        from auth.database_supabase import get_database_stats
        stats = get_database_stats()
        
        # Para SQL Server
        # from auth.database_sqlserver import get_database_size
        # stats = get_database_size()
        
        print(f"📊 DB Size: {stats}")
        
        # Enviar alertas si es necesario
        # send_alert_if_needed(stats)
        
    except Exception as e:
        print(f"❌ Error monitoring: {e}")

# Ejecutar cada hora
schedule.every().hour.do(monitor_database)

# Mantener corriendo
while True:
    schedule.run_pending()
    time.sleep(60)
```

---

## 🎯 Checklist de Migración

### Pre-Migración
- [ ] Backup de datos actuales
- [ ] Instalar dependencias necesarias
- [ ] Configurar credenciales de BD
- [ ] Probar conexión a nueva BD

### Durante Migración
- [ ] Ejecutar scripts de setup
- [ ] Actualizar imports en aplicación
- [ ] Migrar datos de SQLite
- [ ] Probar funcionalidad básica

### Post-Migración
- [ ] Ejecutar tests completos
- [ ] Verificar performance
- [ ] Configurar monitoring
- [ ] Documentar cambios
- [ ] Entrenar al equipo

### Rollback Plan
- [ ] Mantener backup SQLite
- [ ] Documentar proceso de rollback
- [ ] Probar rollback en ambiente test

---

## 📞 Soporte

Si encuentras problemas durante la migración:

1. **Revisar logs de error detallados**
2. **Consultar documentación oficial:**
   - [Supabase Docs](https://supabase.com/docs)
   - [SQL Server Docs](https://docs.microsoft.com/sql/)
3. **Verificar configuración de red/firewall**
4. **Probar con herramientas nativas:**
   - pgAdmin para PostgreSQL
   - SQL Server Management Studio

---

*Guía creada para YOLO Multi-Class Annotator - Migración de Bases de Datos*

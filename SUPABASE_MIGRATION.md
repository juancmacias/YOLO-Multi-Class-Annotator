# 🚀 YOLO Multi-Class Annotator - Migración a Supabase

Esta guía te ayudará a migrar tu aplicación YOLO Multi-Class Annotator de SQLite local a Supabase (PostgreSQL en la nube).

## 📋 Prerrequisitos

1. **Cuenta de Supabase**: [Crear cuenta gratuita](https://supabase.com)
2. **Python 3.8+** con las dependencias actuales
3. **Datos existentes** en SQLite (opcional para migración)

## 🗃️ Archivos Incluidos

- `supabase_setup.sql` - Script SQL completo para crear la base de datos
- `database_supabase.py` - Configuración Python para Supabase
- `SUPABASE_MIGRATION.md` - Esta guía de migración

## 🏗️ Paso 1: Configurar Proyecto en Supabase

### 1.1 Crear Nuevo Proyecto
1. Ve a [app.supabase.com](https://app.supabase.com)
2. Haz clic en "New Project"
3. Selecciona tu organización
4. Nombre del proyecto: `yolo-multi-class-annotator`
5. Contraseña de la base de datos: **¡Guárdala segura!**
6. Región: Selecciona la más cercana a tus usuarios
7. Haz clic en "Create new project"

### 1.2 Obtener Credenciales
Una vez creado el proyecto:
1. Ve a **Settings > API**
2. Copia los siguientes valores:
   - `URL` (Project URL)
   - `anon public` (Anon key)
   - `service_role` (Service key - ¡mantén secreto!)

3. Ve a **Settings > Database**
4. Copia la cadena de conexión:
   - Host: `db.xxx.supabase.co`
   - Puerto: `5432`
   - Database: `postgres`
   - User: `postgres`
   - Password: La que configuraste al crear el proyecto

## 🛠️ Paso 2: Ejecutar Script SQL

### 2.1 En el Dashboard de Supabase
1. Ve a **SQL Editor** en el panel izquierdo
2. Haz clic en "New Query"
3. Copia y pega todo el contenido de `supabase_setup.sql`
4. Haz clic en "Run" (▶️)
5. Verifica que no hay errores en la consola

### 2.2 Verificar Tablas Creadas
1. Ve a **Table Editor**
2. Deberías ver las siguientes tablas:
   - `users`
   - `user_sessions` 
   - `token_blacklist`
   - `projects` (para futuras versiones)
   - `annotation_classes`
   - `images`
   - `annotations`

## ⚙️ Paso 3: Configurar Variables de Entorno

### 3.1 Crear Archivo .env
Crea un archivo `.env` en la carpeta `app-jwt/` con el siguiente contenido:

```bash
# ========================================================
# SUPABASE CONFIGURATION
# ========================================================

# Reemplaza con tus valores reales de Supabase
SUPABASE_URL=https://tu-proyecto-id.supabase.co
SUPABASE_ANON_KEY=tu-clave-anon-aqui
SUPABASE_SERVICE_KEY=tu-clave-service-aqui

# URL completa de PostgreSQL
DATABASE_URL=postgresql://postgres:tu-password@db.tu-proyecto-id.supabase.co:5432/postgres

# ========================================================
# JWT CONFIGURATION (mantener actual)
# ========================================================

SECRET_KEY=tu-clave-secreta-actual
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 3.2 Actualizar requirements.txt
Agrega las siguientes dependencias:

```txt
# Dependencias existentes...

# Nuevas dependencias para Supabase
psycopg2-binary==2.9.7
supabase==1.0.4
python-dotenv==1.0.0
```

### 3.3 Instalar Dependencias
```bash
cd app-jwt
pip install -r requirements.txt
```

## 🔄 Paso 4: Modificar Código de la Aplicación

### 4.1 Actualizar database.py
Reemplaza el contenido de `auth/database.py` con:

```python
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

# Cargar variables de entorno
load_dotenv()

# URL de la base de datos (PostgreSQL en lugar de SQLite)
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL no configurada en variables de entorno")

# Crear engine para PostgreSQL
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=10,
    max_overflow=20
)

# Crear SessionLocal
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency para obtener sesión de DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Crear todas las tablas (solo para desarrollo)
def create_tables():
    Base.metadata.create_all(bind=engine)

def test_connection():
    """Probar conexión a la base de datos"""
    try:
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            print("✅ Conexión a Supabase exitosa!")
            return True
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False
```

### 4.2 Actualizar app_auth.py
Al inicio del archivo, agrega:

```python
from dotenv import load_dotenv

# Cargar variables de entorno al inicio
load_dotenv()
```

### 4.3 Agregar Verificación de Conexión
En `app_auth.py`, después de `create_tables()`:

```python
# Verificar conexión a Supabase
from auth.database import test_connection

if test_connection():
    print("🎉 Aplicación conectada a Supabase exitosamente!")
else:
    print("❌ Error de conexión a Supabase. Verifica tu configuración.")
    exit(1)
```

## 📊 Paso 5: Migrar Datos Existentes (Opcional)

Si tienes datos existentes en SQLite:

### 5.1 Usando el Script de Migración
```python
# En una terminal Python
from auth.database_supabase import migrate_from_sqlite

# Migrar datos desde SQLite local
migrate_from_sqlite("./users.db")
```

### 5.2 Migración Manual
Si prefieres migrar manualmente:

1. **Exportar usuarios desde SQLite:**
```sql
SELECT * FROM users;
```

2. **Insertar en Supabase** (usando SQL Editor):
```sql
INSERT INTO users (username, email, hashed_password, is_admin) 
VALUES ('admin', 'admin@ejemplo.com', '$2b$12$hash...', true);
```

## 🧪 Paso 6: Probar la Aplicación

### 6.1 Ejecutar Tests
```bash
cd app-jwt
python -c "from auth.database_supabase import run_database_tests; run_database_tests()"
```

### 6.2 Iniciar Aplicación
```bash
python app_auth.py
```

### 6.3 Verificar Funcionalidad
1. Registrar nuevo usuario
2. Hacer login
3. Crear sesión de anotación
4. Verificar que los datos se guardan en Supabase

## 🔐 Paso 7: Configuración de Seguridad

### 7.1 Row Level Security (RLS)
El script SQL ya habilita RLS. Para verificar:
1. Ve a **Authentication > Policies** en Supabase
2. Verifica que las políticas están activas
3. Personaliza según tus necesidades

### 7.2 Configuración de Auth (Opcional)
Para usar Supabase Auth en lugar de JWT custom:
1. Ve a **Authentication > Settings**
2. Configura proveedores de auth (email, Google, etc.)
3. Actualiza la aplicación para usar `supabase.auth`

## 🚀 Paso 8: Despliegue en Producción

### 8.1 Variables de Entorno en Producción
```bash
# En tu servidor/hosting
export SUPABASE_URL="https://tu-proyecto.supabase.co"
export SUPABASE_ANON_KEY="tu-clave-anon"
export DATABASE_URL="postgresql://postgres:password@db.proyecto.supabase.co:5432/postgres"
export SECRET_KEY="clave-super-secreta-en-produccion"
```

### 8.2 Configuraciones Adicionales
- Habilitar HTTPS en tu dominio
- Configurar CORS en Supabase si es necesario
- Establecer límites de rate limiting
- Configurar backups automáticos

## 📈 Monitoreo y Mantenimiento

### 9.1 Dashboard de Supabase
- **Database > Logs**: Ver queries y errores
- **API > Logs**: Monitorear requests
- **Reports**: Estadísticas de uso

### 9.2 Limpieza Automática
El script incluye una función para limpiar tokens expirados:
```sql
SELECT cleanup_expired_tokens();
```

Configura un cron job para ejecutarla periódicamente.

## 🆘 Troubleshooting

### Errores Comunes

1. **Error de conexión**: Verifica URL y credenciales
2. **Permisos RLS**: Asegúrate de que las políticas están correctas
3. **Límites de conexión**: Ajusta `pool_size` si es necesario
4. **Migraciones**: Verifica que las tablas existen antes de migrar

### Logs Útiles
```bash
# Ver logs de PostgreSQL en Supabase
tail -f /var/log/postgresql/postgresql.log

# Debug SQL en la aplicación
# Cambiar echo=True en create_engine()
```

## 🎉 Conclusión

¡Felicitaciones! Tu aplicación YOLO Multi-Class Annotator ahora está funcionando con Supabase. Esto te proporciona:

✅ **Escalabilidad**: Base de datos PostgreSQL empresarial
✅ **Respaldos**: Automáticos y configurables  
✅ **Seguridad**: RLS, SSL, y políticas de acceso
✅ **Monitoreo**: Dashboard completo y métricas
✅ **API**: Endpoints automáticos para tus tablas
✅ **Auth**: Sistema de autenticación robusto (opcional)

## 📚 Recursos Adicionales

- [Documentación de Supabase](https://supabase.com/docs)
- [Guía de PostgreSQL](https://www.postgresql.org/docs/)
- [SQLAlchemy con PostgreSQL](https://docs.sqlalchemy.org/en/14/dialects/postgresql.html)
- [Supabase Python Client](https://github.com/supabase-community/supabase-py)

---

**¿Necesitas ayuda?** Abre un issue en el repositorio o consulta la documentación de Supabase.

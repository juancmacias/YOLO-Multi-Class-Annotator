# 🔒 Mejores Prácticas de Seguridad y Despliegue

## 🔐 Configuración de Seguridad

### 1. JWT Secret Key
- **Generar clave fuerte**: Mínimo 32 caracteres aleatorios
- **Nunca usar la clave por defecto**
- **Rotar claves periódicamente**

```python
# Generar clave segura
import secrets
jwt_secret = secrets.token_urlsafe(32)
print(f"JWT_SECRET_KEY={jwt_secret}")
```

### 2. Base de Datos
- **Usuario específico**: Crear usuario dedicado para la aplicación
- **Permisos mínimos**: Solo los necesarios para yolo_annotator
- **Conexión SSL**: Habilitar en producción

```sql
-- Configuración segura MySQL
CREATE USER 'yolo_app'@'localhost' IDENTIFIED BY 'password_muy_fuerte';
GRANT SELECT, INSERT, UPDATE, DELETE ON yolo_annotator.* TO 'yolo_app'@'localhost';
FLUSH PRIVILEGES;
```

### 3. Variables de Entorno
- **Nunca commitear .env** al repositorio
- **Usar variables de entorno del sistema** en producción
- **Validar configuración** al inicio

## 🚀 Despliegue en Producción

### 1. Con Docker (Recomendado)
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8002

CMD ["uvicorn", "app_auth:app", "--host", "0.0.0.0", "--port", "8002"]
```

### 2. Con Gunicorn + Nginx
```bash
# Instalar gunicorn
pip install gunicorn

# Ejecutar con workers
gunicorn app_auth:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8002
```

### 3. Variables de Entorno Producción
```env
# Producción
DEBUG=False
HOST=0.0.0.0
PORT=8002

# Base de datos
DB_HOST=production-mysql-server
DB_SSL_MODE=REQUIRED

# Seguridad
JWT_SECRET_KEY=tu-clave-super-secreta-de-64-caracteres-minimo
ALLOWED_HOSTS=tu-dominio.com,api.tu-dominio.com
```

## 📊 Monitoreo y Logs

### 1. Configurar Logs
```python
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
```

### 2. Métricas Básicas
- **Requests por minuto**
- **Tiempo de respuesta promedio**  
- **Errores 4xx/5xx**
- **Usuarios activos**
- **Sesiones creadas**

## 🔧 Optimización de Rendimiento

### 1. Base de Datos
```sql
-- Índices recomendados
CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_hash ON user_sessions(session_hash);
CREATE INDEX idx_annotation_classes_session ON annotation_classes(session_name);
```

### 2. Archivos Estáticos
- **CDN**: Servir CSS/JS desde CDN
- **Compresión**: Gzip habilitado
- **Cache**: Headers apropiados

### 3. Imágenes
- **Límite de tamaño**: Máximo 10MB por imagen
- **Compresión**: JPEG con calidad 85%
- **Thumbnails**: Generar previsualizaciones

## 🔄 Backup y Recuperación

### 1. Base de Datos
```bash
# Backup diario
mysqldump -u user -p yolo_annotator > backup_$(date +%Y%m%d).sql

# Restaurar
mysql -u user -p yolo_annotator < backup_20231205.sql
```

### 2. Archivos de Anotaciones
```bash
# Backup de annotations/
tar -czf annotations_backup_$(date +%Y%m%d).tar.gz annotations/

# Sincronización con storage externo
rsync -av annotations/ backup-server:/backups/yolo-annotations/
```

## 🚨 Troubleshooting Común

### 1. Memory Issues
```bash
# Aumentar límites si hay muchas imágenes
export UVICORN_MAX_WORKERS=2
export PYTHON_MEMORY_LIMIT=2GB
```

### 2. MySQL Connection Pool
```python
# En database.py - ajustar pool
engine = create_engine(
    database_url,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True
)
```

### 3. File Upload Limits
```python
# En app_auth.py - aumentar límite
app.add_middleware(
    MaxSizeMiddleware, 
    max_size=50_000_000  # 50MB
)
```

## 📋 Checklist Pre-Producción

- [ ] JWT secret único y seguro
- [ ] Base de datos con usuario dedicado
- [ ] SSL/TLS habilitado
- [ ] Logs configurados
- [ ] Backup automático
- [ ] Monitoreo activo
- [ ] Variables de entorno validadas
- [ ] Pruebas de carga realizadas
- [ ] Documentación actualizada
- [ ] Plan de rollback definido

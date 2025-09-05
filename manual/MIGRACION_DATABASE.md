# 🚀 YOLO Multi-Class Annotator - Guía de Base de Datos MySQL

## 📋 Índice

1. [Configuración MySQL](#configuración-mysql)
2. [Migración desde SQLite](#migración-desde-sqlite)
3. [Mantenimiento y Backup](#mantenimiento-y-backup)
4. [Solución de Problemas](#solución-de-problemas)
5. [Optimización](#optimización)

---

## 🗄️ Configuración MySQL

### Requisitos Previos

```bash
# Instalar dependencias de MySQL
pip install pymysql cryptography sqlalchemy

# MySQL Server instalado y corriendo
# Windows: Descargar desde mysql.com
# Linux: sudo apt-get install mysql-server
# Mac: brew install mysql
```

### Configuración de Base de Datos

```sql
-- Conectar a MySQL como root
mysql -u root -p

-- Crear base de datos
CREATE DATABASE yolo_annotator 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

-- Crear usuario dedicado
CREATE USER 'yolo_user'@'localhost' IDENTIFIED BY 'password_seguro';
GRANT ALL PRIVILEGES ON yolo_annotator.* TO 'yolo_user'@'localhost';
FLUSH PRIVILEGES;

-- Verificar creación
SHOW DATABASES;
SELECT User, Host FROM mysql.user WHERE User = 'yolo_user';
```

### Variables de Entorno

```env
# .env - Configuración MySQL
DB_HOST=localhost
DB_PORT=3306
DB_USER=yolo_user
DB_PASSWORD=password_seguro
DB_NAME=yolo_annotator

# JWT y configuración del servidor
JWT_SECRET_KEY=tu-clave-super-secreta-jwt
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440
HOST=127.0.0.1
PORT=8002
DEBUG=True
```

---

## 🔄 Migración desde SQLite

### Script de Migración Automática

```python
#!/usr/bin/env python3
"""
Script de migración de SQLite a MySQL
"""
import sqlite3
import pymysql
from sqlalchemy import create_engine
from auth.database import get_db
from auth.models import Base, User, UserSession, AnnotationClass
import os

def migrate_sqlite_to_mysql():
    """Migrar datos de SQLite a MySQL"""
    
    # Conectar a SQLite
    sqlite_db = "users.db"  # Ruta a tu BD SQLite
    if not os.path.exists(sqlite_db):
        print("❌ No se encontró base de datos SQLite")
        return
    
    # Crear tablas en MySQL
    from auth.database import engine
    Base.metadata.create_all(bind=engine)
    print("✅ Tablas MySQL creadas")
    
    # Conectar a SQLite
    sqlite_conn = sqlite3.connect(sqlite_db)
    sqlite_cursor = sqlite_conn.cursor()
    
    # Obtener datos de usuarios
    sqlite_cursor.execute("SELECT * FROM users")
    users_data = sqlite_cursor.fetchall()
    
    # Migrar usuarios a MySQL
    db = next(get_db())
    
    for user_row in users_data:
        # Adaptar según tu estructura de SQLite
        user = User(
            username=user_row[1],
            email=user_row[2],
            hashed_password=user_row[3],
            is_admin=bool(user_row[4]),
            is_active=True
        )
        db.add(user)
    
    db.commit()
    print(f"✅ Migrados {len(users_data)} usuarios")
    
    # Cerrar conexiones
    sqlite_conn.close()
    db.close()

if __name__ == "__main__":
    migrate_sqlite_to_mysql()
```

---

## 🔧 Mantenimiento y Backup

### Backup Automático

```bash
#!/bin/bash
# backup_mysql.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/yolo_annotator"
mkdir -p $BACKUP_DIR

# Backup completo
mysqldump -u yolo_user -p yolo_annotator > $BACKUP_DIR/backup_$DATE.sql

# Comprimir backup
gzip $BACKUP_DIR/backup_$DATE.sql

echo "✅ Backup completado: backup_$DATE.sql.gz"
```

---

## 🚨 Solución de Problemas

### Error de Conexión

```bash
# Verificar si MySQL está corriendo
sudo systemctl status mysql  # Linux
brew services list | grep mysql  # Mac

# Reiniciar MySQL
sudo systemctl restart mysql  # Linux
brew services restart mysql  # Mac
```

### Error de Permisos

```sql
-- Verificar permisos del usuario
SHOW GRANTS FOR 'yolo_user'@'localhost';

-- Otorgar permisos si es necesario
GRANT ALL PRIVILEGES ON yolo_annotator.* TO 'yolo_user'@'localhost';
FLUSH PRIVILEGES;
```

---

## ⚡ Optimización

### Índices Recomendados

```sql
-- Índices para mejor rendimiento
USE yolo_annotator;

-- Índices en tabla users
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);

-- Índices en tabla user_sessions
CREATE INDEX idx_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_sessions_hash ON user_sessions(session_hash);

-- Índices en tabla annotation_classes
CREATE INDEX idx_annotations_session ON annotation_classes(session_name);
CREATE INDEX idx_annotations_user ON annotation_classes(user_id);
```

---

**✅ MySQL es la base de datos recomendada para el YOLO Multi-Class Annotator**  
- **Rendimiento**: Excelente para aplicaciones web
- **Confiabilidad**: Probado en producción durante décadas  
- **Facilidad**: Configuración sencilla y bien documentada
- **Soporte**: Amplia comunidad y recursos disponibles

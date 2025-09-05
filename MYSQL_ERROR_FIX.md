# 🛠️ Solución al Error #1064 en phpMyAdmin

## 🚨 **Problema Identificado**
El error #1064 en la línea 10 indica un problema de sintaxis. Esto se debe a configuraciones específicas que algunos servidores MySQL no aceptan.

## ✅ **Solución: Ejecutar Paso a Paso**

### **Opción 1: Usar el Script Simplificado**
He creado un script simplificado `mysql_simple_setup.sql` que elimina las configuraciones problemáticas.

### **Opción 2: Ejecutar Comandos Individuales**
Copia y pega estos comandos **uno por uno** en phpMyAdmin:

#### **Paso 1: Crear Base de Datos**
```sql
CREATE DATABASE IF NOT EXISTS yolo_annotator DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

#### **Paso 2: Seleccionar Base de Datos**
```sql
USE yolo_annotator;
```

#### **Paso 3: Crear Tabla de Usuarios**
```sql
CREATE TABLE users (
  id INT NOT NULL AUTO_INCREMENT,
  username VARCHAR(50) NOT NULL,
  email VARCHAR(100) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  is_active TINYINT(1) DEFAULT 1,
  is_admin TINYINT(1) DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  last_login TIMESTAMP NULL DEFAULT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uk_users_username (username),
  UNIQUE KEY uk_users_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

#### **Paso 4: Crear Tabla de Clases de Anotación (LA MÁS IMPORTANTE)**
```sql
CREATE TABLE annotation_classes (
  id INT NOT NULL AUTO_INCREMENT,
  user_id INT NOT NULL,
  project_id INT DEFAULT NULL,
  name VARCHAR(50) NOT NULL,
  color VARCHAR(7) NOT NULL DEFAULT '#FF0000',
  session_name VARCHAR(100) DEFAULT NULL,
  is_global TINYINT(1) DEFAULT 0,
  is_active TINYINT(1) DEFAULT 1,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_annotation_classes_user_session_name (user_id, session_name, name),
  CONSTRAINT fk_annotation_classes_user_id FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

#### **Paso 5: Insertar Usuario Administrador**
```sql
INSERT INTO users (username, email, password_hash, is_active, is_admin) VALUES 
('admin', 'admin@yolo-annotator.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj0WS8P5Vda6', 1, 1);
```

#### **Paso 6: Crear Clases por Defecto**
```sql
INSERT INTO annotation_classes (user_id, name, color, is_global, is_active) VALUES
(1, 'person', '#FF0000', 1, 1),
(1, 'vehicle', '#00FF00', 1, 1),
(1, 'animal', '#0000FF', 1, 1),
(1, 'object', '#FFFF00', 1, 1);
```

#### **Paso 7: Verificar Instalación**
```sql
SELECT 'INSTALACIÓN BÁSICA COMPLETADA' as status;
SHOW TABLES;
SELECT id, username, email, is_admin FROM users;
SELECT id, name, color, is_global FROM annotation_classes;
```

## 🎯 **Configuración Mínima para Funcionar**

Con estos pasos mínimos ya tendrás:
- ✅ Base de datos creada
- ✅ Tabla de usuarios 
- ✅ **Tabla de clases de anotación (funcionalidad principal)**
- ✅ Usuario administrador
- ✅ Clases básicas por defecto

## 📝 **Configurar la Aplicación**

Una vez completados los pasos, actualiza tu configuración:

```python
# En tu archivo de configuración
DATABASE_URL = "mysql+pymysql://tu_usuario:tu_password@localhost:3306/yolo_annotator"
```

## 🚀 **Tablas Adicionales (Opcional)**

Si necesitas todas las tablas, ejecuta estos comandos adicionales:

#### **Tabla de Proyectos**
```sql
CREATE TABLE projects (
  id INT NOT NULL AUTO_INCREMENT,
  name VARCHAR(100) NOT NULL,
  description TEXT,
  user_id INT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  is_active TINYINT(1) DEFAULT 1,
  PRIMARY KEY (id),
  CONSTRAINT fk_projects_user_id FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

#### **Tabla de Imágenes**
```sql
CREATE TABLE images (
  id INT NOT NULL AUTO_INCREMENT,
  filename VARCHAR(255) NOT NULL,
  original_filename VARCHAR(255) NOT NULL,
  file_path VARCHAR(500) NOT NULL,
  user_id INT NOT NULL,
  session_name VARCHAR(100) DEFAULT NULL,
  uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  is_annotated TINYINT(1) DEFAULT 0,
  annotation_count INT DEFAULT 0,
  PRIMARY KEY (id),
  CONSTRAINT fk_images_user_id FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

#### **Tabla de Anotaciones**
```sql
CREATE TABLE annotations (
  id INT NOT NULL AUTO_INCREMENT,
  image_id INT NOT NULL,
  user_id INT NOT NULL,
  class_id INT DEFAULT NULL,
  class_name VARCHAR(50) NOT NULL,
  x_center DECIMAL(10,8) NOT NULL,
  y_center DECIMAL(10,8) NOT NULL,
  width DECIMAL(10,8) NOT NULL,
  height DECIMAL(10,8) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  CONSTRAINT fk_annotations_image_id FOREIGN KEY (image_id) REFERENCES images (id) ON DELETE CASCADE,
  CONSTRAINT fk_annotations_user_id FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
  CONSTRAINT fk_annotations_class_id FOREIGN KEY (class_id) REFERENCES annotation_classes (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

## 🔍 **Si Sigues Teniendo Problemas**

### **Error Común: "SQL_MODE"**
Si ves errores relacionados con SQL_MODE, ignora esas líneas o ejecuta:
```sql
SET SESSION sql_mode = '';
```

### **Error: "IF NOT EXISTS"**
Si tu versión de MySQL no soporta `IF NOT EXISTS`, cambia:
```sql
CREATE DATABASE yolo_annotator DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### **Error: "AUTO_INCREMENT"**
Si tienes problemas con AUTO_INCREMENT, es normal en algunas configuraciones. El script debería funcionar igual.

## ✅ **Verificación Final**

Una vez completado, ejecuta:
```sql
USE yolo_annotator;
DESCRIBE annotation_classes;
SELECT COUNT(*) as total_classes FROM annotation_classes;
```

¡Con esto ya tendrás el sistema de gestión de clases personalizada funcionando en MySQL! 🎉

---

**💡 Tip**: Ejecuta los comandos uno por uno para identificar exactamente dónde ocurre cualquier error.

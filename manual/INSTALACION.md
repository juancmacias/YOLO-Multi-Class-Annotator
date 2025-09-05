# 📦 Guía de Instalación - YOLO Multi-Class Annotator

## 🎯 Requisitos Previos

### Python
- **Python 3.8+** (recomendado Python 3.10 o superior)
- **pip** (gestor de paquetes de Python)

### Base de Datos
- **MySQL Server 8.0+** 
- **Crear base de datos**: `yolo_annotator`

## 🚀 Instalación Paso a Paso

### 1. Clonar el Repositorio
```bash
git clone <repository-url>
cd YOLO-Multi-Class-Annotator
```

### 2. Crear Entorno Virtual (Recomendado)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

### 3. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno
```bash
# Copiar archivo de ejemplo
copy .env.example .env

# Editar .env con tus configuraciones
```

#### Ejemplo de configuración `.env`:
```env
# Base de datos MySQL
DB_HOST=localhost
DB_PORT=3306
DB_USER=tu_usuario
DB_PASSWORD=tu_password
DB_NAME=yolo_annotator

# JWT Configuration
JWT_SECRET_KEY=tu-clave-super-secreta-jwt-muy-larga
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Servidor
HOST=127.0.0.1
PORT=8002
DEBUG=True
```

### 5. Configurar MySQL
```sql
-- Conectar a MySQL y crear la base de datos
CREATE DATABASE yolo_annotator CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Crear usuario (opcional)
CREATE USER 'yolo_user'@'localhost' IDENTIFIED BY 'tu_password';
GRANT ALL PRIVILEGES ON yolo_annotator.* TO 'yolo_user'@'localhost';
FLUSH PRIVILEGES;
```

### 6. Ejecutar la Aplicación
```bash
python app_auth.py
```

### 7. Abrir en el Navegador
```
http://localhost:8002
```

## 🔧 Dependencias Explicadas

### Framework Web
- **FastAPI**: Framework moderno para APIs REST
- **Uvicorn**: Servidor ASGI de alto rendimiento
- **Jinja2**: Motor de plantillas HTML

### Procesamiento de Imágenes
- **Pillow (PIL)**: Manipulación básica de imágenes
- **OpenCV**: Computer vision y augmentaciones avanzadas
- **NumPy**: Operaciones numéricas y arrays

### Base de Datos
- **SQLAlchemy**: ORM para manejo de BD
- **PyMySQL**: Driver MySQL
- **Cryptography**: Seguridad para conexiones

### Autenticación
- **python-jose**: Tokens JWT
- **passlib**: Hash de contraseñas con bcrypt
- **pydantic**: Validación de datos

### Utilidades
- **python-dotenv**: Variables de entorno
- **pandas**: Análisis de datos
- **python-multipart**: Subida de archivos

## 🚨 Solución de Problemas

### Error: "Module not found"
```bash
pip install -r requirements.txt --upgrade
```

### Error MySQL Connection
1. Verificar que MySQL esté corriendo
2. Revisar credenciales en `.env`
3. Verificar que la base de datos existe

### Error Puerto 8002 en uso
```bash
# Cambiar puerto en .env
PORT=8003
```

### Error bcrypt
```bash
pip install --upgrade passlib[bcrypt]
```

## 📚 Uso Después de la Instalación

1. **Primera vez**: Crear cuenta (será admin automáticamente)
2. **Crear sesión privada**: Dashboard → Nueva Sesión
3. **Anotar imágenes**: Subir imagen y dibujar bounding boxes
4. **Compartir sesión**: Usar enlace único generado
5. **Augmentar datos**: Generar variaciones automáticas

## 🔄 Actualización

```bash
git pull origin main
pip install -r requirements.txt --upgrade
python app_auth.py
```

---

**¿Problemas?** Revisa los logs en la consola o crea un issue en el repositorio.

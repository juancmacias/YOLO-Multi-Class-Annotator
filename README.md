# YOLO Multi-Class Annotator con JWT Authentication y Sesiones Privadas

Sistema de anotación YOLO con autenticación JWT completa, gestión de usuarios, aislamiento de datos y sesiones privadas con acceso único.

## 🚀 Características Principales

- **Autenticación JWT**: Sistema seguro de login/registro con tokens
- **Multi-usuario**: Soporte para múltiples usuarios con datos completamente aislados
- **Sesiones privadas**: Cada sesión tiene un hash único para acceso exclusivo
- **Roles de usuario**: Administradores y usuarios regulares
- **Anotador YOLO**: Herramienta completa para crear bounding boxes
- **Visualizador avanzado**: Exploración interactiva de datasets
- **Augmentación de datos**: 6 variantes automáticas de imágenes
- **Base de datos MySQL**: Gestión robusta de datos
- **Descarga de datasets**: Exportación en formato ZIP

## 📦 Instalación

1. **Clonar el repositorio:**
```bash
git clone <repository-url>
cd YOLO-Multi-Class-Annotator
```

2. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

3. **Configurar variables de entorno:**
```bash
cp .env.example .env
# Editar .env con tus configuraciones de MySQL
```

4. **Configurar MySQL:**
   - Instalar MySQL Server
   - Crear base de datos `tu_data_base`
   - Configurar credenciales en `.env`

5. **Ejecutar la aplicación:**
```bash
python app_auth.py
```

6. **Abrir navegador:**
```
http://localhost:8002
```

## � Documentación Completa

Toda la documentación técnica está organizada en la carpeta [`manual/`](./manual/):

- **[📋 Índice completo](./manual/INDEX.md)** - Navegación por toda la documentación
- **[🚀 Guía de instalación](./manual/INSTALACION.md)** - Instalación paso a paso detallada
- **[🔧 Configuración MySQL](./manual/MYSQL_PHPMYADMIN_GUIDE.md)** - Setup de base de datos
- **[🔐 Sistema de autenticación](./manual/IMPLEMENTACION_AUTH_FASTAPI.md)** - JWT y seguridad
- **[🎯 Clases personalizadas](./manual/CLASES_PERSONALIZADAS.md)** - Gestión avanzada
- **[🚀 Despliegue en producción](./manual/PRODUCTION.md)** - Mejores prácticas

## �🔐 Primer Uso

1. **Registro inicial**: La primera cuenta creada será automáticamente administrador
2. **Login**: Inicia sesión con tus credenciales  
3. **Dashboard**: Accede a todas las funcionalidades desde el dashboard personal
4. **Crear sesión privada**: Cada sesión tendrá un hash único para acceso exclusivo

## 🛠️ Funcionalidades

### Autenticación y Sesiones Privadas
- **Registro/Login**: Sistema completo con validación
- **JWT Tokens**: Autenticación segura con tokens
- **Sesiones privadas**: Cada sesión tiene un hash SHA-256 único
- **Acceso exclusivo**: Solo el creador puede ver sus sesiones inicialmente
- **Enlaces compartibles**: URLs únicas para compartir sesiones específicas
- **Roles**: Admin (acceso total) y Usuario (datos propios)

### Anotación
- **Canvas dinámico**: Tamaños configurables (320, 640, 800px)
- **6 clases YOLO**: Colores diferenciados
- **Bounding boxes**: Creación por drag & drop
- **Atajos de teclado**: Números 1-6 para seleccionar clases
- **Vista previa**: Tiempo real de anotaciones

### Gestión de Datos
- **Sesiones por usuario**: Aislamiento completo de datos
- **Base de datos MySQL**: Gestión robusta y escalable
- **Subida de imágenes**: Múltiples formatos soportados
- **Organización automática**: Estructura de carpetas optimizada
- **Descarga ZIP**: Exportación completa de datasets

### Visualización
- **Galería interactiva**: Vista previa con anotaciones
- **Modal ampliado**: Vista detallada de imágenes
- **Estadísticas**: Contadores de imágenes y etiquetas
- **Filtros por sesión**: Navegación eficiente

### Augmentación
- **6 variantes automáticas**:
  - Negativo de colores
  - Ajuste de brillo
  - Espejo horizontal
  - Rotación
  - Desenfoque
  - Ajuste de contraste
- **Procesamiento en background**: No bloquea la interfaz
- **Preservación de etiquetas**: Anotaciones se mantienen correctas

## 📁 Estructura del Proyecto

```
YOLO-Multi-Class-Annotator/
├── app_auth.py              # Aplicación principal con FastAPI
├── requirements.txt         # Dependencias Python
├── .env.example            # Variables de entorno de ejemplo
├── .env                    # Configuración local (MySQL)
├── auth/                   # Módulo de autenticación y sesiones
│   ├── __init__.py
│   ├── models.py          # Modelos de usuario, sesión y clases
│   ├── database.py        # Configuración MySQL con SQLAlchemy
│   ├── auth_utils.py      # Utilidades JWT y passwords
│   ├── dependencies.py    # Dependencies de FastAPI
│   ├── routes.py          # Endpoints de autenticación
│   ├── session_routes.py  # API de sesiones privadas
│   └── session_utils.py   # Utilidades para sesiones con hash
├── templates/             # Templates HTML con Bootstrap
│   ├── index.html         # Página principal
│   ├── login.html         # Formulario de login
│   ├── register.html      # Formulario de registro
│   ├── dashboard.html     # Dashboard personal con sesiones
│   ├── sessions.html      # Gestión de sesiones
│   ├── session_access.html # Acceso por hash único
│   ├── annotator.html     # Herramienta de anotación
│   └── visualizer.html    # Visualizador de datasets
├── static/               # Archivos CSS/JS
│   ├── styles.css        # Estilos principales
│   ├── sessions.js       # JavaScript para gestión de sesiones
│   └── ...
├── manual/               # 📚 Documentación técnica completa
│   ├── INDEX.md          # Índice de toda la documentación
│   ├── INSTALACION.md    # Guía de instalación detallada
│   ├── PRODUCTION.md     # Mejores prácticas para producción
│   ├── MYSQL_PHPMYADMIN_GUIDE.md  # Configuración MySQL
│   └── ...               # Más guías técnicas
├── tests/                # 🧪 Suite completa de tests
│   ├── __init__.py       # Configuración del paquete de tests
│   ├── conftest.py       # Fixtures compartidas de pytest
│   ├── test_auth.py      # Tests de autenticación
│   ├── test_mysql.py     # Tests de base de datos
│   ├── test_token.py     # Tests de JWT
│   ├── run_unit_tests.py # Script para tests unitarios
│   └── README.md         # Documentación de tests
├── annotations/          # Datos de usuarios (se crea automáticamente)
├── temp/                # Archivos temporales
└── pyproject.toml       # Configuración de pytest
```

## 🔧 Configuración

### Variables de entorno (.env)
```env
# Base de datos MySQL
DB_HOST=localhost
DB_PORT=3306
DB_USER=tu_usuario
DB_PASSWORD=tu_password
DB_NAME=yolo_annotator

# JWT Configuration
JWT_SECRET_KEY=tu-clave-super-secreta-jwt
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Servidor
HOST=127.0.0.1
PORT=8002
DEBUG=True
```

### Base de datos MySQL
- **Configuración automática**: Tablas se crean al inicio si no existen
- **Gestión de usuarios**: Tabla `users` con roles y passwords hasheados
- **Sesiones privadas**: Tabla `user_sessions` con hash único
- **Clases de anotación**: Tabla `annotation_classes` por sesión
- **Escalabilidad**: Soporte para múltiples usuarios concurrentes

## 🎯 Uso del Sistema

### 1. Registro y Login
1. Acceder a `http://localhost:8002`
2. Crear cuenta (primera será admin)
3. Login con credenciales

### 2. Gestión de Sesiones Privadas
1. Dashboard → "Nueva Sesión" 
2. Crear sesión con nombre único (genera hash automático)
3. Aparece en "Tus Sesiones Recientes" con indicador privado
4. Usar "Compartir" para obtener enlace único
5. Solo tú puedes ver tus sesiones inicialmente

### 3. Acceso por Hash Único
1. Usar enlace compartido: `http://localhost:8002/s/{hash_unico}`
2. Acceso directo sin necesidad de login
3. Cualquiera con el enlace puede anotar en esa sesión
4. Ideal para colaboración temporal

### 4. Anotación de Imágenes
1. Dashboard → "Anotador Clásico" o usar enlace de sesión
2. Seleccionar sesión (si tienes acceso)
3. Subir imagen y configurar canvas
4. Seleccionar clase (1-6) y dibujar bounding boxes
5. Guardar anotaciones

### 5. Visualización
1. Dashboard → "Visualizador"
2. Seleccionar sesión
3. Explorar imágenes con anotaciones
4. Click para vista ampliada

### 6. Augmentación
1. Sesiones → Botón "Augmentar" en sesión
2. Proceso automático en background
3. Genera 6 variantes por imagen original

## 🔒 Seguridad y Privacidad

- **Passwords hasheados**: bcrypt con salt automático
- **JWT tokens**: Firmados y con expiración configurable
- **Sesiones privadas**: Hash SHA-256 único por sesión
- **Aislamiento de datos**: Usuarios solo ven sus datos
- **Acceso controlado**: Middleware y dependencies de FastAPI
- **Sanitización**: Nombres de archivo y parámetros validados
- **Base de datos segura**: MySQL con conexiones encriptadas

## 📊 APIs Principales

### Autenticación
- `POST /auth/register` - Registro de usuario
- `POST /auth/login` - Login con JWT
- `POST /auth/logout` - Logout y blacklist token
- `GET /auth/me` - Información del usuario actual

### Sesiones Privadas
- `POST /api/sessions/create` - Crear sesión privada
- `GET /api/sessions/my-sessions` - Listar mis sesiones
- `GET /api/sessions/{hash}` - Acceso por hash único
- `GET /api/sessions/{hash}/url` - Obtener enlace de sesión
- `DELETE /api/sessions/{hash}` - Desactivar sesión

### Anotaciones
- `POST /api/upload` - Subir imagen
- `POST /api/save_annotations` - Guardar anotaciones
- `GET /api/session/{name}/visualize` - Datos de visualización
- `POST /api/sessions/{hash}/annotations` - Crear anotación en sesión

## 📝 Licencia

Proyecto educativo - Uso libre para aprendizaje y desarrollo.

## 🤝 Contribución

1. Fork del proyecto
2. Crear rama feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Crear Pull Request

---

**Desarrollado para el curso de IA - F5**  
Sistema completo de anotación YOLO con autenticación JWT 🎯

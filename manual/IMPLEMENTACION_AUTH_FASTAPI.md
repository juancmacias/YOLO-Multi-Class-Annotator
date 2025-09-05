# 🔐 Implementación Práctica: FastAPI + JWT Authentication

## Estructura de Archivos Propuesta

```
YOLO-Multi-Class-Annotator/
├── app_auth.py                   # App principal con autenticación JWT
├── requirements.txt              # + nuevas dependencias auth
├── auth/                         # Nuevo módulo de autenticación
│   ├── __init__.py
│   ├── models.py                 # User, Token models
│   ├── auth.py                   # JWT utilities + password hashing
│   ├── routes.py                 # Endpoints de auth (/login, /register)
│   ├── dependencies.py           # get_current_user, get_db
│   └── database.py               # SQLite setup
├── templates/
│   ├── login.html                # Nueva página de login
│   ├── register.html             # Nueva página de registro
│   ├── index.html                # Modificado con auth
│   └── ...                       # Resto sin cambios
├── static/
│   ├── auth.js                   # JavaScript para manejo de auth
│   └── ...                       # Resto sin cambios
└── users.db                      # Base de datos SQLite
```

---

## 📦 Nuevas Dependencias

```bash
# requirements_auth.txt
pillow
pandas
numpy
fastapi
uvicorn
python-multipart
opencv-python

# Nuevas dependencias para autenticación
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
sqlalchemy==2.0.23
aiosqlite==0.19.0
```

---

## 🗄️ Modelos de Base de Datos

```python
# auth/models.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relación con sesiones
    sessions = relationship("UserSession", back_populates="user")

class UserSession(Base):
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_name = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    user = relationship("User", back_populates="sessions")

class TokenBlacklist(Base):
    __tablename__ = "token_blacklist"
    
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True)
    blacklisted_at = Column(DateTime, default=datetime.utcnow)
```

---

## 🔐 Utilidades de Autenticación

```python
# auth/auth.py
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status

# Configuración
SECRET_KEY = "your-secret-key-here-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 horas

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verificar password contra hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hashear password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Crear JWT token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[str]:
    """Verificar JWT token y devolver username"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return username
    except JWTError:
        return None

def get_token_from_header(authorization: str) -> Optional[str]:
    """Extraer token del header Authorization"""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    return authorization.split(" ")[1]
```

---

## 🔗 Dependencies y Middleware

```python
# auth/dependencies.py
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from .database import get_db
from .models import User, TokenBlacklist
from .auth import verify_token

security = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Dependency para obtener usuario actual autenticado"""
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not credentials:
        raise credentials_exception
    
    token = credentials.credentials
    
    # Verificar si el token está en blacklist
    blacklisted = db.query(TokenBlacklist).filter(
        TokenBlacklist.token == token
    ).first()
    if blacklisted:
        raise credentials_exception
    
    # Verificar token
    username = verify_token(token)
    if username is None:
        raise credentials_exception
    
    # Buscar usuario
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    
    return user

async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Dependency opcional - no falla si no hay auth"""
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None
```

---

## 🌐 Endpoints de Autenticación

```python
# auth/routes.py
from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from .database import get_db
from .models import User, TokenBlacklist
from .auth import verify_password, get_password_hash, create_access_token
from pydantic import BaseModel
from datetime import timedelta

router = APIRouter()

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

@router.post("/register", response_model=dict)
async def register_user(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Registrar nuevo usuario"""
    
    # Verificar si el usuario ya existe
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(
            status_code=400,
            detail="Username already registered"
        )
    
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    # Crear usuario
    hashed_password = get_password_hash(password)
    user = User(
        username=username,
        email=email,
        hashed_password=hashed_password
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return {
        "success": True,
        "message": "User created successfully",
        "user": {"id": user.id, "username": user.username, "email": user.email}
    }

@router.post("/login", response_model=Token)
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login de usuario y generar token"""
    
    user = db.query(User).filter(User.username == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user"
        )
    
    access_token_expires = timedelta(minutes=1440)  # 24 horas
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    }

@router.post("/logout")
async def logout_user(
    token: str = Form(...),
    db: Session = Depends(get_db)
):
    """Logout - agregar token a blacklist"""
    
    blacklist_entry = TokenBlacklist(token=token)
    db.add(blacklist_entry)
    db.commit()
    
    return {"success": True, "message": "Logged out successfully"}

@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Obtener información del usuario actual"""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "created_at": current_user.created_at
    }
```

---

## 🔄 Modificaciones en app_auth.py

```python
# Cambios principales en app_auth.py

# Imports adicionales
from auth.dependencies import get_current_user, get_optional_user
from auth.routes import router as auth_router
from auth.database import engine, Base
from auth.models import User, UserSession

# Crear tablas al inicio
Base.metadata.create_all(bind=engine)

# Incluir router de auth
app.include_router(auth_router, prefix="/auth", tags=["authentication"])

# Modificar endpoints existentes para requerir auth
@app.get("/sessions", response_class=HTMLResponse) 
async def sessions_page(
    request: Request, 
    current_user: User = Depends(get_current_user)  # Nueva dependencia
):
    """Página de gestión de sesiones - ahora protegida"""
    try:
        sessions_dir = "annotations"
        sessions = []
        
        if os.path.exists(sessions_dir):
            # Filtrar solo sesiones del usuario actual
            user_sessions = get_user_sessions(current_user.id)
            
            for session_name in user_sessions:
                session_path = os.path.join(sessions_dir, session_name)
                if os.path.isdir(session_path):
                    # ... resto del código igual
        
        return templates.TemplateResponse("sessions.html", {
            "request": request,
            "sessions": sessions,
            "user": current_user  # Pasar usuario a template
        })
        
    except Exception as e:
        return HTMLResponse(content=f"<h1>Error</h1><p>Error: {str(e)}</p><a href='/'>← Volver</a>")

# Nuevo endpoint para login/register
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Página de login"""
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Página de registro"""
    return templates.TemplateResponse("register.html", {"request": request})

# Middleware para redireccionar si no autenticado
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """Middleware para manejar autenticación"""
    
    # Rutas que no requieren autenticación
    public_paths = ["/", "/login", "/register", "/auth/", "/static/"]
    
    if any(request.url.path.startswith(path) for path in public_paths):
        response = await call_next(request)
        return response
    
    # Verificar autenticación para rutas protegidas
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        # Redireccionar a login si no está autenticado
        return RedirectResponse(url="/login", status_code=302)
    
    response = await call_next(request)
    return response
```

---

## 🎨 Frontend: Formularios de Login/Register

```html
<!-- templates/login.html -->
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - YOLO Annotator</title>
    <link rel="stylesheet" href="/static/styles.css">
    <style>
        .auth-container {
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .auth-card {
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.2);
            width: 100%;
            max-width: 400px;
        }
        .auth-form input {
            width: 100%;
            padding: 12px;
            margin: 10px 0;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-size: 14px;
        }
        .auth-form button {
            width: 100%;
            padding: 12px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <div class="auth-container">
        <div class="auth-card">
            <h2>🔐 Iniciar Sesión</h2>
            <p>Accede a tu cuenta YOLO Annotator</p>
            
            <form id="loginForm" class="auth-form">
                <input type="text" id="username" name="username" placeholder="Usuario" required>
                <input type="password" id="password" name="password" placeholder="Contraseña" required>
                <button type="submit">Iniciar Sesión</button>
            </form>
            
            <p style="text-align: center; margin-top: 20px;">
                ¿No tienes cuenta? <a href="/register">Regístrate aquí</a>
            </p>
        </div>
    </div>
    
    <script src="/static/auth.js"></script>
</body>
</html>
```

```javascript
// static/auth.js
async function login(username, password) {
    try {
        const formData = new FormData();
        formData.append('username', username);
        formData.append('password', password);
        
        const response = await fetch('/auth/login', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Guardar token
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('user', JSON.stringify(data.user));
            
            // Redireccionar a dashboard
            window.location.href = '/sessions';
        } else {
            alert('Error: ' + data.detail);
        }
    } catch (error) {
        alert('Error de conexión: ' + error.message);
    }
}

// Manejar formulario de login
document.getElementById('loginForm').addEventListener('submit', function(e) {
    e.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    login(username, password);
});

// Interceptor para agregar token a requests
function addAuthHeaders() {
    const token = localStorage.getItem('access_token');
    if (token) {
        return {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        };
    }
    return {};
}

// Verificar si usuario está logueado
function isAuthenticated() {
    const token = localStorage.getItem('access_token');
    return !!token;
}

// Logout
function logout() {
    const token = localStorage.getItem('access_token');
    if (token) {
        fetch('/auth/logout', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: `token=${token}`
        });
    }
    
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    window.location.href = '/login';
}
```

---

## 📊 Estimación de Esfuerzo

### Desarrollo Core (8-10 días)
- ✅ **Día 1-2**: Setup base de datos y modelos
- ✅ **Día 3-4**: JWT utilities y endpoints auth
- ✅ **Día 5-6**: Middleware y dependencies
- ✅ **Día 7-8**: Frontend y formularios
- ✅ **Día 9-10**: Testing y ajustes

### Features Adicionales (3-5 días)
- 🔄 **Password reset** por email
- 🔄 **Email verification** 
- 🔄 **Rate limiting**
- 🔄 **Roles y permisos**

---

## 🎯 Beneficios Inmediatos

1. **Seguridad**: Cada usuario ve solo sus propias sesiones
2. **Multiusuario**: Múltiples personas pueden usar la app
3. **Auditoría**: Saber quién hizo qué y cuándo
4. **Escalabilidad**: Base sólida para funciones avanzadas
5. **Estándar**: JWT es estándar industry para APIs

Esta implementación mantiene toda la funcionalidad actual while adding robust authentication with minimal disruption to the existing codebase.

# 🎨 Sistema de Gestión de Clases Personalizadas

## 🌟 Nueva Funcionalidad Implementada

Se ha implementado un **sistema completo de gestión de clases personalizadas** que permite a los usuarios crear, editar y eliminar sus propias clases de anotación de manera dinámica.

---

## ✨ Características Principales

### 🔧 **Gestión Completa de Clases**
- ✅ **Crear** nuevas clases con nombre y color personalizado
- ✅ **Editar** clases existentes (nombre y color)
- ✅ **Eliminar** clases (soft delete)
- ✅ **Colores predefinidos** para facilitar la selección
- ✅ **Validación** de nombres únicos y formatos de color

### 🎯 **Características Avanzadas**
- ✅ **Clases por sesión** - Diferentes clases para cada proyecto
- ✅ **Clases globales** - Para administradores
- ✅ **Importación automática** desde anotaciones existentes
- ✅ **Restablecimiento** a clases por defecto
- ✅ **Colores contrastantes** automáticos para texto

### 🚀 **Integración Perfecta**
- ✅ **Modal intuitivo** en el anotador
- ✅ **Atajos de teclado** (1-9 para seleccionar clases)
- ✅ **Base de datos** con persistencia completa
- ✅ **API REST** para todas las operaciones

---

## 🎮 Cómo Usar

### 1. **Acceder al Gestor de Clases**

En el anotador, después de cargar una imagen:

1. Click en **"⚙️ Gestionar Clases"** 
2. Se abre el modal de gestión

### 2. **Crear Nueva Clase**

```
📝 Formulario de creación:
- Nombre: "Mi Objeto Personalizado"
- Color: Usar selector o colores predefinidos
- Click "Guardar"
```

### 3. **Editar Clase Existente**

```
✏️ En la lista de clases:
- Click en el botón "✏️" de la clase
- Modificar nombre/color
- Click "Guardar"
```

### 4. **Funciones Especiales**

- **🔄 Restablecer por defecto**: Elimina clases personalizadas y crea las básicas
- **📥 Importar desde anotaciones**: Detecta clases usadas en archivos existentes
- **❌ Eliminar**: Soft delete (no elimina físicamente)

---

## 🏗️ Arquitectura Técnica

### **Backend (FastAPI)**
```python
# Nuevos endpoints en /api/classes/
GET    /api/classes/                    # Listar clases
POST   /api/classes/                    # Crear clase
PUT    /api/classes/{id}                # Actualizar clase
DELETE /api/classes/{id}                # Eliminar clase
POST   /api/classes/reset-to-default    # Restablecer
POST   /api/classes/import              # Importar desde anotaciones
GET    /api/classes/available-colors    # Colores predefinidos
```

### **Base de Datos**
```sql
-- Nueva tabla: annotation_classes
CREATE TABLE annotation_classes (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    color VARCHAR(7) DEFAULT '#ff0000',
    user_id INTEGER REFERENCES users(id),
    session_name VARCHAR(255),
    is_global BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### **Frontend (JavaScript)**
```javascript
// Nuevas funciones principales
loadUserClasses()           // Cargar clases del usuario
openClassManager()          // Abrir modal
saveClass()                 // Crear/editar clase
deleteClass()               // Eliminar clase
importClassesFromAnnotations() // Importar automáticamente
```

---

## 🎨 Colores Predefinidos

El sistema incluye 18 colores predefinidos organizados en una cuadrícula:

| Color | Nombre | Hex |
|-------|--------|-----|
| 🔴 | Rojo | #ff0000 |
| 🟢 | Verde | #00ff00 |
| 🔵 | Azul | #0000ff |
| 🟡 | Amarillo | #ffff00 |
| 🟣 | Magenta | #ff00ff |
| 🟦 | Cian | #00ffff |
| 🟠 | Naranja | #ff8800 |
| 🩷 | Rosa | #ff0088 |
| 🟣 | Púrpura | #8800ff |
| 🟢 | Verde Lima | #88ff00 |
| 🔵 | Azul Cielo | #0088ff |
| 🟩 | Turquesa | #00ff88 |
| 🔴 | Rojo Oscuro | #800000 |
| 🟢 | Verde Oscuro | #008000 |
| 🔵 | Azul Oscuro | #000080 |
| 🟤 | Marrón | #8B4513 |
| ⚫ | Gris | #808080 |
| ⚫ | Negro | #000000 |

---

## 🚀 Clases por Defecto

Cuando un usuario nuevo accede al sistema, se crean automáticamente 6 clases por defecto:

1. **Persona** 🔴 (#ff0000)
2. **Vehículo** 🟢 (#00ff00)  
3. **Animal** 🔵 (#0000ff)
4. **Edificio** 🟡 (#ffff00)
5. **Objeto** 🟣 (#ff00ff)
6. **Naturaleza** 🟦 (#00ffff)

---

## ⌨️ Atajos de Teclado

| Tecla | Acción |
|-------|--------|
| **1-9** | Seleccionar clase rápida |
| **Escape** | Cerrar modal / Cancelar anotación |
| **Delete** | Eliminar última anotación |

---

## 🔒 Permisos y Seguridad

### **Usuarios Normales**
- ✅ Crear clases personales
- ✅ Editar sus propias clases
- ✅ Ver clases globales (solo lectura)
- ❌ No pueden crear clases globales

### **Administradores**
- ✅ Todas las funciones de usuarios normales
- ✅ Crear clases globales
- ✅ Editar cualquier clase
- ✅ Eliminar cualquier clase

### **Validaciones**
- ✅ Nombres únicos por usuario/sesión
- ✅ Formato de color hexadecimal (#RRGGBB)
- ✅ Longitud máxima de nombres (50 caracteres)
- ✅ Autorización JWT requerida

---

## 🧪 Testing

### **Script de Prueba Automático**
```bash
cd app-jwt
python test_classes.py
```

Este script:
1. 🔐 Hace login automático
2. 📋 Lista clases actuales
3. ➕ Crea 6 clases de ejemplo
4. ✏️ Edita una clase
5. 🎨 Obtiene colores disponibles
6. 📊 Muestra resultado final

### **Casos de Prueba Manuales**

1. **Flujo Básico**:
   - Login → Annotator → Gestionar Clases → Crear → Usar en anotación

2. **Validaciones**:
   - Nombre vacío ❌
   - Color inválido ❌
   - Nombre duplicado ❌

3. **Funciones Avanzadas**:
   - Importar desde anotaciones existentes
   - Restablecer a valores por defecto
   - Editar y eliminar clases

---

## 🔧 Solución de Problemas

### **Error: "No hay clases definidas"**
```javascript
// Solución: Recargar clases
await loadUserClasses();
```

### **Error: "Clase no encontrada"**
```sql
-- Verificar en BD
SELECT * FROM annotation_classes WHERE is_active = 1;
```

### **Error: "Token expirado"**
```javascript
// Renovar token o hacer login nuevamente
localStorage.removeItem('access_token');
window.location.href = '/login';
```

---

## 📈 Mejoras Futuras

### **Fase 1 - Completada ✅**
- ✅ CRUD completo de clases
- ✅ Modal de gestión
- ✅ Colores predefinidos
- ✅ Importación automática

### **Fase 2 - Posibles Mejoras**
- 🔄 **Plantillas de clases** por tipo de proyecto
- 📤 **Exportar/Importar** configuraciones de clases
- 🎨 **Editor de colores** avanzado con paletas
- 📊 **Estadísticas** de uso por clase
- 🔍 **Búsqueda** y filtrado de clases
- 👥 **Compartir clases** entre usuarios
- 🏷️ **Categorías** de clases anidadas

---

## 💡 Casos de Uso Reales

### **1. Detección de Objetos Urbanos**
```
🚗 Vehículos: Coche, Moto, Camión, Autobús
🚶 Peatones: Persona, Niño, Ciclista
🏢 Infraestructura: Semáforo, Señal, Edificio
```

### **2. Clasificación de Animales**
```
🐕 Mascotas: Perro, Gato, Conejo
🦅 Aves: Paloma, Águila, Loro
🐠 Acuáticos: Pez, Delfín, Tiburón
```

### **3. Inventario de Productos**
```
📱 Electrónicos: Móvil, Tablet, Laptop
👕 Ropa: Camisa, Pantalón, Zapatos
🍎 Comida: Fruta, Verdura, Bebida
```

---

## 🎯 Conclusión

El **Sistema de Gestión de Clases Personalizadas** transforma el anotador YOLO de una herramienta con clases fijas a una **plataforma flexible y personalizable** que se adapta a cualquier proyecto de visión artificial.

### **Beneficios Clave:**
- 🎨 **Flexibilidad total** en definición de clases
- 🚀 **Productividad mejorada** con clases específicas del proyecto
- 👥 **Colaboración** con clases globales para equipos
- 💾 **Persistencia** de configuraciones personalizadas
- 🔄 **Migración fácil** desde anotaciones existentes

**¡Ahora cada usuario puede crear exactamente las clases que necesita para su proyecto específico!** 🎉

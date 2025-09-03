# 🎯 YOLO Multi-Class Annotator


Una aplicación web moderna construida con **FastAPI** y **HTML/JavaScript** para crear datasets de entrenamiento para modelos YOLO de manera rápida e intuitiva.

## ✨ Características

- 🖼️ **Generación de imágenes** con fondos aleatorios personalizables
- 🎨 **Múltiples clases de objetos** (6 clases predefinidas)
- 🖱️ **Selección visual** de áreas arrastrando el ratón
- 📐 **Formato YOLO automático** (coordenadas normalizadas)
- 📁 **Estructura organizada** (`images/` y `labels/`)
- 🔢 **Numeración automática** de archivos
- 💾 **Guardado limpio** (imágenes sin marcas de anotación)

## 🚀 Instalación

### Requisitos previos
- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### 1. Clonar el repositorio
```bash
git clone <tu-repositorio>
cd vision_modelo
```

### 2. Crear entorno virtual
```bash
python3 -m venv venv
source venv/bin/activate  # En macOS/Linux
# o
venv\Scripts\activate     # En Windows
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

## 🎮 Uso

### Iniciar la aplicación
```bash
python app.py
```

La aplicación se iniciará en: **http://localhost:8000**

### Workflow de anotación

1. **📤 Subir imagen**: Selecciona tu imagen base
2. **⚙️ Configurar fondo**: 
   - Tamaño: 320x320 o 640x640
   - Posición de la imagen (sliders X, Y)
   - Fondo aleatorio (opcional)
3. **🖼️ Generar**: Crea la imagen con fondo
4. **🏷️ Seleccionar clase**: Elige el tipo de objeto a anotar
5. **🖱️ Anotar**: Arrastra el ratón sobre las áreas de interés
6. **💾 Guardar**: Introduce un nombre y guarda el dataset

## 📋 Clases disponibles

| ID | Nombre    | Color    |
|----|-----------|----------|
| 0  | objeto 1  | 🔴 Rojo   |
| 1  | objeto 2  | 🟢 Verde  |
| 2  | objeto 3  | 🔵 Azul   |
| 3  | objeto 4  | 🟡 Amarillo |
| 4  | objeto 5  | 🟣 Magenta |
| 5  | objeto 6  | 🟦 Cian   |

## 📁 Estructura de salida

```
annotations/
├── images/
│   ├── adidas.jpg
│   ├── adidas_1.jpg
│   └── nike.jpg
└── labels/
    ├── adidas.txt
    ├── adidas_1.txt
    └── nike.txt
```

### Formato de coordenadas YOLO
```
0 0.484624 0.460602 0.837248 0.710046
```
- `0`: ID de clase
- `0.484624`: x_center normalizado (0-1)
- `0.460602`: y_center normalizado (0-1)  
- `0.837248`: ancho normalizado (0-1)
- `0.710046`: alto normalizado (0-1)

## 🛠️ Configuración avanzada

### Personalizar clases
Edita las clases en `app.py`:
```python
CLASSES = {
    0: {"name": "tu_clase", "color": "#ff0000"},
    1: {"name": "otra_clase", "color": "#00ff00"},
    # ... más clases
}
```

### Cambiar puerto
```python
uvicorn.run(app, host="0.0.0.0", port=8080)  # Puerto 8080
```

### Configurar carpetas de salida
```python
os.makedirs("mi_dataset/images", exist_ok=True)
os.makedirs("mi_dataset/labels", exist_ok=True)
```

## 🧰 Dependencias principales

- **FastAPI**: Framework web rápido
- **Uvicorn**: Servidor ASGI
- **Pillow**: Procesamiento de imágenes
- **python-multipart**: Manejo de formularios

Ver `requirements.txt` para la lista completa.

## 📝 API Endpoints

### `POST /generate`
Genera imagen con fondo personalizado
- `image`: Archivo de imagen
- `size`: Tamaño del canvas (320 o 640)
- `x`, `y`: Posición de la imagen
- `random_bg`: Usar fondo aleatorio

### `POST /save_annotations`  
Guarda dataset con anotaciones
- `annotations`: JSON con coordenadas
- `filename`: Nombre base del archivo
- `image_width`, `image_height`: Dimensiones
- `image_data`: Imagen en base64

## 🎯 Casos de uso

- **Entrenamiento YOLO**: Crear datasets personalizados
- **Computer Vision**: Anotar objetos para detección  
- **Augmentación de datos**: Generar variaciones con fondos
- **Prototipado rápido**: Crear datasets de prueba

## 🐛 Troubleshooting

### Error de puerto ocupado
```bash
lsof -ti:8000 | xargs kill -9  # Liberar puerto 8000
python app.py                  # Reiniciar
```

### Error de permisos en carpetas
```bash
chmod 755 annotations/
chmod 755 annotations/images/
chmod 755 annotations/labels/
```

### Problemas con dependencias
```bash
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Añadir nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo `LICENSE` para detalles.

## 🙏 Agradecimientos

- **YOLO**: Por el formato de anotación estándar
- **FastAPI**: Por el excelente framework web
- **Comunidad Python**: Por las increíbles librerías

---

⭐ **¡Si te resulta útil, dale una estrella al proyecto!** ⭐

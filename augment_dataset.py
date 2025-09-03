import os
import cv2
from PIL import Image, ImageEnhance, ImageFilter
import shutil
import numpy as np
import json
from datetime import datetime

# Configuración de variantes disponibles
AVAILABLE_VARIANTS = {
    'negativo': {
        'name': 'Negativo',
        'description': 'Invierte los colores de la imagen',
        'icon': '🎭',
        'transform': lambda img: cv2.bitwise_not(img),
        'modify_label': False
    },
    'brillo': {
        'name': 'Brillo aumentado',
        'description': 'Aumenta el brillo de la imagen en 50%',
        'icon': '☀️',
        'transform': lambda img: cv2.cvtColor(np.array(ImageEnhance.Brightness(Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))).enhance(1.5)), cv2.COLOR_RGB2BGR),
        'modify_label': False
    },
    'espejo': {
        'name': 'Espejo horizontal',
        'description': 'Crea una imagen espejo (volteo horizontal)',
        'icon': '🪞',
        'transform': lambda img: cv2.flip(img, 1),
        'modify_label': True  # Requiere ajustar coordenadas x
    },
    'rotacion': {
        'name': 'Rotación ligera',
        'description': 'Rota la imagen 15 grados',
        'icon': '🔄',
        'transform': lambda img: rotate_image(img, 15),
        'modify_label': False  # Por simplicidad, mantenemos las etiquetas originales
    },
    'desenfoque': {
        'name': 'Desenfoque gaussiano',
        'description': 'Aplica desenfoque gaussiano suave',
        'icon': '🌀',
        'transform': lambda img: cv2.GaussianBlur(img, (5, 5), 0),
        'modify_label': False
    },
    'contraste': {
        'name': 'Contraste aumentado',
        'description': 'Aumenta el contraste de la imagen',
        'icon': '🌈',
        'transform': lambda img: cv2.cvtColor(np.array(ImageEnhance.Contrast(Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))).enhance(1.3)), cv2.COLOR_RGB2BGR),
        'modify_label': False
    }
}

def rotate_image(img, angle):
    """Rota una imagen por un ángulo específico"""
    height, width = img.shape[:2]
    center = (width // 2, height // 2)
    rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(img, rotation_matrix, (width, height))

def adjust_label_for_mirror(label_path, aug_label_path):
    """
    Ajusta la coordenada x_center para el efecto espejo en formato YOLO.
    """
    with open(label_path, 'r') as f_in, open(aug_label_path, 'w') as f_out:
        for line in f_in:
            parts = line.strip().split()
            if len(parts) == 5:
                # clase, x_center, y_center, ancho, alto
                parts[1] = str(1 - float(parts[1]))
            f_out.write(' '.join(parts) + '\n')

def augment_session(session_name, selected_variants=None, progress_callback=None):
    """
    Aumenta el dataset de una sesión específica aplicando las variantes seleccionadas
    """
    if selected_variants is None:
        selected_variants = list(AVAILABLE_VARIANTS.keys())
    
    session_path = f"annotations/{session_name}"
    images_path = os.path.join(session_path, "images")
    labels_path = os.path.join(session_path, "labels")
    
    if not os.path.exists(images_path):
        raise Exception(f"No se encontró la carpeta de imágenes: {images_path}")
    
    # Crear carpeta de labels si no existe
    os.makedirs(labels_path, exist_ok=True)
    
    # Crear carpeta temp si no existe
    os.makedirs("temp", exist_ok=True)
    
    # Archivo de progreso temporal
    progress_file = f"temp/progress_{session_name}.json"
    
    # Obtener lista de imágenes
    image_files = [f for f in os.listdir(images_path) 
                   if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.bmp'))]
    
    total_operations = len(image_files) * len(selected_variants)
    current_operation = 0
    results = {
        'processed_images': 0,
        'created_variants': 0,
        'errors': [],
        'variants_applied': selected_variants
    }
    
    # Función para actualizar progreso
    def update_progress():
        progress_data = {
            'current': current_operation,
            'total': total_operations,
            'completed': False,
            'message': f'Procesando imagen {results["processed_images"] + 1} de {len(image_files)}'
        }
        with open(progress_file, 'w') as f:
            json.dump(progress_data, f)
    
    # Inicializar progreso
    update_progress()
    
    for img_name in image_files:
        img_path = os.path.join(images_path, img_name)
        label_name = os.path.splitext(img_name)[0] + '.txt'
        label_path = os.path.join(labels_path, label_name)
        
        # Leer imagen original
        img = cv2.imread(img_path)
        if img is None:
            results['errors'].append(f'No se pudo leer {img_path}')
            continue
        
        # Aplicar cada variante seleccionada
        for variant_key in selected_variants:
            current_operation += 1
            
            # Actualizar progreso
            update_progress()
            
            if progress_callback:
                progress = (current_operation / total_operations) * 100
                progress_callback(progress, f"Procesando {img_name} - {AVAILABLE_VARIANTS[variant_key]['name']}")
            
            try:
                variant_config = AVAILABLE_VARIANTS[variant_key]
                
                # Aplicar transformación
                aug_img = variant_config['transform'](img)
                
                # Generar nombre del archivo aumentado
                base_name = os.path.splitext(img_name)[0]
                extension = os.path.splitext(img_name)[1]
                aug_name = f"{base_name}_{variant_key}{extension}"
                aug_path = os.path.join(images_path, aug_name)
                
                # Guardar imagen aumentada
                cv2.imwrite(aug_path, aug_img)
                
                # Manejar etiquetas
                aug_label_name = f"{base_name}_{variant_key}.txt"
                aug_label_path = os.path.join(labels_path, aug_label_name)
                
                if os.path.exists(label_path):
                    if variant_config['modify_label']:
                        adjust_label_for_mirror(label_path, aug_label_path)
                    else:
                        shutil.copy(label_path, aug_label_path)
                
                results['created_variants'] += 1
                
            except Exception as e:
                results['errors'].append(f'Error procesando {img_name} con variante {variant_key}: {str(e)}')
        
        results['processed_images'] += 1
    
    # Marcar como completado
    final_progress = {
        'current': total_operations,
        'total': total_operations,
        'completed': True,
        'message': f'¡Completado! {results["created_variants"]} variantes creadas'
    }
    with open(progress_file, 'w') as f:
        json.dump(final_progress, f)
    
    # Guardar log de augmentación
    log_path = os.path.join(session_path, 'augmentation_log.json')
    log_data = {
        'timestamp': datetime.now().isoformat(),
        'session_name': session_name,
        'variants_applied': selected_variants,
        'results': results
    }
    
    with open(log_path, 'w') as f:
        json.dump(log_data, f, indent=2)
    
    return results

def get_session_stats(session_name):
    """
    Obtiene estadísticas de una sesión (antes de augmentación)
    """
    session_path = f"annotations/{session_name}"
    images_path = os.path.join(session_path, "images")
    labels_path = os.path.join(session_path, "labels")
    
    if not os.path.exists(images_path):
        return None
    
    image_files = [f for f in os.listdir(images_path) 
                   if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.bmp'))]
    
    label_files = []
    if os.path.exists(labels_path):
        label_files = [f for f in os.listdir(labels_path) if f.endswith('.txt')]
    
    # Detectar si ya hay variantes (archivos con sufijos)
    original_images = []
    variant_images = []
    
    for img_file in image_files:
        base_name = os.path.splitext(img_file)[0]
        is_variant = any(base_name.endswith(f'_{variant}') for variant in AVAILABLE_VARIANTS.keys())
        
        if is_variant:
            variant_images.append(img_file)
        else:
            original_images.append(img_file)
    
    return {
        'total_images': len(image_files),
        'original_images': len(original_images),
        'variant_images': len(variant_images),
        'label_files': len(label_files),
        'available_variants': AVAILABLE_VARIANTS
    }

# Función legacy para compatibilidad
def augment_images():
    """Función original para augmentar en estructura by_class (mantenida para compatibilidad)"""
    BASE_DIR = 'by_class'
    IMAGE_SUBDIR = 'images'
    LABEL_SUBDIR = 'labels'
    
    # Variantes legacy
    VARIANTS = [
        ('negativo', lambda img: cv2.bitwise_not(img), False),
        ('brillo', lambda img: cv2.cvtColor(np.array(ImageEnhance.Brightness(Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))).enhance(1.5)), cv2.COLOR_RGB2BGR), False),
        ('espejo', lambda img: cv2.flip(img, 1), True),
    ]
    for class_name in os.listdir(BASE_DIR):
        class_path = os.path.join(BASE_DIR, class_name)
        images_path = os.path.join(class_path, IMAGE_SUBDIR)
        labels_path = os.path.join(class_path, LABEL_SUBDIR)
        if not os.path.isdir(images_path):
            continue
        for img_name in os.listdir(images_path):
            if not img_name.lower().endswith(('.jpg', '.jpeg', '.png')):
                continue
            img_path = os.path.join(images_path, img_name)
            label_name = os.path.splitext(img_name)[0] + '.txt'
            label_path = os.path.join(labels_path, label_name)
            # Leer imagen
            img = cv2.imread(img_path)
            if img is None:
                print(f'No se pudo leer {img_path}')
                continue
            # Generar variantes
            for sufijo, transform, mirror_label in VARIANTS:
                if sufijo == 'negativo' or sufijo == 'espejo':
                    aug_img = transform(img)
                else:
                    aug_img = transform(img)
                aug_name = f"{os.path.splitext(img_name)[0]}_{sufijo}{os.path.splitext(img_name)[1]}"
                aug_path = os.path.join(images_path, aug_name)
                cv2.imwrite(aug_path, aug_img)
                # Copiar o modificar label
                aug_label_name = f"{os.path.splitext(img_name)[0]}_{sufijo}.txt"
                aug_label_path = os.path.join(labels_path, aug_label_name)
                if os.path.exists(label_path):
                    if mirror_label:
                        adjust_label_for_mirror(label_path, aug_label_path)
                    else:
                        shutil.copy(label_path, aug_label_path)
                else:
                    print(f'Label no encontrado: {label_path}')

if __name__ == "__main__":
    augment_images()
    print("Aumento de datos completado.")

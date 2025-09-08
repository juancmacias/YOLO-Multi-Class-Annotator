# Dockerfile básico para YOLO Multi-Class Annotator
FROM python:3.10-slim

# Instalar dependencias del sistema necesarias para OpenCV
RUN apt-get update && apt-get install -y libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*

# Establecer el directorio de trabajo
WORKDIR /app


# Copiar los archivos del proyecto
COPY . /app

# Crear carpetas y dar permisos después del COPY (para Hugging Face)
RUN mkdir -p /app/annotations /app/temp && chmod -R 777 /app/annotations /app/temp

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Exponer el puerto de la app (7860 para Hugging Face)
EXPOSE 7860

# Comando para iniciar la aplicación en el puerto 7860
CMD ["uvicorn", "app_auth:app", "--host", "0.0.0.0", "--port", "7860"]

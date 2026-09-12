# Imagen base oficial ligera de Python
FROM python:3.11-slim

# Evitar la creación de archivos .pyc y permitir logs sin búfer
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar requerimientos e instalar dependencias
COPY src/requirements.txt ./src/
RUN pip install --no-cache-dir -r src/requirements.txt

# Copiar el código del proyecto
COPY . .

# Comando por defecto al ejecutar el contenedor
CMD ["python", "src/main.py"]

# Usar una imagen base ligera de Python
FROM python:3.11-slim

# Evitar que Python genere archivos .pyc y habilitar el volcado de logs sin búfer
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Establecer el directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias (si las hubiera)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar el archivo de requerimientos primero para aprovechar la caché de Docker
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Exponer el puerto que usa Cloud Run (por defecto 8080)
EXPOSE 8080

# Comando para arrancar la aplicación
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]

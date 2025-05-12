# Usar una imagen base de Python
FROM python:3.11-slim

# Crear y establecer el directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de requisitos
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente y el archivo .env
COPY . .

# Instalar el paquete en modo desarrollo
RUN pip install -e .

# Comando por defecto
CMD ["python", "-m", "auditor.agent"] 
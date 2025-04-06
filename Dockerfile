FROM python:3.10-slim

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    curl \
    gnupg \
    chromium-driver \
    chromium \
    && apt-get clean

# Variables de entorno para Chrome
ENV CHROME_BIN="/usr/bin/chromium" \
    PATH="$PATH:/usr/bin/chromium"

# Copiar archivos del proyecto
WORKDIR /app
COPY . .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Exponer el puerto Flask
EXPOSE 10000

# Ejecutar la app
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "app:app"]

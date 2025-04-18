# Usa una imagen base de Python 3.10 slim
FROM python:3.10-slim

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Agregar la clave de Google para instalar Google Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" \
    >> /etc/apt/sources.list.d/google.list

# Instalar Google Chrome estable
RUN apt-get update && apt-get install -y google-chrome-stable

# Descargar e instalar Chromedriver (versión fija)
RUN wget -O /tmp/chromedriver.zip https://storage.googleapis.com/chrome-for-testing-public/135.0.7049.42/linux64/chromedriver-linux64.zip && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin/ && \
    mv /usr/local/bin/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver && \
    rm -rf /usr/local/bin/chromedriver-linux64 && \
    rm /tmp/chromedriver.zip && \
    chmod +x /usr/local/bin/chromedriver

# Configurar el directorio de trabajo
WORKDIR /app

# Copiar el archivo de requerimientos e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Ejecutar la aplicación Flask
CMD ["python", "app.py"]

FROM python:3.11

RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    gnupg \
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libxi6 \
    libxcursor1 \
    libxcomposite1 \
    libasound2 \
    libxdamage1 \
    libxrandr2 \
    libgtk-3-0 \
    libgbm-dev \
    libxshmfence-dev \
    libxss1 \
    libxtst6 \
    fonts-liberation \
    libappindicator1 \
    libappindicator3-1 \
    xdg-utils

# Instalar Google Chrome
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    apt install -y ./google-chrome-stable_current_amd64.deb && \
    rm google-chrome-stable_current_amd64.deb

# ChromeDriver
RUN CHROME_VERSION=$(google-chrome --version | grep -oP '\d+\.\d+\.\d+') && \
    wget https://chromedriver.storage.googleapis.com/$CHROME_VERSION/chromedriver_linux64.zip && \
    unzip chromedriver_linux64.zip && \
    mv chromedriver /usr/bin/chromedriver && \
    chmod +x /usr/bin/chromedriver && \
    rm chromedriver_linux64.zip

WORKDIR /app
COPY . /app
RUN pip install -r requirements.txt

CMD ["python", "app.py"]

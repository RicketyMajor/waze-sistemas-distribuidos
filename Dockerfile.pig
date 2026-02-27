# --------------------------------------------------------------------------
# Imagen Base
# --------------------------------------------------------------------------
# Usamos Eclipse Temurin, el reemplazo oficial y moderno de openjdk.
FROM eclipse-temurin:8-jre-jammy

# --------------------------------------------------------------------------
# Variables de Entorno
# --------------------------------------------------------------------------
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# --------------------------------------------------------------------------
# Instalación de Dependencias del Sistema
# --------------------------------------------------------------------------
# Instala Python, pip y otras herramientas necesarias.
RUN apt-get update && apt-get install -y \
    wget \
    python3 \
    python3-pip \
    libpq-dev \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# --------------------------------------------------------------------------
# Instalación de Apache Pig
# --------------------------------------------------------------------------
ENV PIG_VERSION=0.17.0
ENV PIG_HOME=/opt/pig
ENV PATH=$PIG_HOME/bin:$PATH

RUN wget https://archive.apache.org/dist/pig/pig-${PIG_VERSION}/pig-${PIG_VERSION}.tar.gz && \
    tar -xzf pig-${PIG_VERSION}.tar.gz && \
    mv pig-${PIG_VERSION} /opt/pig && \
    rm pig-${PIG_VERSION}.tar.gz

# --------------------------------------------------------------------------
# Configuración de la Aplicación
# --------------------------------------------------------------------------
WORKDIR /app

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

# --------------------------------------------------------------------------
# Comando de Ejecución
# --------------------------------------------------------------------------
# Mantiene el contenedor vivo para ejecuciones manuales o scripts.
CMD ["tail", "-f", "/dev/null"]
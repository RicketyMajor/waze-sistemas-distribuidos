# Dockerfile.pig
# Contenedor dedicado para Apache Pig y procesamiento MapReduce

# Usamos Eclipse Temurin, el reemplazo oficial y moderno de openjdk
FROM eclipse-temurin:8-jre-jammy

# Evitar escritura de bytecodes y buffer de Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalar Python 3, pip y dependencias necesarias para Pig (PostgreSQL, compiladores)
RUN apt-get update && apt-get install -y \
    wget \
    python3 \
    python3-pip \
    libpq-dev \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Definir variables de entorno para Apache Pig
ENV PIG_VERSION=0.17.0
ENV PIG_HOME=/opt/pig
ENV PATH=$PIG_HOME/bin:$PATH

# Descargar e instalar Apache Pig
RUN wget https://archive.apache.org/dist/pig/pig-${PIG_VERSION}/pig-${PIG_VERSION}.tar.gz && \
    tar -xzf pig-${PIG_VERSION}.tar.gz && \
    mv pig-${PIG_VERSION} /opt/pig && \
    rm pig-${PIG_VERSION}.tar.gz

WORKDIR /app

# Copiamos las dependencias de Python
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copiamos el resto del código
COPY . .

# Mantenemos el contenedor vivo en segundo plano
CMD ["tail", "-f", "/dev/null"]
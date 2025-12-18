# ANTES:
# FROM python:3.9-slim

# AHORA (Cambia esto):
FROM python:3.10-slim

# ... el resto del archivo queda IDÉNTICO ...
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "-m", "traffic_generator.generator"]
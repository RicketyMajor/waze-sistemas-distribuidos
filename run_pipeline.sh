#!/bin/bash
# run_pipeline.sh - Orquestador End-to-End del Sistema de Tráfico Waze

echo "=================================================================="
echo "Iniciando Pipeline de Procesamiento Distribuido (Waze -> Kibana)"
echo "=================================================================="

echo "[1/4] Extrayendo, limpiando y homogeneizando datos (ETL)..."
docker-compose run --rm traffic-app python -m etl.homogenizer

echo "[2/4] Procesando Big Data distribuido con Apache Pig (MapReduce)..."
docker exec -it waze_pig_processor pig -x local /app/processing/traffic_analysis.pig

echo "[3/4] Cargando resultados en capa de baja latencia (Redis Cache)..."
docker-compose run --rm traffic-app python -m etl.cache_loader

echo "[4/4] Indexando datos y métricas para visualización (Elasticsearch)..."
docker-compose run --rm traffic-app python -m etl.es_loader

echo "=================================================================="
echo "¡Pipeline finalizado con éxito!"
echo "Los datos están listos para ser visualizados en Kibana (http://localhost:5601)"
echo "=================================================================="
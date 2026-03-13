import os
import csv
from datetime import datetime
from elasticsearch import Elasticsearch, helpers
from cache_service.redis_client import cache_manager

# --------------------------------------------------------------------------
# Configuración de Elasticsearch
# --------------------------------------------------------------------------
ES_HOST = os.getenv('ELASTICSEARCH_HOST', 'localhost')
ES_PORT = os.getenv('ELASTICSEARCH_PORT', '9200')
ES_URL = f"http://{ES_HOST}:{ES_PORT}"

# --------------------------------------------------------------------------
# Cargador de Datos a Elasticsearch
# --------------------------------------------------------------------------


def setup_elasticsearch():
    """
    Inicializa la conexión con Elasticsearch y crea los índices necesarios
    con sus respectivos mapeos (mappings), especialmente para datos geoespaciales.
    """
    es = Elasticsearch([ES_URL])

    if not es.ping():
        print(f"Error: No se pudo conectar a Elasticsearch en {ES_URL}")
        return None

    print(f"¡Conexión exitosa a Elasticsearch en {ES_URL}!")

    # Mapeo estricto para que Kibana reconozca el campo 'location' como coordenadas en un mapa
    waze_mapping = {
        "properties": {
            "location": {"type": "geo_point"},
            "fecha": {"type": "date", "format": "yyyy-MM-dd"},
            "@timestamp": {"type": "date"}
        }
    }

    # Crear índice para eventos si no existe (Sintaxis actualizada para Elasticsearch 8.x)
    if not es.indices.exists(index="waze_events"):
        es.indices.create(index="waze_events", mappings=waze_mapping)
        print("Índice 'waze_events' creado con mapeo geoespacial.")

    # Crear índice para métricas de caché y rendimiento
    if not es.indices.exists(index="waze_metrics"):
        es.indices.create(index="waze_metrics")
        print("Índice 'waze_metrics' creado.")

    return es


def load_cleaned_events_to_es(es):
    """
    Lee el archivo CSV de eventos homogeneizados y los indexa en Elasticsearch.
    """
    file_path = '/app/shared_data/cleaned_waze_events.csv'
    if not os.path.exists(file_path):
        print(
            f"Advertencia: No se encontró el archivo de eventos limpios en {file_path}")
        return

    print("--- ENVIANDO EVENTOS LIMPIOS A ELASTICSEARCH ---")
    actions = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=',')
            for row in reader:
                # Estructura del CSV: id, fecha, tipo_incidente, subtipo, comuna, calle, latitud, longitud
                doc = {
                    "waze_uuid": row[0],
                    "fecha": row[1],
                    "tipo_incidente": row[2],
                    "subtipo": row[3],
                    "comuna": row[4],
                    "calle": row[5],
                    "location": {
                        "lat": float(row[6]),
                        "lon": float(row[7])
                    },
                    "@timestamp": datetime.utcnow().isoformat() + "Z"
                }

                action = {
                    "_index": "waze_events",
                    "_source": doc
                }
                actions.append(action)

        # Usamos helpers.bulk para una inserción masiva y eficiente (mucho más rápido que 1 por 1)
        if actions:
            success, _ = helpers.bulk(es, actions)
            print(f"{success} eventos indexados correctamente en 'waze_events'.")

    except Exception as e:
        print(f"Error cargando eventos a Elasticsearch: {e}")


def load_cache_metrics_to_es(es):
    """
    Extrae las estadísticas del CacheMiddleware (Redis) y las envía a Elasticsearch
    para cumplir con los requerimientos de métricas de visualización.
    """
    print("--- ENVIANDO MÉTRICAS DE CACHÉ A ELASTICSEARCH ---")
    try:
        stats = cache_manager.stats
        total_requests = stats["hits"] + stats["misses"]
        hit_rate = (stats["hits"] / total_requests) * \
            100 if total_requests > 0 else 0

        doc = {
            "hits": stats["hits"],
            "misses": stats["misses"],
            "total_time": stats["total_time"],
            "hit_rate": hit_rate,
            "@timestamp": datetime.utcnow().isoformat() + "Z"
        }

        es.index(index="waze_metrics", document=doc)
        print("Métricas de rendimiento de caché indexadas correctamente en 'waze_metrics'.")

    except Exception as e:
        print(f"Error cargando métricas a Elasticsearch: {e}")


if __name__ == "__main__":
    es_client = setup_elasticsearch()
    if es_client:
        load_cleaned_events_to_es(es_client)
        load_cache_metrics_to_es(es_client)

import json
import time
import redis
from storage.db_client import pg_manager

# Configuración de Redis
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
TTL_SECONDS = 60  # Tiempo de vida de la clave (opcional)


class CacheMiddleware:
    def __init__(self):
        # Conexión a Redis
        try:
            self.client = redis.Redis(
                host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
            self.client.ping()
            print("Conectado a Redis Cache")
        except Exception as e:
            print(f"Error conectando a Redis: {e}")
            self.client = None

        # Métricas para el informe
        self.stats = {"hits": 0, "misses": 0, "total_time": 0}

    def get_event(self, event_uuid):
        """
        Flujo del Cache:
        1. Buscar en Redis (Rápido)
        2. Si no está -> Buscar en Postgres (Lento) -> Guardar en Redis
        """
        start_time = time.time()
        result = None
        source = "DB"

        # 1. Intento de Cache (HIT)
        if self.client:
            cached_data = self.client.get(event_uuid)
            if cached_data:
                self.stats["hits"] += 1
                result = json.loads(cached_data)
                source = "CACHE"

        # 2. Fallo de Cache (MISS) -> Ir a BD
        if not result:
            self.stats["misses"] += 1
            # Simulamos buscar en la BD (podríamos hacer una query real SELECT WHERE uuid=...)
            # Como el generador ya tiene los datos, simularemos que la BD los retorna.
            # En un sistema real, aquí harías: pg_manager.get_by_id(event_uuid)
            pass

        elapsed = (time.time() - start_time) * 1000  # ms
        self.stats["total_time"] += elapsed

        return source, elapsed

    def save_to_cache(self, event_uuid, data_dict):
        """Guarda un dato en Redis para futuras consultas"""
        if self.client:
            self.client.setex(event_uuid, TTL_SECONDS, json.dumps(data_dict))

    def get_metrics(self):
        total = self.stats["hits"] + self.stats["misses"]
        if total == 0:
            return "Sin datos"
        hit_rate = (self.stats["hits"] / total) * 100
        return f"Hits: {self.stats['hits']} | Misses: {self.stats['misses']} | Hit Rate: {hit_rate:.1f}%"


# Instancia global
cache_manager = CacheMiddleware()

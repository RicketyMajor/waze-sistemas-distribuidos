import os
import time
import json
import redis
# Configuración Inteligente
# Leemos la variable de entorno. Si no existe, avisa.
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = 6379
TTL_SECONDS = 60


class CacheMiddleware:
    def __init__(self):
        self.client = None
        self.stats = {"hits": 0, "misses": 0, "total_time": 0}

        print(
            f"Configuración detectada -> Host Redis: '{REDIS_HOST}' Puerto: {REDIS_PORT}")
        self._connect_with_retries()

    def _connect_with_retries(self):
        """Intenta conectar a Redis varias veces antes de rendirse"""
        max_retries = 5
        for i in range(max_retries):
            try:
                # Intentamos conectar
                self.client = redis.Redis(
                    host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
                # El ping es crucial: valida que la conexión es real
                self.client.ping()
                print(f"¡Conexión exitosa a Redis en '{REDIS_HOST}'!")
                return
            except redis.ConnectionError as e:
                print(
                    f"Intento {i+1}/{max_retries} fallido conectando a Redis ({e}). Reintentando en 2s...")
                self.client = None
                time.sleep(2)
            except Exception as e:
                print(f"Error desconocido en Redis: {e}")

        print("ERROR: No se pudo conectar a Redis tras varios intentos. El Cache estará DESACTIVADO.")

    def get_event(self, event_uuid):
        start_time = time.time()
        result = None
        source = "DB"

        # Si el cliente no existe (falló conexión), retornamos DB directo
        if not self.client:
            return "DB (Cache Down)", 0

        try:
            cached_data = self.client.get(event_uuid)
            if cached_data:
                self.stats["hits"] += 1
                result = json.loads(cached_data)
                source = "CACHE"
            else:
                self.stats["misses"] += 1

        except redis.ConnectionError:
            # Si Redis muere a mitad de camino
            print("Error de conexión leyendo Cache")
            source = "DB (Redis Error)"

        elapsed = (time.time() - start_time) * 1000
        self.stats["total_time"] += elapsed
        return source, elapsed

    def save_to_cache(self, event_uuid, data_dict):
        if self.client:
            try:
                self.client.setex(event_uuid, TTL_SECONDS,
                                  json.dumps(data_dict))
            except Exception as e:
                print(f"No se pudo guardar en cache: {e}")

    def get_metrics(self):
        total = self.stats["hits"] + self.stats["misses"]
        if total == 0:
            return "Sin datos (0 consultas)"
        hit_rate = (self.stats["hits"] / total) * 100
        return f"Hits: {self.stats['hits']} | Misses: {self.stats['misses']} | Hit Rate: {hit_rate:.1f}%"


cache_manager = CacheMiddleware()

import time
import random
import os
import csv
from storage.db_client import pg_manager
from cache_service.redis_client import cache_manager

# - - - - - - - - - - - - - - - - - - - - - -
# Traffic Generator
# - - - - - - - - - - - - - - - - - - - - - -

class TrafficGenerator:
    def __init__(self):
        """Initializes the Traffic Generator with Telemetry."""
        print("Inicializando Generador de Tráfico con Telemetría...")
        self.seeds = pg_manager.get_simulation_seeds(limit=50)

        # Logging setup
        self.exp_name = os.getenv('EXPERIMENT_NAME', 'default_run')
        self.csv_file = f"results/{self.exp_name}.csv"

        if not os.path.exists(self.csv_file):
            with open(self.csv_file, mode='w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(
                    ["timestamp", "seconds_elapsed", "total_queries", "hit_rate"])

        print(f"Guardando métricas en: {self.csv_file}")

    def log_metrics(self, start_time, total_queries):
        """Logs the current metrics to a CSV file."""
        metrics = cache_manager.stats
        total = metrics["hits"] + metrics["misses"]
        hit_rate = (metrics["hits"] / total * 100) if total > 0 else 0

        elapsed = time.time() - start_time

        with open(self.csv_file, mode='a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([time.strftime("%H:%M:%S"), round(
                elapsed, 2), total_queries, round(hit_rate, 2)])

    def simulate_query(self):
        """Simulates a single query to the cache."""
        if not self.seeds:
            return
        target = random.choice(self.seeds)
        uuid = target[0]
        fake_data = {"uuid": uuid, "info": "Simulated"}

        source, _ = cache_manager.get_event(uuid)
        if source.startswith("DB"):
            cache_manager.save_to_cache(uuid, fake_data)

    def start_mixed_traffic(self, duration_hours):
        """Starts a mixed traffic simulation for a given duration."""
        print(
            f"--- INICIANDO EXPERIMENTO DE {duration_hours} HORAS ({self.exp_name}) ---")

        start_time = time.time()
        end_time = start_time + (duration_hours * 3600)
        query_count = 0

        try:
            while time.time() < end_time:
                mode = random.choice(['normal', 'normal', 'normal', 'burst'])

                if mode == 'normal':
                    for _ in range(20):
                        self.simulate_query()
                        query_count += 1
                        time.sleep(random.expovariate(5.0))
                else:
                    for _ in range(50):
                        self.simulate_query()
                        query_count += 1
                        time.sleep(0.01)

                if query_count % 100 == 0:
                    self.log_metrics(start_time, query_count)
                    print(
                        f"Log registrado. Consultas: {query_count} | Hit Rate actual: {cache_manager.get_metrics()}")

        except KeyboardInterrupt:
            print("\nExperimento detenido manualmente.")

# - - - - - - - - - - - - - - - - - - - - - -
# Main
# - - - - - - - - - - - - - - - - - - - - - -

if __name__ == "__main__":
    gen = TrafficGenerator()
    if gen.seeds:
        duration_env = os.getenv('EXPERIMENT_DURATION', '1.0')

        try:
            duration = float(duration_env)
        except ValueError:
            print(
                f"Error leyendo duración '{duration_env}', usando 1.0 por defecto.")
            duration = 1.0

        print(
            f"Configuración recibida desde Docker: Duración = {duration} horas")

        gen.start_mixed_traffic(duration_hours=duration)

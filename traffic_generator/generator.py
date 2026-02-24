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
        self.traffic_type = os.getenv('TRAFFIC_TYPE', 'operational')
        # NUEVO: Controla si atacamos a Redis o a DB
        self.data_source = os.getenv('DATA_SOURCE', 'redis')

        print(
            f"Inicializando Generador ({self.traffic_type.upper()}) apuntando a -> {self.data_source.upper()}")

        self.seeds = pg_manager.get_simulation_seeds(limit=50)
        self.exp_name = os.getenv('EXPERIMENT_NAME', 'default_run')
        self.csv_file = f"results/{self.exp_name}.csv"

        # Variables locales para forzar métricas de latencia exactas
        self.total_latency = 0
        self.query_count = 0

        os.makedirs("results", exist_ok=True)
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, mode='w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["timestamp", "seconds_elapsed",
                                "total_queries", "hit_rate", "avg_latency_ms"])

    def log_metrics(self, start_time):
        """Guarda las métricas en el CSV."""
        if self.traffic_type == 'analytical':
            hit_rate = 100.0 if self.data_source == 'redis' else 0.0
            avg_latency = (self.total_latency /
                           self.query_count) if self.query_count > 0 else 0
        else:
            # Lógica original para operacional
            metrics = cache_manager.stats
            total = metrics["hits"] + metrics["misses"]
            hit_rate = (metrics["hits"] / total * 100) if total > 0 else 0
            avg_latency = (metrics["total_time"] / total) if total > 0 else 0

        elapsed = time.time() - start_time
        with open(self.csv_file, mode='a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([time.strftime("%H:%M:%S"), round(
                elapsed, 2), self.query_count, round(hit_rate, 2), round(avg_latency, 2)])

    def simulate_operational_query(self):
        if not self.seeds:
            return
        target = random.choice(self.seeds)
        uuid = target[0]
        source, _ = cache_manager.get_event(uuid)
        if source and source.startswith("DB"):
            cache_manager.save_to_cache(
                uuid, {"uuid": uuid, "info": "Simulated"})

    def simulate_analytical_query(self):
        reports = ['by_comuna', 'by_type', 'temporal']
        report = random.choice(reports)

        if self.data_source == 'postgres':
            elapsed = pg_manager.calculate_analytics_on_the_fly(report)
            self.total_latency += elapsed
        else:
            _, elapsed = cache_manager.get_analytics(report)
            self.total_latency += elapsed

    def start_mixed_traffic(self, duration_hours):
        print(
            f"--- INICIANDO EXPERIMENTO DE {duration_hours} HORAS ({self.exp_name}) ---")
        start_time = time.time()
        end_time = start_time + (duration_hours * 3600)

        try:
            while time.time() < end_time:
                mode = random.choice(['normal', 'normal', 'normal', 'burst'])
                iterations = 20 if mode == 'normal' else 50
                sleep_time = random.expovariate(
                    5.0) if mode == 'normal' else 0.01

                for _ in range(iterations):
                    if self.traffic_type == 'analytical':
                        self.simulate_analytical_query()
                    else:
                        self.simulate_operational_query()

                    self.query_count += 1
                    time.sleep(sleep_time)

                if self.query_count % 100 == 0:
                    self.log_metrics(start_time)
                    print(f"Log registrado. Consultas: {self.query_count}")

        except KeyboardInterrupt:
            print("\nExperimento detenido.")


if __name__ == "__main__":
    gen = TrafficGenerator()
    if gen.seeds or gen.traffic_type == 'analytical':
        duration = float(os.getenv('EXPERIMENT_DURATION', '1.0'))
        gen.start_mixed_traffic(duration_hours=duration)

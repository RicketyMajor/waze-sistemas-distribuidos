import time
import random
from storage.db_client import pg_manager
from cache_service.redis_client import cache_manager


class TrafficGenerator:
    def __init__(self):
        print("Inicializando Generador de Tráfico...")
        # Aumentamos el límite para tener variedad
        self.seeds = pg_manager.get_simulation_seeds(limit=1000)

        if not self.seeds:
            print("ADVERTENCIA: No hay datos en la BD para simular.")
            print("   -> Solución: Corre el scraper un rato para llenar la tabla.")
        else:
            print(
                f"Cargadas {len(self.seeds)} ubicaciones semilla desde PostgreSQL.")

    def simulate_query(self):
        if not self.seeds:
            return

        # Elegimos un evento al azar para consultar
        target = random.choice(self.seeds)
        uuid = target[0]

        # Datos falsos que simulamos recibir
        fake_data = {
            "uuid": uuid, "lat": target[2], "lon": target[1], "info": "Simulated payload"}

        # 1. Consultamos al Cache
        source, latency = cache_manager.get_event(uuid)

        # 2. Si falló el cache (MISS), guardamos para la próxima (Simulando lectura de BD)
        if source == "DB":
            cache_manager.save_to_cache(uuid, fake_data)

        # --- IMPRESIÓN EN PANTALLA (Ahora activada) ---
        # Usamos colores simples si tu terminal lo soporta, o texto plano
        icon = "HIT " if source == "CACHE" else "MISS"
        print(
            f"{icon} [{source}] UUID:{uuid[:8]}... | Latencia: {latency:.2f}ms")

    def start_poisson_mode(self, duration_seconds=15, lambd=5.0):
        print(f"\n--- INICIANDO MODO NORMAL (Poisson) ---")
        print(
            f"   (Simulando usuarios llegando aleatoriamente por {duration_seconds}s)")

        end_time = time.time() + duration_seconds
        while time.time() < end_time:
            self.simulate_query()
            # Espera aleatoria exponencial
            time.sleep(random.expovariate(lambd))

        print(f"\n📊 RESUMEN POISSON: {cache_manager.get_metrics()}")

    def start_burst_mode(self, duration_seconds=10, intensity=0.01):
        print(f"\n--- INICIANDO MODO RÁFAGA (Burst/Tráfico Pesado) ---")
        print(f"   (Simulando avalancha de consultas por {duration_seconds}s)")

        end_time = time.time() + duration_seconds
        while time.time() < end_time:
            self.simulate_query()
            # Espera constante muy corta
            time.sleep(intensity)

        print(f"\nRESUMEN RÁFAGA: {cache_manager.get_metrics()}")


if __name__ == "__main__":
    gen = TrafficGenerator()
    if gen.seeds:
        # Fase 1: Tráfico Normal
        gen.start_poisson_mode(duration_seconds=10, lambd=10)

        time.sleep(1)

        # Fase 2: Tráfico Intenso (Aquí verás muchos HITs)
        gen.start_burst_mode(duration_seconds=5, intensity=0.005)

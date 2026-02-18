import json
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from scraper.data_processor import process_waze_event
from storage.db_client import pg_manager

# - - - - - - - - - - - - - - - - - - - - - -
# Zonas de la Región Metropolitana
# - - - - - - - - - - - - - - - - - - - - - -
ZONAS_RM = [
    {"nombre": "Santiago Centro", "lat": "-33.4489", "lon": "-70.6693"},
    {"nombre": "Providencia/Las Condes", "lat": "-33.4150", "lon": "-70.5850"},
    {"nombre": "Maipú/Cerrillos", "lat": "-33.5100", "lon": "-70.7587"},
    {"nombre": "La Florida/Macul", "lat": "-33.5226", "lon": "-70.5985"},
    {"nombre": "Puente Alto", "lat": "-33.6117", "lon": "-70.5758"},
    {"nombre": "Quilicura/Huechuraba", "lat": "-33.3653", "lon": "-70.7303"},
    {"nombre": "San Bernardo", "lat": "-33.5912", "lon": "-70.7046"},
    {"nombre": "Pudahuel/Lo Prado", "lat": "-33.4400", "lon": "-70.7500"}
]
zoom = "13"  # Zoom 13 abarca más kilómetros cuadrados por cada coordenada

# - - - - - - - - - - - - - - - - - - - - - -
# Waze Scraper
# - - - - - - - - - - - - - - - - - - - - - -


def get_waze_traffic_data(lat, lon, nombre_zona):
    """Gets Waze traffic data across multiple zones and stores it in the database."""
    print(f"--- INICIANDO SCRAPER ZONA: {nombre_zona} (PostgreSQL) ---")

    # Creamos la URL dinámicamente según la zona que pasemos por parámetro
    WAZE_URL = f"https://www.waze.com/es-419/live-map/directions?latlng={lat}%2C{lon}&zoom={zoom}"

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    chrome_options.add_argument(f'user-agent={user_agent}')
    chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    new_events_count = 0

    try:
        driver.get(WAZE_URL)
        print("Cargando mapa... (esperando 8s)")
        time.sleep(8)
        driver.execute_script("window.scrollTo(0, 100);")
        time.sleep(2)

        logs = driver.get_log('performance')

        for entry in logs:
            try:
                message_json = json.loads(entry['message'])
                message = message_json['message']
                if message['method'] == 'Network.responseReceived':
                    response_url = message['params']['response']['url']

                    if "live-map/api/georss" in response_url:
                        request_id = message['params']['requestId']
                        response_body = driver.execute_cdp_cmd(
                            'Network.getResponseBody', {'requestId': request_id})
                        raw_data = json.loads(response_body['body'])

                        items_to_process = []
                        if 'alerts' in raw_data:
                            items_to_process.extend(raw_data['alerts'])
                        if 'jams' in raw_data:
                            items_to_process.extend(raw_data['jams'])

                        for item in items_to_process:
                            clean_event = process_waze_event(item)
                            if clean_event:
                                saved = pg_manager.insert_event(clean_event)
                                if saved:
                                    new_events_count += 1

            except Exception:
                pass

    except Exception as e:
        print(f"Error en scraping: {e}")
    finally:
        driver.quit()

    total_in_db = pg_manager.count_events()
    print(f"--- RESUMEN CICLO ({nombre_zona}) ---")
    print(f"Nuevos eventos guardados: {new_events_count}")
    print(f"Total en PostgreSQL:      {total_in_db}")

    return new_events_count

# - - - - - - - - - - - - - - - - - - - - - -
# Main
# - - - - - - - - - - - - - - - - - - - - - -


if __name__ == "__main__":
    print("Iniciando recolección continua MULTIZONA hacia PostgreSQL.")
    try:
        while True:
            for zona in ZONAS_RM:
                # Llamamos a la función por cada zona
                get_waze_traffic_data(zona["lat"], zona["lon"], zona["nombre"])
                time.sleep(5)  # Breve pausa entre zonas para no saturar CPU

            wait_time = random.randint(15, 30)
            print(
                f"Ciclo RM completado. Durmiendo {wait_time} segundos antes del siguiente barrido...")
            time.sleep(wait_time)

    except KeyboardInterrupt:
        print("\nRecolección detenida manualmente.")

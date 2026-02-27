import json
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from scraper.data_processor import process_waze_event
from storage.db_client import pg_manager

# --------------------------------------------------------------------------
# Zonas de la Región Metropolitana
# --------------------------------------------------------------------------
ZONAS_RM = [
    # Provincia de Santiago
    {"nombre": "Santiago", "lat": "-33.4489",
        "lon": "-70.6693"}, {"nombre": "Cerrillos", "lat": "-33.5000", "lon": "-70.7167"},
    {"nombre": "Cerro Navia", "lat": "-33.4222",
        "lon": "-70.7389"}, {"nombre": "Conchali", "lat": "-33.3833", "lon": "-70.6833"},
    {"nombre": "El Bosque", "lat": "-33.5667", "lon": "-70.6667"}, {
        "nombre": "Estacion Central", "lat": "-33.4667", "lon": "-70.7000"},
    {"nombre": "Huechuraba", "lat": "-33.3667", "lon": "-70.6333"}, {
        "nombre": "Independencia", "lat": "-33.4167", "lon": "-70.6667"},
    {"nombre": "La Cisterna", "lat": "-33.5333",
        "lon": "-70.6667"}, {"nombre": "La Florida", "lat": "-33.5167", "lon": "-70.5333"},
    {"nombre": "La Granja", "lat": "-33.5333",
        "lon": "-70.6167"}, {"nombre": "La Pintana", "lat": "-33.5833", "lon": "-70.6333"},
    {"nombre": "La Reina", "lat": "-33.4500",
        "lon": "-70.5333"}, {"nombre": "Las Condes", "lat": "-33.4167", "lon": "-70.5833"},
    {"nombre": "Lo Barnechea", "lat": "-33.3500",
        "lon": "-70.5167"}, {"nombre": "Lo Espejo", "lat": "-33.5167", "lon": "-70.6833"},
    {"nombre": "Lo Prado", "lat": "-33.4500",
        "lon": "-70.7167"}, {"nombre": "Macul", "lat": "-33.5000", "lon": "-70.6000"},
    {"nombre": "Maipu", "lat": "-33.5167", "lon": "-70.7667"}, {"nombre": "Nunoa",
                                                                "lat": "-33.4500", "lon": "-70.6000"},
    {"nombre": "Pedro Aguirre Cerda", "lat": "-33.4833",
        "lon": "-70.6667"}, {"nombre": "Penalolen", "lat": "-33.4833", "lon": "-70.5333"},
    {"nombre": "Providencia", "lat": "-33.4333",
        "lon": "-70.6167"}, {"nombre": "Pudahuel", "lat": "-33.4333", "lon": "-70.7667"},
    {"nombre": "Quilicura", "lat": "-33.3667", "lon": "-70.7333"}, {
        "nombre": "Quinta Normal", "lat": "-33.4333", "lon": "-70.6833"},
    {"nombre": "Recoleta", "lat": "-33.4000",
        "lon": "-70.6333"}, {"nombre": "Renca", "lat": "-33.4000", "lon": "-70.7333"},
    {"nombre": "San Joaquin", "lat": "-33.4833",
        "lon": "-70.6333"}, {"nombre": "San Miguel", "lat": "-33.4833", "lon": "-70.6500"},
    {"nombre": "San Ramon", "lat": "-33.5333",
        "lon": "-70.6333"}, {"nombre": "Vitacura", "lat": "-33.4000", "lon": "-70.6000"},
    # Provincias Periféricas (Cordillera, Maipo, Melipilla, Talagante, Chacabuco)
    {"nombre": "Puente Alto", "lat": "-33.6167",
        "lon": "-70.5833"}, {"nombre": "Pirque", "lat": "-33.6333", "lon": "-70.5500"},
    {"nombre": "San Jose de Maipo", "lat": "-33.6333",
        "lon": "-70.3500"}, {"nombre": "San Bernardo", "lat": "-33.5833", "lon": "-70.7000"},
    {"nombre": "Buin", "lat": "-33.7333", "lon": "-70.7333"}, {
        "nombre": "Calera de Tango", "lat": "-33.6333", "lon": "-70.7833"},
    {"nombre": "Paine", "lat": "-33.8167", "lon": "-70.7500"}, {"nombre": "Melipilla",
                                                                "lat": "-33.6833", "lon": "-71.2167"},
    {"nombre": "Alhue", "lat": "-34.0333", "lon": "-71.1000"}, {"nombre": "Curacavi",
                                                                "lat": "-33.4000", "lon": "-71.1500"},
    {"nombre": "Maria Pinto", "lat": "-33.5167",
        "lon": "-71.1167"}, {"nombre": "San Pedro", "lat": "-33.9000", "lon": "-71.4667"},
    {"nombre": "Talagante", "lat": "-33.6667",
        "lon": "-70.9333"}, {"nombre": "El Monte", "lat": "-33.6833", "lon": "-71.0167"},
    {"nombre": "Isla de Maipo", "lat": "-33.7500", "lon": "-70.9000"}, {
        "nombre": "Padre Hurtado", "lat": "-33.5667", "lon": "-70.8167"},
    {"nombre": "Penaflor", "lat": "-33.6000",
        "lon": "-70.8833"}, {"nombre": "Colina", "lat": "-33.2000", "lon": "-70.6667"},
    {"nombre": "Lampa", "lat": "-33.2833", "lon": "-70.8667"}, {"nombre": "Tiltil",
                                                                "lat": "-33.0833", "lon": "-70.9333"}
]
zoom = "14"

# --------------------------------------------------------------------------
# Waze Scraper
# --------------------------------------------------------------------------


def get_waze_traffic_data(lat, lon, nombre_zona):
    """
    Realiza scraping de datos de tráfico de Waze para una zona específica y
    los almacena en la base de datos PostgreSQL.
    """
    print(f"--- INICIANDO SCRAPER ZONA: {nombre_zona} (PostgreSQL) ---")

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

# --------------------------------------------------------------------------
# Bucle Principal de Ejecución
# --------------------------------------------------------------------------


if __name__ == "__main__":
    print("Iniciando recolección continua MULTIZONA hacia PostgreSQL.")
    try:
        while True:
            for zona in ZONAS_RM:
                get_waze_traffic_data(zona["lat"], zona["lon"], zona["nombre"])
                time.sleep(5)

            wait_time = random.randint(15, 30)
            print(
                f"Ciclo RM completado. Durmiendo {wait_time} segundos antes del siguiente barrido...")
            time.sleep(wait_time)

    except KeyboardInterrupt:
        print("\nRecolección detenida manually.")

import json
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from scraper.data_processor import process_waze_event

# Coordenadas de Santiago Centro (Zoom ajustado para abarcar más área)
# Waze carga datos según el viewport.
lat = "-33.4489"
lon = "-70.6693"
zoom = "14"
WAZE_URL = f"https://www.waze.com/es-419/live-map/directions?latlng={lat}%2C{lon}&zoom={zoom}"


def get_waze_traffic_data():
    print(f"--- INICIANDO SCRAPER ---")
    print(f"Target: {WAZE_URL}")

    # 1. Configuración del Navegador
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    # User-Agent "humano"
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    chrome_options.add_argument(f'user-agent={user_agent}')

    # Habilitar logs de performance
    chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    events_found = []

    try:
        driver.get(WAZE_URL)

        # Esperamos a que cargue el mapa visualmente
        print("Cargando mapa... (esperando 10s)")
        time.sleep(10)

        # Hacemos un pequeño scroll y movimiento del mouse (simulado) para forzar la petición de datos
        driver.execute_script("window.scrollTo(0, 100);")
        time.sleep(3)

        # 2. Leer logs de red
        logs = driver.get_log('performance')
        print(f"Analizando {len(logs)} eventos de red...")

        for entry in logs:
            try:
                message_json = json.loads(entry['message'])
                message = message_json['message']

                if message['method'] == 'Network.responseReceived':
                    response_url = message['params']['response']['url']

                    # FILTRO CLAVE: Buscamos la llamada 'georss' que descubrimos
                    if "live-map/api/georss" in response_url:
                        print(
                            f"¡Interceptada API de datos! -> {response_url[:60]}...")

                        request_id = message['params']['requestId']

                        # Extraemos el cuerpo de la respuesta
                        response_body = driver.execute_cdp_cmd(
                            'Network.getResponseBody',
                            {'requestId': request_id}
                        )

                        raw_data = json.loads(response_body['body'])

                        # Waze suele devolver listas directas o un objeto con claves
                        # Inspeccionamos qué llaves trae
                        # print(f"Llaves encontradas en JSON: {raw_data.keys()}")

                        if 'alerts' in raw_data:
                            print(
                                f" -> Procesando {len(raw_data['alerts'])} alertas...")
                            for item in raw_data['alerts']:
                                clean_item = process_waze_event(item)
                                if clean_item:
                                    events_found.append(clean_item)

                        if 'jams' in raw_data:
                            print(
                                f" -> Procesando {len(raw_data['jams'])} atascos...")
                            for item in raw_data['jams']:
                                clean_item = process_waze_event(item)
                                if clean_item:
                                    events_found.append(clean_item)

            except Exception as e:
                # Ignoramos errores de parseo de logs irrelevantes
                pass

    except Exception as e:
        print(f"Error fatal en el scraper: {e}")
    finally:
        driver.quit()
        print("--- SCRAPER FINALIZADO ---")

    return events_found


if __name__ == "__main__":
    data = get_waze_traffic_data()

    if len(data) > 0:
        filename = "sample_data.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"\n¡ÉXITO! Se guardaron {len(data)} eventos en '{filename}'.")
        print("Abre el archivo para ver la estructura.")
    else:
        print("\nResultado: 0 eventos. Si ves 'Interceptada API' arriba pero 0 eventos, es que el área del mapa estaba limpia en ese momento.")

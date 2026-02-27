import csv
import os
from storage.db_client import pg_manager

# --------------------------------------------------------------------------
# Proceso ETL: Filtrado y Homogeneización de Eventos
# --------------------------------------------------------------------------

def clean_and_homogenize():
    """
    Realiza un proceso de ETL (Extract, Transform, Load) sobre los datos
    crudos de eventos de Waze.
    """
    print("--- INICIANDO ETL: FILTRADO Y HOMOGENEIZACIÓN ---")
    raw_events = pg_manager.get_all_events()
    print(f"Total de eventos crudos extraídos de DB: {len(raw_events)}")

    type_mapping = {
        'ACCIDENT': 'ACCIDENTE',
        'JAM': 'CONGESTION',
        'ROAD_CLOSED': 'CORTE_RUTA',
        'WEATHERHAZARD': 'PELIGRO_VIAL',
        'HAZARD': 'PELIGRO_VIAL'
    }

    cleaned_data = {}

    for row in raw_events:
        waze_uuid, ts, lon, lat, e_type, e_subtype, desc, street, city = row

        if lon is None or lat is None or not e_type:
            continue

        city = city.strip() if city else "DESCONOCIDA"
        street = street.strip() if street else "SIN NOMBRE"
        e_subtype = e_subtype if e_subtype else "NO_ESPECIFICADO"

        std_type = type_mapping.get(e_type.upper(), 'OTRO')

        date_str = str(ts)[:10]
        geo_temp_key = f"{std_type}_{date_str}_{round(lat, 3)}_{round(lon, 3)}"

        if geo_temp_key not in cleaned_data:
            cleaned_data[geo_temp_key] = {
                "id": waze_uuid,
                "fecha": date_str,
                "tipo_incidente": std_type,
                "subtipo": e_subtype,
                "comuna": city.upper(),
                "calle": street,
                "latitud": round(lat, 5),
                "longitud": round(lon, 5)
            }

    final_events = list(cleaned_data.values())
    print(
        f"Total de eventos tras filtrado y homogeneización espacial: {len(final_events)}")

    output_path = '/app/shared_data/cleaned_waze_events.csv'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=',')
        for event in final_events:
            writer.writerow([
                event["id"],
                event["fecha"],
                event["tipo_incidente"],
                event["subtipo"],
                event["comuna"],
                event["calle"],
                event["latitud"],
                event["longitud"]
            ])

    print(f"Datos limpios y homogeneizados exportados a: {output_path}")


if __name__ == "__main__":
    clean_and_homogenize()

import uuid
from datetime import datetime


def process_waze_event(raw_event):
    """
    Transforma un evento crudo de Waze al formato del proyecto.
    """
    # Identificar tipo
    event_type = raw_event.get('type', 'UNKNOWN')
    subtype = raw_event.get('subType', '')

    # Si tiene velocidad, es un atochamiento (JAM)
    if 'speed' in raw_event:
        event_type = 'JAM'

    # Extraer coordenadas
    coords = None
    if 'location' in raw_event:
        waze_loc = raw_event['location']
        coords = [waze_loc['x'], waze_loc['y']]  # GeoJSON: [Lon, Lat]
    elif 'line' in raw_event:
        # En jams, tomamos el primer punto de la línea
        first_point = raw_event['line'][0]
        coords = [first_point['x'], first_point['y']]

    if not coords:
        return None

    # Construir objeto final
    processed_event = {
        "event_uuid": str(uuid.uuid4()),
        "waze_uuid": raw_event.get('uuid', raw_event.get('id', 'no-id')),
        "timestamp_scraped": datetime.utcnow().isoformat() + "Z",
        "location": {
            "type": "Point",
            "coordinates": coords
        },
        "type": event_type,
        "subtype": subtype,
        "description": raw_event.get('reportDescription', raw_event.get('street', '')),
        "city": raw_event.get('city', 'Santiago'),
        "street": raw_event.get('street', '')
    }

    return processed_event

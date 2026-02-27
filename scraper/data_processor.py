import uuid
from datetime import datetime

# --------------------------------------------------------------------------
# Procesador de Datos de Waze
# --------------------------------------------------------------------------

def process_waze_event(raw_event):
    """
    Transforma un evento crudo de Waze al formato estándar del proyecto,
    extrayendo y limpiando la información relevante.
    """
    event_type = raw_event.get('type', 'UNKNOWN')
    subtype = raw_event.get('subType', '')

    if 'speed' in raw_event:
        event_type = 'JAM'

    coords = None
    if 'location' in raw_event:
        waze_loc = raw_event['location']
        coords = [waze_loc['x'], waze_loc['y']]
    elif 'line' in raw_event:
        first_point = raw_event['line'][0]
        coords = [first_point['x'], first_point['y']]

    if not coords:
        return None

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

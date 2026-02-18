import uuid
from datetime import datetime

# - - - - - - - - - - - - - - - - - - - - - -
# Data Processing
# - - - - - - - - - - - - - - - - - - - - - -

def process_waze_event(raw_event):
    """Transforms a raw Waze event into the project's format."""
    # Identify event type
    event_type = raw_event.get('type', 'UNKNOWN')
    subtype = raw_event.get('subType', '')

    if 'speed' in raw_event:
        event_type = 'JAM'

    # Extract coordinates
    coords = None
    if 'location' in raw_event:
        waze_loc = raw_event['location']
        coords = [waze_loc['x'], waze_loc['y']]
    elif 'line' in raw_event:
        first_point = raw_event['line'][0]
        coords = [first_point['x'], first_point['y']]

    if not coords:
        return None

    # Build final object
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

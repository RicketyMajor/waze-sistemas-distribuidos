import os
import time
import psycopg2
from psycopg2.extras import Json

# - - - - - - - - - - - - - - - - - - - - - -
# Configuration
# - - - - - - - - - - - - - - - - - - - - - -

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_NAME = "waze_db"
DB_USER = "waze_user"
DB_PASS = "waze_password"
DB_PORT = "5432"

# - - - - - - - - - - - - - - - - - - - - - -
# Waze Postgres Client
# - - - - - - - - - - - - - - - - - - - - - -

class WazePostgresClient:
    def __init__(self):
        self.conn = None
        self._connect()
        self._create_table()

    def _connect(self):
        """Connects to the database with retries."""
        attempts = 0
        while attempts < 5:
            try:
                self.conn = psycopg2.connect(
                    host=DB_HOST,
                    database=DB_NAME,
                    user=DB_USER,
                    password=DB_PASS,
                    port=DB_PORT
                )
                self.conn.autocommit = True
                print("Conectado exitosamente a PostgreSQL")
                return
            except Exception as e:
                print(f"Esperando a PostgreSQL... ({e})")
                time.sleep(2)
                attempts += 1
        raise Exception("No se pudo conectar a la Base de Datos")

    def _create_table(self):
        """Defines the table schema and enables PostGIS."""
        with self.conn.cursor() as cur:
            # Enable PostGIS extension
            cur.execute("CREATE EXTENSION IF NOT EXISTS postgis;")

            # Create table if it doesn't exist
            cur.execute("""
                CREATE TABLE IF NOT EXISTS traffic_events (
                    id SERIAL PRIMARY KEY,
                    waze_uuid VARCHAR(100) UNIQUE,
                    event_uuid VARCHAR(100),
                    timestamp_scraped TIMESTAMP,
                    location GEOMETRY(Point, 4326), 
                    type VARCHAR(50),
                    subtype VARCHAR(50),
                    description TEXT,
                    street VARCHAR(200),
                    city VARCHAR(100),
                    raw_data JSONB
                );
            """)

            # Create spatial index
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_traffic_location 
                ON traffic_events USING GIST (location);
            """)

    def insert_event(self, event):
        """Inserts an event, transforming coordinates to PostGIS format."""
        try:
            with self.conn.cursor() as cur:
                lon, lat = event['location']['coordinates']
                point_str = f'POINT({lon} {lat})'

                cur.execute("""
                    INSERT INTO traffic_events 
                    (waze_uuid, event_uuid, timestamp_scraped, location, type, subtype, description, street, city)
                    VALUES (%s, %s, %s, ST_GeomFromText(%s, 4326), %s, %s, %s, %s, %s)
                    ON CONFLICT (waze_uuid) DO NOTHING;
                """, (
                    event['waze_uuid'],
                    event['event_uuid'],
                    event['timestamp_scraped'],
                    point_str,
                    event['type'],
                    event['subtype'],
                    event['description'],
                    event['street'],
                    event['city']
                ))

                return cur.rowcount > 0

        except Exception as e:
            print(f"Error insertando: {e}")
            return False

    def get_simulation_seeds(self, limit=100):
        """Retrieves a batch of real coordinates and IDs for the traffic generator."""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT waze_uuid, ST_X(location) as lon, ST_Y(location) as lat 
                    FROM traffic_events 
                    ORDER BY RANDOM() 
                    LIMIT %s;
                """, (limit,))
                return cur.fetchall()
        except Exception as e:
            print(f"Error obteniendo semillas: {e}")
            return []

    def count_events(self):
        """Counts the total number of events in the database."""
        with self.conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM traffic_events;")
            return cur.fetchone()[0]


pg_manager = WazePostgresClient()

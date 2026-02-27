import os
import time
import psycopg2
from psycopg2.extras import Json

# --------------------------------------------------------------------------
# Configuración de la Base de Datos
# --------------------------------------------------------------------------

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_NAME = "waze_db"
DB_USER = "waze_user"
DB_PASS = "waze_password"
DB_PORT = "5432"

# --------------------------------------------------------------------------
# Cliente de PostgreSQL para Waze
# --------------------------------------------------------------------------

class WazePostgresClient:
    """
    Cliente para gestionar la conexión y operaciones con la base de datos
    PostgreSQL, incluyendo la creación de tablas y la inserción de eventos.
    """
    def __init__(self):
        self.conn = None
        self._connect()
        self._create_table()

    def _connect(self):
        """Conecta a la base de datos con reintentos."""
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
        """Define el esquema de la tabla y habilita PostGIS."""
        with self.conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
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
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_traffic_location
                ON traffic_events USING GIST (location);
            """)

    def insert_event(self, event):
        """Inserta un evento, transformando coordenadas al formato PostGIS."""
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
        """Obtiene un lote de coordenadas reales para el generador de tráfico."""
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
        """Cuenta el número total de eventos en la base de datos."""
        with self.conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM traffic_events;")
            return cur.fetchone()[0]

    def get_all_events(self):
        """Obtiene todos los eventos para el proceso ETL de Big Data."""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT waze_uuid, timestamp_scraped, ST_X(location) as lon, ST_Y(location) as lat,
                           type, subtype, description, street, city
                    FROM traffic_events;
                """)
                return cur.fetchall()
        except Exception as e:
            print(f"Error obteniendo todos los eventos para ETL: {e}")
            return []

    def calculate_analytics_on_the_fly(self, report_name):
        """Calcula analíticas directamente en SQL para comparar latencia."""
        start_time = time.time()
        try:
            with self.conn.cursor() as cur:
                if report_name == 'by_type':
                    cur.execute(
                        "SELECT type, COUNT(*) FROM traffic_events GROUP BY type;")
                elif report_name == 'by_comuna':
                    cur.execute(
                        "SELECT city, COUNT(*) FROM traffic_events GROUP BY city;")
                elif report_name == 'temporal':
                    cur.execute(
                        "SELECT timestamp_scraped::date, city, type, COUNT(*) FROM traffic_events GROUP BY 1, 2, 3;")
                cur.fetchall()
        except Exception as e:
            pass
        elapsed = (time.time() - start_time) * 1000
        return elapsed


pg_manager = WazePostgresClient()

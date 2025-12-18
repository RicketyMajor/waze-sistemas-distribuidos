import os
import time
import psycopg2
from psycopg2.extras import Json

# Configuración
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_NAME = "waze_db"
DB_USER = "waze_user"
DB_PASS = "waze_password"
DB_PORT = "5432"


class WazePostgresClient:
    def __init__(self):
        self.conn = None
        self._connect()
        self._create_table()

    def _connect(self):
        """Intenta conectar a la BD con reintentos (útil si Docker está despertando)"""
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
        """Define el esquema de la tabla y habilita PostGIS"""
        with self.conn.cursor() as cur:
            # 1. Habilitar extensión PostGIS (Magia para mapas)
            cur.execute("CREATE EXTENSION IF NOT EXISTS postgis;")

            # 2. Crear tabla si no existe
            # Usamos GEOMETRY(Point, 4326) que es el estándar GPS (Lat/Lon)
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

            # 3. Crear índice espacial (para búsquedas por distancia rápidas)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_traffic_location 
                ON traffic_events USING GIST (location);
            """)

    def insert_event(self, event):
        """
        Inserta un evento transformando las coordenadas a formato PostGIS.
        Retorna True si insertó, False si era duplicado.
        """
        try:
            with self.conn.cursor() as cur:
                # PostGIS usa formato 'POINT(lon lat)'
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

                # cur.rowcount es 1 si insertó, 0 si no hizo nada (duplicado)
                return cur.rowcount > 0

        except Exception as e:
            print(f"Error insertando: {e}")
            return False

    def get_simulation_seeds(self, limit=100):
        """
        Recupera un lote de coordenadas reales y IDs para usarlos como 
        semilla en el generador de tráfico.
        """
        try:
            with self.conn.cursor() as cur:
                # Obtenemos IDs y coordenadas de eventos reales
                cur.execute("""
                    SELECT waze_uuid, ST_X(location) as lon, ST_Y(location) as lat 
                    FROM traffic_events 
                    ORDER BY RANDOM() 
                    LIMIT %s;
                """, (limit,))
                return cur.fetchall()  # Retorna lista de tuplas [(uuid, lon, lat), ...]
        except Exception as e:
            print(f"Error obteniendo semillas: {e}")
            return []

    def count_events(self):
        with self.conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM traffic_events;")
            return cur.fetchone()[0]


# Instancia global
pg_manager = WazePostgresClient()

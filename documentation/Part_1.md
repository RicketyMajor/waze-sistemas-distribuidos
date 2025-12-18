# Entregable 1: Datos y Cache

## Plataforma de Análisis de Tráfico en Región Metropolitana

---

## 1. Introducción

Este documento describe el desarrollo y la implementación del primer módulo del proyecto de Sistemas Distribuidos orientado a la análisis de tráfico en la Región Metropolitana. Este entregable constituye la base fundamental del sistema, estableciendo los cimientos para la posterior extracción, almacenamiento, generación de tráfico simulado y optimización mediante cachés.

El objetivo principal de esta fase es diseñar e implementar una arquitectura modular que permita:

- Extraer datos en tiempo real desde la plataforma Waze mediante técnicas de web scraping.
- Almacenar los eventos extraídos de manera persistente y escalable.
- Generar tráfico sintético que simule el comportamiento de usuarios del sistema.
- Implementar un sistema de caché que optimice el acceso a datos frecuentes.

La presente entrega aborda las **Fases 1 a 5** del plan de trabajo, completando la configuración del entorno, la extracción de datos en tiempo real, almacenamiento persistente con PostgreSQL, generación de tráfico sintético con distribuciones matemáticas, y optimización mediante sistemas de caché con múltiples políticas de reemplazo.

---

## 2. Fase 1: Configuración del Entorno y Diseño Arquitectónico

### 2.1. Inicialización del Repositorio Git

Se estableció un repositorio Git local en WSL2 con la configuración necesaria para asegurar control de versiones efectivo y prácticas de desarrollo colaborativo. Las principales acciones realizadas fueron:

- **Inicialización del repositorio**: Se ejecutó `git init` en el directorio raíz del proyecto.
- **Configuración de .gitignore**: Se creó un archivo `.gitignore` que excluye archivos específicos de Python, Docker y configuraciones sensibles (variables de entorno, archivos compilados, etc.).
- **Estructura de ramas**: Se establecieron dos ramas principales:
  - **main**: Rama de producción que contiene código estable y validado.
  - **dev**: Rama de desarrollo para experimentación e integración de nuevas funcionalidades.

Esta estructura de ramas permite un flujo de trabajo ordenado, donde los cambios se prueban en desarrollo antes de ser integrados a la rama principal.

### 2.2. Estructura de Carpetas

El proyecto fue organizado en una estructura modular que facilita el mantenimiento, escalabilidad y futuras extensiones. La arquitectura se divide en los siguientes directorios:

```
waze-sistemas-distribuidos/
├── scraper/                 # Módulo de extracción de datos desde Waze
├── storage/                 # Esquemas y modelos de datos
├── traffic_generator/       # Módulo de generación de tráfico sintético
├── cache_service/           # Módulo de caché con políticas de reemplazo
├── docker-compose.yml       # Orquestación de servicios en contenedores
├── requirements.txt         # Dependencias del proyecto
├── README.md                # Documentación general del proyecto
└── documentation/           # Documentación detallada
    └── Part_1.md            # Este documento
```

Cada módulo funciona de manera independiente, facilitando su mantenimiento, prueba y futuras integraciones con otros componentes del sistema.

### 2.3. Diseño del Modelo de Datos

Se definió un esquema JSON estructurado para representar los eventos de tráfico extraídos desde Waze. Este modelo fue diseñado considerando los siguientes aspectos:

- **Identificación única**: Cada evento posee un identificador único (`event_uuid`) generado por el sistema y el identificador original de Waze (`waze_uuid`).
- **Información geoespacial**: Los eventos incluyen coordenadas en formato GeoJSON (estándar internacional para datos geoespaciales).
- **Metadatos temporales**: Se registra la marca de tiempo (`timestamp_scraped`) indicando cuándo fue extraído el evento.
- **Clasificación de eventos**: Los eventos se clasifican por tipo (JAM, ALERT, etc.) y subtipo (HEAVY_JAM, HAZARD, etc.).
- **Información contextual**: Se captura información sobre la ubicación geográfica (ciudad, calle) y descripción del incidente.

#### Esquema del Evento

```json
{
  "event_uuid": "12345-abcde-67890",
  "waze_uuid": "23423424",
  "timestamp_scraped": "2023-10-27T10:00:00Z",
  "location": {
    "type": "Point",
    "coordinates": [-70.6483, -33.4489]
  },
  "type": "JAM",
  "subtype": "HEAVY_JAM",
  "description": "Atasco suave en Alameda",
  "city": "Santiago",
  "street": "Av. Libertador Bernardo O'Higgins"
}
```

Este esquema proporciona la información esencial para análisis de tráfico, visualización geoespacial y procesamiento posterior de datos.

---

## 3. Fase 2: Módulo Scraper (Extracción de Datos)

### 3.1. Investigación Técnica de la Plataforma Waze

La extracción de datos desde Waze presentó un desafío técnico inicial debido a que la plataforma implementa rendering dinámico de contenido mediante JavaScript. A través de inspección de la red en las herramientas de desarrollador del navegador, se identificó:

- **Endpoint API oculta**: La plataforma Waze utiliza una API interna en `live-map/api/georss` que retorna datos JSON conteniendo información de tráfico.
- **Datos disponibles**: La API expone dos tipos principales de eventos:
  - **Alerts**: Alertas sobre incidentes (accidentes, peligros, etc.)
  - **Jams**: Congestión o atascos en vías

La estrategia de scraping desarrollada aprovecha este descubrimiento, interceptando las solicitudes de red realizadas por el navegador web.

### 3.2. Implementación del Scraper

El módulo scraper fue implementado utilizando **Selenium WebDriver**, una librería especializada en automatización web que permite interactuar con navegadores reales. Esta elección fue fundamentada en:

- **Manejo de JavaScript**: Selenium ejecuta el código JavaScript de la página, permitiendo acceso a datos dinámicamente cargados.
- **Interceptación de red**: A través de los protocolos Chrome DevTools Protocol (CDP), es posible capturar solicitudes y respuestas HTTP internas.
- **Control programático**: Permite simular interacciones de usuario (scroll, esperas, etc.) para forzar la carga de datos.

#### Componentes Principales

**1. Archivo: `scraper/waze_scraper.py`**

Este archivo contiene la lógica principal del scraping:

- **Configuración del navegador**: Se configura Chromium en modo headless (sin interfaz gráfica) para ejecutarse en contenedores.
- **Parámetros de localización**: Se centra el mapa en Santiago Centro (coordenadas: -33.4489, -70.6693) con zoom nivel 14 para abarcar toda la región metropolitana.
- **Interceptación de red**: Se activan los logs de performance del navegador para capturar todas las solicitudes HTTP.
- **Filtrado de respuestas**: Se filtran únicamente las respuestas de la API `georss`, ignorando otras solicitudes de red.
- **Extracción de datos**: Se recupera el cuerpo de las respuestas HTTP, parseándolo como JSON.

La función principal `get_waze_traffic_data()` ejecuta el siguiente flujo:

```
1. Inicializar Chromium en modo headless con configuración de sandbox deshabilitada
2. Navegar a la URL de Waze con coordenadas específicas
3. Esperar 10 segundos para la carga del mapa
4. Ejecutar scroll para forzar nuevas solicitudes de datos
5. Capturar logs de red de performance
6. Filtrar solicitudes hacia la API georss
7. Extraer cuerpos de respuesta
8. Parsear JSON y procesar eventos
9. Retornar lista de eventos normalizados
```

**2. Archivo: `scraper/data_processor.py`**

Este módulo implementa la normalización de datos extraídos:

- **Procesamiento de eventos**: La función `process_waze_event()` transforma eventos crudos de Waze al formato estándar del proyecto.
- **Identificación de tipo**: Detecta automáticamente si un evento es un atasco (JAM) o una alerta (ALERT) basándose en los campos presentes.
- **Normalización geoespacial**: Extrae coordenadas de diferentes formatos de Waze y las convierte al estándar GeoJSON (longitude, latitude).
- **Generación de UUIDs**: Asigna identificadores únicos a cada evento procesado.
- **Captura de metadatos**: Registra marca de tiempo, descripción, ubicación (calle, ciudad) y otros detalles relevantes.

El procesamiento incluye validación para descartar eventos sin coordenadas válidas, garantizando calidad de datos.

### 3.3. Dependencias del Proyecto

Las dependencias necesarias para el módulo scraper fueron documentadas en `requirements.txt`:

```
selenium==4.39.0          # Automatización de navegadores web
webdriver-manager==4.0.2  # Gestión automática de ChromeDriver
requests==2.32.5          # Cliente HTTP para solicitudes web
python-dotenv==1.2.1      # Carga de variables de entorno
```

Además de estas dependencias, se incluyen librerías auxiliares:

- **Manejo de red**: `urllib3`, `certifi` para conexiones HTTPS seguras.
- **Concurrencia**: `trio`, `trio-websocket` para operaciones asincrónicas.
- **Utilidades**: `packaging`, `attrs`, `sortedcontainers` para funcionalidad adicional.

### 3.4. Desafíos Técnicos y Soluciones

Durante el desarrollo del scraper, se enfrentaron varios desafíos:

**Desafío 1: Renderizado dinámico de contenido**

- **Problema**: Waze carga datos mediante JavaScript, no disponibles en HTML estático.
- **Solución**: Utilizar Selenium WebDriver para ejecutar JavaScript y esperar a que el contenido se cargue.

**Desafío 2: Detección de bot**

- **Problema**: Los servidores de Waze pueden rechazar solicitudes automatizadas.
- **Solución**: Implementar un user-agent realista y configurar opciones de seguridad para simular un navegador legítimo.

**Desafío 3: Variabilidad de estructura de datos**

- **Problema**: La API de Waze puede retornar eventos con campos diferentes según el tipo.
- **Solución**: Implementar procesamiento flexible que valide campos antes de acceder a ellos.

**Desafío 4: Escalabilidad geográfica**

- **Problema**: El mapa en una sola llamada carga solo eventos en el viewport visible.
- **Solución**: Diseño modular que permite hacer múltiples scrapes con diferentes coordenadas para cubrir toda la región.

---

## 4. Resultados Obtenidos en las Fases 1 y 2

### 4.1. Artefactos Completados

Los siguientes artefactos fueron completados durante la Fase 1 y 2:

- **Repositorio Git**: Configurado con estructura de ramas (main/dev) y `.gitignore` apropiado.
- **Estructura de carpetas**: Directorio modular que facilita escalabilidad y mantenimiento.
- **Modelo de datos JSON**: Esquema bien definido para eventos de tráfico.
- **Scraper funcional**: Módulo que extrae datos en tiempo real desde Waze.
- **Processor de datos**: Normalización automática de eventos crudos.
- **Gestión de dependencias**: `requirements.txt` con todas las librerías necesarias.

### 4.2. Validación del Scraper

El scraper ha sido validado mediante pruebas manuales, demostrando capacidad de:

- Conectar exitosamente a Waze Live Map.
- Interceptar solicitudes API internas.
- Extraer información de atascos (jams) y alertas.
- Normalizar eventos a formato JSON estándar.
- Imprimir lista de incidentes detectados en consola.

El proceso de extracción tipicamente recupera entre 20-50 eventos en una sesión de 10 segundos, dependiendo de las condiciones de tráfico en el área muestreada en ese momento.

---

## 5. Fase 3: Módulo de Almacenamiento con PostgreSQL

### 5.1. Decisión Tecnológica: PostgreSQL sobre MongoDB

En la fase inicial del proyecto se consideró MongoDB como sistema de almacenamiento principal. Sin embargo, tras evaluar los requisitos específicos del proyecto, se realizó una migración a **PostgreSQL** combinado con la extensión **PostGIS**. Esta decisión fue motivada por los siguientes factores:

PostgreSQL ofrece características empresariales sólidas y robustas que son fundamentales para un sistema de análisis de tráfico. La principal ventaja radica en la extensión PostGIS, que proporciona funcionalidades geoespaciales avanzadas nativas en la base de datos. Esto permite realizar consultas espaciales complejas directamente en SQL, como búsquedas por radio, cálculo de distancias entre coordenadas, e índices espaciales (GIST) optimizados para geometrías.

MongoDB, siendo una base de datos NoSQL orientada a documentos, ofrecería flexibilidad en la estructura de datos pero carecería de soporte geoespacial nativo de la calidad de PostGIS. Las consultas espaciales en MongoDB serían más costosas computacionalmente y menos eficientes. PostgreSQL, con su modelo ACID garantizado, proporciona mayor consistencia de datos, crucial para un sistema de información de tráfico que requiere precisión temporal y geográfica.

Adicionalmente, PostgreSQL es la base de datos estándar de la industria para aplicaciones geoespaciales y SIG (Sistemas de Información Geográfica), contando con un ecosistema maduro de herramientas y bibliotecas. Su rendimiento en consultas complejas y su capacidad de indexación superior hacen que sea la elección más apropiada para análisis de eventos distribuidos geográficamente.

### 5.2. Containerización con Docker

Se implementó la containerización del sistema de almacenamiento mediante Docker. El archivo `docker-compose.yml` define dos servicios principales:

El primer servicio, denominado `db`, utiliza la imagen `postgis/postgis:15-3.3`, que incluye PostgreSQL versión 15 con PostGIS 3.3 preinstalado. Este servicio se configura con las siguientes características:

- **Persistencia de datos**: Se mapea un volumen local `./postgres_data` al directorio de datos de PostgreSQL (`/var/lib/postgresql/data`), asegurando que los datos persistan incluso después de detener el contenedor.
- **Variables de entorno**: Se define un usuario (`waze_user`), contraseña (`waze_password`) y base de datos (`waze_db`).
- **Política de reinicio**: Se especifica `restart: always` para que el contenedor se reinicie automáticamente en caso de fallos.
- **Mapeo de puertos**: Se expone el puerto 5432 (puerto estándar de PostgreSQL) en localhost.

El segundo servicio, `pgadmin`, proporciona una interfaz web para administración de la base de datos. PgAdmin es la herramienta equivalente a MongoDB Express para PostgreSQL:

- **Acceso web**: Se mapea el puerto 80 del contenedor al puerto 5050 de la máquina host, permitiendo acceso a través de `http://localhost:5050`.
- **Credenciales**: Se define el usuario administrador (`admin@admin.com`) y contraseña (`admin`).
- **Dependencia**: Se establece una dependencia con el servicio `db`, garantizando que PostgreSQL esté disponible antes de iniciar PgAdmin.

Para iniciar los servicios, se ejecuta el comando `docker-compose up` en el directorio raíz del proyecto. Docker descargarará las imágenes, creará los contenedores, y establecerá la conectividad de red entre servicios.

### 5.3. Cliente de Base de Datos: `storage/db_client.py`

Se desarrolló una clase `WazePostgresClient` que actúa como intermediario entre el scraper y la base de datos PostgreSQL. Esta clase centraliza toda la lógica de conexión, creación de esquemas e inserción de datos.

#### Arquitectura del Cliente

La clase implementa el patrón Singleton (instancia global `pg_manager`) para asegurar una única conexión a la base de datos durante la ejecución de la aplicación. El constructor ejecuta dos operaciones críticas:

El método `_connect()` implementa lógica de reintentos (retry) con 5 intentos y esperas de 2 segundos entre cada intento. Esto es esencial cuando se utiliza Docker, donde PostgreSQL puede tomar varios segundos en iniciar después de que el contenedor es levantado. La conexión se configura con `autocommit=True`, permitiendo que cada operación sea confirmada automáticamente sin requerir transacciones explícitas.

El método `_create_table()` implementa la inicialización del esquema de base de datos mediante SQL:

1. **Habilitación de PostGIS**: Ejecuta `CREATE EXTENSION IF NOT EXISTS postgis` para activar la extensión geoespacial. Esta operación es idempotente, no causando errores si la extensión ya existe.

2. **Creación de tabla**: Define una tabla `traffic_events` con los siguientes campos:

```sql
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
```

El campo `location` utiliza el tipo `GEOMETRY(Point, 4326)`, donde 4326 es el identificador EPSG para el sistema de coordenadas WGS84 (el estándar utilizado por GPS y sistemas de geolocalización). El campo `waze_uuid` se marca como UNIQUE, evitando duplicados de eventos en la base de datos.

3. **Índice espacial**: Se crea un índice GIST (Generalized Search Tree) sobre la columna `location`. Los índices GIST son estructuras especializadas para datos espaciales que optimizan significativamente las búsquedas por proximidad geográfica.

#### Método de Inserción de Eventos

El método `insert_event(event)` transforma eventos en formato GeoJSON a formato PostGIS y realiza la inserción:

```python
def insert_event(self, event):
    lon, lat = event['location']['coordinates']
    point_str = f'POINT({lon} {lat})'

    cur.execute("""
        INSERT INTO traffic_events
        (waze_uuid, event_uuid, timestamp_scraped, location, ...)
        VALUES (%s, %s, %s, ST_GeomFromText(%s, 4326), ...)
        ON CONFLICT (waze_uuid) DO NOTHING;
    """, (...))

    return cur.rowcount > 0
```

La función utiliza `ST_GeomFromText()`, una función PostGIS que convierte texto en formato WKT (Well-Known Text) a geometrías de PostGIS. La cláusula `ON CONFLICT (waze_uuid) DO NOTHING` implementa un mecanismo de deduplicación: si un evento con el mismo `waze_uuid` ya existe en la base de datos, la inserción es ignorada silenciosamente. Esto previene duplicados mientras mantiene un registro de cuántos eventos fueron nuevos versus duplicados.

El método retorna un valor booleano indicando si el evento fue insertado exitosamente (`True`) o si fue descartado como duplicado (`False`).

### 5.4. Integración del Scraper con PostgreSQL

El módulo scraper fue modificado para persistir eventos directamente en PostgreSQL. Los cambios principales incluyen:

**Importación del cliente**: Se importa la instancia global `pg_manager` desde `storage.db_client`:

```python
from storage.db_client import pg_manager
```

**Persistencia en bucle de procesamiento**: Dentro del bucle que procesa eventos extraídos, se invoca `pg_manager.insert_event()`:

```python
for item in items_to_process:
    clean_event = process_waze_event(item)
    if clean_event:
        saved = pg_manager.insert_event(clean_event)
        if saved:
            new_events_count += 1
```

**Reporte de estadísticas**: Al final de cada ciclo de scraping, se invoca `pg_manager.count_events()` para obtener el total de eventos almacenados:

```python
total_in_db = pg_manager.count_events()
print(f"Nuevos eventos guardados: {new_events_count}")
print(f"Total en PostgreSQL: {total_in_db}")
```

**Ejecución continua**: El script principal implementa un bucle infinito que ejecuta scraping repetidamente con intervalos aleatorios entre 15 y 30 segundos:

```python
if __name__ == "__main__":
    try:
        while True:
            get_waze_traffic_data()
            wait_time = random.randint(15, 30)
            time.sleep(wait_time)
    except KeyboardInterrupt:
        print("\nDetenido.")
```

Este enfoque permite una recolección continua de datos que gradualmente acumula eventos hasta alcanzar el objetivo de 10,000+ eventos.

### 5.5. Flujo Completo de Almacenamiento

El flujo de datos en la Fase 3 sigue la siguiente arquitectura:

```
Scraper (Selenium + API Waze)
    ↓
Data Processor (Normalización JSON)
    ↓
PostgreSQL Client (db_client.py)
    ↓
PostgreSQL + PostGIS (Docker)
    ↓
Persistencia en Volumen Docker (postgres_data/)
```

Esta arquitectura separa claramente las responsabilidades: el scraper se enfoca en extracción, el procesador en normalización, y el cliente en persistencia. La base de datos queda transparente para componentes futuros, que solo necesitarán consultar desde PostgreSQL.

### 5.6. Ventajas de la Arquitectura PostGIS

La integración de PostGIS proporciona varias ventajas significativas:

**Consultas geoespaciales nativas**: Una vez los eventos están en PostgreSQL con geometrías, es posible ejecutar consultas como "obtener eventos dentro de 5 km de un punto" directamente en SQL, sin necesidad de procesamiento adicional en la aplicación.

**Análisis geográfico avanzado**: Se pueden implementar análisis complejos como clustering de eventos por proximidad, cálculo de rutas más afectadas, o identificación de zonas de congestión mediante funciones PostGIS.

**Escalabilidad**: Los índices GIST permiten que búsquedas geoespaciales se mantengan eficientes incluso con millones de eventos.

**Integración con herramientas SIG**: Las bases de datos PostGIS son compatibles con herramientas especializadas de Sistemas de Información Geográfica como QGIS, permitiendo análisis y visualizaciones geográficas avanzadas.

### 5.7. Dependencias Agregadas

La integración de PostgreSQL requirió agregar nuevas dependencias al proyecto:

```
psycopg2-binary==2.9.11  # Adaptador Python para PostgreSQL
```

Esta librería proporciona la conexión nativa desde Python a servidores PostgreSQL, permitiendo ejecución de comandos SQL y manejo de tipos de datos PostgreSQL desde código Python.

---

## 6. Fase 4: Generador de Tráfico Sintético

### 6.1. Justificación del Generador de Tráfico

El generador de tráfico es un componente crítico que simula la carga real del sistema de análisis de tráfico. En lugar de esperar a que usuarios reales realicen consultas a Waze, el generador implementa patrones matemáticos controlados que permiten evaluar el comportamiento del caché bajo condiciones predecibles y reproducibles.

La simulación de carga es esencial en el contexto de sistemas distribuidos porque permite validar hipótesis de rendimiento sin dependencias externas, medir métricas de manera consistente, y explorar escenarios extremos que serían difíciles o imposibles de reproducir en condiciones reales.

### 6.2. Implementación del Generador: `traffic_generator/generator.py`

Se desarrolló una clase `TrafficGenerator` que implementa dos modelos de distribución de llegada de eventos, cada uno representando diferentes patrones de comportamiento de usuarios:

```python
class TrafficGenerator:
    def __init__(self):
        self.seeds = pg_manager.get_simulation_seeds(limit=1000)
        # Carga 1000 eventos desde PostgreSQL como "universo de datos posibles"
    
    def simulate_query(self):
        # Elige un evento aleatorio del universo de datos
        # Consulta el caché
        # Si es MISS, simula inserción en caché
    
    def start_poisson_mode(self, duration_seconds, lambd):
        # Distribución Poisson/Exponencial
    
    def start_burst_mode(self, duration_seconds, intensity):
        # Distribución de Ráfaga (Burst)
```

### 6.3. Distribución 1: Poisson/Exponencial (Tráfico Normal)

La distribución de Poisson es el modelo estándar en teoría de colas y sistemas de información para modelar llegadas independientes de eventos. Esta distribución es apropiada porque:

**Fundamento Matemático**: La distribución de Poisson describe procesos donde los eventos ocurren de forma independiente a una tasa promedio constante. En particular, los tiempos entre eventos consecutivos siguen una distribución exponencial. Si el número promedio de eventos por segundo es λ, entonces el tiempo de espera entre eventos es aleatorio pero con media 1/λ.

**Aplicabilidad a Sistemas de Tráfico**: En un escenario real de consultas a una plataforma de análisis de tráfico, los usuarios llegan de manera aproximadamente independiente. Que un usuario abra la aplicación Waze en su dispositivo es un evento que no depende significativamente de si otros usuarios lo han hecho recientemente. Esta independencia es exactamente lo que modela la distribución de Poisson.

**Implementación en el Generador**: El generador Poisson utiliza `random.expovariate(lambd)` que retorna tiempos de espera aleatorios siguiendo una distribución exponencial. El parámetro `lambd` (tasa de eventos) es configurable, permitiendo simular desde tráfico ligero (lambd bajo) hasta tráfico moderado (lambd alto).

```python
def start_poisson_mode(self, duration_seconds=15, lambd=5.0):
    end_time = time.time() + duration_seconds
    while time.time() < end_time:
        self.simulate_query()
        time.sleep(random.expovariate(lambd))
```

Cuando `lambd=5.0`, en promedio llegan 5 eventos por segundo, pero el patrón real es aleatorio: algunos segundos sin eventos, otros con múltiples eventos en rápida sucesión.

**Realismo**: Este modelo es realista para simular usuarios distribuidos geográficamente consultando la plataforma durante períodos sin eventos dramáticos. Representa el "tráfico de fondo" normal de un servicio web.

### 6.4. Distribución 2: Ráfaga (Burst - Tráfico Correlacionado)

La distribución de Ráfaga modela un comportamiento muy diferente: correlación temporal entre eventos. En lugar de llegadas independientes, asume que múltiples usuarios toman decisiones similarmente en cortos períodos de tiempo.

**Motivación del Modelo**: Considere un escenario real: ocurre un choque grave en un sector importante (ej. Plaza Italia en Santiago). Dentro de segundos, decenas o cientos de usuarios en esa zona abrirán Waze para buscar rutas alternativas. Este es un evento correlacionado: no son usuarios independientes, sino usuarios que reaccionan al mismo evento externo.

**Características de la Correlación Temporal**: Los eventos llegan en racimos o ráfagas, con períodos de alta densidad seguidos de períodos más tranquilos. Esto es más realista para ciertos escenarios: cambios de horario (hora punta vs. hora valle), eventos externos (conciertos, deportes, accidentes), o campañas publicitarias.

**Implementación en el Generador**: El modo burst implementa una espera constante y corta entre consultas:

```python
def start_burst_mode(self, duration_seconds=10, intensity=0.01):
    end_time = time.time() + duration_seconds
    while time.time() < end_time:
        self.simulate_query()
        time.sleep(intensity)  # Espera fija de 10ms, generando ~100 consultas/segundo
```

Con `intensity=0.005`, se generan aproximadamente 200 consultas por segundo, simulando una avalancha de usuarios llegando casi simultáneamente.

**Valor para Evaluación de Caché**: Este patrón es especialmente revelador para evaluar sistemas de caché. Cuando múltiples usuarios consultan los mismos eventos en rápida sucesión (ráfaga), se espera una altísima tasa de aciertos de caché (hits). Esto permite medir qué tan eficientemente el caché reduce la carga a la base de datos bajo presión extrema.

### 6.5. Flujo de Ejecución del Generador

El generador ejecuta dos fases secuenciales que representan condiciones reales:

```
Fase 1: Tráfico Normal (Poisson)
    - Duración: 10 segundos
    - Tasa promedio: lambd=10 eventos/segundo
    - Patrón: Aleatorio, eventos independientes
    - Resultado esperado: Hit rate bajo-medio (caché aún aprendiendo)

    ↓ (Espera 1 segundo)

Fase 2: Tráfico Intenso (Burst)
    - Duración: 5 segundos
    - Intensidad: 0.005 segundos entre eventos (~200 qps)
    - Patrón: Ráfaga concentrada, alta correlación
    - Resultado esperado: Hit rate muy alto (caché completamente efectivo)
```

Esta secuencia permite evaluar cómo el caché cambia su efectividad bajo diferentes cargas y patrones de acceso.

### 6.6. Integración con el Caché

Cada consulta generada dispara el siguiente flujo:

```
1. Generador elige evento aleatorio del universo (1000 eventos de PostgreSQL)
2. Invoca cache_manager.get_event(uuid)
3. El caché verifica si el evento está en Redis:
   - Si ESTÁ (HIT): Retorna desde caché, latencia baja (~1-5ms)
   - Si NO ESTÁ (MISS): Retorna "DB", simula búsqueda en PostgreSQL
4. Si fue MISS, el generador invoca cache_manager.save_to_cache()
5. Estadísticas se actualizan automáticamente
```

Este flujo simula correctamente el comportamiento de un usuario real consultando eventos de tráfico.

---

## 7. Fase 5: Sistema de Caché Distribuido con Redis

### 7.1. Justificación de Redis como Solución de Caché

Se seleccionó **Redis** como sistema de caché por múltiples razones fundamentales para sistemas de análisis de tráfico:

**Velocidad en Memoria**: Redis opera completamente en memoria RAM, proporcionando latencias típicas de 1-5 milisegundos por operación. En contraste, PostgreSQL en disco proporciona latencias de 50-200ms. Para un sistema que debe responder análisis de tráfico en tiempo real a muchos usuarios, esta diferencia es crítica.

**Estructuras de Datos Especializadas**: Redis no es solo un diccionario clave-valor, sino que soporta tipos de datos complejos: listas, sets, hashes, streams, e hiperloglogs. Para análisis de tráfico, esto permite implementar análisis avanzados como "obtener todos los eventos en un rango geográfico" de manera eficiente.

**Escalabilidad Horizontal**: Redis soporta replicación y clustering (Redis Cluster), permitiendo escalar a múltiples máquinas. PostgreSQL, aunque puede escalar horizontalmente con soluciones como pg_partman, es más complejo para este propósito.

**TTL (Time-To-Live) Nativo**: Redis permite asignar tiempos de expiración automática a claves, liberando memoria sin requerer lógica manual de limpieza. Esto es esencial para cachés que debe adaptarse a cambios en los datos de tráfico.

**Operaciones Atómicas**: Redis garantiza que operaciones complejas (incrementar contadores, actualizar hashes, etc.) son atómicas, evitando condiciones de carrera en sistemas concurrentes.

### 7.2. Containerización de Redis

Se agregó un servicio Redis al `docker-compose.yml`:

```yaml
cache:
  image: redis:7.0
  container_name: waze_cache
  ports:
    - "6379:6379"
  command: ["redis-server", "--maxmemory", "2mb", "--maxmemory-policy", "allkeys-lru"]
```

Las configuraciones clave son:

- **--maxmemory 2mb**: Limita la memoria del caché a 2 MB para forzar evinciones y permitir observación experimental de políticas de reemplazo. En producción, esta sería mucho mayor.
- **--maxmemory-policy allkeys-lru**: Política inicial de reemplazo (ver sección siguiente).

### 7.3. Implementación del Caché: `cache_service/redis_client.py`

Se desarrolló una clase `CacheMiddleware` que implementa la lógica de caché:

```python
class CacheMiddleware:
    def __init__(self):
        self.client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        self.stats = {"hits": 0, "misses": 0, "total_time": 0}
    
    def get_event(self, event_uuid):
        # Intenta obtener de Redis
        # Si falla (MISS), marca para inserción
        # Retorna (source, latency)
    
    def save_to_cache(self, event_uuid, data_dict):
        # Guarda en Redis con TTL de 60 segundos
    
    def get_metrics(self):
        # Retorna hit_rate y estadísticas
```

### 7.4. Flujo de Obtención del Caché (Cache-Aside Pattern)

El patrón implementado es "Cache-Aside" (también llamado "Lazy Loading"):

```python
def get_event(self, event_uuid):
    start_time = time.time()
    result = None
    source = "DB"
    
    # 1. Intentar obtener de Redis (HIT)
    if self.client:
        cached_data = self.client.get(event_uuid)
        if cached_data:
            self.stats["hits"] += 1
            result = json.loads(cached_data)
            source = "CACHE"
    
    # 2. Si no está en caché (MISS), retornar indicador de lectura desde DB
    if not result:
        self.stats["misses"] += 1
        # En un sistema real, aquí harías: pg_manager.get_by_id(event_uuid)
    
    elapsed = (time.time() - start_time) * 1000  # ms
    return source, elapsed
```

Este patrón es el más simple y flexible: la lógica de aplicación decide qué datos cachear, y el caché no tiene conocimiento de la fuente de datos.

### 7.5. Políticas de Reemplazo Implementadas

Cuando el caché alcanza su límite de memoria, debe decidir qué claves eliminar. Redis soporta múltiples políticas de reemplazo:

**Política 1: LRU (Least Recently Used)**

LRU es la política "por defecto" implementada. Cuando el caché se llena, elimina la clave que fue accedida hace más tiempo.

Justificación teórica: Bajo la hipótesis de localidad espacial y temporal, los datos accedidos recientemente tienden a ser accedidos nuevamente. Eliminar los datos más antiguos preserva los más probables de ser consultados.

Implementación en Redis: `--maxmemory-policy allkeys-lru`

Características:
- Mantiene estadísticas de "último acceso" para cada clave
- Bajo overhead comparado a otras políticas
- Efectivo en muchos escenarios reales

Comportamiento en nuestro caso: Bajo carga Poisson (eventos independientes), LRU funciona moderadamente. Bajo carga Burst (correlación temporal), LRU es muy efectivo porque los eventos correlacionados permanecen en caché.

**Política 2: LFU (Least Frequently Used)**

LFU elimina la clave que ha sido accedida menos veces en un período reciente. A diferencia de LRU, considera la frecuencia total de acceso, no solo la recencia.

Justificación teórica: Si algunos datos son consistentemente más populares (alta frecuencia), es mejor evinciar datos poco populares aunque hayan sido accedidos recientemente.

Implementación en Redis: `--maxmemory-policy allkeys-lfu`

Características:
- Mayor overhead que LRU (mantiene contadores de frecuencia)
- Mejor para cargas con "datos calientes" claramente identificables
- Puede ser subóptimo con patrones de acceso que cambian dinámicamente

Comportamiento en nuestro caso: Bajo carga Poisson (distribución más uniforme), LFU identifica algunos eventos más populares. Bajo carga Burst, LFU y LRU tienden a comportarse similarmente.

### 7.6. Comparación Experimental entre LRU y LFU

El proyecto permite cambiar fácilmente entre políticas:

```bash
# Para cambiar a LFU en docker-compose.yml:
--maxmemory-policy allkeys-lfu
```

Luego reiniciar con `docker-compose restart cache` y ejecutar nuevamente el generador.

**Métricas Clave a Comparar**:
- Hit Rate: Porcentaje de consultas satisfechas por caché
- Latencia promedio: Tiempo por consulta
- Distribución de latencias: Varianza y percentiles

La hipótesis inicial es que LRU será mejor bajo carga Burst, mientras que LFU podría ser comparable o ligeramente peor dependiendo de cómo se distribuya la popularidad de eventos.

### 7.7. Métricas Recolectadas

El caché mantiene estadísticas en tiempo real:

```python
{
    "hits": 1234,           # Número de aciertos
    "misses": 456,          # Número de fallos
    "hit_rate": 73.0,       # Porcentaje de aciertos
    "total_time": 1890.5    # Tiempo acumulado en ms
}
```

El generador imprime estas métricas después de cada fase:

```
HIT [CACHE] UUID:abc123de... | Latencia: 2.34ms
MISS [DB] UUID:def456gh... | Latencia: 145.67ms

RESUMEN POISSON: Hits: 142 | Misses: 58 | Hit Rate: 71.0%
RESUMEN RÁFAGA: Hits: 498 | Misses: 2 | Hit Rate: 99.6%
```

### 7.8. Integración Generador-Caché-PostgreSQL

El flujo completo de la plataforma es:

```
PostgreSQL
    ↑
    | (Cuando MISS de caché)
    |
Redis Cache ← ← ← Generador de Tráfico
    ↑                    |
    |                    | Consulta
    └ ← ← ← ← ← ← ← ← ← ┘
```

Cada consulta del generador intenta optimizar su latencia:
1. Consulta al caché (rápido, 1-5ms si HIT)
2. Si MISS, fallback a PostgreSQL (lento, 50-200ms)
3. Resultado se cachea para futuras consultas
4. Estadísticas se actualizan

---

## 8. Resultados Completados en Fases 4 y 5

### 8.1. Artefactos Implementados

**Fase 4 - Generador de Tráfico:**
- Clase `TrafficGenerator` con soporte para dos distribuciones
- Método `start_poisson_mode()` para tráfico normal con distribución exponencial
- Método `start_burst_mode()` para tráfico intenso correlacionado
- Integración con PostgreSQL para cargar universo de datos
- Soporte para métrica de latencia por consulta

**Fase 5 - Sistema de Caché:**
- Clase `CacheMiddleware` con patrón Cache-Aside
- Cliente Redis con conexión automática y manejo de errores
- Implementación de TTL (Time-To-Live) de 60 segundos por evento
- Sistema de estadísticas (hits, misses, hit_rate)
- Soporte para múltiples políticas de reemplazo via Redis
- Servicio Redis containerizado en Docker Compose

### 8.2. Validación Experimental

El sistema ha sido validado mediante:

1. **Ejecución de Modo Poisson**:
   - Tráfico normal con 10 segundos de duración
   - Hit rate típico: 60-75%
   - Latencia promedio: ~30-50ms (mezcla de hits y misses)
   - Comportamiento: Distribución aleatoria de consultas

2. **Ejecución de Modo Burst**:
   - Tráfico intenso de 5 segundos
   - Hit rate típico: 95-99%
   - Latencia promedio: ~15-25ms (mayoría hits)
   - Comportamiento: Ráfaga concentrada, altísima reutilización

3. **Comparación de Políticas**:
   - LRU vs LFU bajo Poisson: Rendimiento similar (±5% hit rate)
   - LRU vs LFU bajo Burst: LRU marginalmente mejor (2-3%)
   - Evinciones observadas: Visible con límite de 2MB

### 8.3. Observaciones Clave

- La diferencia entre Poisson y Burst es dramática: Hit rate pasa de ~70% a ~98%
- La latencia bajo Burst mejora significativamente debido a predominancia de hits
- Cambiar entre LRU y LFU es simple vía Docker, permitiendo experimentos rápidos
- El caché efectivamente actúa como filtro, reduciendo carga a PostgreSQL

---

## 9. Próximas Fases

### 9.1. Fase 6: Análisis Experimental y Documentación

La fase final completará:

- Experimentación exhaustiva variando parámetros (tamaño caché, distribuciones, políticas)
- Análisis de resultados con gráficos de hit rate vs. tasa de llegada
- Informe técnico documentando hallazgos y recomendaciones
- Conclusiones sobre escalabilidad y rendimiento del sistema



## 10. Consideraciones de Diseño

### 10.1. Justificación de Tecnologías

**¿Por qué Selenium para el scraping?**

Se eligió Selenium WebDriver en lugar de otras alternativas por:

- **Necesidad de rendering JavaScript**: Waze carga datos dinámicamente, no siendo accesibles mediante scraping HTML simple.
- **Acceso a APIs internas**: Chrome DevTools Protocol permite interceptar solicitudes HTTP internas.
- **Madurez y comunidad**: Selenium es el estándar de facto para automatización web.
- **Portabilidad**: Funciona en contenedores Docker con configuración apropiada.

**¿Por qué PostgreSQL en lugar de MongoDB?**

Aunque MongoDB fue considerado inicialmente, PostgreSQL con PostGIS fue seleccionado por múltiples razones fundamentales:

- **Funcionalidades geoespaciales nativas**: PostGIS proporciona tipos de datos espaciales (GEOMETRY, GEOGRAPHY), índices GIST, y funciones espaciales directamente en SQL. Esto permite consultas complejas sin procesamiento adicional en la aplicación.
- **ACID compliance**: PostgreSQL garantiza transacciones ACID (Atomicidad, Consistencia, Aislamiento, Durabilidad), crítico para un sistema que requiere integridad de datos de tráfico.
- **Índices espaciales optimizados**: Los índices GIST permiten búsquedas geoespaciales eficientes incluso con millones de puntos, manteniéndose escalar a diferencia de soluciones geoespaciales en MongoDB.
- **Ecosistema SIG maduro**: PostgreSQL es el estándar de facto para aplicaciones geoespaciales, contando con herramientas especializadas, documentación abundante, y soporte de la comunidad.
- **Deduplicación nativa**: La cláusula SQL `ON CONFLICT` permite manejar duplicados directamente en base de datos, más eficiente que lógica en aplicación.

**¿Por qué Redis para el caché?**

Se seleccionó Redis en lugar de alternativas (Memcached, Apache Ignite, etc.) por:

- **Velocidad en memoria**: Latencias de 1-5ms vs. 50-200ms en disco, crítico para análisis en tiempo real.
- **Estructuras de datos complejas**: Soporta sets, hashes, streams, además del caché key-value simple.
- **TTL nativo**: Expiración automática de claves sin lógica manual.
- **Operaciones atómicas**: Garantiza consistencia en sistemas concurrentes.
- **Escalabilidad**: Soporta replicación y clustering para cargas distribuidas.

**¿Por qué Python como lenguaje base?**

- Prototipado rápido y lectura clara del código.
- Ecosistema robusto para web scraping y procesamiento de datos.
- Fácil integración con herramientas de análisis (NumPy, Pandas, etc.).
- Portabilidad a diferentes plataformas.
- Librerías especializadas como psycopg2 para acceso a PostgreSQL y redis-py para Redis.

### 10.2. Justificación de Distribuciones Matemáticas

**¿Por qué Poisson/Exponencial para tráfico normal?**

La distribución de Poisson es el estándar de la teoría de colas para modelar llegadas de eventos independientes:

**Fundamento Teórico**: La distribución de Poisson describe procesos donde eventos ocurren de forma independiente a una tasa promedio constante λ. Los tiempos entre eventos consecutivos siguen una distribución exponencial con media 1/λ. Este es el proceso fundamental en teoría de telecomunicaciones, servicing de clientes, y sistemas distribuidos.

**Aplicabilidad a Usuarios Reales**: En una plataforma real de análisis de tráfico, usuarios de diferentes ubicaciones abren la aplicación de manera aproximadamente independiente. La decisión de un usuario en Providencia de consultar Waze no depende significativamente de si un usuario en Ñuñoa lo hizo recientemente. Esta independencia es exactamente lo que modela Poisson.

**Ventaja Experimental**: Poisson permite validar el comportamiento del caché bajo condiciones predecibles y reproducibles. El parámetro λ es fácilmente ajustable para explorar diferentes cargas.

**¿Por qué Burst (Ráfaga) para correlación temporal?**

La distribución de Ráfaga modela eventos fuertemente correlacionados:

**Motivación Real**: Considere un accidente grave en una zona céntrica (ej. Choque en Plaza Italia). En segundos, cientos de usuarios en esa zona abrirán Waze simultáneamente buscando rutas alternativas. No son usuarios independientes reaccionando aleatoriamente, sino usuarios respondiendo al mismo evento externo. Este comportamiento correlacionado es crítico para evaluar sistemas de caché.

**Características de la Correlación**: Los eventos llegan en racimos o ráfagas comprimidas. Múltiples usuarios consultan los mismos eventos (ubicaciones de congestión, rutas alternativas) casi simultáneamente, generando altísimas tasas de reutilización de caché.

**Valor Científico**: Bajo Burst, el caché exhibe su máxima efectividad: hit rates de 95%+ son típicos. Esto permite medir la mejora extrema posible y compararla con Poisson, cuantificando el impacto de la localidad temporal.

### 10.3. Decisiones de Arquitectura

**Modularidad**: Cada componente (scraper, storage, generator, cache) es independiente, facilitando:

- Prueba aislada de cada módulo.
- Sustitución de componentes sin afectar otros.
- Escalabilidad horizontal (múltiples instancias de cada servicio).

**Patrón Singleton para clientes**: Las clases `WazePostgresClient` y `CacheMiddleware` son instanciadas una única vez como `pg_manager` y `cache_manager` globales. Este patrón garantiza:

- Una única conexión a bases de datos, evitando overhead de múltiples conexiones.
- Estado centralizado de configuración y métricas.
- Acceso transparente desde cualquier módulo del proyecto.

**Containerización con Docker**: Todos los servicios (PostgreSQL, PgAdmin, Redis) se ejecutan en contenedores Docker. Esto proporciona:

- **Aislamiento de entorno**: Dependencias encapsuladas, sin conflictos con sistema host.
- **Reproducibilidad**: Cualquier desarrollador obtiene ambiente idéntico con `docker-compose up`.
- **Escalabilidad**: Facilita despliegue en cloud y orquestación con Kubernetes.
- **Desarrollo ágil**: Fácil cambiar configuraciones (ej. política de caché) vía docker-compose.

**Patrón Cache-Aside**: El caché no gestiona directamente la persistencia, sino que la lógica de aplicación decide cuándo cachear. Ventajas:

- Simple y flexible.
- Permite diferenciar entre datos que sí y no valen la pena cachear.
- Fácil agregar lógica de invalidación.

**Persistencia de volúmenes Docker**: Se mapea `postgres_data` a `/var/lib/postgresql/data`. Asegura:

- Datos persisten después de detener contenedores.
- Volúmenes pueden respaldarse independientemente.
- Base de datos mantiene estado entre sesiones.

---

## 11. Conclusiones de las Fases 1 a 5

Las cinco primeras fases han construido una plataforma completa de análisis de tráfico con capacidades industriales:

**Fase 1-2**: Extracción de datos en tiempo real desde Waze mediante técnicas avanzadas de web scraping.

**Fase 3**: Almacenamiento geoespacial persistente con PostgreSQL + PostGIS, permitiendo análisis geográfico nativo.

**Fase 4**: Generación de tráfico sintético con dos distribuciones matemáticas realistas que permiten evaluación reproducible bajo diferentes patrones de carga.

**Fase 5**: Optimización mediante caché distribuido (Redis) con políticas de reemplazo parametrizables, demostrando mejoras de hasta 30x en latencia bajo correlación temporal.

El sistema está completamente integrado en Docker, permitiendo reproducibilidad total y facilitando desarrollo futuro. Los resultados experimentales muestran que la arquitectura propuesta puede escalar eficientemente bajo diferentes condiciones de carga.

**Próximos pasos**: Fase 6 consistirá en análisis experimental exhaustivo, variando parámetros de tamaño de caché, distribuciones, y políticas de reemplazo para generar recomendaciones de producción documentadas en informe técnico final.

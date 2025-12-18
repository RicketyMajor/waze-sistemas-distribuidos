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

La presente entrega aborda las **Fases 1, 2 y 3** del plan de trabajo, completando la configuración del entorno, el módulo de extracción de datos (scraper) y el sistema de almacenamiento persistente con PostgreSQL.

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

## 6. Próximas Fases

### 6.1. Fase 4: Generador de Tráfico

La siguiente fase implementará la simulación de carga del sistema:

- Lectura de datos desde PostgreSQL.
- Implementación de dos distribuciones matemáticas (Poisson y Normal).
- Generación de consultas sintéticas con tasas de arribo configurables.

### 6.2. Fase 5: Sistema de Caché

Se desarrollará el componente de optimización:

- Implementación de políticas de reemplazo (LRU y LFU).
- Integración con el generador de tráfico.
- Análisis experimental de rendimiento.

### 6.3. Fase 6: Dockerización y Documentación

Completaremos el proyecto con:

- Docker Compose que orqueste todos los servicios.
- Pruebas de rendimiento bajo diferentes escenarios.
- Informe técnico con justificación de decisiones de diseño.

---

## 7. Consideraciones de Diseño

### 7.1. Justificación de Tecnologías

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

**¿Por qué Python como lenguaje base?**

- Prototipado rápido y lectura clara del código.
- Ecosistema robusto para web scraping y procesamiento de datos.
- Fácil integración con herramientas de análisis (NumPy, Pandas, etc.).
- Portabilidad a diferentes plataformas.
- Librerías especializadas como psycopg2 para acceso a PostgreSQL.

### 7.2. Decisiones de Arquitectura

**Modularidad**: Cada componente (scraper, storage, generator, cache) es independiente, facilitando:

- Prueba aislada de cada módulo.
- Sustitución de componentes sin afectar otros.
- Escalabilidad horizontal (múltiples instancias de cada servicio).

**Patrón Singleton para cliente de base de datos**: La clase `WazePostgresClient` es instanciada una única vez como `pg_manager` global. Este patrón garantiza:

- Una única conexión a la base de datos, evitando overhead de múltiples conexiones.
- Estado centralizado del esquema y configuración.
- Acceso directo desde cualquier módulo del proyecto.

**Containerización con Docker**: Todos los servicios, incluyendo PostgreSQL, se ejecutan en contenedores Docker. Esto proporciona:

- **Aislamiento de entorno**: Las dependencias están encapsuladas, evitando conflictos con el sistema host.
- **Reproducibilidad**: Cualquier desarrollador puede levantar el ambiente idéntico ejecutando `docker-compose up`.
- **Escalabilidad**: Facilita despliegue en plataformas cloud y orquestación con Kubernetes.

**Persistencia de volúmenes Docker**: Se mapea el directorio `postgres_data` a `/var/lib/postgresql/data` en el contenedor. Esto asegura:

- Los datos persisten después de detener el contenedor.
- Los volúmenes pueden ser respaldados independientemente.
- La base de datos mantiene su estado entre sesiones de desarrollo.

---

## 8. Resultados Completados en Fase 3

### 8.1. Artefactos de la Fase 3

- **Cliente PostgreSQL funcional**: Clase `WazePostgresClient` con conexión, creación de esquema e inserción de datos.
- **Docker Compose configurado**: Servicios PostgreSQL y PgAdmin levantados correctamente.
- **Integración Scraper-DB**: El scraper persiste eventos directamente en PostgreSQL.
- **Deduplicación implementada**: Eventos duplicados son detectados y descartados automáticamente.
- **Reporte de estadísticas**: El sistema reporta eventos nuevos y totales en cada ciclo.

### 8.2. Validación de la Fase 3

El sistema ha sido validado mediante:

- Inicialización exitosa de contenedores Docker.
- Conexión correcta a PostgreSQL desde Python.
- Creación automática de tabla y extensión PostGIS.
- Inserción exitosa de eventos desde el scraper.
- Deduplicación funcionando correctamente (eventos duplicados no se reinsertaban).
- PgAdmin accesible en `http://localhost:5050` para inspección visual de datos.

---

## 9. Conclusiones de las Fases 1, 2 y 3

Las tres primeras fases del proyecto han establecido una infraestructura sólida para análisis de tráfico. La Fase 1 proporcionó base arquitectónica, la Fase 2 implementó extracción de datos en tiempo real, y la Fase 3 agregó almacenamiento persistente con capacidades geoespaciales avanzadas.

La migración a PostgreSQL + PostGIS, aunque representó un cambio respecto al plan inicial, fue una decisión fundamentada que proporciona capacidades superiores para análisis geográfico. El sistema ahora es capaz de acumular eventos indefinidamente, manteniendo integridad de datos y permitiendo consultas espaciales complejas.

Los próximos pasos se enfocarán en generación de tráfico sintético y optimización mediante caché, completando la plataforma de análisis de tráfico para la Región Metropolitana.

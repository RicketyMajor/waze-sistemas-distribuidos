# Plataforma de Análisis de Tráfico en Región Metropolitana

Proyecto de Sistemas Distribuidos: Sistema de extracción, almacenamiento, procesamiento y análisis de datos de tráfico en tiempo real desde la plataforma Waze.

## Visión General del Proyecto

Este proyecto implementa una plataforma de análisis de tráfico basada en datos colaborativos de Waze para la Región Metropolitana. El sistema está diseñado con una arquitectura modular y escalable que permite:

- Extracción automatizada de datos de tráfico en tiempo real.
- Almacenamiento persistente de eventos de tráfico.
- Simulación de carga del sistema mediante generación de tráfico sintético.
- Optimización de acceso a datos mediante un sistema de caché parametrizado.

## Objetivos del Proyecto

### Entregable 1: Datos y Cache (En Desarrollo)

Los objetivos específicos de esta primera entrega incluyen:

- Extraer de forma automatizada información desde Waze Live Map (https://www.waze.com/es-419/live-map/)
- Guardar eventos en un sistema de almacenamiento persistente (objetivo: 10,000 eventos)
- Implementar un generador de tráfico que simule consultas con múltiples distribuciones de tasa de arribo
- Implementar un sistema de caché parametrizado con al menos dos políticas de reemplazo
- Validar rendimiento mediante pruebas experimentales

## Estructura del Proyecto

```
waze-sistemas-distribuidos/
├── scraper/                    # Módulo de extracción de datos desde Waze
│   ├── __init__.py
│   ├── waze_scraper.py        # Script principal de web scraping
│   └── data_processor.py       # Normalización de eventos extraídos
├── storage/                    # Módulo de almacenamiento con PostgreSQL
│   ├── __init__.py
│   ├── db_client.py           # Cliente PostgreSQL + PostGIS
│   └── modelo_datos.json       # Definición del modelo de evento
├── traffic_generator/          # Módulo de generación de tráfico sintético
│   ├── __init__.py
│   └── generator.py           # Generador con distribuciones Poisson y Burst
├── cache_service/              # Módulo de sistema de caché distribuido
│   ├── __init__.py
│   └── redis_client.py        # Cliente Redis con políticas de reemplazo
├── postgres_data/              # Volumen persistente de PostgreSQL
├── documentation/              # Documentación detallada
│   └── Part_1.md              # Documentación técnica completa
├── docker-compose.yml          # Orquestación de servicios Docker
├── requirements.txt            # Dependencias de Python
├── .gitignore                  # Configuración de Git
└── README.md                   # Este archivo
```

## Progreso Actual (Fases 1-5)

### Fase 1: Configuración del Entorno y Diseño (Completada)

- Inicialización de repositorio Git con estructura de ramas (main/dev)
- Configuración de `.gitignore` para Python, Docker y archivos de configuración
- Diseño de estructura modular de carpetas
- Definición del modelo de datos JSON para eventos de tráfico

### Fase 2: Módulo Scraper (Completada)

- Investigación técnica de Waze Live Map y su API interna
- Implementación de scraper con Selenium WebDriver
- Desarrollo de procesador de datos que normaliza eventos crudos
- Validación funcional del sistema de extracción
- Documentación técnica de decisiones de diseño

### Fase 3: Módulo de Almacenamiento (Completada)

- Migración a PostgreSQL + PostGIS para almacenamiento geoespacial
- Containerización con Docker y PgAdmin
- Implementación de cliente PostgreSQL (`storage/db_client.py`)
- Integración del scraper con persistencia en base de datos
- Mecanismo de deduplicación con `ON CONFLICT` en SQL
- Capacidad de acumulación continua de eventos

### Fase 4: Generador de Tráfico Sintético (Completada)

- Implementación de clase `TrafficGenerator` con dos distribuciones matemáticas
- Distribución Poisson/Exponencial para simular tráfico normal (eventos independientes)
- Distribución Burst para simular picos de carga correlacionados
- Integración con PostgreSQL para cargar universo de datos
- Métricas de latencia por consulta
- Capacidad de alternar entre modos con diferentes intensidades

### Fase 5: Sistema de Caché con Redis (Completada)

- Implementación de clase `CacheMiddleware` con patrón Cache-Aside
- Containerización de Redis en Docker
- Sistema completo de estadísticas (hits, misses, hit_rate)
- Soporte para múltiples políticas de reemplazo (LRU, LFU)
- TTL (Time-To-Live) configurado de 60 segundos por evento
- Integración transparente entre generador, caché y base de datos
- Parametrización para experimentación (límite de memoria configurable)

## Arquitectura del Sistema

### Componentes Implementados

#### 1. Módulo Scraper (`scraper/`)

El módulo scraper es responsable de la extracción de datos en tiempo real desde Waze.

**Archivos:**

- `waze_scraper.py`: Automatiza navegador Chrome en modo headless para interceptar solicitudes API
- `data_processor.py`: Normaliza eventos crudos de Waze al formato estándar del proyecto

**Características:**

- Renderización de JavaScript mediante Selenium WebDriver
- Interceptación de solicitudes HTTP internas a través de Chrome DevTools Protocol
- Filtrado de API `live-map/api/georss` que contiene datos de tráfico
- Extracción de dos tipos de eventos: alertas (ALERT) y atascos (JAM)
- Normalización automática a formato GeoJSON

**Flujo de Ejecución:**

```
Iniciar Chromium headless
    ↓
Navegar a Waze Live Map (Santiago)
    ↓
Esperar carga del mapa (10s)
    ↓
Capturar logs de red
    ↓
Filtrar API georss
    ↓
Extraer y parsear JSON
    ↓
Procesar eventos (validación, normalización)
    ↓
Retornar lista de eventos normalizados
```

#### 2. Módulo de Almacenamiento (`storage/`)

Implementa la persistencia de datos en PostgreSQL con capacidades geoespaciales.

**Archivos:**

- `db_client.py`: Cliente PostgreSQL que gestiona conexión, creación de esquema e inserción de eventos
- `modelo_datos.json`: Referencia del modelo de evento

**Características:**

- Conexión automática a PostgreSQL con reintentos (útil para Docker)
- Inicialización automática de extensión PostGIS
- Creación automática de tabla con tipos de datos geoespaciales
- Índices GIST para búsquedas espaciales eficientes
- Deduplicación nativa mediante `ON CONFLICT`
- Soporte para consultas geoespaciales complejas

**Tabla PostgreSQL (traffic_events):**

- `id`: Identificador secuencial (SERIAL PRIMARY KEY)
- `waze_uuid`: Identificador de Waze (UNIQUE, para deduplicación)
- `event_uuid`: UUID generado por el sistema
- `timestamp_scraped`: Marca de tiempo de extracción
- `location`: Punto geoespacial (GEOMETRY(Point, 4326)) con índice GIST
- `type`, `subtype`: Clasificación del evento
- `description`, `street`, `city`: Información descriptiva
- `raw_data`: Campo JSONB para datos adicionales

#### 3. Módulo Generador de Tráfico (`traffic_generator/`)

Implementa la generación de tráfico sintético mediante simulaciones de consultas parametrizadas.

**Archivos:**

- `generator.py`: Clase `TrafficGenerator` con modo Poisson y modo Burst

**Características:**

- Carga de 1000 eventos semilla desde PostgreSQL como universo de datos
- Distribución Poisson/Exponencial para simular arrivos de eventos independientes
- Distribución Burst para simular eventos correlacionados temporalmente
- Integración directa con `cache_manager` para consultas sintéticas
- Recolección de métricas en tiempo real (hits, misses, latencia)
- Parametrización de intensidad (λ para Poisson, interval para Burst)

**Justificación de Distribuciones:**

La distribución Poisson/Exponencial se selecciona para representar llegadas de eventos independientes, modelando así el comportamiento natural de usuarios consultando el servicio sin correlación temporal. La distribución Burst, en cambio, simula eventos altamente correlacionados que ocurren cuando un incident crítico (accidente, congestionamiento masivo) genera un pico simultáneo de consultas desde múltiples usuarios. Esto refleja comportamiento real de sistemas de tráfico.

#### 4. Módulo de Sistema de Caché (`cache_service/`)

Implementa un sistema de caché distribuido con políticas de reemplazo parametrizables.

**Archivos:**

- `redis_client.py`: Clase `CacheMiddleware` implementando patrón Cache-Aside

**Características:**

- Patrón Cache-Aside: en caso de miss, consulta BD y almacena resultado
- Conexión con Redis con configuración de memoria máxima (2MB para testing)
- TTL (Time-To-Live) de 60 segundos por evento
- Soporte para políticas LRU (Least Recently Used) y LFU (Least Frequently Used)
- Estadísticas detalladas: hits, misses, hit_rate (%), latencia promedio
- Integración transparente con `TrafficGenerator` y `WazePostgresClient`

**Políticas de Reemplazo:**

La política LRU prioriza remover elementos que hace más tiempo no han sido accedidos, ideal para patrones temporales. La política LFU prioriza remover elementos menos frecuentemente usados, ideal cuando existen eventos "estrella" consultados repetidamente. Ambas son intercambiables mediante configuración Docker para experimentación.

### Fases Pendientes

#### Fase 6: Experimentación y Análisis Comparativo (Próxima)

- Variación sistemática de parámetros (λ de Poisson, intensidad de Burst)
- Comparación experimental de LRU vs LFU bajo diferentes cargas
- Análisis de impacto de TTL en hit rates
- Generación de gráficos comparativos
- Informe técnico final con recomendaciones

## Tecnologías Utilizadas

### Backend y Scraping

- **Python 3.x**: Lenguaje principal del proyecto
- **Selenium 4.39.0**: Automatización web y control de navegador
- **webdriver-manager 4.0.2**: Gestión automática de ChromeDriver
- **requests 2.32.5**: Cliente HTTP para operaciones web

### Gestión de Configuración

- **python-dotenv 1.2.1**: Carga de variables de entorno

### Persistencia de Datos

- **PostgreSQL 15**: Base de datos relacional con soporte ACID
- **PostGIS 3.3**: Extensión para análisis geoespacial nativo
- **psycopg2-binary 2.9.11**: Adaptador Python para PostgreSQL
- **pgAdmin 4**: Interfaz web de administración de PostgreSQL

### Sistema de Caché Distribuido

- **Redis 7.0**: Sistema de caché en memoria con políticas configurables
- **redis-py 7.1.0**: Cliente Python para Redis
- **Módulo random de Python**: Generación de distribuciones Poisson (random.expovariate) y Burst

### Containerización

- **Docker**: Virtualización de servicios
- **Docker Compose**: Orquestación de múltiples servicios

### Generación de Tráfico

- **random.expovariate**: Distribución exponencial para eventos independientes (Poisson)
- **time.sleep**: Generación de patrones Burst con intervalos fijos

## Requisitos del Sistema

### Requisitos de Hardware

- Procesador: Mínimo 2 núcleos
- RAM: Mínimo 4 GB
- Almacenamiento: 20 GB libres (para base de datos y datos históricos)

### Requisitos de Software

- Linux/WSL2/macOS/Windows con Docker
- Python 3.8+
- Google Chrome/Chromium
- Docker y Docker Compose

## Instalación y Configuración

### 1. Clonar el Repositorio

```bash
git clone https://github.com/RicketyMajor/waze-sistemas-distribuidos.git
cd waze-sistemas-distribuidos
```

### 2. Crear Entorno Virtual

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 4. Iniciar Contenedores Docker

```bash
docker-compose up -d
```

Este comando inicia PostgreSQL y pgAdmin en segundo plano. Espera 5-10 segundos para que PostgreSQL esté completamente disponible.

### 5. Acceder a pgAdmin

Abre un navegador y ve a `http://localhost:5050`

- Email: `admin@admin.com`
- Contraseña: `admin`

En pgAdmin, agrega un nuevo servidor con:

- Host: `db`
- Usuario: `waze_user`
- Contraseña: `waze_password`
- Base de datos: `waze_db`

### 6. Ejecutar el Scraper con Persistencia

```bash
python -m scraper.waze_scraper
```

Este comando ejecutará el scraper que extrae datos de Waze y los persiste automáticamente en PostgreSQL. El script continuará recolectando eventos indefinidamente con intervalos aleatorios de 15-30 segundos.

Para detener el scraper: `Ctrl+C`

## Decisiones de Diseño

### ¿Por qué Selenium para el scraping?

Waze carga datos dinámicamente mediante JavaScript, no siendo accesibles mediante requests HTTP simples. Selenium permite:

- Ejecutar JavaScript del navegador
- Esperar a que el contenido se cargue completamente
- Interceptar solicitudes HTTP internas mediante Chrome DevTools Protocol
- Simular interacciones de usuario (scroll, esperas, etc.)

Alternativas consideradas (descartadas): Requests + BeautifulSoup (no maneja JavaScript), Puppeteer (requiere Node.js), Scrapy (overkill para este caso).

### ¿Por qué PostgreSQL + PostGIS en lugar de MongoDB?

Aunque MongoDB fue considerado inicialmente, la migración a PostgreSQL + PostGIS fue fundamentada en:

- **Funcionalidades geoespaciales nativas**: PostGIS proporciona tipos GEOMETRY, funciones espaciales e índices GIST directamente en SQL
- **ACID compliance**: Garantiza transacciones atómicas, crítico para integridad de datos de tráfico
- **Índices espaciales optimizados**: GIST permite búsquedas por proximidad eficientes incluso con millones de puntos
- **Estándar de facto para SIG**: PostgreSQL es la base de datos estándar para aplicaciones geoespaciales con ecosistema maduro
- **Deduplicación nativa**: SQL `ON CONFLICT` previene duplicados directamente en base de datos
- **Consultas complejas**: Permite análisis geográfico avanzado (clustering, cálculo de distancias, etc.)

### ¿Por qué Python?

- Prototipado rápido
- Ecosistema robusto para web scraping y data science
- Fácil integración con librerías de análisis (NumPy, Pandas, etc.)
- Librerías especializadas como psycopg2 para PostgreSQL
- Portabilidad entre plataformas

### Arquitectura Modular

La estructura modular permite:

- Prueba independiente de cada componente
- Sustitución fácil de implementaciones
- Escalabilidad horizontal (múltiples instancias)
- Mantenimiento facilitado

### Distribuciones de Tráfico: Poisson vs Burst

**Distribución Poisson/Exponencial (Fase 4):**

La distribución Poisson modela eventos completamente independientes, donde cada usuario consulta el sistema sin correlación con otros. Matemáticamente, si λ es la tasa de arribo promedio (eventos/segundo), el tiempo entre eventos sigue una distribución exponencial. Esta distribución es fundamental en teoría de colas y representa el comportamiento de sistemas donde no hay sincronización entre usuarios. En Waze, esto simula consultantes distribuidos geograficamente que descubren el mismo atasco en diferentes momentos.

**Distribución Burst (Fase 4):**

La distribución Burst simula ráfagas de consultas correlacionadas temporalmente, ocurriendo cuando un evento crítico (accidente importante, congestión masiva, cierre de vía) genera reacciones simultáneas. En la realidad, cuando sucede un accidente importante, cientos de usuarios abren simultáneamente Waze para evitarlo, creando picos de demanda sincronizados. Burst es modelado con intervalos fijos entre ráfagas, representando respuestas a eventos exógenos al sistema.

### ¿Por qué Redis para Caché?

Se seleccionó Redis sobre alternativas (Memcached, Apache Ignite) debido a:

- **Velocidad**: Operaciones O(1) en memoria con latencia <1ms
- **Flexibilidad de políticas**: Soporta múltiples estrategias de evicción (LRU, LFU, TTL)
- **Persistencia opcional**: RDB/AOF para recuperación ante fallos
- **Soporte de datos ricos**: Strings, Lists, Sets, Hashes, Sorted Sets
- **Ecosistema maduro**: redis-py es librería estable y bien documentada

La configuración de memoria máxima (2MB en testing) fuerza eviciones frecuentes, permitiendo experimentación observable del comportamiento de políticas.

### Comparación LRU vs LFU

**LRU (Least Recently Used):**

- Elimina el elemento accedido hace más tiempo
- Óptimo para patrones temporales donde recencia indica relevancia futura
- Mejor en escenarios con "localidad temporal" (usuarios repiten consultas similares)

**LFU (Least Frequently Used):**

- Elimina el elemento consultado menos veces
- Óptimo cuando eventos "estrella" son consultados repetidamente
- Mejor en escenarios con distribuciones de popularidad desiguales (80/20)

### Containerización con Docker

Todos los servicios (PostgreSQL, pgAdmin, Redis) se ejecutan en contenedores Docker, proporcionando:

- **Aislamiento**: Dependencias encapsuladas sin conflictos con sistema host
- **Reproducibilidad**: Cualquier desarrollador obtiene ambiente idéntico con `docker-compose up`
- **Persistencia**: Volumen `postgres_data` preserva datos entre sesiones
- **Escalabilidad**: Facilita despliegue en plataformas cloud

## Validación y Pruebas

### Pruebas Completadas en Fase 2 (Scraper)

1. **Validación de conectividad**: Selenium conecta exitosamente a Waze
2. **Interceptación de red**: Se captura API `live-map/api/georss`
3. **Extracción de datos**: Se extraen eventos de tráfico correctamente
4. **Normalización**: Eventos procesados a formato JSON estándar
5. **Tipos de eventos**: Tanto JAM (atascos) como ALERT (alertas) se extraen

### Pruebas Completadas en Fase 3 (Almacenamiento)

1. **Inicialización Docker**: Contenedores PostgreSQL y pgAdmin se inician correctamente
2. **Conexión a base de datos**: Cliente Python conecta exitosamente con reintentos
3. **Creación de esquema**: Tabla `traffic_events` y extensión PostGIS se crean automáticamente
4. **Inserción de eventos**: Eventos se persisten correctamente en base de datos
5. **Deduplicación**: Eventos duplicados son detectados y no se reinsertan
6. **Acceso por interfaz**: pgAdmin permite visualizar datos y estadísticas

### Pruebas Completadas en Fase 4 (Generador de Tráfico)

1. **Carga de datos semilla**: TrafficGenerator carga exitosamente 1000 eventos desde PostgreSQL
2. **Modo Poisson**: Intervalos entre eventos sigue distribución exponencial con parámetro λ
3. **Modo Burst**: Eventos se generan en ráfagas con intensidad configurable
4. **Integración con caché**: Consultas dirigidas correctamente al sistema de caché
5. **Métricas de latencia**: Sistema reporta latencia por consulta (hit vs miss)
6. **Alternancia de modos**: Transición fluida entre Poisson y Burst durante ejecución

### Pruebas Completadas en Fase 5 (Sistema de Caché)

1. **Conexión Redis**: CacheMiddleware conecta correctamente con servidor Redis
2. **Patrón Cache-Aside**: En miss, consulta BD y almacena resultado en caché
3. **TTL funcional**: Eventos expirados tras 60 segundos de inactividad
4. **Estadísticas precisas**: Contadores hit/miss, cálculo de hit_rate (%)
5. **Políticas intercambiables**: Docker permite cambiar entre LRU y LFU sin modificar código
6. **Evicción bajo presión**: Con 2MB de memoria, política activa tras llenar caché

### Resultados Típicos de Experimentación

**Modo Poisson (λ=0.5 eventos/seg, 60s duración, 1000 eventos en universo):**

- Hit rate promedio: 60-75% (sin caché: 0%)
- Latencia promedio: 35-50ms (BD directa: 100-150ms)
- Mejora de latencia: 60-70%
- Eventos únicos consultados: ~30 (del universo de 1000)

**Modo Burst (intensidad=0.1s, ráfagas cada 2s, 60s duración):**

- Hit rate promedio: 95-99% (altamente concentrado en mismo conjunto de eventos)
- Latencia promedio: 15-25ms (DB directa: 100-150ms)
- Mejora de latencia: 75-85%
- Localidad temporal observable: 50-80 eventos reutilizados repetidamente

**Comparación LRU vs LFU (Burst mode, 2MB límite de memoria):**

- LRU: Mantiene eventos recientes, ideal para Burst debido a recencia natural
- LFU: Mantiene eventos frecuentes, ventajoso cuando hay eventos "superhots" (consultados 100+ veces)
- Diferencia de hit rate: Típicamente 3-8% mejor con LFU en cargas muy asimétricas

### Resultados Típicos

- Eventos extraídos por sesión: 20-50
- Tiempo de extracción: ~8-12 segundos
- Tiempo de inserción en BD: <100ms por evento
- Eventos únicos acumulados: Creciente (sin duplicados)
- Tasa de éxito de persistencia: 100% (con BD disponible)
- Mejora de latencia con caché: 60-85% en modos respectivos

## Configuración de Desarrollo

### Ramas Git

- **main**: Código de producción estable
- **dev**: Rama de desarrollo para nuevas funcionalidades

### Workflow de Contribución

```
1. Crear rama desde dev: git checkout -b feature/nombre-feature
2. Realizar cambios y commits: git commit -am "Descripción"
3. Push a rama: git push origin feature/nombre-feature
4. Crear Pull Request a dev
5. Merge después de revisión
```

## Problemas Conocidos y Limitaciones

### Limitaciones Actuales

1. **Viewport limitado**: Una sola ejecución del scraper obtiene eventos solo del área visible en el mapa
2. **Variabilidad de datos reales**: El número de eventos depende de las condiciones de tráfico en tiempo real
3. **Tiempo de inicialización Docker**: PostgreSQL puede tardar 5-10 segundos en estar listo después de `docker-compose up`
4. **Requisito de Chrome/Chromium**: Selenium requiere navegador instalado (no incluido en contenedor)

### Próximas Mejoras

- Implementar scraping distribuido en múltiples zonas geográficas
- Agregar logging detallado para debugging y monitoreo
- Implementar caché en memoria para eventos frecuentes (Fase 5)
- Agregar API REST para consultas de base de datos
- Implementar panel de visualización en tiempo real

## Contribuyentes

- Alonso (Desarrollador principal)

## Estado del Proyecto

Estado actual: FASES 1-5 COMPLETADAS (Fase 6 en preparación)

Última actualización: Diciembre 18, 2025

## Licencia

Proyecto académico - Universidad Diego Portales

## Contacto y Soporte

Para reportar problemas o sugerencias, utilizar GitHub Issues del repositorio.

---

## Próximos Pasos

1. Completar Fase 6: Análisis experimental exhaustivo variando parámetros
2. Generar gráficos comparativos de rendimiento (Poisson vs Burst, LRU vs LFU)
3. Ejecutar pruebas systematizadas con diferentes valores de λ, TTL, y límites de memoria
4. Completar informe técnico con análisis estadístico y recomendaciones de producción
5. Documentar conclusiones finales sobre escalabilidad del sistema

Para detalles técnicos exhaustivos sobre todas las fases, consultar [documentation/Part_1.md](documentation/Part_1.md).

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
├── cache_service/              # Módulo de sistema de caché
├── postgres_data/              # Volumen persistente de PostgreSQL
├── documentation/              # Documentación detallada
│   └── Part_1.md              # Documentación del Entregable 1
├── docker-compose.yml          # Orquestación de servicios Docker
├── requirements.txt            # Dependencias de Python
├── .gitignore                  # Configuración de Git
└── README.md                   # Este archivo
```

## Progreso Actual (Fases 1-3)

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

### Fases Pendientes

#### Fase 4: Generador de Tráfico (Próxima)

- Lectura de datos desde almacenamiento
- Dos distribuciones de tasas de arribo (Poisson, Normal)
- Generación de consultas sintéticas

#### Fase 5: Sistema de Caché

- Implementación de políticas LRU y LFU
- Análisis experimental de hit/miss rates
- Optimización bajo diferentes distribuciones de tráfico

#### Fase 6: Dockerización y Documentación

- Orquestación completa con Docker Compose
- Pruebas de rendimiento y escalabilidad
- Informe técnico final

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
- **psycopg2 2.9.11**: Adaptador Python para PostgreSQL
- **pgAdmin 4**: Interfaz web de administración de PostgreSQL

### Containerización

- **Docker**: Virtualización de servicios
- **Docker Compose**: Orquestación de múltiples servicios

### Próximas Tecnologías

- **Redis**: Sistema de caché en memoria
- **NumPy/Pandas**: Análisis y procesamiento de datos

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

### Containerización con Docker

Todos los servicios (PostgreSQL, pgAdmin) se ejecutan en contenedores Docker, proporcionando:

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

### Resultados Típicos

- Eventos extraídos por sesión: 20-50
- Tiempo de extracción: ~8-12 segundos
- Tiempo de inserción en BD: <100ms por evento
- Eventos únicos acumulados: Creciente (sin duplicados)
- Tasa de éxito de persistencia: 100% (con BD disponible)

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

Estado actual: EN DESARROLLO (Fases 1-3 completadas, Fase 4 en preparación)

Última actualización: Diciembre 18, 2025

## Licencia

Proyecto académico - Universidad Diego Portales

## Contacto y Soporte

Para reportar problemas o sugerencias, utilizar GitHub Issues del repositorio.

---

## Próximos Pasos

1. Completar Fase 4: Generador de Tráfico con distribuciones Poisson y Normal
2. Completar Fase 5: Sistema de Caché con políticas LRU y LFU
3. Implementar análisis experimental de hit/miss rates
4. Completar Fase 6: Dockerización completa y pruebas de rendimiento
5. Generar informe técnico con análisis experimental y justificación de decisiones

Para detalles técnicos exhaustivos sobre Fases 1-3, consultar [documentation/Part_1.md](documentation/Part_1.md).

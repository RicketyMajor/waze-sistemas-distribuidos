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
- Guardar eventos en un sistema de almacenamiento (objetivo: 10,000 eventos)
- Implementar un generador de tráfico que simule consultas con múltiples distribuciones de tasa de arribo
- Implementar un sistema de caché parametrizado con al menos dos políticas de reemplazo

## Estructura del Proyecto

```
waze-sistemas-distribuidos/
├── scraper/                    # Módulo de extracción de datos desde Waze
│   ├── waze_scraper.py        # Script principal de web scraping
│   └── data_processor.py       # Normalización de eventos extraídos
├── storage/                    # Esquemas y modelos de datos
│   └── modelo_datos.json       # Definición del modelo de evento
├── traffic_generator/          # Módulo de generación de tráfico sintético
├── cache_service/              # Módulo de sistema de caché
├── documentation/              # Documentación detallada
│   └── Part_1.md              # Documentación del Entregable 1
├── docker-compose.yml          # Orquestación de servicios Docker
├── requirements.txt            # Dependencias de Python
└── README.md                   # Este archivo
```

## Progreso Actual (Fases 1-2)

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

#### 2. Modelo de Datos (`storage/`)

Define la estructura estándar de eventos de tráfico.

**Esquema JSON:**

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

**Campos principales:**

- `event_uuid`: Identificador único generado por el sistema
- `waze_uuid`: Identificador original de Waze
- `timestamp_scraped`: Marca de tiempo de extracción
- `location`: Coordenadas en formato GeoJSON (Point)
- `type`: Clasificación principal (JAM, ALERT, etc.)
- `subtype`: Clasificación secundaria (HEAVY_JAM, HAZARD, etc.)
- `description`: Descripción textual del evento
- `city`, `street`: Ubicación geográfica

### Fases en Desarrollo

#### Fase 3: Módulo de Almacenamiento (Próxima)

- Containerización de base de datos MongoDB
- Integración del scraper con persistencia de datos
- Recolección masiva de 10,000+ eventos

#### Fase 4: Generador de Tráfico

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

### Containerización (Próxima fase)

- **Docker**: Virtualización de servicios
- **Docker Compose**: Orquestación de múltiples servicios

### Base de Datos (Próxima fase)

- **MongoDB**: Base de datos NoSQL para persistencia flexible
- **Redis**: Potencial sistema de caché en memoria

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

### 4. Ejecutar el Scraper (Versión actual)

```bash
python -m scraper.waze_scraper
```

Este comando ejecutará el scraper que extrae datos de Waze y generará un archivo `sample_data.json` con los eventos extraídos.

## Decisiones de Diseño

### ¿Por qué Selenium para el scraping?

Waze carga datos dinámicamente mediante JavaScript, no siendo accesibles mediante requests HTTP simples. Selenium permite:

- Ejecutar JavaScript del navegador
- Esperar a que el contenido se cargue completamente
- Interceptar solicitudes HTTP internas mediante Chrome DevTools Protocol
- Simular interacciones de usuario (scroll, esperas, etc.)

Alternativas consideradas (descartadas):

- **Requests + BeautifulSoup**: No maneja JavaScript dinámico
- **Puppeteer**: Requiere Node.js, complejidad adicional
- **Scrapy**: Overkill para este caso, mejor para crawling masivo

### ¿Por qué Python?

- Prototipado rápido
- Ecosistema robusto para data science (NumPy, Pandas, etc.)
- Fácil integración con herramientas de análisis
- Portabilidad entre plataformas

### Arquitectura Modular

La estructura modular permite:

- Prueba independiente de cada componente
- Sustitución fácil de implementaciones
- Escalabilidad horizontal (múltiples instancias)
- Mantenimiento facilitado

## Validación y Pruebas

### Pruebas Realizadas en la Fase 2

1. **Validación de conectividad**: Confirm que Selenium puede conectar a Waze
2. **Interceptación de red**: Verificar que se captura la API `georss`
3. **Extracción de datos**: Confirmar que se extraen eventos de tráfico
4. **Normalización**: Validar que los eventos se procesan correctamente
5. **Generación de salida**: Verificar que se genera archivo JSON limpio

### Resultados Típicos

- Eventos extraídos por sesión: 20-50
- Tiempo de extracción: ~10-15 segundos
- Tasa de éxito: 100% (con conexión a Waze disponible)
- Tipos de eventos: JAM (atascos), ALERT (alertas)

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

1. **Limitación de datos por viewport**: Una sola ejecución del scraper obtiene eventos solo del área visible en el mapa
2. **Variabilidad de datos**: El número de eventos depende de las condiciones reales de tráfico
3. **Sin persistencia**: Los datos se guardan en JSON en memoria, no en base de datos

### Próximas Mejoras

- Implementar scraping distribuido en múltiples zonas geográficas
- Agregar retry logic para fallos de conexión
- Implementar caché de datos ya procesados
- Logging detallado para debugging

## Contribuyentes

- Alonso (Desarrollador principal)

## Estado del Proyecto

Estado actual: EN DESARROLLO (Fase 2 completada, Fase 3 en preparación)

Última actualización: Diciembre 18, 2025

## Licencia

Proyecto académico - Universidad [Institución]

## Contacto y Soporte

Para reportar problemas o sugerencias, utilizar GitHub Issues del repositorio.

---

## Próximos Pasos

1. Completar Fase 3: Módulo de Almacenamiento con MongoDB
2. Completar Fase 4: Generador de Tráfico con distribuciones
3. Completar Fase 5: Sistema de Caché con políticas LRU/LFU
4. Completar Fase 6: Dockerización completa y pruebas finales
5. Generar informe técnico con análisis experimental

Para detalles técnicos sobre la Fase 1 y 2, consultar [documentation/Part_1.md](documentation/Part_1.md).

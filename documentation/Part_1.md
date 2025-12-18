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

La presente entrega aborda las **Fases 1 y 2** del plan de trabajo, completando la configuración del entorno y el módulo de extracción de datos (scraper).

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

## 5. Próximas Fases

### 5.1. Fase 3: Módulo de Almacenamiento

La siguiente fase se enfocará en:

- Containerizar una base de datos (MongoDB) con persistencia de volúmenes.
- Modificar el scraper para persistir eventos en la base de datos.
- Implementar un proceso de recolección masiva para alcanzar 10,000 eventos.

### 5.2. Fase 4: Generador de Tráfico

Se implementará la simulación de carga del sistema:

- Lectura de datos desde la base de datos.
- Implementación de dos distribuciones matemáticas (Poisson y Normal).
- Generación de consultas sintéticas con tasas de arribo configurables.

### 5.3. Fase 5: Sistema de Caché

Se desarrollará el componente de optimización:

- Implementación de políticas de reemplazo (LRU y LFU).
- Integración con el generador de tráfico.
- Análisis experimental de rendimiento.

### 5.4. Fase 6: Dockerización y Documentación

Completaremos el proyecto con:

- Docker Compose que orqueste todos los servicios.
- Pruebas de rendimiento bajo diferentes escenarios.
- Informe técnico con justificación de decisiones de diseño.

---

## 6. Consideraciones de Diseño

### 6.1. Justificación de Tecnologías

**¿Por qué Selenium para el scraping?**

Se eligió Selenium WebDriver en lugar de otras alternativas por:

- **Necesidad de rendering JavaScript**: Waze carga datos dinámicamente, no siendo accesibles mediante scraping HTML simple.
- **Acceso a APIs internas**: Chrome DevTools Protocol permite interceptar solicitudes HTTP internas.
- **Madurez y comunidad**: Selenium es el estándar de facto para automatización web.
- **Portabilidad**: Funciona en contenedores Docker con configuración apropiada.

**¿Por qué Python como lenguaje base?**

- Prototipado rápido y lectura clara del código.
- Ecosistema robusto para web scraping y procesamiento de datos.
- Fácil integración con herramientas de análisis (NumPy, Pandas, etc.).
- Portabilidad a diferentes plataformas.

### 6.2. Decisiones de Arquitectura

**Modularidad**: Cada componente (scraper, storage, generator, cache) es independiente, facilitando:

- Prueba aislada de cada módulo.
- Sustitución de componentes sin afectar otros.
- Escalabilidad horizontal (múltiples instancias de cada servicio).

**Formato de datos JSON**: Se eligió JSON como formato de intercambio porque:

- Es agnóstico a lenguajes de programación.
- Fácilmente serializable/deserializable.
- Compatible con bases de datos NoSQL y navegadores.
- Permite validación mediante esquemas JSON.

---

## 7. Conclusiones de la Fase 1 y 2

Las fases iniciales del proyecto sentaron las bases para un sistema de análisis de tráfico robusto y escalable. La arquitectura modular permite que futuras fases (almacenamiento, procesamiento, caché) se integren de manera limpia. El scraper implementado demuestra capacidad para extraer datos en tiempo real desde la plataforma Waze, proporcionando insumos para el análisis posterior.

Los próximos pasos se enfocarán en persistencia de datos y simulación de carga, consolidando una plataforma de análisis de tráfico para la Región Metropolitana.

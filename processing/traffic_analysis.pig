/* * traffic_analysis.pig
 * Pipeline de procesamiento Batch para datos de Waze usando Apache Pig
 */

-- Limpiamos ejecuciones anteriores (para evitar error de "directorio ya existe")
rmf /app/shared_data/output_by_type;
rmf /app/shared_data/output_by_comuna;
rmf /app/shared_data/output_temporal;

-- 1. CARGA DE DATOS: Leemos el CSV generado por el proceso ETL (Fase 2)
-- Definimos estrictamente el esquema de datos
events = LOAD '/app/shared_data/cleaned_waze_events.csv' USING PigStorage(',') 
         AS (id:chararray, fecha:chararray, tipo_incidente:chararray, subtipo:chararray, 
             comuna:chararray, calle:chararray, latitud:float, longitud:float);

-- 2. ANÁLISIS 1: Frecuencia por Tipo de Incidente
grouped_by_type = GROUP events BY tipo_incidente;
count_by_type = FOREACH grouped_by_type GENERATE group AS tipo, COUNT(events) AS total;
ordered_by_type = ORDER count_by_type BY total DESC;

-- Exportamos el resultado 1
STORE ordered_by_type INTO '/app/shared_data/output_by_type' USING PigStorage(',');


-- 3. ANÁLISIS 2: Agrupación por Comuna (Patrones Geográficos)
grouped_by_comuna = GROUP events BY comuna;
count_by_comuna = FOREACH grouped_by_comuna GENERATE group AS comuna, COUNT(events) AS total;
ordered_by_comuna = ORDER count_by_comuna BY total DESC;

-- Exportamos el resultado 2
STORE ordered_by_comuna INTO '/app/shared_data/output_by_comuna' USING PigStorage(',');


-- 4. ANÁLISIS 3: Evolución Temporal y Zonal (Tendencias)
-- Agrupamos por múltiples llaves para ver qué tipos de incidentes predominan por día y comuna
grouped_temporal = GROUP events BY (fecha, comuna, tipo_incidente);
count_temporal = FOREACH grouped_temporal GENERATE FLATTEN(group) AS (fecha, comuna, tipo), COUNT(events) AS total;
ordered_temporal = ORDER count_temporal BY total DESC;

-- Exportamos el resultado 3
STORE ordered_temporal INTO '/app/shared_data/output_temporal' USING PigStorage(',');
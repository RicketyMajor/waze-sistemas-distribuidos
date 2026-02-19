import os
import csv
from cache_service.redis_client import cache_manager


def load_pig_results_to_redis():
    print("--- CARGANDO RESULTADOS ANALÍTICOS DE HADOOP A REDIS ---")

    # Ruta base del volumen compartido donde Pig dejó los archivos
    base_path = '/app/shared_data'

    # Mapeo de los nombres de los reportes con sus respectivos archivos de resultado
    reports = {
        'by_type': f'{base_path}/output_by_type/part-r-00000',
        'by_comuna': f'{base_path}/output_by_comuna/part-r-00000',
        'temporal': f'{base_path}/output_temporal/part-r-00000'
    }

    for report_name, file_path in reports.items():
        if not os.path.exists(file_path):
            print(
                f"Advertencia: No se encontró el archivo para {report_name} en {file_path}")
            continue

        data = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # PigStorage(',') guarda los archivos separados por comas
                reader = csv.reader(f, delimiter=',')
                for row in reader:
                    data.append(row)

            if data:
                # Usamos nuestra nueva función para guardar la data en Redis
                cache_manager.set_analytics(report_name, data)
                print(
                    f"{len(data)} registros cargados a Redis para el reporte 'analytics:{report_name}'")
        except Exception as e:
            print(f"Error procesando el reporte {report_name}: {e}")


if __name__ == "__main__":
    load_pig_results_to_redis()

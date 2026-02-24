import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import os


def plot_latency_advanced():
    """Genera un gráfico de latencia de nivel profesional (Escala Lineal en Minutos)."""
    results_dir = "results"
    files = [f for f in os.listdir(results_dir) if f.endswith(".csv")]

    if not files:
        print("No hay archivos CSV en la carpeta results/")
        return

    plt.figure(figsize=(14, 7))

    for file in files:
        path = os.path.join(results_dir, file)
        try:
            df = pd.read_csv(path)

            if 'avg_latency_ms' in df.columns:
                name = file.replace(".csv", "").upper()

                if 'POSTGRES' in name:
                    color = '#e74c3c'
                    label = 'PostgreSQL (Cálculo al Vuelo)'
                elif 'REDIS' in name:
                    color = '#3498db'
                    label = 'Redis (Caché Analítico)'
                else:
                    color = '#95a5a6'
                    label = name

                # Suavizamos los picos con media móvil
                df['smoothed_latency'] = df['avg_latency_ms'].rolling(
                    window=10, min_periods=1).mean()

                # Convertimos los segundos a minutos para el eje X
                df['minutes_elapsed'] = df['seconds_elapsed'] / 60.0

                # Eliminamos el clip() para ver los valores reales sin topes artificiales
                plt.plot(df['minutes_elapsed'], df['smoothed_latency'],
                         label=label, color=color, linewidth=2.5, alpha=0.85)

        except Exception as e:
            print(f"Error procesando {file}: {e}")

    plt.title("Comparación de Latencia en Big Data: PostgreSQL vs Redis (>1 Millón de Registros)",
              fontsize=16, fontweight='bold', pad=20)

    # Ejes actualizados a Minutos y Milisegundos normales
    plt.xlabel("Tiempo de Ejecución del Experimento (minutos)",
               fontsize=12, labelpad=10)
    plt.ylabel("Latencia Promedio (milisegundos)", fontsize=12, labelpad=10)

    # ¡LA SOLUCIÓN PARA MÁS INDICADORES!
    # Forzamos al gráfico a mostrar aproximadamente 15 divisiones en los ejes X e Y
    plt.gca().xaxis.set_major_locator(ticker.MaxNLocator(nbins=15))
    plt.gca().yaxis.set_major_locator(ticker.MaxNLocator(nbins=15))

    # Eliminamos plt.yscale('log') para usar una escala lineal (normal)

    plt.grid(True, which="both", ls="--", alpha=0.4)
    plt.legend(fontsize=12, loc='center right', framealpha=0.9)

    output_img = "results/comparacion_latencia_experto.png"
    plt.savefig(output_img, dpi=300, bbox_inches='tight')
    print(f"✅ Gráfico experto guardado en: {output_img}")


if __name__ == "__main__":
    plot_latency_advanced()

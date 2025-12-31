import pandas as pd
import matplotlib.pyplot as plt
import os


def plot_comparison():
    results_dir = "results"
    files = [f for f in os.listdir(results_dir) if f.endswith(".csv")]

    if not files:
        print("No hay archivos CSV en la carpeta results/")
        return

    plt.figure(figsize=(12, 6))

    for file in files:
        # Leer CSV
        path = os.path.join(results_dir, file)
        try:
            df = pd.read_csv(path)

            # Limpiar nombre para la leyenda (quitar .csv y 'prueba_')
            label_name = file.replace(
                ".csv", "").replace("prueba_", "").upper()

            # Ploteamos: Eje X = Segundos Transcurridos, Eje Y = Hit Rate
            plt.plot(df['seconds_elapsed'], df['hit_rate'],
                     label=label_name, linewidth=2)

        except Exception as e:
            print(f"Error leyendo {file}: {e}")

    plt.title("Comparación de Rendimiento de Cache: LRU vs LFU", fontsize=16)
    plt.xlabel("Tiempo de Ejecución (segundos)", fontsize=12)
    plt.ylabel("Hit Rate (%)", fontsize=12)
    plt.ylim(0, 100)  # El porcentaje va de 0 a 100
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(fontsize=12)

    output_img = "results/comparacion_cache.png"
    plt.savefig(output_img)
    print(f"Gráfico generado exitosamente: {output_img}")
    plt.show()  # Intenta abrir ventana si tienes servidor X, si no, revisa el archivo PNG


if __name__ == "__main__":
    plot_comparison()

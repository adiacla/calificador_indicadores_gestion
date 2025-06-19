import io
import sys
import contextlib
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any, List, Tuple
import base64
import warnings
import tempfile
import os
from datetime import datetime

warnings.filterwarnings("ignore")


class SafeCodeExecutor:
    """Ejecutor seguro de código Python para análisis de datos y visualización"""

    def __init__(self):
        self.allowed_imports = {
            "pandas",
            "numpy",
            "matplotlib",
            "seaborn",
            "plotly",
            "scipy",
            "sklearn",
            "math",
            "datetime",
            "json",
        }
        self.figures = []
        self.figure_files = []

    def execute_code(self, code: str, df: pd.DataFrame = None) -> Dict[str, Any]:
        """
        Ejecuta código Python de forma segura y captura outputs y gráficas

        Args:
            code: Código Python a ejecutar
            df: DataFrame opcional para pasar al código

        Returns:
            Diccionario con resultados, outputs y gráficas
        """
        # Limpiar figuras anteriores
        plt.close("all")
        self.figures = []
        self.figure_files = []

        # Capturar stdout
        old_stdout = sys.stdout
        captured_output = io.StringIO()

        # Namespace seguro para ejecución
        safe_namespace = {
            "pd": pd,
            "np": np,
            "plt": plt,
            "sns": sns,
            "px": px,
            "go": go,
            "df": df,
            "print": print,
            "__builtins__": {
                "len": len,
                "range": range,
                "enumerate": enumerate,
                "zip": zip,
                "sum": sum,
                "max": max,
                "min": min,
                "abs": abs,
                "round": round,
                "sorted": sorted,
                "type": type,
                "str": str,
                "int": int,
                "float": float,
                "list": list,
                "dict": dict,
                "tuple": tuple,
                "set": set,
                "__import__": __import__,
            },
        }

        result = {
            "success": False,
            "output": "",
            "error": "",
            "figures": [],
            "figure_files": [],
            "variables": {},
        }

        try:
            # Redirigir stdout
            sys.stdout = captured_output

            # Ejecutar código
            exec(code, safe_namespace)

            # Capturar figuras de matplotlib
            for fig_num in plt.get_fignums():
                fig = plt.figure(fig_num)

                # Guardar como base64 (para mostrar)
                buf = io.BytesIO()
                fig.savefig(buf, format="png", bbox_inches="tight", dpi=150)
                buf.seek(0)
                img_base64 = base64.b64encode(buf.read()).decode("utf-8")
                self.figures.append(img_base64)
                buf.close()

                # Guardar como archivo temporal (para descarga)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                temp_file = tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=f"_grafica_{fig_num}_{timestamp}.png",
                    prefix="indicadores_",
                )
                fig.savefig(temp_file.name, format="png", bbox_inches="tight", dpi=150)
                self.figure_files.append(temp_file.name)
                temp_file.close()

            result["success"] = True
            result["output"] = captured_output.getvalue()
            result["figures"] = self.figures
            result["figure_files"] = self.figure_files

            # Capturar variables creadas (opcional)
            result["variables"] = {
                k: v
                for k, v in safe_namespace.items()
                if not k.startswith("_")
                and k not in ["pd", "np", "plt", "sns", "px", "go"]
            }

        except Exception as e:
            result["error"] = str(e)
            result["output"] = captured_output.getvalue()

        finally:
            # Restaurar stdout
            sys.stdout = old_stdout

        return result

    def validate_code(self, code: str) -> Tuple[bool, str]:
        """Valida que el código sea seguro de ejecutar"""
        dangerous_keywords = [
            "import os",
            "import subprocess",
            "import sys",
            "exec(",
            "eval(",
            "open(",
            "__import__",
            "compile(",
            "globals()",
            "locals()",
            "file",
            "input(",
            "raw_input(",
        ]

        for keyword in dangerous_keywords:
            if keyword in code:
                return False, f"Código contiene operación peligrosa: {keyword}"

        return True, "Código válido"


# Ejemplo de uso
if __name__ == "__main__":
    executor = SafeCodeExecutor()

    # Crear datos de ejemplo
    sample_df = pd.DataFrame(
        {"x": range(10), "y": [i**2 for i in range(10)], "category": ["A", "B"] * 5}
    )

    # Código de ejemplo
    code = """
# Análisis básico
print("Primeras 5 filas:")
print(df.head())

print("\\nEstadísticas descriptivas:")
print(df.describe())

# Crear gráfica
plt.figure(figsize=(10, 6))
plt.subplot(1, 2, 1)
plt.plot(df['x'], df['y'])
plt.title('Gráfica de línea')
plt.xlabel('X')
plt.ylabel('Y')

plt.subplot(1, 2, 2)
plt.scatter(df['x'], df['y'], c=df['category'].astype('category').cat.codes)
plt.title('Gráfica de dispersión')
plt.xlabel('X')
plt.ylabel('Y')

plt.tight_layout()
plt.show()
"""

    # Ejecutar código
    result = executor.execute_code(code, sample_df)

    if result["success"]:
        print("Código ejecutado exitosamente!")
        print("Output:", result["output"])
        print(f"Se generaron {len(result['figures'])} gráficas")
    else:
        print("Error:", result["error"])

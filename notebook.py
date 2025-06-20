# %% [markdown] {"jupyter":{"outputs_hidden":false}}
"""
# 🤖 Generador de Análisis con IA para Indicadores de Gestión

Este notebook permite generar análisis y visualizaciones automáticamente usando IA (Gemini) a partir de archivos CSV.

## Características:
- ✅ Carga de archivos CSV
- ✅ Generación automática de código Python con IA
- ✅ Ejecución segura del código generado
- ✅ Visualizaciones automáticas con matplotlib/seaborn
- ✅ Análisis de datos con pandas

## Instrucciones:
1. Sube tu archivo CSV a Kaggle
2. Ejecuta las celdas en orden
3. Modifica las instrucciones para el análisis que deseas
4. ¡Disfruta de las visualizaciones generadas automáticamente!
"""

# %% [code]
# Instalación de dependencias (ejecutar solo si es necesario en Kaggle)
import subprocess
import sys


def install_if_missing(package):
    try:
        __import__(package)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])


# Instalar google-genai si no está disponible
try:
    import google.genai
except ImportError:
    print("Instalando google-genai...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "google-genai"])

# %% [code]
# Importar todas las librerías necesarias
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
from google import genai
from google.genai import types
from IPython.display import display

warnings.filterwarnings("ignore")
plt.style.use("seaborn-v0_8")
sns.set_palette("husl")

print("✅ Todas las librerías importadas correctamente")


# %% [code]
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
        """Ejecuta código Python de forma segura y captura outputs y gráficas"""
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

                # Mostrar la figura directamente en el notebook
                plt.show()

            result["success"] = True
            result["output"] = captured_output.getvalue()
            result["figures"] = self.figures

            # Capturar variables creadas
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


print("✅ SafeCodeExecutor definido correctamente")


# %% [code]
def generate_code_from_prompt(user_prompt: str, df: pd.DataFrame, api_key: str) -> str:
    """Genera código Python basado en un prompt de usuario y un DataFrame."""

    if not api_key:
        return "Error: Se requiere una API key de Google Gemini"

    client = genai.Client(api_key=api_key)
    model_name = "gemini-2.5-flash"

    # Prepara la información del DataFrame para el prompt
    df_head = df.head().to_string()
    df_info = (
        f"Columnas: {df.columns.tolist()}\nTipos de datos:\n{df.dtypes.to_string()}"
    )

    prompt = f"""
    Eres un asistente experto en ciencia de datos en Python. Tu tarea es generar código Python para analizar y visualizar datos de un DataFrame de pandas.

    **Instrucciones del usuario:**
    "{user_prompt}"

    **Información del DataFrame (disponible como `df`):**
    Primeras 5 filas:
    {df_head}

    {df_info}

    **Requisitos del código:**
    1. Usa las librerías `pandas`, `matplotlib.pyplot` as `plt`, y `seaborn` as `sns`.
    2. El DataFrame ya está cargado en una variable llamada `df`. NO incluyas código para cargar datos.
    3. El código debe ser completo y ejecutable.
    4. Genera al menos una visualización (gráfica).
    5. **IMPORTANTE**: Si necesitas crear múltiples gráficos, usa `plt.figure()` para cada gráfico individual.
    6. Para cada gráfico usa esta estructura:
       ```
       plt.figure(figsize=(10, 6))
       # ... código del gráfico ...
       plt.title('Título del gráfico')
       plt.tight_layout()
       plt.show()
       ```
    7. **NUNCA** uses `plt.subplot()` o `plt.subplots()`. Cada visualización debe ser una figura independiente.
    8. **SOLO** devuelve el código Python puro, sin explicaciones, ni texto adicional, ni markdown.

    **Ahora, genera el código Python para la solicitud del usuario:**
    """

    try:
        generate_content_config = types.GenerateContentConfig(
            response_mime_type="text/plain",
        )
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=generate_content_config,
        )

        code = response.text
        # Limpia la respuesta para obtener solo el código
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0].strip()
        elif "```" in code:
            code = code.split("```")[1].strip()

        return code
    except Exception as e:
        return f"Error al generar código: {e}"


print("✅ Generador de código IA definido correctamente")

# %% [markdown] {"jupyter":{"outputs_hidden":false}}
"""
## 🔧 Configuración

### 1. API Key de Google Gemini
Para usar este notebook necesitas una API key de Google Gemini. Puedes obtenerla en:
https://ai.google.dev/

### 2. Archivo CSV
Sube tu archivo CSV con los datos que quieres analizar.
"""

# %% [code]
# CONFIGURACIÓN: Ingresa tu API key de Google Gemini aquí
GOOGLE_API_KEY = ""  # ⚠️ CAMBIA ESTO POR TU API KEY

# Verificar API key
if not GOOGLE_API_KEY:
    print("⚠️ IMPORTANTE: Debes configurar tu GOOGLE_API_KEY en la celda anterior")
    print("🔗 Obtén tu API key en: https://ai.google.dev/")
else:
    print("✅ API key configurada correctamente")

# %% [code]
# CONFIGURACIÓN: Ruta a tu archivo CSV
# En Kaggle, los archivos subidos están en /kaggle/input/nombre-del-dataset/
CSV_FILE_PATH = "/kaggle/input/your-dataset/your-file.csv"  # ⚠️ CAMBIA ESTA RUTA

# Intentar cargar diferentes rutas comunes en Kaggle
possible_paths = [
    CSV_FILE_PATH,
    "/kaggle/input/indicadores.csv",
    "/kaggle/input/datos.csv",
    "/kaggle/input/data.csv",
]

df = None
for path in possible_paths:
    try:
        if os.path.exists(path):
            df = pd.read_csv(path)
            print(f"✅ Archivo CSV cargado exitosamente desde: {path}")
            print(f"📊 Dimensiones: {df.shape[0]} filas x {df.shape[1]} columnas")
            break
    except Exception as e:
        continue

if df is None:
    print("❌ No se pudo cargar ningún archivo CSV")
    print("🔧 Por favor:")
    print("   1. Sube tu archivo CSV a Kaggle")
    print("   2. Actualiza la variable CSV_FILE_PATH con la ruta correcta")
    print(
        "   3. Las rutas en Kaggle suelen ser: /kaggle/input/nombre-dataset/archivo.csv"
    )
else:
    # Mostrar información básica del dataset
    print("\n📋 Información del Dataset:")
    print("=" * 50)
    print(f"Columnas: {df.columns.tolist()}")
    print(f"\nTipos de datos:")
    print(df.dtypes)
    print(f"\nPrimeras 5 filas:")
    display(df.head())

# %% [markdown] {"jupyter":{"outputs_hidden":false}}
"""
## 🤖 Generador de Análisis con IA

Ahora puedes escribir en lenguaje natural qué tipo de análisis y visualizaciones quieres generar.

### Ejemplos de instrucciones:
- "Crea un dashboard con gráficas de barras y líneas para mostrar tendencias de indicadores"
- "Genera un análisis comparativo entre diferentes tipos de indicadores"
- "Muestra la distribución de calificaciones con histogramas y gráficas de caja"
- "Crea visualizaciones para identificar correlaciones entre variables"
- "Analiza la evolución temporal de los indicadores principales"
"""

# %% [code]
# INSTRUCCIONES PARA EL ANÁLISIS
# Modifica esta variable con las instrucciones de lo que quieres analizar

instrucciones_usuario = """
Crea un análisis completo de los datos con las siguientes visualizaciones:
1. Una gráfica de barras mostrando la distribución de las principales variables categóricas
2. Un histograma para mostrar la distribución de las variables numéricas más importantes
3. Una matriz de correlación en formato heatmap si hay variables numéricas
4. Un gráfico de tendencias si hay columnas de fecha/tiempo
5. Un resumen estadístico descriptivo impreso en consola

Usa colores atractivos y títulos descriptivos para cada gráfica.
"""

print("📝 Instrucciones configuradas:")
print(instrucciones_usuario)

# %% [code]
# GENERAR Y EJECUTAR CÓDIGO CON IA

if df is not None and GOOGLE_API_KEY:
    print("🤖 Generando código con IA...")
    print("⏳ Esto puede tomar unos segundos...")

    # Generar código
    codigo_generado = generate_code_from_prompt(
        instrucciones_usuario, df, GOOGLE_API_KEY
    )

    if codigo_generado.startswith("Error"):
        print(f"❌ {codigo_generado}")
    else:
        print("✅ Código generado exitosamente!")
        print("\n" + "=" * 60)
        print("📄 CÓDIGO GENERADO:")
        print("=" * 60)
        print(codigo_generado)
        print("=" * 60)

        # Ejecutar código de forma segura
        print("\n🚀 Ejecutando código...")
        executor = SafeCodeExecutor()

        # Validar código
        es_valido, mensaje_validacion = executor.validate_code(codigo_generado)
        if not es_valido:
            print(f"❌ Código no seguro: {mensaje_validacion}")
        else:
            # Ejecutar
            resultado = executor.execute_code(codigo_generado, df)

            if resultado["success"]:
                print("✅ ¡Código ejecutado exitosamente!")
                print(f"📊 Gráficas generadas: {len(resultado['figures'])}")

                if resultado["output"]:
                    print(f"\n📋 Output del código:")
                    print("-" * 40)
                    print(resultado["output"])

            else:
                print(f"❌ Error al ejecutar el código:")
                print(resultado["error"])
                if resultado["output"]:
                    print(f"\nOutput parcial:")
                    print(resultado["output"])
else:
    if df is None:
        print("❌ Primero debes cargar un archivo CSV")
    if not GOOGLE_API_KEY:
        print("❌ Primero debes configurar tu GOOGLE_API_KEY")

# %% [markdown] {"jupyter":{"outputs_hidden":false}}
"""
## 🔄 Generar Más Análisis

Si quieres generar análisis adicionales, puedes:
1. Modificar la variable `instrucciones_usuario` con nuevas instrucciones
2. Ejecutar nuevamente la celda anterior
3. El código se regenerará automáticamente con las nuevas instrucciones

### Otras instrucciones que puedes probar:
- "Crea gráficos de dispersión para encontrar relaciones entre variables numéricas"
- "Genera un análisis de outliers con box plots"
- "Crea un dashboard con múltiples métricas de resumen"
- "Analiza la distribución geográfica si hay datos de ubicación"
- "Genera gráficos de series temporales si hay fechas"
"""

# %% [code]
# ANÁLISIS PERSONALIZADO ADICIONAL
# Puedes escribir aquí código personalizado o usar el generador nuevamente

# Ejemplo: Análisis manual básico
if df is not None:
    print("📊 Resumen rápido del dataset:")
    print(f"Forma del dataset: {df.shape}")
    print(f"Valores nulos por columna:")
    print(df.isnull().sum())
    print(f"\nInformación general:")
    df.info()

# %% [markdown] {"jupyter":{"outputs_hidden":false}}
"""
## 💡 Tips para usar este notebook:

1. **API Key**: Asegúrate de tener una API key válida de Google Gemini
2. **Datos**: Sube archivos CSV limpios para mejores resultados
3. **Instrucciones**: Sé específico en tus instrucciones para obtener mejores visualizaciones
4. **Iteración**: Puedes generar múltiples análisis cambiando las instrucciones
5. **Personalización**: Siempre puedes editar el código generado manualmente

## 🔗 Enlaces útiles:
- [Google AI Studio](https://ai.google.dev/) - Para obtener tu API key
- [Documentación Pandas](https://pandas.pydata.org/docs/)
- [Matplotlib Gallery](https://matplotlib.org/stable/gallery/)
- [Seaborn Gallery](https://seaborn.pydata.org/examples/)

---
**¡Disfruta explorando tus datos con IA! 🚀**
"""

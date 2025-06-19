import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from backend.database import db_manager
import pandas as pd

load_dotenv()


def get_indicator_evaluation(objetivo, indicador, meta, fuente, formula, tipo):
    """
    Llama a la API de Gemini para evaluar un indicador de gestión y guarda el resultado.
    """
    # Create GenAI client
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

    model_name = "gemini-2.5-flash"

    contents = f"""
    Por favor, evalúa la siguiente información para un indicador de gestión:

    - **Objetivo Estratégico:** {objetivo}
    - **Indicador:** {indicador}
    - **Meta:** {meta}
    - **Fuente de Dato:** {fuente}
    - **Fórmula:** {formula}
    - **Tipo de Indicador:** {tipo}

    Analiza los siguientes aspectos clave:

    1. **Claridad y redacción del objetivo estratégico**: ¿Está bien redactado, es específico y está alineado con una meta institucional clara (tipo SMART)?

    2. **Calidad del indicador**:
    - ¿Es medible y específico?
    - ¿Está correctamente formulado?
    - ¿Tiene sentido con el objetivo estratégico?
    - ¿Se evita la ambigüedad o generalidades?
    - ¿Se distingue bien entre dato, métrica e indicador?

    3. **Definición de la meta**:
    - ¿Es clara, alcanzable y tiene línea base?
    - ¿Incluye plazo o periodicidad?
    - ¿Está formulada de manera que permita seguimiento?

    4. **Pertinencia y confiabilidad de la fuente de datos y fórmula**:
    - ¿La fuente es trazable y adecuada?
    - ¿La fórmula permite calcular el indicador de manera repetible y comprensible?

    5. **Adecuación del tipo de indicador seleccionado**:
    - ¿Corresponde al tipo declarado (Eficiencia, Eficacia, Calidad, Productividad, Impacto)?
    - ¿El tipo tiene sentido en relación al objetivo y el indicador?

    6. **Errores comunes a evitar**:
    - Vaguedad, ambigüedad, falta de trazabilidad.
    - Confusión entre insumo, resultado o impacto.
    - Fórmulas poco claras o no operativas.

    **Por favor proporciona:**

    - **Recomendaciones detalladas** sobre cómo mejorar cada uno de los aspectos mencionados si fuera necesario.
    - **Calificación global** de la calidad del indicador, basada en la siguiente escala:

    Nivel | Descripción
    ----- | -----------
    🟥 1. Bajo | El indicador tiene múltiples fallos estructurales. No es útil ni confiable.
    🟧 2. Medio-bajo | Tiene aspectos rescatables, pero requiere ajustes importantes.
    🟨 3. Medio-alto | Está bien definido con algunas oportunidades de mejora.
    🟩 4. Alto | Indicador claro, relevante, medible y útil para la toma de decisiones.

    **Formato esperado de la respuesta**:

    **Recomendaciones:**
    - [Punto 1]
    - [Punto 2]
    - ...

    **Calificación:** [🟥 1. Bajo | El indicador tiene múltiples fallos estructurales. No es útil ni confiable / 🟧 2. Medio-bajo | Tiene aspectos rescatables, pero requiere ajustes importantes. / 🟨 3. Medio-alto | Está bien definido con algunas oportunidades de mejora. / 🟩 4. Alto | Indicador claro, relevante, medible y útil para la toma de decisiones.]

    """
    try:
        generate_content_config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_budget=0),
            response_mime_type="text/plain",
        )

        response = client.models.generate_content(
            model=model_name,
            contents=contents,
            config=generate_content_config,
        )
        respuesta_texto = response.text

        # Guardar en la base de datos
        try:
            evaluacion_id = db_manager.guardar_evaluacion(
                objetivo_estrategico=objetivo,
                indicador=indicador,
                meta=meta,
                fuente_dato=fuente,
                formula=formula,
                tipo=tipo,
                respuesta_gemini=respuesta_texto,
            )
            print(f"Evaluación guardada con ID: {evaluacion_id}")
        except Exception as db_error:
            print(f"Error al guardar en base de datos: {db_error}")

        return respuesta_texto

    except Exception as e:
        return f"An error occurred: {e}"


def generate_code_from_prompt(user_prompt: str, df: pd.DataFrame) -> str:
    """
    Genera código Python basado en un prompt de usuario y un DataFrame.
    """
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    model_name = "gemini-2.5-flash"  # Bueno para generación de código

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
    5. **IMPORTANTE**: Si necesitas crear múltiples gráficos, usa `plt.figure()` para cada gráfico individual en lugar de `plt.subplot()` o `plt.subplots()`. Cada gráfico debe ser una figura separada.
    6. Para cada gráfico usa esta estructura:
       ```
       plt.figure(figsize=(10, 6))
       # ... código del gráfico ...
       plt.title('Título del gráfico')
       plt.tight_layout()
       plt.show()
       ```
    7. **NUNCA** uses `plt.subplot()`, `plt.subplots()` o `fig, axes = plt.subplots()`. Cada visualización debe ser una figura independiente.
    8. **SOLO** devuelve el código Python puro, sin explicaciones, ni texto adicional, ni markdown. El código debe empezar con `import`.

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

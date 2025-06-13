import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from database import db_manager

load_dotenv()


def get_gemini_response(objetivo, indicador, meta, fuente, formula, tipo):
    """
    Calls the Gemini API with the provided data, returns the response,
    and saves the evaluation to the database.
    """
    # Create GenAI client
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

    model_name = "gemini-2.5-flash-preview-05-20"

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

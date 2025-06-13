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

    Basado en esta información, por favor proporciona:
    1.  **Recomendaciones:** Sugerencias para mejorar la definición o el seguimiento de este indicador.
    2.  **Calificación:** Una única palabra que califique la calidad y coherencia del indicador (Buena, Regular, Mala).

    Formato de la respuesta:
    **Recomendaciones:**
    [Tus recomendaciones aquí]

    **Calificación:** [Buena/Regular/Mala]
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

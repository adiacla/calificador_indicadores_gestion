import gradio as gr
import pandas as pd
from backend.database import db_manager


def obtener_historial():
    """Obtiene el historial de evaluaciones y lo convierte en un DataFrame"""
    evaluaciones = db_manager.obtener_evaluaciones(limit=100)
    if evaluaciones:
        df = pd.DataFrame(evaluaciones)
        # Renombrar columnas para mejor presentación
        df = df.rename(
            columns={
                "id": "ID",
                "fecha_creacion": "Fecha",
                "objetivo_estrategico": "Objetivo Estratégico",
                "indicador": "Indicador",
                "meta": "Meta",
                "fuente_dato": "Fuente de Datos",
                "formula": "Fórmula",
                "tipo": "Tipo",
                "respuesta_gemini": "Respuesta Gemini",
                "calificacion": "Calificación",
                "recomendaciones": "Recomendaciones",
            }
        )
        # Reordenar columnas para mostrar la información de forma lógica
        ordered_columns = [
            "ID",
            "Fecha",
            "Objetivo Estratégico",
            "Indicador",
            "Meta",
            "Fuente de Datos",
            "Fórmula",
            "Tipo",
            "Calificación",
            "Recomendaciones",
            "Respuesta Gemini",
        ]
        df = df[ordered_columns]
        return df
    else:
        return pd.DataFrame(
            columns=[
                "ID",
                "Fecha",
                "Objetivo Estratégico",
                "Indicador",
                "Meta",
                "Fuente de Datos",
                "Fórmula",
                "Tipo",
                "Calificación",
                "Recomendaciones",
                "Respuesta Gemini",
            ]
        )


def crear_tab_historial():
    """Crea la pestaña de Historial"""
    with gr.TabItem("Historial"):
        with gr.Row():
            with gr.Column():
                refresh_btn = gr.Button(
                    "🔄 Actualizar Historial", elem_classes="submit-button"
                )
                historial_df = gr.Dataframe(
                    value=obtener_historial(),
                    label="Evaluaciones Recientes",
                    interactive=False,
                )

        # Configurar evento
        refresh_btn.click(fn=obtener_historial, outputs=historial_df)

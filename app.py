import gradio as gr
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from gemini_client import get_gemini_response
from database import db_manager

# CSS personalizado para un estilo profesional inspirado en Google
custom_css = """
@import url('https://fonts.googleapis.com/css2?family=Ubuntu:wght@400;500;700&family=Roboto:wght@400;500;700&display=swap');
body {
    font-family: 'Ubuntu', 'Roboto', sans-serif;
    background-color: #F8F9FA;
    color: #202124;
}
.gradio-container {
    max-width: 1100px !important;
    margin: 0 auto !important;
    padding: 16px;
}
.main-header h1 {
    font-size: 32px;
    font-weight: 600;
    margin: 0;
    color: #202124;
}
.main-header p {
    font-size: 16px;
    color: #5F6368;
    margin-top: 4px;
}
.card {
    background: #FFFFFF;
    border: 1px solid #E0E0E0;
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(60, 64, 67, 0.15);
    padding: 24px;
}
.submit-button {
    background: #1A73E8 !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 4px !important;
    font-weight: 500 !important;
    height: 42px !important;
    transition: box-shadow 0.2s ease;
}
.submit-button:hover {
    box-shadow: 0 3px 5px rgba(60, 64, 67, 0.3) !important;
}
label {
    font-size: 16px !important;
    font-weight: 600 !important;
    color: #202124 !important;
}

/* Estilos para los campos de entrada para mayor contraste */
textarea, input[type="text"] {
    border: 1px solid #AEB1B5 !important; /* Borde más oscuro para contraste */
    background-color: #FFFFFF !important;
    color: #202124 !important; /* Texto de entrada negro */
    font-size: 15px !important; /* Texto más grande en inputs */
}
textarea:focus, input[type="text"]:focus {
    border-color: #1A73E8 !important;
    box-shadow: 0 0 0 1px #1A73E8 !important;
}

/* Estilos para el área de respuesta de Gemini */
.output-area {
    font-size: 16px !important;
    line-height: 1.6 !important;
}

.output-area h1, .output-area h2, .output-area h3 {
    font-size: 20px !important;
    font-weight: 600 !important;
    color: #202124 !important;
    margin-top: 16px !important;
    margin-bottom: 8px !important;
}

.output-area p, .output-area li {
    font-size: 16px !important;
    color: #202124 !important;
    margin-bottom: 8px !important;
}

.output-area strong {
    font-weight: 600 !important;
    color: #202124 !important;
}
"""


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


def generar_estadisticas():
    """Genera el markdown y las gráficas (pie y bar) para la pestaña de estadísticas."""
    stats = db_manager.obtener_estadisticas()

    # Markdown con estadísticas
    markdown_text = f"""## 📊 Estadísticas de Evaluaciones

**Total de evaluaciones realizadas:** {stats['total_evaluaciones']}

### Distribución por Calificación (1-5):
"""

    # Agregar detalles de calificaciones al markdown
    calificacion_labels = {
        "1": "🟥 1 - Muy Bajo",
        "2": "🟧 2 - Bajo",
        "3": "🟨 3 - Medio",
        "4": "🟦 4 - Alto",
        "5": "🟢 5 - Muy Alto",
    }

    calificaciones_ordenadas = sorted(
        [
            item
            for item in stats["por_calificacion"].items()
            if item[0] and item[0].isdigit()
        ],
        key=lambda x: int(x[0]),
    )

    for calificacion, cantidad in calificaciones_ordenadas:
        label = calificacion_labels.get(calificacion, f"Nivel {calificacion}")
        markdown_text += f"- {label}: {cantidad} evaluaciones\n"

    markdown_text += "\n### Distribución por Tipo de Indicador:\n"
    tipos_ordenados = sorted(stats["por_tipo"].items())
    for tipo, cantidad in tipos_ordenados:
        markdown_text += f"- **{tipo}:** {cantidad} evaluaciones\n"

    # Preparar datos para las gráficas
    df_calificacion = pd.DataFrame(
        list(stats["por_calificacion"].items()),
        columns=["Calificación", "Cantidad"],
    )

    # Filtrar solo calificaciones válidas (no None) y procesar
    if not df_calificacion.empty:
        df_calificacion = df_calificacion[
            df_calificacion["Calificación"].notna()
        ].copy()
        df_calificacion["Calificación"] = df_calificacion["Calificación"].astype(str)
        df_calificacion = df_calificacion[
            df_calificacion["Calificación"].str.isdigit()
        ].copy()

        if not df_calificacion.empty:
            df_calificacion["Calificación_num"] = df_calificacion[
                "Calificación"
            ].astype(int)
            df_calificacion = df_calificacion.sort_values("Calificación_num")
            df_calificacion["Label"] = df_calificacion["Calificación"].map(
                calificacion_labels
            )

    df_tipo = pd.DataFrame(
        list(stats["por_tipo"].items()),
        columns=["Tipo", "Cantidad"],
    )

    # Gráfica 1: Pie chart de calificaciones
    if not df_calificacion.empty and "Label" in df_calificacion.columns:
        colors = ["#EA4335", "#FF9800", "#FFEB3B", "#2196F3", "#4CAF50"]

        fig_calificacion = px.pie(
            df_calificacion,
            names="Label",
            values="Cantidad",
            title="Distribución por Calificación (1-5)",
            hole=0.4,
            color="Calificación",
            color_discrete_map={str(i): colors[i - 1] for i in range(1, 6)},
        )
        fig_calificacion.update_traces(textposition="inside", textinfo="percent+label")
        fig_calificacion.update_layout(
            showlegend=True,
            height=400,
            margin=dict(t=50, b=50, l=50, r=50),
            legend=dict(
                orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.05
            ),
        )
    else:
        fig_calificacion = go.Figure().add_annotation(
            text="No hay datos de calificación disponibles",
            showarrow=False,
            font=dict(size=16),
        )
        fig_calificacion.update_layout(
            title="Distribución por Calificación (1-5)", height=400
        )

    # Gráfica 2: Bar chart de tipos de indicador
    if not df_tipo.empty and len(df_tipo) > 0:
        fig_tipo = go.Figure()
        colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]

        for i, row in df_tipo.iterrows():
            fig_tipo.add_trace(
                go.Bar(
                    x=[row["Tipo"]],
                    y=[row["Cantidad"]],
                    name=row["Tipo"],
                    marker_color=colors[i % len(colors)],
                    text=[row["Cantidad"]],
                    textposition="outside",
                    width=0.5,
                )
            )

        fig_tipo.update_layout(
            title_text="Distribución por Tipo de Indicador",
            height=400,
            margin=dict(t=60, b=50, l=50, r=50),
            yaxis_title="Cantidad de Evaluaciones",
            xaxis_title="Tipo de Indicador",
            showlegend=False,
            plot_bgcolor="white",
            barmode="group",
            yaxis=dict(
                gridcolor="lightgray",
                zeroline=True,
                zerolinecolor="gray",
                range=[0, df_tipo["Cantidad"].max() * 1.25 + 1],
            ),
            xaxis=dict(showgrid=False, type="category"),
        )
    else:
        fig_tipo = go.Figure().add_annotation(
            text="No hay datos de tipo de indicador disponibles",
            showarrow=False,
            font=dict(size=16),
        )
        fig_tipo.update_layout(title="Distribución por Tipo de Indicador", height=400)

    return markdown_text, fig_calificacion, fig_tipo


# Obtener valores iniciales para cargar al arrancar la app
try:
    initial_markdown, initial_fig_cal, initial_fig_tipo = generar_estadisticas()
except Exception as e:
    print(f"Error al generar estadísticas iniciales: {e}")
    initial_markdown = "No se pudieron cargar las estadísticas."
    initial_fig_cal = go.Figure()
    initial_fig_tipo = go.Figure()


with gr.Blocks(
    css=custom_css,
    title="Calificador de Indicadores de Gestión",
    theme=gr.themes.Default(),
) as demo:
    # Encabezado principal
    gr.HTML("""
        <div class="main-header" style="text-align:center; margin-bottom:24px;">
            <h1>Calificador de Indicadores de Gestión</h1>
            <p>Evalúa y mejora tus indicadores con inteligencia artificial</p>
        </div>
    """)

    with gr.Tabs():
        with gr.TabItem("Nueva Evaluación"):
            with gr.Row(equal_height=True):
                with gr.Column(scale=2, elem_classes="card"):
                    objetivo_estrategico = gr.Textbox(
                        label="Objetivo Estratégico",
                        placeholder="Describe el objetivo estratégico...",
                        lines=3,
                    )
                    indicador = gr.Textbox(
                        label="Indicador", placeholder="Nombre del indicador (KPI)"
                    )
                    meta = gr.Textbox(
                        label="Meta", placeholder="Valor objetivo y plazo"
                    )
                    fuente_dato = gr.Textbox(
                        label="Fuente de Datos",
                        placeholder="Sistema, base de datos o reporte",
                        lines=2,
                    )
                    formula = gr.Textbox(
                        label="Fórmula de Cálculo",
                        placeholder="Expresión matemática o método",
                        lines=2,
                    )
                    tipo = gr.Dropdown(
                        label="Tipo de Indicador",
                        choices=[
                            "Eficiencia",
                            "Eficacia",
                            "Calidad",
                            "Productividad",
                            "Impacto",
                        ],
                    )
                    submit_btn = gr.Button(
                        "Evaluar Indicador", elem_classes="submit-button"
                    )

                with gr.Column(scale=3, elem_classes="card"):
                    output_text = gr.Markdown(
                        label="Resultado",
                        value="Completa los campos y presiona 'Evaluar Indicador' para ver el análisis.",
                        elem_classes="output-area",
                    )

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

        with gr.TabItem("Estadísticas"):
            with gr.Row():
                with gr.Column():
                    refresh_stats_btn = gr.Button(
                        "🔄 Actualizar Estadísticas", elem_classes="submit-button"
                    )
                    estadisticas_text = gr.Markdown(
                        value=initial_markdown, label="Resumen Estadístico"
                    )
                    fig_calificacion_plot = gr.Plot(
                        value=initial_fig_cal, label="Distribución por Calificación"
                    )
                    fig_tipo_plot = gr.Plot(
                        value=initial_fig_tipo,
                        label="Distribución por Tipo de Indicador",
                    )

    # Eventos
    submit_btn.click(
        fn=get_gemini_response,
        inputs=[objetivo_estrategico, indicador, meta, fuente_dato, formula, tipo],
        outputs=output_text,
        show_progress=True,
    )

    refresh_btn.click(fn=obtener_historial, outputs=historial_df)

    refresh_stats_btn.click(
        fn=generar_estadisticas,
        outputs=[estadisticas_text, fig_calificacion_plot, fig_tipo_plot],
    )

if __name__ == "__main__":
    demo.launch(share=True)

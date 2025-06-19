import gradio as gr
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from backend.database import db_manager


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


def crear_tab_estadisticas():
    """Crea la pestaña de Estadísticas"""
    # Obtener valores iniciales para cargar al arrancar la app
    try:
        initial_markdown, initial_fig_cal, initial_fig_tipo = generar_estadisticas()
    except Exception as e:
        print(f"Error al generar estadísticas iniciales: {e}")
        initial_markdown = "No se pudieron cargar las estadísticas."
        initial_fig_cal = go.Figure()
        initial_fig_tipo = go.Figure()

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

        # Configurar evento
        refresh_stats_btn.click(
            fn=generar_estadisticas,
            outputs=[estadisticas_text, fig_calificacion_plot, fig_tipo_plot],
        )

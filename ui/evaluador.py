import gradio as gr
from backend.gemini_client import get_indicator_evaluation


def crear_tab_nueva_evaluacion():
    """Crea la pestaña de Nueva Evaluación"""
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
                meta = gr.Textbox(label="Meta", placeholder="Valor objetivo y plazo")
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

        # Configurar evento
        submit_btn.click(
            fn=get_indicator_evaluation,
            inputs=[objetivo_estrategico, indicador, meta, fuente_dato, formula, tipo],
            outputs=output_text,
            show_progress=True,
        )

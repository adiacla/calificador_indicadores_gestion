import gradio as gr
import pandas as pd
import base64
import io
import os
from backend.gemini_client import generate_code_from_prompt
from backend.code_executor import SafeCodeExecutor


def procesar_csv_y_generar_codigo(archivo_csv, instrucciones_usuario):
    """
    Procesa el archivo CSV subido, genera código usando IA y lo ejecuta
    """
    if archivo_csv is None:
        return "❌ Por favor, sube un archivo CSV.", [], "", ""

    if not instrucciones_usuario.strip():
        return (
            "❌ Por favor, proporciona instrucciones sobre qué visualizar.",
            [],
            "",
            "",
        )

    try:
        # Leer el archivo CSV
        df = pd.read_csv(archivo_csv.name)

        # Validar que el DataFrame no esté vacío
        if df.empty:
            return "❌ El archivo CSV está vacío.", [], "", ""

        # Generar código usando Gemini
        codigo_generado = generate_code_from_prompt(instrucciones_usuario, df)

        if codigo_generado.startswith("Error"):
            return f"❌ Error al generar código: {codigo_generado}", [], "", ""

        # Ejecutar el código de forma segura
        executor = SafeCodeExecutor()

        # Validar código antes de ejecutar
        es_valido, mensaje_validacion = executor.validate_code(codigo_generado)
        if not es_valido:
            return f"❌ Código no seguro: {mensaje_validacion}", [], codigo_generado, ""

        # Ejecutar código
        resultado = executor.execute_code(codigo_generado, df)

        if resultado["success"]:
            # Preparar archivos de gráficas para el Gallery
            archivos_graficas = []
            if resultado["figure_files"]:
                for i, archivo in enumerate(resultado["figure_files"]):
                    if os.path.exists(archivo):
                        # Renombrar archivo para descarga con nombre más descriptivo
                        nombre_descriptivo = f"grafica_{i+1}_indicadores.png"
                        archivos_graficas.append((archivo, nombre_descriptivo))

            # Preparar información del dataset
            dataset_info = f"""## 📊 Información del Dataset

**Filas:** {len(df):,}  
**Columnas:** {len(df.columns)}  
**Columnas disponibles:** {', '.join(df.columns.tolist())}

### Output del código:
```
{resultado["output"]}
```

**Variables creadas:** {len(resultado["variables"])}  
**Gráficas generadas:** {len(resultado["figures"])}
"""

            success_message = "✅ **Código ejecutado exitosamente!**"

            return success_message, archivos_graficas, codigo_generado, dataset_info

        else:
            error_msg = f"""❌ **Error al ejecutar el código:**

```
{resultado["error"]}
```

**Output parcial:**
```
{resultado["output"]}
```
"""
            return error_msg, [], codigo_generado, ""

    except Exception as e:
        return f"❌ Error al procesar el archivo: {str(e)}", [], "", ""


def crear_tab_generador_ia():
    """Crea la pestaña del Generador IA"""
    with gr.TabItem("Generador IA"):
        gr.HTML("""
            <div style="text-align: center; margin-bottom: 20px;">
                <h3>🤖 Generador de Análisis con IA</h3>
                <p>Sube un archivo CSV y describe qué visualizaciones quieres ver sobre tus indicadores de gestión</p>
            </div>
        """)

        # Primera fila: Input completo (CSV + instrucciones + botón)
        with gr.Row():
            with gr.Column(elem_classes="card"):
                archivo_csv = gr.File(
                    label="📁 Subir archivo CSV",
                    file_types=[".csv"],
                    file_count="single",
                    elem_classes="file-upload",
                )

                instrucciones = gr.Textbox(
                    label="📝 Instrucciones para el análisis",
                    placeholder="""Ejemplos de instrucciones:
- Crea un dashboard con gráficas de barras y líneas para mostrar tendencias de indicadores
- Genera un análisis comparativo entre diferentes tipos de indicadores
- Muestra la distribución de calificaciones con histogramas y gráficas de caja
- Crea visualizaciones para identificar correlaciones entre variables
- Analiza la evolución temporal de los indicadores principales""",
                    lines=6,
                )

                with gr.Row():
                    generar_btn = gr.Button(
                        "🚀 Generar Análisis",
                        elem_classes="submit-button",
                    )
                    status_output = gr.Markdown(
                        value="Sube un archivo CSV y proporciona instrucciones para comenzar el análisis.",
                        elem_classes="output-area",
                    )

        # Segunda fila: Visualizaciones generadas con botones de descarga
        with gr.Row():
            with gr.Column(elem_classes="card"):
                graficas_output = gr.Gallery(
                    label="📈 Visualizaciones Generadas (Haz clic en cada imagen para descargar)",
                    show_label=True,
                    elem_id="graficas-gallery",
                    columns=2,
                    rows=2,
                    object_fit="contain",
                    height="auto",
                    allow_preview=True,
                    show_download_button=True,
                    interactive=True,
                )

        # Tercera fila: Código generado
        with gr.Row():
            with gr.Column(elem_classes="card"):
                codigo_output = gr.Code(
                    label="🔧 Código Generado", language="python", interactive=False
                )

        # Cuarta fila: Información del dataset
        with gr.Row():
            with gr.Column(elem_classes="card"):
                dataset_info_output = gr.Markdown(
                    label="📊 Información del Dataset", elem_classes="output-area"
                )

        # Configurar evento
        generar_btn.click(
            fn=procesar_csv_y_generar_codigo,
            inputs=[archivo_csv, instrucciones],
            outputs=[
                status_output,
                graficas_output,
                codigo_output,
                dataset_info_output,
            ],
            show_progress=True,
        )

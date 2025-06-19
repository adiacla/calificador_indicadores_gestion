import gradio as gr
from ui.evaluador import crear_tab_nueva_evaluacion
from ui.historial import crear_tab_historial
from ui.estadisticas import crear_tab_estadisticas
from ui.generador_ia import crear_tab_generador_ia

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

/* Limitar altura del componente File cuando está vacío */
.file-upload {
    min-height: 60px !important;
    max-height: 120px !important;
}

.file-upload .upload-button {
    height: 60px !important;
    min-height: 60px !important;
}

.file-upload .file-preview {
    max-height: 80px !important;
}

/* Estilo específico para el área de drop de archivos */
input[type="file"] {
    height: 60px !important;
    min-height: 60px !important;
}

.upload-area {
    height: 60px !important;
    min-height: 60px !important;
    max-height: 100px !important;
}


"""

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
        crear_tab_nueva_evaluacion()
        crear_tab_historial()
        crear_tab_estadisticas()
        crear_tab_generador_ia()

if __name__ == "__main__":
    demo.launch(share=True)

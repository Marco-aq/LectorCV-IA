from crewai.tools import tool
import pdfplumber

@tool("Lector_de_PDF")
def leer_pdf_tool(ruta_archivo: str) -> str:
    """
    Herramienta vital para extraer texto de archivos PDF.
    Debe recibir como argumento la ruta exacta del archivo.
    """
    try:
        texto_completo = ""
        with pdfplumber.open(ruta_archivo) as pdf:
            for pagina in pdf.pages:
                texto = pagina.extract_text()
                if texto:
                    texto_completo += texto + "\n"
        return texto_completo
    except Exception as e:
        return f"Error crítico al leer el archivo PDF: {e}"
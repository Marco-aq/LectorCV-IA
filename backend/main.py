from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import shutil
import os
import json

# Importamos las funciones agénticas que creaste en agents.py
from agents import procesar_cv_y_generar_preguntas, evaluar_respuestas_candidato

app = FastAPI(title="API de Reclutamiento con IA Agéntica")

# Configuración de CORS (Crucial para que Streamlit pueda comunicarse con FastAPI)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # En producción, aquí pones la URL de tu frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# UTILIDADES
# ==========================================
def extraer_json_de_texto(texto_raw: str) -> dict:
    """
    Los LLMs a veces devuelven el JSON envuelto en bloques de código (```json ... 
```).
    Esta función limpia ese formato para asegurar que FastAPI devuelva un JSON real.
    """
    texto_limpio = texto_raw.strip()
    if texto_limpio.startswith("```json"):
        texto_limpio = texto_limpio[7:]
    if texto_limpio.startswith("```"):
        texto_limpio = texto_limpio[3:]
    if texto_limpio.endswith("```"):
        texto_limpio = texto_limpio[:-3]
        
    try:
        return json.loads(texto_limpio.strip())
    except json.JSONDecodeError:
        # Si falla, devolvemos el texto como un diccionario genérico
        return {"raw_response": texto_raw}

# Modelo de datos para la Fase 2
class RespuestasCandidato(BaseModel):
    respuestas: str

# ==========================================
# ENDPOINTS (Rutas de la API)
# ==========================================

@app.post("/generar-preguntas/")
async def endpoint_generar_preguntas(
    descripcion_puesto: str = Form(...),
    cv: UploadFile = File(...)
):
    """
    Fase 1: Recibe la oferta de trabajo y el CV. Genera las 4 preguntas.
    """
    if not cv.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="El archivo debe ser un PDF.")

    # 1. Guardamos el PDF temporalmente en el servidor
    ruta_temporal = f"temp_{cv.filename}"
    with open(ruta_temporal, "wb") as buffer:
        shutil.copyfileobj(cv.file, buffer)

    try:
        # 2. Despertamos a los agentes 1, 2 y 3
        resultado_raw = procesar_cv_y_generar_preguntas(descripcion_puesto, ruta_temporal)
        
        # 3. Limpiamos la respuesta para devolver un JSON perfecto
        json_limpio = extraer_json_de_texto(resultado_raw)
        return json_limpio

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # 4. Limpiamos: Borramos el PDF temporal para no saturar el servidor
        if os.path.exists(ruta_temporal):
            os.remove(ruta_temporal)


@app.post("/evaluar-candidato/")
async def endpoint_evaluar_candidato(datos: RespuestasCandidato):
    """
    Fase 2: Recibe las respuestas del candidato y emite el veredicto final.
    """
    try:
        # 1. Despertamos al Agente 4 (Clasificador)
        resultado_raw = evaluar_respuestas_candidato(datos.respuestas)
        
        # 2. Limpiamos y devolvemos el veredicto
        json_limpio = extraer_json_de_texto(resultado_raw)
        return json_limpio

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Para probar que el servidor está vivo
@app.get("/")
def read_root():
    return {"mensaje": "La API de IA Agéntica está en línea y lista."}
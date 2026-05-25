import os
import streamlit as st
import requests

# Configuración de la página
st.set_page_config(page_title="Reclutador IA", page_icon="🤖", layout="wide")

# ==========================================
# CONFIGURACIÓN
# ==========================================
# La URL del backend se lee desde variable de entorno; por defecto apunta a localhost
API_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Inicializar el estado de la sesión para no perder datos al recargar la pantalla
if "preguntas" not in st.session_state:
    st.session_state.preguntas = None
if "veredicto" not in st.session_state:
    st.session_state.veredicto = None
if "cargando" not in st.session_state:
    st.session_state.cargando = False

# ==========================================
# INTERFAZ GRÁFICA
# ==========================================
st.title(" Agente de Reclutamiento con IA")
st.markdown("Sube una oferta de trabajo y un CV para que nuestro sistema multi-agente genere una entrevista técnica personalizada.")

# --- FASE 1: Subida de Datos (RRHH) ---
if st.session_state.preguntas is None and st.session_state.veredicto is None:
    st.header("1. Configuración de la Evaluación")
    
    col1, col2 = st.columns(2)
    
    with col1:
        descripcion_puesto = st.text_area(
            "Descripción del Puesto Ideal:", 
            height=300, 
            placeholder="Pega aquí los requisitos, hard skills y soft skills..."
        )
        
    with col2:
        cv_pdf = st.file_uploader("Sube el CV del Candidato (PDF)", type=["pdf"])

    if st.button("Analizar CV y Generar Entrevista "):
        if not descripcion_puesto or not cv_pdf:
            st.warning("Por favor, completa la descripción y sube un PDF.")
        else:
            with st.spinner("Los Agentes están analizando el perfil y cruzando datos... (Esto puede tomar un minuto)"):
                # Preparamos los datos para enviar a FastAPI
                datos = {"descripcion_puesto": descripcion_puesto}
                archivos = {"cv": (cv_pdf.name, cv_pdf.getvalue(), "application/pdf")}
                
                try:
                    respuesta = requests.post(f"{API_URL}/generar-preguntas/", data=datos, files=archivos)
                    if respuesta.status_code == 200:
                        st.session_state.preguntas = respuesta.json()
                        st.rerun() # Recargamos la pantalla para mostrar la Fase 2
                    else:
                        st.error(f"Error del servidor: {respuesta.text}")
                except Exception as e:
                    st.error(f"No se pudo conectar al Backend. ¿Está corriendo uvicorn? Error: {e}")

# --- FASE 2: Entrevista (Candidato) ---
elif st.session_state.preguntas is not None and st.session_state.veredicto is None:
    st.header("2. Entrevista Técnica del Candidato")
    st.info("Responde a las siguientes preguntas generadas específicamente para tu perfil.")
    
    # Creamos un formulario para recopilar las respuestas
    with st.form("formulario_entrevista"):
        respuestas_usuario = {}
        
        # Iteramos sobre el JSON que nos devolvió el Backend
        preguntas_lista = st.session_state.preguntas.get("preguntas", [])
        
        for p in preguntas_lista:
            st.markdown(f"**Pregunta {p['id']} ({p['tipo'].capitalize()}):** {p['pregunta']}")
            respuestas_usuario[p['id']] = st.text_area(f"Tu respuesta a la pregunta {p['id']}:", height=100)
            st.markdown("---")
            
        submit_respuestas = st.form_submit_button("Enviar Respuestas al Evaluador 📨")
        
        if submit_respuestas:
            with st.spinner("El Agente Clasificador está evaluando tus respuestas..."):
                # Concatenamos todas las respuestas en un solo texto para el Agente 4
                texto_respuestas = ""
                for id_preg, respuesta in respuestas_usuario.items():
                    texto_respuestas += f"Respuesta a pregunta {id_preg}: {respuesta}\n\n"
                
                payload = {"respuestas": texto_respuestas}
                
                try:
                    res = requests.post(f"{API_URL}/evaluar-candidato/", json=payload)
                    if res.status_code == 200:
                        st.session_state.veredicto = res.json()
                        st.rerun()
                    else:
                        st.error(f"Error del servidor: {res.text}")
                except Exception as e:
                    st.error(f"Error de conexión: {e}")

# --- FASE 3: Veredicto Final (RRHH) ---
elif st.session_state.veredicto is not None:
    st.header("3. Veredicto del Reclutador Senior ")
    
    v = st.session_state.veredicto
    resultado_final = v.get("veredicto", "NO DEFINIDO")
    
    # Coloreamos el veredicto
    if resultado_final == "APTO":
        st.success(f"## DECISIÓN: {resultado_final}")
    elif resultado_final == "NO APTO":
        st.error(f"## DECISIÓN: {resultado_final}")
    else:
        st.warning(f"## DECISIÓN: {resultado_final}")
        
    st.markdown(f"**Justificación:** {v.get('justificacion_corta', '')}")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Fortalezas Demostradas 🟢")
        for f in v.get("fortalezas_demostradas", []):
            st.markdown(f"- {f}")
            
    with col2:
        st.markdown("### Debilidades Críticas 🔴")
        for d in v.get("debilidades_criticas", []):
            st.markdown(f"- {d}")
            
    st.markdown("---")
    st.markdown("### Feedback para el Candidato 📩")
    st.info(v.get("recomendacion_feedback", ""))
    
    # Botón para reiniciar la aplicación
    if st.button("Evaluar a otro candidato 🔄"):
        st.session_state.preguntas = None
        st.session_state.veredicto = None
        st.rerun()
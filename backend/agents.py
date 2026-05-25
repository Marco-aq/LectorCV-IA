import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, LLM
from tools import leer_pdf_tool

# EVITAR CONGELAMIENTOS DE TELEMETRÍA
os.environ["OTEL_SDK_DISABLED"] = "true"
os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"
# Cargar variables de entorno desde el archivo .env
load_dotenv()
clave_api = os.getenv("GOOGLE_API_KEY")

# Inicializamos el motor de IA
mi_llm = LLM(
    model="gemini/gemini-3.1-flash-lite",
    api_key=clave_api,
    temperature=0.2
)

# ==========================================
# DEFINICIÓN DE AGENTES (Reutilizables con Skills)
# ==========================================

analista_perfil = Agent(
    role='Analista Senior de Reclutamiento Técnico',
    goal='Analizar descripciones de puestos de trabajo y extraer requisitos obligatorios en formato JSON.',
    backstory='''Eres un experto en recursos humanos de una empresa tecnológica de élite. 
    Tus habilidades (skills) incluyen:
    - Análisis semántico de requerimientos técnicos.
    - Mapeo de competencias tecnológicas (identificar si un framework pertenece a Frontend, Backend, Infraestructura, o Machine Learning).
    - Diferenciación estricta entre herramientas obligatorias y "nice-to-have".''',
    verbose=True,
    allow_delegation=False,
    llm=mi_llm
)

evaluador_cv = Agent(
    role='Evaluador Técnico de Talento',
    goal='Analizar el texto extraído de un CV y compararlo rigurosamente contra el perfil de puesto ideal.',
    backstory='''Eres un evaluador técnico implacable pero justo. 
    Tus habilidades (skills) incluyen:
    - Evaluación estructurada de perfiles técnicos.
    - Detección de "falsos positivos" (candidatos que mencionan una tecnología de pasada vs. experiencia real).
    - Comprensión profunda de ecosistemas: entiendes cómo se relacionan herramientas como Python, Docker, redes TCP/UDP y bases de datos en un entorno real.
    - Pensamiento crítico para identificar brechas de conocimiento.''',
    verbose=True,
    allow_delegation=False,
    tools=[leer_pdf_tool],
    llm=mi_llm
)

entrevistador = Agent(
    role='Entrevistador Técnico Especializado',
    goal='Diseñar preguntas de entrevista personalizadas basadas en el reporte de compatibilidad del candidato.',
    backstory='''Eres un líder técnico de ingeniería. 
    Tus habilidades (skills) incluyen:
    - Dominio de la metodología STAR (Situación, Tarea, Acción, Resultado) para formular preguntas conductuales.
    - Creación de escenarios hipotéticos para evaluar resolución de problemas.
    - Evaluación de adaptabilidad: sabes formular preguntas para descubrir si el candidato puede usar lo que ya sabe para aprender herramientas nuevas rápidamente.
    No haces preguntas genéricas ni de libro de texto; diseñas retos intelectuales.''',
    verbose=True,
    allow_delegation=False,
    llm=mi_llm
)

clasificador = Agent(
    role='Reclutador Senior y Tomador de Decisiones',
    goal='Analizar las respuestas de la entrevista técnica y emitir un veredicto final: APTO, NO APTO o EN OBSERVACIÓN.',
    backstory='''Eres el director de ingeniería. Tienes la última palabra en las contrataciones. 
    Tus habilidades (skills) incluyen:
    - Toma de decisiones basada en datos empíricos.
    - Análisis de potencial vs. experiencia actual.
    - Redacción de feedback constructivo, profesional y empático.
    Valoras la honestidad y la capacidad de aprendizaje sistemático, pero priorizas las necesidades técnicas y urgencias del proyecto al emitir tu veredicto.''',
    verbose=True,
    allow_delegation=False,
    llm=mi_llm
)

# ==========================================
# FUNCIONES PARA FASTAPI
# ==========================================

def procesar_cv_y_generar_preguntas(descripcion_puesto: str, ruta_pdf: str) -> str:
    """Ejecuta la Fase 1: Analiza oferta, evalúa CV y genera 4 preguntas."""
    
    tarea_analisis = Task(
        description=f'Analiza la siguiente descripción de puesto: {descripcion_puesto}. Extrae hard skills, soft skills y herramientas. Devuelve ESTRICTAMENTE JSON.',
        expected_output='JSON con claves: hard_skills, soft_skills, experiencia, herramientas.',
        agent=analista_perfil
    )

    tarea_evaluacion = Task(
        description=f'''
        1. Usa la herramienta Lector_de_PDF para extraer el texto de: "{ruta_pdf}".
        2. Compara el texto contra el JSON de la tarea anterior.
        3. Redacta un reporte con el porcentaje de compatibilidad, matches y brechas.
        ''',
        expected_output='Reporte analítico de compatibilidad y brechas.',
        agent=evaluador_cv
    )

    tarea_preguntas = Task(
        description='''
        Revisa el reporte de compatibilidad generado en la tarea anterior.
        Diseña 4 preguntas: 2 de adaptación (Match) y 2 de aprendizaje (Brechas).
        Devuelve ESTRICTAMENTE un JSON con la clave "preguntas" (array de objetos con id, tipo, pregunta).
        ''',
        expected_output='Un JSON estricto con 4 preguntas personalizadas.',
        agent=entrevistador
    )

    crew_fase1 = Crew(
        agents=[analista_perfil, evaluador_cv, entrevistador],
        tasks=[tarea_analisis, tarea_evaluacion, tarea_preguntas],
        verbose=True
    )
    
    resultado = crew_fase1.kickoff()
    return resultado.raw

def evaluar_respuestas_candidato(respuestas_candidato: str) -> str:
    """Ejecuta la Fase 2: Evalúa las respuestas y emite veredicto."""
    
    tarea_clasificacion = Task(
        description=f'''
        Evalúa estas respuestas dadas por el candidato:
        {respuestas_candidato}
        
        Redacta un JSON ESTRICTO con la estructura:
        {{
          "veredicto": "APTO" | "NO APTO" | "EN OBSERVACIÓN",
          "justificacion_corta": "...",
          "fortalezas_demostradas": ["..."],
          "debilidades_criticas": ["..."],
          "recomendacion_feedback": "..."
        }}
        ''',
        expected_output='JSON con la clasificación final y el feedback.',
        agent=clasificador
    )

    crew_fase2 = Crew(
        agents=[clasificador],
        tasks=[tarea_clasificacion],
        verbose=True
    )
    
    resultado = crew_fase2.kickoff()
    return resultado.raw
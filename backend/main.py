import os
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import List

from backend.database import (
    init_db,
    get_insured_by_id_and_policy,
    get_specialty_by_id,
    get_all_cities,
    get_all_specialties
)
from backend.business_rules import rank_hospitals_for_patient
from backend.llm import analyze_symptoms
from backend.schemas import (
    ValidarAseguradoRequest,
    ValidarAseguradoResponse,
    EstimarCopagoRequest,
    EstimarCopagoResponse,
    HospitalOption
)

# Initialize database
init_db()

app = FastAPI(
    title="Health Insurance Copay Assistant API",
    description="Backend para el Estimador Agéntico de Copago y Cobertura para el Paciente",
    version="1.0.0"
)

# Configure CORS (useful for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Disclaimer text
DISCLAIMER_TEXT = "Estimación informativa preliminar, no constituye una autorización de cobertura ni costo final por parte de la aseguradora."

@app.get("/api/ciudades", response_model=List[str])
def obtener_ciudades():
    """Retorna las ciudades disponibles en la base de datos."""
    try:
        return get_all_cities()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener ciudades: {str(e)}"
        )

@app.post("/api/validar-asegurado", response_model=ValidarAseguradoResponse)
def validar_asegurado(req: ValidarAseguradoRequest):
    """Verifica si el usuario existe en la base de datos con su cédula y póliza."""
    try:
        insured = get_insured_by_id_and_policy(req.national_id.strip(), req.policy_number.strip())
        if insured:
            return ValidarAseguradoResponse(
                success=True,
                message="Asegurado validado correctamente.",
                insured_name=insured["name"],
                plan_name=insured["plan_name"]
            )
        else:
            return ValidarAseguradoResponse(
                success=False,
                message="Identificación o número de póliza incorrectos. Por favor, verifique los datos."
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en el servidor al validar asegurado: {str(e)}"
        )

@app.post("/api/estimar-copago", response_model=EstimarCopagoResponse)
def estimar_copago(req: EstimarCopagoRequest):
    """
    Infiere la especialidad médica usando el LLM y calcula de manera determinista 
    los copagos y la cobertura para los hospitales de la red en la ciudad elegida.
    """
    # 1. Validar al asegurado primero
    insured = get_insured_by_id_and_policy(req.national_id.strip(), req.policy_number.strip())
    if not insured:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Asegurado no validado. Verifique su número de identificación y póliza."
        )

    # 2. Validar campos de entrada
    if not req.city.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Debe seleccionar una ciudad.")
    
    symptom_text = req.symptom.strip()
    if not symptom_text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El síntoma no puede estar vacío.")

    # 3. Invocar al LLM para clasificar especialidad y obtener explicación
    # Si viene con una aclaración (segundo intento), la adjuntamos
    llm_result = analyze_symptoms(
        symptom=symptom_text,
        context=req.previous_symptom.strip() if req.previous_symptom else None
    )

    specialty_id = llm_result.get("specialty_id", "medicina_general")
    confidence = llm_result.get("confidence", 0.5)
    explanation = llm_result.get("explanation", "Evaluación inicial de síntomas generales.")
    emergency_detected = llm_result.get("emergency_detected", False)
    needs_clarification = (specialty_id == "vague")
    clarifying_question = llm_result.get("clarifying_question")

    # 4. Si requiere aclaración y no la hemos obtenido ya, detenemos y retornamos la pregunta
    if needs_clarification and not req.clarification_answer:
        return EstimarCopagoResponse(
            specialty="Pendiente de aclaración",
            confidence=confidence,
            coverage_percentage=0.0,
            estimated_copay=0.0,
            best_hospital="N/A",
            hospital_options=[],
            explanation="Se requiere mayor información para determinar la especialidad médica.",
            needs_clarification=True,
            clarifying_question=clarifying_question,
            emergency_detected=emergency_detected,
            disclaimer=DISCLAIMER_TEXT
        )

    # Si ya se contestó la aclaración pero la confianza sigue baja, forzamos a medicina_general
    if needs_clarification and req.clarification_answer:
        # Combinamos original + respuesta para un re-análisis
        combined_symptoms = f"{symptom_text}. Aclaración: {req.clarification_answer.strip()}"
        print(f"[LLM] Re-evaluating combined symptoms: {combined_symptoms}")
        llm_result = analyze_symptoms(combined_symptoms)
        specialty_id = llm_result.get("specialty_id", "medicina_general")
        confidence = llm_result.get("confidence", 0.5)
        explanation = llm_result.get("explanation", "Clasificación posterior a aclaración.")
        emergency_detected = emergency_detected or llm_result.get("emergency_detected", False)
        
        # Si sigue marcando vago, forzamos a medicina general como fallback definitivo
        if specialty_id == "vague":
            specialty_id = "medicina_general"
            explanation = "No logramos definir una especialidad específica tras la aclaración. Se deriva a Medicina General por seguridad."

    # 5. Obtener los detalles de la especialidad desde la BD
    specialty_db = get_specialty_by_id(specialty_id)
    if not specialty_db:
        # Fallback de especialidad desconocida
        specialty_id = "medicina_general"
        specialty_db = get_specialty_by_id("medicina_general")
        explanation += " (Especialidad derivada a Medicina General debido a parámetros no identificados)"

    specialty_name_es = specialty_db["name_es"] if specialty_db else "Medicina General"

    # 6. Calcular copagos y ranking de hospitales determinísticamente en código
    ranked_hospitals = rank_hospitals_for_patient(
        city=req.city,
        specialty_id=specialty_id,
        plan_details={
            "coinsurance_rate": insured["coinsurance_rate"],
            "max_copay_cap": insured["max_copay_cap"],
            "min_copay_floor": insured["min_copay_floor"]
        }
    )

    # Cobertura nominal de referencia para el plan (ej. 90% para Platino, 80% para Oro, 60% para Básico)
    nominal_coverage = round((1 - insured["coinsurance_rate"]) * 100, 1)

    # 7. Manejo si no hay hospitales con la especialidad en la ciudad
    if not ranked_hospitals:
        # Intentamos buscar medicina general en la ciudad como alternativa
        if specialty_id != "medicina_general":
            print(f"[Rules] No network hospitals found for {specialty_id} in {req.city}. Checking general medicine...")
            ranked_hospitals = rank_hospitals_for_patient(
                city=req.city,
                specialty_id="medicina_general",
                plan_details={
                    "coinsurance_rate": insured["coinsurance_rate"],
                    "max_copay_cap": insured["max_copay_cap"],
                    "min_copay_floor": insured["min_copay_floor"]
                }
            )
            specialty_name_es = f"{specialty_name_es} (Atención inicial en Medicina General)"
            explanation += " Nota: No se encontraron hospitales de la red especializados en su ciudad, se muestra red de Medicina General."
            
        if not ranked_hospitals:
            # Si aún no hay nada en esa ciudad, error amigable
            return EstimarCopagoResponse(
                specialty=specialty_name_es,
                confidence=confidence,
                coverage_percentage=nominal_coverage,
                estimated_copay=0.0,
                best_hospital="Sin red en esta ciudad",
                hospital_options=[],
                explanation="No disponemos de hospitales en convenio activos para esta especialidad en la ciudad seleccionada. Por favor contacte soporte.",
                needs_clarification=False,
                clarifying_question=None,
                emergency_detected=emergency_detected,
                disclaimer=DISCLAIMER_TEXT
            )

    # Convertir a objetos HospitalOption para la respuesta
    options = [HospitalOption(**opt) for opt in ranked_hospitals]
    best_opt = options[0]

    return EstimarCopagoResponse(
        specialty=specialty_name_es,
        confidence=confidence,
        coverage_percentage=nominal_coverage,
        estimated_copay=best_opt.estimated_copay,
        best_hospital=best_opt.name,
        hospital_options=options,
        explanation=explanation,
        needs_clarification=False,
        clarifying_question=None,
        emergency_detected=emergency_detected,
        disclaimer=DISCLAIMER_TEXT
    )

# Serve Frontend static files
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")

if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/")
    def read_root():
        index_path = os.path.join(frontend_dir, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {"message": "Health Insurance Copay Assistant is running, but frontend/index.html was not found."}
else:
    @app.get("/")
    def read_root():
        return {"message": "Health Insurance Copay Assistant is running. Static frontend directory not found yet."}

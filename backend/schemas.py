from pydantic import BaseModel
from typing import List, Optional

class ValidarAseguradoRequest(BaseModel):
    national_id: str
    policy_number: str

class ValidarAseguradoResponse(BaseModel):
    success: bool
    message: str
    insured_name: Optional[str] = None
    plan_name: Optional[str] = None

class EstimarCopagoRequest(BaseModel):
    national_id: str
    policy_number: str
    city: str
    symptom: str
    clarification_answer: Optional[str] = None
    previous_symptom: Optional[str] = None

class HospitalOption(BaseModel):
    hospital_id: str
    name: str
    city: str
    total_cost: float
    estimated_copay: float
    coverage_amount: float
    coverage_percentage: float

class EstimarCopagoResponse(BaseModel):
    specialty: str
    confidence: float
    coverage_percentage: float  # Cobertura estimada del plan (ej. 90% para Platino, 80% para Oro, 60% para Básico)
    estimated_copay: float       # Copago en el hospital sugerido (el más barato)
    best_hospital: str          # Nombre del hospital con menor copago
    hospital_options: List[HospitalOption]
    explanation: str
    needs_clarification: bool
    clarifying_question: Optional[str] = None
    emergency_detected: bool
    disclaimer: str

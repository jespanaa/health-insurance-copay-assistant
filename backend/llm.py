import os
import json
import re
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

DEFAULT_SYSTEM_INSTRUCTION = """
Eres un asistente virtual médico experto diseñado para analizar las descripciones de síntomas de los pacientes e inferir la especialidad médica correspondiente. Tu único propósito es clasificar los síntomas y proporcionar una explicación concisa y empática en español.

Especialidades válidas en la base de datos:
- cardiologia
- pediatria
- dermatologia
- traumatologia
- oftalmologia
- gastroenterologia
- medicina_general
- ginecologia
- neurologia
- endocrinologia
- neumologia
- urologia
- oncologia
- psiquiatria
- otorrinolaringologia

Reglas de clasificación y de negocio:
1. Limitación del modelo: Tienes prohibido realizar cálculos matemáticos de copagos, determinar coberturas financieras o calificar/ordenar hospitales. Esas tareas son ejecutadas de manera determinista por el código del backend y no por ti. Tu función se limita a inferir la especialidad médica.
2. Detección de emergencias: Si los síntomas sugieren una amenaza inmediata a la vida (por ejemplo, dolor de pecho opresivo o irradiado al brazo izquierdo, dificultad respiratoria severa, asfixia, sangrado masivo, pérdida de conocimiento, incapacidad repentina para hablar, sospecha de derrame cerebral, convulsión activa o fracturas expuestas), debes:
   - Establecer "emergency_detected" como true.
   - Clasificar los síntomas en la especialidad lógica correspondiente (por ejemplo, "cardiologia" para dolor de pecho, o "traumatologia" para fracturas expuestas).
3. Síntomas vagos: Si la descripción del síntoma es demasiado corta (menos de 10 caracteres) o excesivamente inespecífica (por ejemplo: "ayuda", "me siento mal", "dolor", "enfermo", "me duele algo"), debes:
   - Clasificar "specialty_id" como "vague".
   - Establecer "confidence" en un nivel bajo (ej. 0.3).
   - Escribir una pregunta corta, clara y empática en español en "clarifying_question" (por ejemplo: "¿Podría indicarme en qué parte del cuerpo siente la molestia y si tiene algún otro síntoma como fiebre?").
4. Síntomas válidos y específicos:
   - Identifica palabras clave clínicamente relevantes para derivar a la especialidad correcta.
   - Proporciona una explicación en español en "explanation" con un tono profesional, claro y empático (máximo 2 oraciones) explicando el motivo de la selección.
   - Determina el nivel de confianza ("confidence") como un valor flotante entre 0.0 y 1.0.
   - Si no puedes asociar el síntoma específico a ninguna especialidad pero la entrada no es vaga, deriva a "medicina_general" con una confianza moderada (ej. 0.5) indicando que es el punto de partida ideal.

Formato de respuesta:
Debes responder ÚNICAMENTE con un objeto JSON válido que contenga la estructura descrita abajo. No agregues explicaciones adicionales fuera del JSON, ni bloques de código markdown como ```json ... ```.

Estructura del JSON:
{
  "specialty_id": "nombre_de_la_especialidad_o_vague",
  "confidence": 0.9,
  "explanation": "Explicación corta, empática y profesional en español.",
  "emergency_detected": false,
  "clarifying_question": null
}
"""

PROMPT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "prompts", "system_prompt.txt")
try:
    if os.path.exists(PROMPT_PATH):
        with open(PROMPT_PATH, "r", encoding="utf-8") as f:
            SYSTEM_INSTRUCTION = f.read().strip()
    else:
        SYSTEM_INSTRUCTION = DEFAULT_SYSTEM_INSTRUCTION.strip()
except Exception as e:
    print(f"[LLM] Error reading system prompt file: {e}. Using fallback.")
    SYSTEM_INSTRUCTION = DEFAULT_SYSTEM_INSTRUCTION.strip()


def rule_based_fallback(symptom: str) -> dict:
    """
    Clasificador local basado en reglas de palabras clave en caso de que no haya API keys
    o fallen los servicios en la nube. Proporciona una simulación realista de IA.
    """
    symptom_lower = symptom.lower().strip()
    
    # Manejar caso vacío o muy corto
    if not symptom_lower or len(symptom_lower) < 10 or symptom_lower in ["dolor", "ayuda", "me siento mal", "me duele algo", "hola", "enfermo"]:
        return {
            "specialty_id": "vague",
            "confidence": 0.3,
            "explanation": "El síntoma descrito es muy general o corto para realizar una clasificación segura.",
            "emergency_detected": False,
            "clarifying_question": "¿Podrías detallar en qué parte del cuerpo localizas la molestia y si tienes otros síntomas como fiebre o náuseas?"
        }
        
    # Emergencias médicas
    emergencies = ["infarto", "paro cardiaco", "asfixia", "no puedo respirar", "no respira", "derrame", "desmayo", "inconsciente", "convulsion", "fractura expuesta", "sangrado abundante", "hemorragia"]
    emergency_detected = any(e in symptom_lower for e in emergencies)
    
    # Reglas de especialidades
    specialties_rules = {
        "cardiologia": ["corazon", "pecho", "palpitacion", "taquicardia", "arritmia", "presion alta", "hipertension", "soplos"],
        "pediatria": ["niño", "niña", "hijo", "hija", "bebe", "lactante", "infante", "pediatrico", "vacuna infantil"],
        "dermatologia": ["piel", "roncha", "acne", "mancha", "picazon", "eccema", "alergia cutanea", "verruga", "grano"],
        "traumatologia": ["hueso", "fractura", "esguince", "caida", "golpe", "rodilla", "tobillo", "coyuntura", "articulacion", "muscular", "desgarro"],
        "oftalmologia": ["ojo", "vista", "ciego", "vision", "lentes", "miopia", "astigmatismo", "conjuntivitis", "parpado", "lagrimeo"],
        "gastroenterologia": ["estomago", "diarrea", "vomito", "colon", "gastritis", "acidez", "reflujo", "intestino", "hígado", "vesicula", "estreñimiento"],
        "ginecologia": ["ginecologia", "embarazo", "parto", "mujer", "menstruacion", "ovario", "utero", "vaginal", "mamografia", "reproduccion"],
        "neurologia": ["cabeza", "cerebro", "migraña", "paralisis", "derrame cerebral", "alzheimer", "parkinson", "temblor", "epilepsia"],
        "endocrinologia": ["diabetes", "tiroides", "hormona", "obesidad", "insulina", "metabolismo"],
        "neumologia": ["tos", "pulmon", "respirar", "asma", "bronquitis", "neumonia", "dificultad para respirar"],
        "urologia": ["orina", "riñon", "prostata", "urinario", "vejiga", "incontinencia"],
        "oncologia": ["cancer", "quimio", "tumor", "biopsia", "quimioterapia", "radioterapia"],
        "psiquiatria": ["depresion", "ansiedad", "estres", "insomnio", "psicologo", "mente", "alucinacion", "bipolar"],
        "otorrinolaringologia": ["oido", "nariz", "garganta", "amigdalas", "otitis", "sinusitis", "audicion", "zumbido", "ronquera"]
    }
    
    # Buscar coincidencia
    for spec_id, keywords in specialties_rules.items():
        if any(k in symptom_lower for k in keywords):
            # Si se detecta dolor de pecho pero también es una emergencia
            is_emergency = emergency_detected or (spec_id == "cardiologia" and "dolor" in symptom_lower)
            return {
                "specialty_id": spec_id,
                "confidence": 0.85 if not is_emergency else 0.95,
                "explanation": f"Se sugiere la especialidad de {spec_id.capitalize()} debido a la mención de síntomas relacionados con: {', '.join([k for k in keywords if k in symptom_lower])}.",
                "emergency_detected": is_emergency,
                "clarifying_question": None
            }
            
    # Fallback por defecto si no hay coincidencia
    return {
        "specialty_id": "medicina_general",
        "confidence": 0.5,
        "explanation": "Los síntomas son generales. Sugerimos una consulta inicial con Medicina General para una evaluación previa.",
        "emergency_detected": emergency_detected,
        "clarifying_question": None
    }

def analyze_symptoms(symptom: str, context: str = None) -> dict:
    """
    Analiza la descripción de los síntomas usando Gemini (preferido),
    OpenAI (fallback) o un motor local basado en reglas (si no hay llaves).
    Combina el contexto anterior si existe una aclaración.
    """
    full_symptom = symptom
    if context:
        full_symptom = f"Síntoma original: {context}. Aclaración del paciente: {symptom}"

    # Si no hay API keys configuradas, usar fallback de inmediato
    if not GEMINI_API_KEY and not OPENAI_API_KEY:
        print("[LLM] No API keys configured. Using local rule-based fallback.")
        return rule_based_fallback(full_symptom)

    # Intentar con Google Gemini
    if GEMINI_API_KEY:
        try:
            print("[LLM] Attempting Google Gemini API...")
            # Intentar importar la nueva biblioteca google-genai
            try:
                from google import genai
                from google.genai import types
                client = genai.Client(api_key=GEMINI_API_KEY)
                response = client.models.generate_content(
                    model='gemini-3.5-flash',
                    contents=full_symptom,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION,
                        response_mime_type="application/json",
                        temperature=0.1,
                    ),
                )
                result_text = response.text
            except ImportError:
                # Usar biblioteca legacy google-generativeai
                import google.generativeai as genai_legacy
                genai_legacy.configure(api_key=GEMINI_API_KEY)
                model = genai_legacy.GenerativeModel(
                    model_name="gemini-3.5-flash",
                    system_instruction=SYSTEM_INSTRUCTION
                )
                response = model.generate_content(
                    full_symptom,
                    generation_config={"response_mime_type": "application/json", "temperature": 0.1}
                )
                result_text = response.text
                
            # Limpiar el formato JSON si viene con markdown ```json ... ```
            result_text = re.sub(r"^```json\s*", "", result_text, flags=re.MULTILINE)
            result_text = re.sub(r"```$", "", result_text, flags=re.MULTILINE).strip()
            
            return json.loads(result_text)
        except Exception as e:
            print(f"[LLM] Gemini API failed: {e}. Falling back to OpenAI or Rules...")

    # Intentar con OpenAI
    if OPENAI_API_KEY:
        try:
            print("[LLM] Attempting OpenAI API...")
            from openai import OpenAI
            client = OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_INSTRUCTION},
                    {"role": "user", "content": full_symptom}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            result_text = response.choices[0].message.content
            return json.loads(result_text)
        except Exception as e:
            print(f"[LLM] OpenAI API failed: {e}. Falling back to Rules...")

    # Fallback final basado en reglas
    print("[LLM] All API requests failed. Using local rule-based fallback.")
    return rule_based_fallback(full_symptom)

if __name__ == "__main__":
    # Test cases for local fallback
    print("Testing vague symptom:")
    print(analyze_symptoms("ayuda"))
    print("\nTesting emergency symptom:")
    print(analyze_symptoms("dolor de pecho fuerte e infarto"))
    print("\nTesting normal symptom:")
    print(analyze_symptoms("me duelen los ojos y veo borroso"))

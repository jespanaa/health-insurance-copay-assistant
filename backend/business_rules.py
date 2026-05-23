import json
from backend.database import get_hospitals_by_city, get_specialty_by_id

def calculate_copay(coinsurance_rate, max_copay_cap, min_copay_floor, total_cost):
    """
    Calcula el copago que debe realizar el paciente basado en las reglas del plan.
    - coinsurance_rate: Tasa de coaseguro (ej. 0.10 para 10% de copago, lo que significa 90% de cobertura)
    - max_copay_cap: Límite máximo de copago que pagará el paciente (cap)
    - min_copay_floor: Límite mínimo de copago que pagará el paciente (floor)
    - total_cost: Costo total de la consulta en el hospital
    """
    # El copago base es la tasa de coaseguro multiplicada por el costo total
    copay = total_cost * coinsurance_rate
    
    # Aplicar el floor (mínimo a pagar) si aplica
    if min_copay_floor > 0 and copay < min_copay_floor:
        copay = min_copay_floor
        
    # Aplicar el cap (máximo a pagar) si aplica
    if max_copay_cap < 9999.0 and copay > max_copay_cap:
        copay = max_copay_cap
        
    # El copago no puede ser mayor que el costo total de la consulta
    if copay > total_cost:
        copay = total_cost
        
    return round(copay, 2)

def rank_hospitals_for_patient(city, specialty_id, plan_details):
    """
    Filtra los hospitales de la red en la ciudad que tengan la especialidad,
    calcula los costos y copagos para cada uno, y los ordena de menor a mayor costo de copago.
    """
    specialty = get_specialty_by_id(specialty_id)
    if not specialty:
        return []
        
    base_cost = specialty['base_consultation_cost']
    hospitals = get_hospitals_by_city(city)
    
    ranked_options = []
    for h in hospitals:
        try:
            supported_specs = json.loads(h['specialties_supported'])
        except Exception:
            supported_specs = []
            
        if specialty_id in supported_specs:
            # Calcular el costo total en este hospital específico
            hosp_cost = round(base_cost * h['cost_factor'], 2)
            
            # Calcular el copago estimado del paciente
            patient_copay = calculate_copay(
                coinsurance_rate=plan_details['coinsurance_rate'],
                max_copay_cap=plan_details['max_copay_cap'],
                min_copay_floor=plan_details['min_copay_floor'],
                total_cost=hosp_cost
            )
            
            # Calcular el monto cubierto por el seguro
            coverage_amt = round(hosp_cost - patient_copay, 2)
            
            # Porcentaje de cobertura real de la transacción
            coverage_percentage = round((coverage_amt / hosp_cost) * 100, 1) if hosp_cost > 0 else 0.0
            
            ranked_options.append({
                "hospital_id": h['hospital_id'],
                "name": h['name'],
                "city": h['city'],
                "total_cost": hosp_cost,
                "estimated_copay": patient_copay,
                "coverage_amount": coverage_amt,
                "coverage_percentage": coverage_percentage
            })
            
    # Ordenar por copago estimado (menor costo para el paciente) y luego por costo total
    ranked_options.sort(key=lambda x: (x['estimated_copay'], x['total_cost']))
    return ranked_options

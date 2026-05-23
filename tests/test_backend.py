import sys
import os
import pytest
from fastapi.testclient import TestClient

# Add parent directory to path so we can import backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app
from backend.database import init_db, get_insured_by_id_and_policy, get_specialty_by_id
from backend.business_rules import calculate_copay, rank_hospitals_for_patient
from backend.llm import rule_based_fallback

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    init_db()

def test_database_initialization():
    specialty = get_specialty_by_id("cardiologia")
    assert specialty is not None
    assert specialty["name_es"] == "Cardiología"
    assert specialty["base_consultation_cost"] == 120.0

def test_insured_retrieval_valid():
    user = get_insured_by_id_and_policy("1712345678", "POL-PLATINUM-001")
    assert user is not None
    assert user["name"] == "Juan Fernando Noboa"
    assert user["plan_id"] == "PLAN_PLATINUM"

def test_insured_retrieval_invalid():
    user = get_insured_by_id_and_policy("1712345678", "POL-WRONG-99")
    assert user is None

def test_copay_calculation_platinum():
    # 10% coinsurance, $20 cap, $0 floor
    # Cost 150 -> 10% is 15 -> should be 15
    assert calculate_copay(0.10, 20.0, 0.0, 150.0) == 15.0
    # Cost 250 -> 10% is 25 -> exceeds cap of 20 -> should be 20
    assert calculate_copay(0.10, 20.0, 0.0, 250.0) == 20.0

def test_copay_calculation_gold():
    # 20% coinsurance, $45 cap, $0 floor
    # Cost 200 -> 20% is 40 -> should be 40
    assert calculate_copay(0.20, 45.0, 0.0, 200.0) == 40.0
    # Cost 300 -> 20% is 60 -> exceeds cap of 45 -> should be 45
    assert calculate_copay(0.20, 45.0, 0.0, 300.0) == 45.0

def test_copay_calculation_basic():
    # 40% coinsurance, no cap (99999.0), $30 floor
    # Cost 50 -> 40% is 20 -> below floor of 30 -> should be 30
    assert calculate_copay(0.40, 99999.0, 30.0, 50.0) == 30.0
    # Cost 200 -> 40% is 80 -> should be 80
    assert calculate_copay(0.40, 99999.0, 30.0, 200.0) == 80.0

def test_hospital_ranking_sorting():
    plan_platinum = {
        "coinsurance_rate": 0.10,
        "max_copay_cap": 20.0,
        "min_copay_floor": 0.0
    }
    ranked = rank_hospitals_for_patient("Quito", "cardiologia", plan_platinum)
    assert len(ranked) > 0
    copays = [h["estimated_copay"] for h in ranked]
    assert copays == sorted(copays)

def test_rule_based_fallback_vague():
    res = rule_based_fallback("ayuda")
    assert res["specialty_id"] == "vague"
    assert res["clarifying_question"] is not None

def test_rule_based_fallback_emergency():
    res = rule_based_fallback("infarto de corazon")
    assert res["emergency_detected"] is True
    assert res["specialty_id"] == "cardiologia"

def test_endpoint_validar_asegurado_valid():
    response = client.post("/api/validar-asegurado", json={
        "national_id": "1712345678",
        "policy_number": "POL-PLATINUM-001"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["insured_name"] == "Juan Fernando Noboa"

def test_endpoint_validar_asegurado_invalid():
    response = client.post("/api/validar-asegurado", json={
        "national_id": "1712345678",
        "policy_number": "POL-INVALID-99"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False

def test_endpoint_estimar_copago_vague():
    response = client.post("/api/estimar-copago", json={
        "national_id": "1712345678",
        "policy_number": "POL-PLATINUM-001",
        "city": "Quito",
        "symptom": "ayuda"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["needs_clarification"] is True
    assert data["specialty"] == "Pendiente de aclaración"

def test_endpoint_estimar_copago_emergency():
    response = client.post("/api/estimar-copago", json={
        "national_id": "1712345678",
        "policy_number": "POL-PLATINUM-001",
        "city": "Quito",
        "symptom": "me duele el pecho y tengo un infarto de corazon"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["emergency_detected"] is True
    assert len(data["hospital_options"]) > 0

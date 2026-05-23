import os
import sqlite3
import json

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DB_PATH = os.path.join(DB_DIR, "insurance.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    # Ensure data directory exists
    os.makedirs(DB_DIR, exist_ok=True)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create Tables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS plan (
        plan_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        coinsurance_rate REAL NOT NULL,
        max_copay_cap REAL NOT NULL,
        min_copay_floor REAL NOT NULL
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS insured (
        national_id TEXT PRIMARY KEY,
        policy_number TEXT NOT NULL,
        name TEXT NOT NULL,
        plan_id TEXT NOT NULL,
        FOREIGN KEY (plan_id) REFERENCES plan (plan_id)
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS specialty (
        specialty_id TEXT PRIMARY KEY,
        name_es TEXT NOT NULL,
        base_consultation_cost REAL NOT NULL
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS hospital (
        hospital_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        city TEXT NOT NULL,
        cost_factor REAL NOT NULL,
        specialties_supported TEXT NOT NULL -- JSON list of specialty_ids
    )
    """)
    
    # Check if we need to seed data
    cursor.execute("SELECT COUNT(*) FROM plan")
    if cursor.fetchone()[0] == 0:
        # Seed Plans
        plans = [
            ("PLAN_PLATINUM", "Plan Platino Seguro", 0.10, 20.0, 0.0),
            ("PLAN_GOLD", "Plan Oro Care", 0.20, 45.0, 0.0),
            ("PLAN_BASIC", "Plan Básico Essential", 0.40, 99999.0, 30.0) # 99999 means no cap
        ]
        cursor.executemany("INSERT INTO plan VALUES (?, ?, ?, ?, ?)", plans)
        
        # Seed Insured Users
        # Ecuadorian ID format (10 digits)
        insured_users = [
            ("1712345678", "POL-PLATINUM-001", "Juan Fernando Noboa", "PLAN_PLATINUM"),
            ("0987654321", "POL-GOLD-002", "María Estela Espinoza", "PLAN_GOLD"),
            ("0102030405", "POL-BASIC-003", "Carlos Andrés Vega", "PLAN_BASIC"),
            ("1723456789", "POL-PLATINUM-004", "Gabriela Sofia Pinto", "PLAN_PLATINUM"),
            ("1804567890", "POL-GOLD-005", "Roberto Xavier Moncayo", "PLAN_GOLD"),
            ("1305678901", "POL-BASIC-006", "Diana Carolina Moreira", "PLAN_BASIC"),
            ("1706789012", "POL-PLATINUM-007", "Mateo Alejandro Castro", "PLAN_PLATINUM"),
            ("0907890123", "POL-GOLD-008", "Lucía Belén Guerrero", "PLAN_GOLD"),
            ("0708901234", "POL-BASIC-009", "José Gabriel Ordóñez", "PLAN_BASIC"),
            ("1109012345", "POL-PLATINUM-010", "Paola Alexandra Torres", "PLAN_PLATINUM")
        ]
        cursor.executemany("INSERT INTO insured VALUES (?, ?, ?, ?)", insured_users)
        
        # Seed Specialties (15 specialties)
        specialties = [
            ("cardiologia", "Cardiología", 120.0),
            ("pediatria", "Pediatría", 60.0),
            ("dermatologia", "Dermatología", 80.0),
            ("traumatologia", "Traumatología", 95.0),
            ("oftalmologia", "Oftalmología", 75.0),
            ("gastroenterologia", "Gastroenterología", 90.0),
            ("medicina_general", "Medicina General", 35.0),
            ("ginecologia", "Ginecología y Obstetricia", 85.0),
            ("neurologia", "Neurología", 110.0),
            ("endocrinologia", "Endocrinología", 85.0),
            ("neumologia", "Neumología", 80.0),
            ("urologia", "Urología", 85.0),
            ("oncologia", "Oncología", 130.0),
            ("psiquiatria", "Psiquiatría", 70.0),
            ("otorrinolaringologia", "Otorrinolaringología", 80.0)
        ]
        cursor.executemany("INSERT INTO specialty VALUES (?, ?, ?)", specialties)
        
        # Seed In-Network Hospitals
        all_specs = [s[0] for s in specialties]
        hospitals = [
            # Quito
            ("hosp_metropolitano_uio", "Hospital Metropolitano", "Quito", 1.4, json.dumps(all_specs)),
            ("hosp_vozandes_uio", "Hospital Vozandes", "Quito", 1.1, json.dumps(["cardiologia", "pediatria", "dermatologia", "medicina_general", "ginecologia", "neurologia", "traumatologia", "urologia"])),
            ("hosp_clinica_pichincha_uio", "Clínica Pichincha", "Quito", 1.2, json.dumps(["medicina_general", "traumatologia", "oftalmologia", "gastroenterologia", "otorrinolaringologia"])),
            # Guayaquil
            ("hosp_clinica_kennedy_gye", "Clínica Kennedy", "Guayaquil", 1.3, json.dumps(all_specs)),
            ("hosp_alcivar_gye", "Hospital Alcívar", "Guayaquil", 1.1, json.dumps(["traumatologia", "medicina_general", "neurologia", "cardiologia", "urologia", "pediatria"])),
            ("hosp_panamericana_gye", "Clínica Panamericana", "Guayaquil", 1.0, json.dumps(["medicina_general", "ginecologia", "gastroenterologia", "neumologia", "psiquiatria"])),
            # Cuenca
            ("hosp_monte_sinai_cue", "Hospital Monte Sinaí", "Cuenca", 1.2, json.dumps(["medicina_general", "cardiologia", "pediatria", "ginecologia", "traumatologia", "dermatologia", "endocrinologia"])),
            ("hosp_santa_ines_cue", "Hospital Santa Inés", "Cuenca", 1.1, json.dumps(["medicina_general", "gastroenterologia", "neurologia", "oftalmologia", "urologia", "otorrinolaringologia"])),
            # Santo Domingo
            ("hosp_espinosa_std", "Clínica de Especialidades Santo Domingo", "Santo Domingo", 0.9, json.dumps(["medicina_general", "pediatria", "ginecologia", "traumatologia", "otorrinolaringologia", "dermatologia"])),
            # Machala
            ("hosp_ciguena_mch", "Clínica La Cigueña", "Machala", 1.0, json.dumps(["traumatologia", "medicina_general", "urologia", "cardiologia"])),
            # Manta
            ("hosp_manta_mta", "Hospital de Especialidades Manta", "Manta", 1.0, json.dumps(["medicina_general", "pediatria", "dermatologia", "gastroenterologia", "oncologia"])),
            # Portoviejo
            ("hosp_san_francisco_pjo", "Clínica San Francisco", "Portoviejo", 0.95, json.dumps(["medicina_general", "pediatria", "ginecologia", "oftalmologia"])),
            # Ambato
            ("hosp_durana_amb", "Hospital Durana", "Ambato", 0.9, json.dumps(["medicina_general", "traumatologia", "cardiologia", "otorrinolaringologia"]))
        ]
        cursor.executemany("INSERT INTO hospital VALUES (?, ?, ?, ?, ?)", hospitals)
        
        conn.commit()
    
    conn.close()

def get_insured_by_id_and_policy(national_id, policy_number):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT i.national_id, i.policy_number, i.name, i.plan_id, p.name as plan_name, p.coinsurance_rate, p.max_copay_cap, p.min_copay_floor
        FROM insured i
        JOIN plan p ON i.plan_id = p.plan_id
        WHERE i.national_id = ? AND i.policy_number = ?
    """, (national_id, policy_number))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_hospitals_by_city(city):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM hospital WHERE city = ?", (city,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_specialty_by_id(specialty_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM specialty WHERE specialty_id = ?", (specialty_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_all_specialties():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM specialty")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_all_cities():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT city FROM hospital ORDER BY city")
    cities = [row[0] for row in cursor.fetchall()]
    conn.close()
    return cities

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
    # Check seed
    insured = get_insured_by_id_and_policy("1712345678", "POL-PLATINUM-001")
    print("Test User Retrieval:", insured)
    print("Test Cities:", get_all_cities())

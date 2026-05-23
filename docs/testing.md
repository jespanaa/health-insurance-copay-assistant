# Documentación de la Suite de Pruebas

Este documento describe la estructura, los comandos de ejecución y los escenarios validados por la suite de pruebas automatizadas del Asistente de Copagos de Seguros de Salud.

---

## 1. Comando de Ejecución de Pruebas

Las pruebas están escritas empleando el framework estándar `pytest`. Para ejecutar la suite de pruebas automatizadas, corra el siguiente comando desde el directorio raíz del proyecto:

```powershell
python -m pytest -v
```

Asegúrese de tener instaladas todas las dependencias del archivo `requirements.txt` antes de ejecutar las pruebas.

---

## 2. Estructura de la Suite de Pruebas

El archivo de pruebas se encuentra en `tests/test_backend.py` y está dividido en las siguientes categorías:
- **Pruebas Unitarias de Base de Datos**: Confirma que las tablas se creen y se pueblen con los registros iniciales esperados.
- **Pruebas Unitarias de Reglas de Negocio**: Verifica el cálculo matemático de las pólizas (coaseguros, topes máximos y mínimos) y el ordenamiento de hospitales.
- **Pruebas Unitarias del Motor Local (Fallback)**: Valida el clasificador local por palabras clave que se ejecuta en ausencia de llaves de API.
- **Pruebas de Integración de API**: Emplea el cliente de pruebas de FastAPI (`TestClient`) para validar los contratos JSON de las rutas HTTP.

---

## 3. Escenarios Validados

### Sembrado de Base de Datos
- **`test_database_initialization`**: Consulta la tabla de especialidades para verificar que las 15 especialidades de la red estén registradas con sus costos base de consulta correctos (por ejemplo, Cardiología configurada en $120.00).

### Consulta de Asegurados
- **`test_insured_retrieval_valid`**: Valida que al buscar una cédula y póliza válidas (ej. `1712345678` / `POL-PLATINUM-001`) se recupere la información correcta del asegurado ("Juan Fernando Noboa", plan "PLAN_PLATINUM").
- **`test_insured_retrieval_invalid`**: Valida que al ingresar credenciales incorrectas, el sistema retorne `None` de forma segura.

### Fórmulas Matemáticas de Copagos
- **`test_copay_calculation_platinum`**: Valida que para el Plan Platino (10% coaseguro, tope de $20, mínimo de $0), una consulta de $150 resulte en un copago de $15 (cálculo porcentual) y una consulta de $250 resulte en un copago de $20 (aplicación del tope máximo).
- **`test_copay_calculation_gold`**: Valida que para el Plan Oro (20% coaseguro, tope de $45, mínimo de $0), una consulta de $200 resulte en un copago de $40 y una de $300 resulte en un copago de $45 (aplicación del tope máximo).
- **`test_copay_calculation_basic`**: Valida que para el Plan Básico (40% coaseguro, sin tope, mínimo de $30), una consulta de $50 resulte en un copago de $30 (aplicación del pago mínimo) y una consulta de $200 resulte en un copago de $80.

### Ordenamiento de Hospitales (Ranking)
- **`test_hospital_ranking_sorting`**: Calcula la red de Cardiología para un asegurado en la ciudad de Quito. Confirma que la lista de hospitales devuelta esté clasificada de forma estrictamente ascendente por el costo del copago del paciente.

### Motor de Reglas Local (Fallback)
- **`test_rule_based_fallback_vague`**: Evalúa una frase vaga como "ayuda" y confirma que el motor local de contingencia devuelva la clasificación `"vague"` junto con una pregunta aclaratoria en español.
- **`test_rule_based_fallback_emergency`**: Evalúa una frase urgente como "infarto de corazon" y confirma que active la bandera de emergencia y clasifique la consulta en la especialidad de `"cardiologia"`.

### Rutas HTTP de la API (Integración)
- **`test_endpoint_validar_asegurado_valid`**: Simula una petición POST a `/api/validar-asegurado` con credenciales correctas y verifica el retorno de `success: true`.
- **`test_endpoint_validar_asegurado_invalid`**: Simulates una petición con datos erróneos y confirma la respuesta `success: false`.
- **`test_endpoint_estimar_copago_vague`**: Envía un síntoma ambiguo a `/api/estimar-copago` y confirma que la API responda solicitando aclaración (`needs_clarification: true`).
- **`test_endpoint_estimar_copago_emergency`**: Envía un síntoma crítico y verifica que la API responda activando la alerta de emergencia (`emergency_detected: true`).

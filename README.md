# Asistente de Copagos de Seguros de Salud - Especificación Técnica

Este repositorio contiene el Producto Mínimo Viable (MVP) para el desafío de hackathon "Estimador Agéntico de Copago y Cobertura para el Paciente". La solución calcula la cobertura de seguros, estima los copagos de los pacientes y recomienda hospitales de la red en convenio en Ecuador a partir de la descripción de síntomas en lenguaje natural.

---

## 1. Resumen del Proyecto y Contexto del Desafío

En los sistemas de salud, los pacientes suelen tener dificultades para entender los beneficios de sus pólizas, predecir el costo de una consulta y encontrar proveedores de la red que ofrezcan la mejor relación de costos. Esta solución resuelve ese problema mediante una aplicación web interactiva que:
- Valida la identidad del paciente y extrae los detalles del plan de su póliza.
- Traduce los síntomas descritos en lenguaje natural a especialidades médicas específicas.
- Aplica reglas de negocio deterministas para calcular el copago exacto.
- Ordena y recomienda los hospitales de la red en la ciudad del usuario de menor a mayor costo de copago.
- Identifica alertas de emergencia y ejecuta flujos interactivos de aclaración para síntomas vagos.

---

## 2. Características Principales

- **Validación de Identidad**: Comprueba la cédula ecuatoriana y el número de póliza contra una base de datos local para cargar el perfil del asegurado.
- **Clasificación de Síntomas**: Emplea inteligencia artificial (Google Gemini 3.5 Flash) para mapear descripciones de síntomas a una de 15 especialidades médicas disponibles.
- **Flujo Conversacional de Aclaración**: Si la descripción es ambigua (por ejemplo, "me duele"), el sistema solicita más detalles específicos mediante una interfaz interactiva de chat.
- **Detección de Emergencias**: Identifica síntomas de riesgo vital inmediato y emite alertas de alta prioridad para instar al usuario a acudir a urgencias o llamar al 911.
- **Cálculo Determinista de Copagos**: Realiza todas las operaciones aritméticas en código Python, evitando las alucinaciones numéricas de los modelos de lenguaje.
- **Ranking de la Red en Convenio**: Filtra y ordena los proveedores activos de la red por menor copago para el paciente en la ciudad elegida.
- **Historial de Consultas**: Almacena las consultas previas de forma local (`localStorage`) para permitir re-ejecutar búsquedas con un solo clic.

---

## 3. Arquitectura y División de Tareas (IA vs. Código)

El sistema impone un límite estricto entre el procesamiento probabilístico de la inteligencia artificial y el cálculo financiero determinista:

- **Procesamiento por Inteligencia Artificial (IA)**:
  - Analiza e interpreta los síntomas redactados de forma libre.
  - Genera un objeto JSON estructurado con la especialidad recomendada (`specialty_id`), confianza, indicador de emergencia y pregunta aclaratoria si aplica.
  - Redacta una explicación médica breve y empática en español sobre la recomendación.
- **Procesamiento Determinista (Python y SQLite)**:
  - Recupera los coeficientes del plan del asegurado (coaseguro, tope de copago y deducible mínimo) desde la base de datos local.
  - Multiplica el costo base de la especialidad por el factor de costo específico del hospital para obtener el costo total de la consulta.
  - Aplica las reglas del plan del asegurado para calcular el copago y la cobertura.
  - Ordena la lista de hospitales y devuelve los resultados ordenados.

Los diagramas de secuencia detallados se encuentran en el archivo de arquitectura: [architecture.md](./docs/architecture.md).

---

## 4. Modelo Matemático y Criterios de Ordenamiento

### Fórmula de Cálculo de Copago
Sea $C_{base}$ el costo base de la consulta para la especialidad médica inferida.
Sea $F_{hosp}$ el factor de costo asignado a un hospital en convenio.
El costo total de la consulta en ese hospital se define como:

$$\text{Costo Total} = C_{base} \times F_{hosp}$$

El copago del paciente se calcula aplicando los parámetros de su plan contratado:
- **Plan Platino**: Coaseguro del 10%, con un tope máximo (cap) de copago de $20.00 por consulta.
  $$\text{Copago} = \min(\text{Costo Total} \times 0.10, 20.00)$$
- **Plan Oro**: Coaseguro del 20%, con un tope máximo (cap) de copago de $45.00 por consulta.
  $$\text{Copago} = \min(\text{Costo Total} \times 0.20, 45.00)$$
- **Plan Básico**: Coaseguro del 40%, con un pago mínimo obligatorio (floor) de $30.00 por consulta.
  $$\text{Copago} = \max(\text{Costo Total} \times 0.40, 30.00)$$
  *Nota: Si el copago calculado bajo cualquier plan supera el Costo Total de la consulta, dicho copago se ajusta al Costo Total.*

### Criterio de Ordenamiento de Hospitales
Los proveedores de salud se listan en orden de conveniencia empleando dos criterios de ordenamiento sucesivos:
1. **Criterio Principal**: Copago Estimado del Paciente (de menor a mayor costo out-of-pocket).
2. **Criterio Secundario**: Costo Total de la Consulta (de menor a mayor, para favorecer el ahorro de la aseguradora ante copagos idénticos debido a topes o mínimos).

---

## 5. Catálogo de Datos de Prueba

La base de datos local se inicializa y semilla automáticamente con registros simulados de Ecuador. Los listados completos de datos están detallados en el catálogo de datos: [sample-data.md](./docs/sample-data.md).

### Credenciales de Asegurados (Paso 1)
| Identificación (Cédula) | Número de Póliza | Nombre del Asegurado | Tipo de Plan | Cobertura del Plan |
| :--- | :--- | :--- | :--- | :--- |
| `1712345678` | `POL-PLATINUM-001` | Juan Fernando Noboa | Platino | 10% Coaseguro, Tope máximo $20 |
| `0987654321` | `POL-GOLD-002` | María Estela Espinoza | Oro | 20% Coinsurance, Tope máximo $45 |
| `0102030405` | `POL-BASIC-003` | Carlos Andrés Vega | Básico | 40% Coaseguro, Mínimo de copago $30 |

### Ciudades Soportadas
- Quito, Guayaquil, Cuenca, Santo Domingo, Machala, Manta, Portoviejo y Ambato.

---

## 6. Especificación de Rutas de la API

### 1. `GET /api/ciudades`
Retorna la lista de ciudades disponibles en la red.
- **Respuesta (200 OK)**: `["Ambato", "Cuenca", "Guayaquil", "Machala", "Manta", "Portoviejo", "Quito", "Santo Domingo"]`

### 2. `POST /api/validar-asegurado`
Valida si la combinación de identificación y número de póliza existe en la base de datos.
- **Cuerpo de la Petición**:
  ```json
  {
    "national_id": "1712345678",
    "policy_number": "POL-PLATINUM-001"
  }
  ```
- **Respuesta (Éxito)**:
  ```json
  {
    "success": true,
    "message": "Asegurado validado correctamente.",
    "insured_name": "Juan Fernando Noboa",
    "plan_name": "Plan Platino Seguro"
  }
  ```

### 3. `POST /api/estimar-copago`
Clasifica síntomas, comprueba alertas de emergencia y genera copagos detallados por hospital.
- **Cuerpo de la Petición**:
  ```json
  {
    "national_id": "1712345678",
    "policy_number": "POL-PLATINUM-001",
    "city": "Quito",
    "symptom": "Tengo un dolor muy fuerte en el pecho que se me pasa al brazo",
    "clarification_answer": null,
    "previous_symptom": null
  }
  ```
- **Respuesta (Emergencia Detectada)**:
  ```json
  {
    "specialty": "Cardiología",
    "confidence": 0.95,
    "coverage_percentage": 90.0,
    "estimated_copay": 13.2,
    "best_hospital": "Hospital Vozandes",
    "hospital_options": [
      {
        "hospital_id": "hosp_vozandes_uio",
        "name": "Hospital Vozandes",
        "city": "Quito",
        "total_cost": 132.0,
        "estimated_copay": 13.2,
        "coverage_amount": 118.8,
        "coverage_percentage": 90.0
      },
      {
        "hospital_id": "hosp_metropolitano_uio",
        "name": "Hospital Metropolitano",
        "city": "Quito",
        "total_cost": 168.0,
        "estimated_copay": 16.8,
        "coverage_amount": 151.2,
        "coverage_percentage": 90.0
      }
    ],
    "explanation": "Se sugiere la especialidad de Cardiologia debido a dolor de pecho con posible alerta cardiovascular.",
    "needs_clarification": false,
    "clarifying_question": null,
    "emergency_detected": true,
    "disclaimer": "Estimación informativa preliminar, no constituye una autorización de cobertura ni costo final por parte de la aseguradora."
  }
  ```

---

## 7. Supuestos, Casos Borde y Respuestas de Seguridad

### Supuestos del Sistema
1. Los síntomas se ingresan en idioma español.
2. Los factores de costo de los hospitales multiplican la tarifa base de consulta de las especialidades.

### Mecanismos de Robustez
- **Triage de Fallback Local**: Si la clave de la API del LLM no está configurada o si las llamadas a la API fallan, el servidor conmuta de manera invisible al motor de coincidencia léxica basado en expresiones regulares, garantizando que el servicio continúe disponible.
- **Derivación por Baja Confianza**: Si el LLM no logra identificar una especialidad clara (confianza menor al 50%), la petición se deriva automáticamente a **Medicina General** para una evaluación de seguridad inicial.
- **Loop de Aclaración**: Si la descripción es vaga, la API responde indicando que requiere aclaración. La interfaz web congela el formulario y despliega un chat donde el usuario puede responder la pregunta aclaratoria.
- **Especialidad no Disponible en Ciudad**: Si no hay proveedores de una especialidad en la ciudad indicada, el sistema busca alternativas de **Medicina General** en esa ubicación para garantizar opciones de atención.

---

## 8. Guía de Configuración y Ejecución Local

### Paso 1: Configurar Variables de Entorno
Cree un archivo `.env` en la raíz del proyecto basándose en `.env.example` e ingrese sus claves de API:
```env
PORT=8000
GEMINI_API_KEY=su_clave_api_de_google_gemini
OPENAI_API_KEY=su_clave_api_de_openai
```
*Nota: Si no se definen claves de API, el backend utilizará de forma automática el motor de clasificación local basado en expresiones regulares, asegurando el funcionamiento sin conexión.*

### Paso 2: Instalar Dependencias
Instale los paquetes requeridos mediante pip:
```bash
pip install -r requirements.txt
```

### Paso 3: Ejecutar la Suite de Pruebas
Valide el correcto funcionamiento de los cálculos de coaseguros, límites, ordenamiento de la red de hospitales y los endpoints ejecutando:
```bash
python -m pytest -v
```
Para más información sobre los casos de prueba, consulte [testing.md](./docs/testing.md).

### Paso 4: Iniciar el Servidor Local
Levante el servidor web de desarrollo con Uvicorn:
```bash
python -m uvicorn backend.main:app --reload --port 8000
```
Acceda a la aplicación en su navegador a través de la dirección: [http://localhost:8000](http://localhost:8000).


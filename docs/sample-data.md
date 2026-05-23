# Catálogo de Datos de Prueba de la Base de Datos

Este documento detalla toda la información pre-sembrada en la base de datos local SQLite (`data/insurance.db`). La base de datos se crea y se pobla automáticamente la primera vez que se inicia el servidor backend.

---

## 1. Planes de Seguro de Salud

El sistema administra tres niveles de planes de seguro de salud, cada uno con diferentes tasas de coaseguro, topes máximos de copago (caps) y pagos mínimos obligatorios (floors).

| ID del Plan | Nombre del Plan | Tasa de Coaseguro | Tope Máximo (Cap) | Mínimo Obligatorio (Floor) | Notas |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **PLAN_PLATINUM** | Plan Platino Seguro | 10% (0.10) | $20.00 | $0.00 | Cobertura alta, copago máximo de $20 |
| **PLAN_GOLD** | Plan Oro Care | 20% (0.20) | $45.00 | $0.00 | Cobertura media-alta, copago máximo de $45 |
| **PLAN_BASIC** | Plan Básico Essential | 40% (0.40) | Sin tope ($99,999.00) | $30.00 | Cobertura baja, pago mínimo de $30 |

---

## 2. Asegurados de Prueba

Estos usuarios simulados pueden emplearse para superar el Paso 1 de validación en la interfaz web. El número de identificación corresponde a formatos de cédulas de Ecuador (10 dígitos).

| Identificación (Cédula) | Número de Póliza | Nombre del Asegurado | ID del Plan | Nombre del Plan Asociado |
| :--- | :--- | :--- | :--- | :--- |
| `1712345678` | `POL-PLATINUM-001` | Juan Fernando Noboa | PLAN_PLATINUM | Plan Platino Seguro |
| `0987654321` | `POL-GOLD-002` | María Estela Espinoza | PLAN_GOLD | Plan Oro Care |
| `0102030405` | `POL-BASIC-003` | Carlos Andrés Vega | PLAN_BASIC | Plan Básico Essential |
| `1723456789` | `POL-PLATINUM-004` | Gabriela Sofia Pinto | PLAN_PLATINUM | Plan Platino Seguro |
| `1804567890` | `POL-GOLD-005` | Roberto Xavier Moncayo | PLAN_GOLD | Plan Oro Care |
| `1305678901` | `POL-BASIC-006` | Diana Carolina Moreira | PLAN_BASIC | Plan Básico Essential |
| `1706789012` | `POL-PLATINUM-007` | Mateo Alejandro Castro | PLAN_PLATINUM | Plan Platino Seguro |
| `0907890123` | `POL-GOLD-008` | Lucía Belén Guerrero | PLAN_GOLD | Plan Oro Care |
| `0708901234` | `POL-BASIC-009` | José Gabriel Ordóñez | PLAN_BASIC | Plan Básico Essential |
| `1109012345` | `POL-PLATINUM-010` | Paola Alexandra Torres | PLAN_PLATINUM | Plan Platino Seguro |

---

## 3. Especialidades Médicas

Cada especialidad está configurada en el sistema con un costo base estandarizado para la consulta de consulta externa.

| ID de Especialidad | Nombre en Español (ES) | Costo Base de la Consulta |
| :--- | :--- | :--- |
| `cardiologia` | Cardiología | $120.00 |
| `pediatria` | Pediatría | $60.00 |
| `dermatologia` | Dermatología | $80.00 |
| `traumatologia` | Traumatología | $95.00 |
| `oftalmologia` | Oftalmología | $75.00 |
| `gastroenterologia` | Gastroenterología | $90.00 |
| `medicina_general` | Medicina General | $35.00 |
| `ginecologia` | Ginecología y Obstetricia | $85.00 |
| `neurologia` | Neurología | $110.00 |
| `endocrinologia` | Endocrinología | $85.00 |
| `neumologia` | Neumología | $80.00 |
| `urologia` | Urología | $85.00 |
| `oncologia` | Oncología | $130.00 |
| `psiquiatria` | Psiquiatría | $70.00 |
| `otorrinolaringologia` | Otorrinolaringología | $80.00 |

---

## 4. Hospitales de la Red en Convenio

Los centros de salud representan los hospitales en convenio en Ecuador. Cada hospital cuenta con un factor multiplicador de costo que escala la tarifa base de la especialidad. Si un hospital no cubre una especialidad específica, se omite de la lista de opciones.

| ID de Hospital | Nombre del Hospital | Ciudad | Factor de Costo | Especialidades Cubiertas |
| :--- | :--- | :--- | :--- | :--- |
| `hosp_metropolitano_uio` | Hospital Metropolitano | Quito | 1.4 | Las 15 especialidades |
| `hosp_vozandes_uio` | Hospital Vozandes | Quito | 1.1 | cardiologia, pediatria, dermatologia, medicina_general, ginecologia, neurologia, traumatologia, urologia |
| `hosp_clinica_pichincha_uio` | Clínica Pichincha | Quito | 1.2 | medicina_general, traumatologia, oftalmologia, gastroenterologia, otorrinolaringologia |
| `hosp_clinica_kennedy_gye` | Clínica Kennedy | Guayaquil | 1.3 | Las 15 especialidades |
| `hosp_alcivar_gye` | Hospital Alcívar | Guayaquil | 1.1 | traumatologia, medicina_general, neurologia, cardiologia, urologia, pediatria |
| `hosp_panamericana_gye` | Clínica Panamericana | Guayaquil | 1.0 | medicina_general, ginecologia, gastroenterologia, neumologia, psiquiatria |
| `hosp_monte_sinai_cue` | Hospital Monte Sinaí | Cuenca | 1.2 | medicina_general, cardiologia, pediatria, ginecologia, traumatologia, dermatologia, endocrinologia |
| `hosp_santa_ines_cue` | Hospital Santa Inés | Cuenca | 1.1 | medicina_general, gastroenterologia, neurologia, oftalmologia, urologia, otorrinolaringologia |
| `hosp_espinosa_std` | Clínica de Especialidades Santo Domingo | Santo Domingo | 0.9 | medicina_general, pediatria, ginecologia, traumatologia, otorrinolaringologia, dermatologia |
| `hosp_ciguena_mch` | Clínica La Cigueña | Machala | 1.0 | traumatologia, medicina_general, urologia, cardiologia |
| `hosp_manta_mta` | Hospital de Especialidades Manta | Manta | 1.0 | medicina_general, pediatria, dermatologia, gastroenterologia, oncologia |
| `hosp_san_francisco_pjo` | Clínica San Francisco | Portoviejo | 0.95 | medicina_general, pediatria, ginecologia, oftalmologia |
| `hosp_durana_amb` | Hospital Durana | Ambato | 0.9 | medicina_general, traumatologia, cardiologia, otorrinolaringologia |

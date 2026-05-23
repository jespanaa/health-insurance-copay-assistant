// Health Insurance Copay Assistant - Frontend Application Logic

// API Configuration
const API_BASE_URL = "/api";

// App State
let authenticatedUser = null; // Stores { nationalId, policyNumber, name, planName }
let previousSymptomContext = null; // Stores the original vague symptom for clarification loops

// DOM Elements
const loginForm = document.getElementById("login-form");
const nationalIdInput = document.getElementById("national-id");
const policyNumberInput = document.getElementById("policy-number");
const userProfile = document.getElementById("user-profile");
const profileName = document.getElementById("profile-name");
const profilePlan = document.getElementById("profile-plan");
const btnLogout = document.getElementById("btn-logout");

const estimatorCard = document.getElementById("estimator-card");
const estimatorLockOverlay = document.getElementById("estimator-lock-overlay");
const estimatorForm = document.getElementById("estimator-form");
const citySelector = document.getElementById("city-selector");
const symptomText = document.getElementById("symptom-text");
const btnEstimate = document.getElementById("btn-estimate");

const clarificationContainer = document.getElementById("clarification-container");
const clarificationPromptText = document.getElementById("clarification-prompt-text");
const clarificationAnswerInput = document.getElementById("clarification-answer");
const btnSubmitClarification = document.getElementById("btn-submit-clarification");
const btnCancelClarification = document.getElementById("btn-cancel-clarification");

const emergencyAlert = document.getElementById("emergency-alert");
const resultsCard = document.getElementById("results-card");
const resultsPlaceholder = document.getElementById("results-placeholder");
const resultsContent = document.getElementById("results-content");

const resSpecialty = document.getElementById("res-specialty");
const resConfidenceBar = document.getElementById("res-confidence-bar");
const resConfidenceText = document.getElementById("res-confidence-text");
const resCopay = document.getElementById("res-copay");
const resCoverage = document.getElementById("res-coverage");
const resExplanation = document.getElementById("res-explanation");
const resCity = document.getElementById("res-city");
const resHospitalsList = document.getElementById("res-hospitals-list");
const resDisclaimer = document.getElementById("res-disclaimer");

const historyList = document.getElementById("history-list");
const btnClearHistory = document.getElementById("btn-clear-history");

// ==========================================================================
// INIT APP
// ==========================================================================
document.addEventListener("DOMContentLoaded", () => {
    loadCities();
    loadSearchHistory();
    setupEventListeners();
});

// ==========================================================================
// API CALLS
// ==========================================================================

// Fetch Ecuadorian cities from Backend
async function loadCities() {
    try {
        const response = await fetch(`${API_BASE_URL}/ciudades`);
        if (!response.ok) throw new Error("No se pudieron cargar las ciudades.");
        const cities = await response.json();
        
        citySelector.innerHTML = '<option value="" disabled selected>Selecciona tu ciudad...</option>';
        cities.forEach(city => {
            const option = document.createElement("option");
            option.value = city;
            option.textContent = city;
            citySelector.appendChild(option);
        });
    } catch (error) {
        console.error("Error loading cities:", error);
        showToast("Error de conexión al cargar ciudades.", "error");
    }
}

// Perform Insured User Validation
async function validateInsured(nationalId, policyNumber) {
    showLoadingButton(loginForm.querySelector("button[type='submit']"), true, "Verificando...");
    
    try {
        const response = await fetch(`${API_BASE_URL}/validar-asegurado`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                national_id: nationalId,
                policy_number: policyNumber
            })
        });

        if (!response.ok) throw new Error("Error en el servidor de validación.");
        
        const data = await response.json();
        
        if (data.success) {
            authenticatedUser = {
                nationalId: nationalId.trim(),
                policyNumber: policyNumber.trim(),
                name: data.insured_name,
                planName: data.plan_name
            };
            
            // UI Updates
            loginForm.classList.add("hidden");
            profileName.textContent = data.insured_name;
            profilePlan.innerHTML = `<i class="fa-solid fa-crown text-gold"></i> ${data.plan_name}`;
            userProfile.classList.remove("hidden");
            
            // Unlock Estimator
            estimatorCard.classList.remove("locked");
            estimatorLockOverlay.classList.add("hidden");
            
            showToast("Asegurado verificado con éxito.", "success");
        } else {
            showToast(data.message, "error");
        }
    } catch (error) {
        console.error("Validation error:", error);
        showToast("Error al conectar con el servidor.", "error");
    } finally {
        showLoadingButton(loginForm.querySelector("button[type='submit']"), false, "Verificar Póliza");
    }
}

// Perform Copay and Coverage Estimation
async function estimateCopay(payload) {
    showLoadingButton(btnEstimate, true, "Analizando...");
    
    try {
        const response = await fetch(`${API_BASE_URL}/estimar-copago`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || "Error en el cálculo del estimado.");
        }
        
        const result = await response.json();
        
        if (result.needs_clarification) {
            // Show Clarification UI and lock main inputs
            clarificationPromptText.textContent = result.clarifying_question;
            clarificationContainer.classList.remove("hidden");
            estimatorForm.querySelector("button[type='submit']").classList.add("hidden");
            symptomText.disabled = true;
            citySelector.disabled = true;
            previousSymptomContext = payload.symptom; // Save original symptom
            
            // Scroll clarification box into view
            clarificationContainer.scrollIntoView({ behavior: "smooth" });
        } else {
            // Render regular results
            renderResults(result, payload.city);
            
            // Add to localStorage History
            saveToHistory({
                symptom: previousSymptomContext || payload.symptom,
                clarification: payload.clarification_answer || null,
                specialty: result.specialty,
                copay: result.estimated_copay,
                city: payload.city,
                date: new Date().toLocaleDateString("es-EC")
            });
            
            // Reset clarification loop state
            resetClarificationUI();
        }
    } catch (error) {
        console.error("Estimation error:", error);
        showToast(error.message || "Error al calcular el estimado.", "error");
    } finally {
        showLoadingButton(btnEstimate, false, "Calcular Cobertura");
    }
}

// ==========================================================================
// RENDER METHODS
// ==========================================================================

function renderResults(data, city) {
    resultsPlaceholder.classList.add("hidden");
    resultsContent.classList.remove("hidden");
    
    // Set Fields
    resSpecialty.textContent = data.specialty;
    resConfidenceText.textContent = `${Math.round(data.confidence * 100)}%`;
    resConfidenceBar.style.width = `${data.confidence * 100}%`;
    resExplanation.textContent = data.explanation;
    resCity.textContent = city;
    resDisclaimer.textContent = data.disclaimer;
    
    // Check Emergency
    if (data.emergency_detected) {
        emergencyAlert.classList.remove("hidden");
        emergencyAlert.scrollIntoView({ behavior: "smooth", block: "center" });
    } else {
        emergencyAlert.classList.add("hidden");
    }

    // Best Copay amount
    if (data.hospital_options.length > 0) {
        resCopay.textContent = `$${data.estimated_copay.toFixed(2)}`;
        resCoverage.textContent = `Póliza cubre el ${data.coverage_percentage}%`;
    } else {
        resCopay.textContent = "N/A";
        resCoverage.textContent = "Sin cobertura de red";
    }

    // Render Hospitals list
    resHospitalsList.innerHTML = "";
    if (data.hospital_options.length === 0) {
        resHospitalsList.innerHTML = `
            <div class="results-placeholder">
                <i class="fa-solid fa-hospital-user placeholder-icon"></i>
                <p>No se encontraron hospitales con convenio disponibles en esta ciudad para la especialidad requerida.</p>
            </div>
        `;
        return;
    }

    data.hospital_options.forEach((hosp, index) => {
        const isCheapest = (index === 0);
        const card = document.createElement("div");
        card.className = `hospital-item ${isCheapest ? 'cheapest' : ''}`;
        
        card.innerHTML = `
            <div class="hospital-main">
                <div class="hospital-name">
                    ${isCheapest ? '<i class="fa-solid fa-circle-check text-cyan" style="margin-right: 4px;"></i>' : ''} 
                    ${hosp.name}
                </div>
                <div class="hospital-city"><i class="fa-solid fa-location-dot"></i> ${hosp.city} (Convenio Activo)</div>
            </div>
            <div class="hospital-pricing">
                <div class="patient-copay-amount">$${hosp.estimated_copay.toFixed(2)}</div>
                <div class="total-hosp-cost">Costo total: $${hosp.total_cost.toFixed(2)}</div>
            </div>
            <div class="hospital-coverage-detail">
                <div class="cov-bar">
                    <div class="cov-fill" style="width: ${hosp.coverage_percentage}%; background-color: ${isCheapest ? 'var(--success)' : 'var(--primary)'}"></div>
                </div>
                <span class="cov-text">Cobertura: ${hosp.coverage_percentage}% (Ahorro: $${hosp.coverage_amount.toFixed(2)})</span>
            </div>
        `;
        resHospitalsList.appendChild(card);
    });
    
    // Scroll results card into view
    resultsCard.scrollIntoView({ behavior: "smooth" });
}

function resetClarificationUI() {
    clarificationContainer.classList.add("hidden");
    estimatorForm.querySelector("button[type='submit']").classList.remove("hidden");
    symptomText.disabled = false;
    citySelector.disabled = false;
    clarificationAnswerInput.value = "";
    previousSymptomContext = null;
}

// ==========================================================================
// LOCAL STORAGE HISTORY
// ==========================================================================

function saveToHistory(query) {
    let history = JSON.parse(localStorage.getItem("copay_history")) || [];
    // Filter duplicates of same symptom
    history = history.filter(item => item.symptom.toLowerCase() !== query.symptom.toLowerCase());
    // Insert at front
    history.unshift(query);
    // Keep max 5
    if (history.length > 5) history.pop();
    
    localStorage.setItem("copay_history", JSON.stringify(history));
    renderHistory(history);
}

function loadSearchHistory() {
    const history = JSON.parse(localStorage.getItem("copay_history")) || [];
    renderHistory(history);
}

function renderHistory(history) {
    historyList.innerHTML = "";
    if (history.length === 0) {
        historyList.innerHTML = '<p class="history-placeholder">No hay consultas recientes.</p>';
        return;
    }

    history.forEach(item => {
        const div = document.createElement("div");
        div.className = "history-item";
        div.innerHTML = `
            <div class="history-info">
                <div class="history-symptom" title="${item.symptom}">${item.symptom}</div>
                <div class="history-meta">
                    <span><i class="fa-solid fa-location-dot"></i> ${item.city}</span>
                    <span><i class="fa-solid fa-calendar"></i> ${item.date}</span>
                </div>
            </div>
            <div class="history-badge">${item.specialty}</div>
        `;
        
        div.addEventListener("click", () => {
            if (!authenticatedUser) {
                showToast("Por favor, valide su identidad primero para repetir la consulta.", "warning");
                nationalIdInput.focus();
                return;
            }
            
            // Popule inputs
            citySelector.value = item.city;
            symptomText.value = item.symptom;
            
            // Reset clarification loop state
            resetClarificationUI();
            
            // Auto submit
            triggerEstimation();
        });
        
        historyList.appendChild(div);
    });
}

// ==========================================================================
// EVENT LISTENERS
// ==========================================================================

function setupEventListeners() {
    // Paso 1 Form Submission
    loginForm.addEventListener("submit", (e) => {
        e.preventDefault();
        validateInsured(nationalIdInput.value, policyNumberInput.value);
    });

    // Change Assured / Logout
    btnLogout.addEventListener("click", () => {
        authenticatedUser = null;
        userProfile.classList.add("hidden");
        loginForm.classList.remove("hidden");
        loginForm.reset();
        
        // Lock Estimator
        estimatorCard.classList.add("locked");
        estimatorLockOverlay.classList.remove("hidden");
        estimatorForm.reset();
        
        // Clear results
        clearResults();
        resetClarificationUI();
    });

    // Paso 2 Form Submission
    estimatorForm.addEventListener("submit", (e) => {
        e.preventDefault();
        triggerEstimation();
    });

    // Clarification Submissions
    btnSubmitClarification.addEventListener("click", () => {
        const answer = clarificationAnswerInput.value.strip ? clarificationAnswerInput.value.strip() : clarificationAnswerInput.value.trim();
        if (!answer) {
            showToast("Por favor ingrese su aclaración médica.", "warning");
            clarificationAnswerInput.focus();
            return;
        }

        const payload = {
            national_id: authenticatedUser.nationalId,
            policy_number: authenticatedUser.policyNumber,
            city: citySelector.value,
            symptom: previousSymptomContext,
            clarification_answer: answer,
            previous_symptom: previousSymptomContext
        };
        
        estimateCopay(payload);
    });

    btnCancelClarification.addEventListener("click", () => {
        resetClarificationUI();
    });

    // Clear History
    btnClearHistory.addEventListener("click", () => {
        localStorage.removeItem("copay_history");
        renderHistory([]);
        showToast("Historial borrado.", "success");
    });
}

function triggerEstimation() {
    if (!authenticatedUser) {
        showToast("Error de seguridad: Asegurado no validado.", "error");
        return;
    }

    const payload = {
        national_id: authenticatedUser.nationalId,
        policy_number: authenticatedUser.policyNumber,
        city: citySelector.value,
        symptom: symptomText.value.trim()
    };

    estimateCopay(payload);
}

function clearResults() {
    resultsContent.classList.add("hidden");
    resultsPlaceholder.classList.remove("hidden");
    emergencyAlert.classList.add("hidden");
}

// ==========================================================================
// HELPER UI FUNCTIONS
// ==========================================================================

function showLoadingButton(buttonEl, isLoading, text) {
    const textEl = buttonEl.querySelector(".btn-text");
    const iconEl = buttonEl.querySelector(".btn-icon");
    
    if (isLoading) {
        buttonEl.disabled = true;
        if (textEl) textEl.textContent = text;
        if (iconEl) {
            iconEl.className = "fa-solid fa-spinner fa-spin btn-icon";
        }
    } else {
        buttonEl.disabled = false;
        if (textEl) textEl.textContent = text;
        if (iconEl) {
            // Restore icon by restoring standard classes
            if (buttonEl.id === "btn-estimate") {
                iconEl.className = "fa-solid fa-wand-magic-sparkles btn-icon";
            } else if (buttonEl.id === "btn-submit-clarification") {
                iconEl.className = "";
            } else {
                iconEl.className = "fa-solid fa-shield-halved btn-icon";
            }
        }
    }
}

// Simple Toast Notification Implementation
function showToast(message, type = "success") {
    // Remove existing toast if any
    const existingToast = document.querySelector(".toast-notification");
    if (existingToast) existingToast.remove();

    const toast = document.createElement("div");
    toast.className = `toast-notification toast-${type}`;
    
    let iconClass = "fa-circle-check";
    if (type === "error") iconClass = "fa-circle-xmark";
    if (type === "warning") iconClass = "fa-triangle-exclamation";
    
    toast.innerHTML = `
        <i class="fa-solid ${iconClass} toast-icon"></i>
        <span>${message}</span>
    `;
    
    document.body.appendChild(toast);
    
    // Trigger entrance animation
    setTimeout(() => toast.classList.add("show"), 10);
    
    // Remove after 4 seconds
    setTimeout(() => {
        toast.classList.remove("show");
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// Append Toast Style dynamically
const toastStyle = document.createElement("style");
toastStyle.textContent = `
.toast-notification {
    position: fixed;
    top: 24px;
    right: 24px;
    padding: 14px 20px;
    border-radius: var(--border-radius-md);
    background: rgba(15, 23, 42, 0.9);
    backdrop-filter: blur(12px);
    border: 1px solid var(--border-color);
    color: var(--text-primary);
    display: flex;
    align-items: center;
    gap: 10px;
    z-index: 9999;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4);
    transform: translateY(-20px);
    opacity: 0;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    font-family: var(--font-body);
    font-size: 0.85rem;
}
.toast-notification.show {
    transform: translateY(0);
    opacity: 1;
}
.toast-icon {
    font-size: 1.1rem;
}
.toast-success { border-color: rgba(16, 185, 129, 0.3); color: var(--success); }
.toast-error { border-color: rgba(239, 68, 68, 0.3); color: var(--danger); }
.toast-warning { border-color: rgba(245, 158, 11, 0.3); color: var(--warning); }
`;
document.head.appendChild(toastStyle);

/**
 * MeterVision Installer App
 * Mobile-first installation wizard with AI discovery and calibration
 */

// API Configuration
const API_URL = '';  // Same origin
let authToken = localStorage.getItem('installer_token');
let currentUser = null;
let selectedOrganization = null;
let currentStep = 1;
let qrScanner = null;

// Installation State
const installationData = {
    cameraSerial: null,
    meterSerial: null,
    meterType: null,
    meterUnit: null,
    expectedReading: null,
    meterLocation: null,
    organizationId: null,
    sessionId: null
};

// ====================
// Initialization
// ====================

document.addEventListener('DOMContentLoaded', () => {
    if (authToken) {
        checkAuth();
    } else {
        showScreen('login-screen');
    }

    setupEventListeners();
});

function setupEventListeners() {
    // Login
    document.getElementById('login-form')?.addEventListener('submit', handleLogin);

    // Logout
    document.getElementById('logout-btn')?.addEventListener('click', handleLogout);

    // Step 1: Manual Serial
    document.getElementById('manual-submit-btn')?.addEventListener('click', handleManualSerial);

    // Step 2: AI Discovery
    document.getElementById('discovery-capture-btn')?.addEventListener('click', () => document.getElementById('discovery-input').click());
    document.getElementById('discovery-upload-btn')?.addEventListener('click', () => document.getElementById('discovery-upload-input').click());
    document.getElementById('discovery-input')?.addEventListener('change', handleDiscovery);
    document.getElementById('discovery-upload-input')?.addEventListener('change', handleDiscovery);
    document.getElementById('discovery-skip-btn')?.addEventListener('click', () => goToStep(3));

    // Step 3: Meter Form
    document.getElementById('meter-form')?.addEventListener('submit', handleMeterForm);
    document.getElementById('meter-back-btn')?.addEventListener('click', () => goToStep(2));

    // Step 4: Validation
    document.getElementById('validate-back-btn')?.addEventListener('click', () => goToStep(3));
    document.getElementById('validate-continue-btn')?.addEventListener('click', handleComplete);

    // Step 5: New Installation
    document.getElementById('new-installation-btn')?.addEventListener('click', startNewInstallation);
}

// ====================
// Authentication
// ====================

async function handleLogin(e) {
    e.preventDefault();

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const errorDiv = document.getElementById('login-error');

    try {
        const response = await fetch(`${API_URL}/token`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({ username, password })
        });

        if (!response.ok) throw new Error('Invalid credentials');

        const data = await response.json();
        authToken = data.access_token;
        localStorage.setItem('installer_token', authToken);

        // Get user info
        await loadUserInfo();

        // Show organization selection
        await loadOrganizations();

    } catch (error) {
        errorDiv.textContent = error.message;
        errorDiv.classList.add('show');
    }
}

async function loadUserInfo() {
    try {
        const payload = JSON.parse(atob(authToken.split('.')[1]));
        currentUser = { username: payload.sub };
        document.getElementById('username-display').textContent = currentUser.username;
    } catch (error) {
        console.error('Failed to load user info:', error);
    }
}

function handleLogout() {
    localStorage.removeItem('installer_token');
    authToken = null;
    currentUser = null;
    selectedOrganization = null;
    window.location.reload();
}

async function checkAuth() {
    try {
        await loadUserInfo();
        await loadOrganizations();
    } catch (error) {
        handleLogout();
    }
}

// ====================
// Organization Selection
// ====================

async function loadOrganizations() {
    try {
        const response = await apiCall('/api/organizations/my-organizations');
        const organizations = response;

        if (organizations.length === 0) {
            alert('No organizations assigned. Contact your administrator.');
            handleLogout();
            return;
        }

        if (organizations.length === 1) {
            selectOrganization(organizations[0]);
        } else {
            displayOrganizations(organizations);
            showScreen('org-selection-screen');
        }
    } catch (error) {
        console.error('Failed to load organizations:', error);
        handleLogout();
    }
}

function displayOrganizations(organizations) {
    const orgList = document.getElementById('org-list');
    orgList.innerHTML = '';

    organizations.forEach(org => {
        const card = document.createElement('div');
        card.className = 'org-card';
        card.innerHTML = `
            <h3>${org.name}</h3>
            <p>${org.subdomain}.metervision.io</p>
        `;
        card.addEventListener('click', () => selectOrganization(org));
        orgList.appendChild(card);
    });
}

function selectOrganization(org) {
    selectedOrganization = org;
    installationData.organizationId = org.id;
    startInstallation();
}

// ====================
// Wizard Navigation
// ====================

function startInstallation() {
    showScreen('wizard-screen');
    goToStep(1);
    initializeQRScanner();
}

function goToStep(stepNumber) {
    currentStep = stepNumber;

    // Correct index mapping (1 -> 0, 2 -> 1, 3 -> 2, 4 -> 3, 5 -> 4)
    const stepIdx = stepNumber - 1;

    // Update step indicators
    document.querySelectorAll('.step').forEach((step, index) => {
        step.classList.remove('active', 'completed');
        if (index < stepIdx) {
            step.classList.add('completed');
        } else if (index === stepIdx) {
            step.classList.add('active');
        }
    });

    // Update step content visibility
    document.querySelectorAll('.wizard-step').forEach((step, index) => {
        step.classList.toggle('active', index === stepIdx);
    });

    // Handle QR scanner lifecycle
    if (stepNumber === 1) {
        if (!qrScanner) setTimeout(() => initializeQRScanner(), 100);
    } else {
        if (qrScanner) stopQRScanner();
    }

    // Completion summary if going to step 5
    if (stepNumber === 5) {
        showCompletionSummary();
    }
}

// ====================
// Step 1: QR & Manual
// ====================

function initializeQRScanner() {
    const qrReaderDiv = document.getElementById('qr-reader');
    if (!qrReaderDiv || qrScanner) return;

    qrScanner = new Html5Qrcode("qr-reader");
    const config = { fps: 10, qrbox: { width: 250, height: 250 }, aspectRatio: 1.0 };

    qrScanner.start(
        { facingMode: "environment" },
        config,
        (decodedText) => handleQRScan(decodedText),
        () => { }
    ).catch(err => console.error('QR Scanner failed:', err));
}

function stopQRScanner() {
    if (qrScanner) {
        qrScanner.stop().then(() => { qrScanner = null; }).catch(err => console.error(err));
    }
}

function handleQRScan(serial) {
    if (installationData.cameraSerial) return;
    stopQRScanner();
    processCameraSerial(serial);
}

function handleManualSerial() {
    const serial = document.getElementById('manual-serial').value.trim();
    if (serial) processCameraSerial(serial);
}

function processCameraSerial(serial) {
    installationData.cameraSerial = serial;
    goToStep(2);
}

// ====================
// Step 2: AI Discovery
// ====================

async function handleDiscovery(e) {
    const file = e.target.files[0];
    if (!file) return;

    // Show preview
    const reader = new FileReader();
    reader.onload = (event) => {
        const preview = document.getElementById('discovery-preview');
        preview.innerHTML = `<img src="${event.target.result}" alt="Captured meter">`;
    };
    reader.readAsDataURL(file);

    document.getElementById('discovery-loading').style.display = 'block';

    try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_URL}/api/installations/analyze-image`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${authToken}` },
            body: formData
        });

        if (!response.ok) throw new Error('AI analysis failed');
        const data = await response.json();
        const suggestions = data.suggestions;

        // Pre-fill Step 3 form
        if (suggestions.serial_number && suggestions.serial_number !== 'UNKNOWN') {
            document.getElementById('meter-serial').value = suggestions.serial_number;
            document.getElementById('ai-serial-badge').style.display = 'inline-block';
        }
        if (suggestions.meter_type) {
            document.getElementById('meter-type').value = suggestions.meter_type;
            document.getElementById('ai-type-badge').style.display = 'inline-block';

            const unitSelect = document.getElementById('meter-unit');
            if (suggestions.meter_type === 'Electricity') unitSelect.value = 'kWh';
            else if (suggestions.meter_type === 'Gas') unitSelect.value = 'm3';
            else if (suggestions.meter_type === 'Water') unitSelect.value = 'L';
        }
        if (suggestions.reading) {
            document.getElementById('meter-reading').value = suggestions.reading;
            document.getElementById('suggested-reading-val').textContent = suggestions.reading;
            document.getElementById('ai-reading-suggestion').style.display = 'block';
        }

        await delay(1500);
        goToStep(3);
    } catch (error) {
        console.error('Discovery error:', error);
        goToStep(3);
    } finally {
        document.getElementById('discovery-loading').style.display = 'none';
    }
}

// ====================
// Step 3: Meter Info
// ====================

async function handleMeterForm(e) {
    e.preventDefault();

    installationData.meterSerial = document.getElementById('meter-serial').value;
    installationData.meterType = document.getElementById('meter-type').value;
    installationData.meterUnit = document.getElementById('meter-unit').value;
    installationData.expectedReading = document.getElementById('meter-reading').value;
    installationData.meterLocation = document.getElementById('meter-location').value || '';

    try {
        const response = await apiCall('/api/installations/start', {
            method: 'POST',
            body: JSON.stringify({
                camera_serial: installationData.cameraSerial,
                meter_serial: installationData.meterSerial,
                meter_type: installationData.meterType,
                meter_unit: installationData.meterUnit,
                organization_id: installationData.organizationId,
                meter_location: installationData.meterLocation
            })
        });

        installationData.sessionId = response.session_id;
        goToStep(4);
        await runValidation();
    } catch (error) {
        alert('Failed: ' + error.message);
    }
}

// ====================
// Step 4: Validation
// ====================

async function runValidation() {
    document.querySelectorAll('.validation-item').forEach(i => i.classList.add('pending'));

    try {
        const response = await apiCall(`/api/installations/${installationData.sessionId}/validate`, { method: 'POST' });
        const results = response.validation_results;

        updateValidationUI('connection', results.connection);
        await delay(300);
        updateValidationUI('fov', results.fov);
        await delay(300);
        updateValidationUI('glare', results.glare);
        await delay(300);
        updateValidationUI('ocr', results.ocr);

        const allPassed = results.connection.passed && results.fov.passed && results.ocr.passed;
        document.getElementById('validate-continue-btn').disabled = !allPassed;
    } catch (error) {
        console.error(error);
    }
}

function updateValidationUI(checkType, result) {
    const item = document.querySelector(`.validation-item[data-check="${checkType}"]`);
    if (!item) return;
    const icon = item.querySelector('.validation-icon i');
    const status = item.querySelector('.validation-status');

    item.classList.remove('pending');
    if (result.passed) {
        item.classList.add('passed');
        icon.className = 'ph ph-check-circle';
        status.textContent = result.message;
    } else {
        item.classList.add('failed');
        icon.className = 'ph ph-x-circle';
        status.textContent = result.message || 'Failed';
    }
}

async function handleComplete() {
    try {
        await apiCall(`/api/installations/${installationData.sessionId}/complete`, {
            method: 'POST',
            body: JSON.stringify({
                installer_confirmed: true,
                expected_reading: parseFloat(installationData.expectedReading),
                serial_number: installationData.meterSerial,
                meter_type: installationData.meterType
            })
        });
        goToStep(5);
    } catch (error) {
        alert('Completion failed: ' + error.message);
    }
}

// ====================
// Step 5: Summary
// ====================

function showCompletionSummary() {
    document.getElementById('summary-camera-serial').textContent = installationData.cameraSerial;
    document.getElementById('summary-meter-serial').textContent = installationData.meterSerial;
    document.getElementById('summary-meter-type').textContent = installationData.meterType;
    document.getElementById('summary-location').textContent = installationData.meterLocation || 'Not specified';
}

function startNewInstallation() {
    window.location.reload();
}

// ====================
// Utils
// ====================

async function apiCall(endpoint, options = {}) {
    const headers = { 'Content-Type': 'application/json', ...options.headers };
    if (authToken) headers['Authorization'] = `Bearer ${authToken}`;

    const response = await fetch(`${API_URL}${endpoint}`, { ...options, headers });
    if (!response.ok) throw new Error(await response.text());
    return response.json();
}

function showScreen(screenId) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    document.getElementById(screenId)?.classList.add('active');
}

function delay(ms) { return new Promise(r => setTimeout(r, ms)); }

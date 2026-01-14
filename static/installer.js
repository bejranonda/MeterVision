/**
 * MeterVision Installer App
 * Mobile-first installation wizard with QR scanning and validation
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

    // Step navigation
    document.getElementById('manual-submit-btn')?.addEventListener('click', handleManualSerial);
    document.getElementById('meter-form')?.addEventListener('submit', handleMeterForm);
    document.getElementById('meter-back-btn')?.addEventListener('click', () => goToStep(1));
    document.getElementById('validate-back-btn')?.addEventListener('click', () => goToStep(2));
    document.getElementById('validate-continue-btn')?.addEventListener('click', () => goToStep(4));
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
        // For now, we'll use a simple username display
        // In production, you might want to fetch user details
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
            // Auto-select if only one organization
            selectOrganization(organizations[0]);
        } else {
            // Show organization selection
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
// Installation Wizard
// ====================

function startInstallation() {
    showScreen('wizard-screen');
    goToStep(1);
    initializeQRScanner();
}

function goToStep(stepNumber) {
    currentStep = stepNumber;

    // Update step indicators
    document.querySelectorAll('.step').forEach((step, index) => {
        const num = index + 1;
        step.classList.remove('active', 'completed');

        if (num < stepNumber) {
            step.classList.add('completed');
        } else if (num === stepNumber) {
            step.classList.add('active');
        }
    });

    // Update step content
    document.querySelectorAll('.wizard-step').forEach((step, index) => {
        step.classList.toggle('active', index + 1 === stepNumber);
    });

    // Handle QR scanner lifecycle
    if (stepNumber === 1 && !qrScanner) {
        setTimeout(() => initializeQRScanner(), 100);
    } else if (stepNumber !== 1 && qrScanner) {
        stopQRScanner();
    }
}

// ====================
// QR Code Scanner
// ====================

function initializeQRScanner() {
    const qrReaderDiv = document.getElementById('qr-reader');
    if (!qrReaderDiv || qrScanner) return;

    qrScanner = new Html5Qrcode("qr-reader");

    const config = {
        fps: 10,
        qrbox: { width: 250, height: 250 },
        aspectRatio: 1.0
    };

    qrScanner.start(
        { facingMode: "environment" },
        config,
        (decodedText) => {
            handleQRScan(decodedText);
        },
        (errorMessage) => {
            // Ignore scan errors
        }
    ).catch(err => {
        console.error('QR Scanner failed to start:', err);
        // Scanner not available, user can use manual input
    });
}

function stopQRScanner() {
    if (qrScanner) {
        qrScanner.stop().then(() => {
            qrScanner = null;
        }).catch(err => {
            console.error('Failed to stop scanner:', err);
        });
    }
}

function handleQRScan(serial) {
    if (installationData.cameraSerial) return;  // Already scanned

    stopQRScanner();
    processCameraSerial(serial);
}

function handleManualSerial() {
    const serial = document.getElementById('manual-serial').value.trim();
    if (serial) {
        processCameraSerial(serial);
    }
}

async function processCameraSerial(serial) {
    installationData.cameraSerial = serial;
    console.log('Camera serial:', serial);

    // Move to meter info step
    goToStep(2);
}

// ====================
// Meter Information
// ====================

async function handleMeterForm(e) {
    e.preventDefault();

    installationData.meterSerial = document.getElementById('meter-serial').value;
    installationData.meterType = document.getElementById('meter-type').value;
    installationData.meterUnit = document.getElementById('meter-unit').value;
    installationData.meterLocation = document.getElementById('meter-location').value || '';

    // Move to validation step
    goToStep(3);

    // Start validation
    await runValidation();
}

// ====================
// Validation
// ====================

async function runValidation() {
    const checks = ['connection', 'fov', 'glare', 'ocr'];

    for (const check of checks) {
        await runValidationCheck(check);
        await delay(1500);  // Delay between checks
    }

    // All checks complete
    document.getElementById('validate-continue-btn').disabled = false;
}

async function runValidationCheck(checkType) {
    const item = document.querySelector(`.validation-item[data-check="${checkType}"]`);
    const icon = item.querySelector('.validation-icon i');
    const status = item.querySelector('.validation-status');

    // Mark as pending
    item.classList.add('pending');
    icon.className = 'ph ph-circle-notch spinner';

    // Simulate validation (in production, call actual API)
    const result = await simulateValidation(checkType);

    // Update UI based on result
    if (result.passed) {
        item.classList.remove('pending');
        item.classList.add('passed');
        icon.className = 'ph ph-check-circle';
        status.textContent = result.message;
    } else {
        item.classList.remove('pending');
        item.classList.add('failed');
        icon.className = 'ph ph-x-circle';
        status.textContent = result.message;
    }
}

async function simulateValidation(checkType) {
    // In production, this would call the backend API
    // For now, we simulate with delays and mock responses

    await delay(2000);

    const messages = {
        connection: { passed: true, message: 'Camera connected successfully' },
        fov: { passed: true, message: 'Meter fully visible in frame' },
        glare: { passed: true, message: 'No glare detected, lighting good' },
        ocr: { passed: true, message: 'Initial reading: 12345.67 kWh (confidence: 95%)' }
    };

    return messages[checkType];
}

// ====================
// Complete Installation
// ====================

function goToStep(stepNum) {
    if (stepNum === 4) {
        showCompletionSummary();
    }

    currentStep = stepNum;

    // Update step indicators
    document.querySelectorAll('.step').forEach((step, index) => {
        const num = index + 1;
        step.classList.remove('active', 'completed');

        if (num < stepNum) {
            step.classList.add('completed');
        } else if (num === stepNum) {
            step.classList.add('active');
        }
    });

    // Update step content
    document.querySelectorAll('.wizard-step').forEach((step, index) => {
        step.classList.toggle('active', index + 1 === stepNum);
    });
}

function showCompletionSummary() {
    document.getElementById('summary-camera-serial').textContent = installationData.cameraSerial;
    document.getElementById('summary-meter-serial').textContent = installationData.meterSerial;
    document.getElementById('summary-meter-type').textContent = installationData.meterType;
    document.getElementById('summary-location').textContent = installationData.meterLocation || 'Not specified';
}

function startNewInstallation() {
    // Reset installation data
    Object.keys(installationData).forEach(key => {
        if (key !== 'organizationId') {
            installationData[key] = null;
        }
    });

    // Reset form
    document.getElementById('manual-serial').value = '';
    document.getElementById('meter-form').reset();

    // Reset validation items
    document.querySelectorAll('.validation-item').forEach(item => {
        item.classList.remove('pending', 'passed', 'failed');
        item.querySelector('.validation-icon i').className = 'ph ph-circle-notch';
        item.querySelector('.validation-status').textContent = 'Waiting...';
    });

    document.getElementById('validate-continue-btn').disabled = true;

    // Go back to step 1
    goToStep(1);
}

// ====================
// Utility Functions
// ====================

async function apiCall(endpoint, options = {}) {
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };

    if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
    }

    const response = await fetch(`${API_URL}${endpoint}`, {
        ...options,
        headers
    });

    if (!response.ok) {
        const error = await response.text();
        throw new Error(error || 'API request failed');
    }

    return response.json();
}

function showScreen(screenId) {
    document.querySelectorAll('.screen').forEach(screen => {
        screen.classList.remove('active');
    });
    document.getElementById(screenId)?.classList.add('active');
}

function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

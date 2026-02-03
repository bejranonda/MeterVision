const API_URL = "";
let state = {
    token: localStorage.getItem('access_token'),
    view: 'login', // login, dashboard
    data: {
        projects: [],
        customers: [],
        buildings: [],
        places: [],
        meters: [],
        readings: []
    },
    // Flattened view for dashboard
    flatMeters: [],
    breadcrumbs: [],
    username: 'User'
};

const app = document.getElementById('app');

/* --- RENDERING --- */
function render() {
    if (!state.token) {
        renderLogin();
        return;
    }

    // Main App Layout
    app.innerHTML = `
        ${renderTopNav()}
        <div class="container">
            ${renderDashboard()}
        </div>
        ${renderModals()}
    `;

    // Re-attach event listeners if needed
    feather.replace(); // If using feather icons, but we use Phosphor
}

function renderTopNav() {
    return `
        <nav class="top-nav">
            <div class="logo">
                <i class="ph-fill ph-house-line" style="color: var(--accent-green);"></i>
                Meter<span>Vision</span>
            </div>
            <div class="nav-links">
                <div class="nav-item active">Dashboard</div>
                <div class="nav-item">Analysis</div>
                <div class="nav-item">Settings</div>
            </div>
            <div class="user-profile">
                <span>Hello, ${state.username}!</span>
                <i class="ph-fill ph-user-circle" style="font-size: 2rem; color: #333;"></i>
                <i class="ph ph-sign-out" style="font-size: 1.5rem; cursor: pointer; margin-left: 10px;" onclick="window.logout()"></i>
            </div>
        </nav>
    `;
}

function renderLogin() {
    app.innerHTML = `
        <div class="auth-wrapper">
            <div class="auth-card">
                <div class="logo" style="justify-content: center; margin-bottom: 2rem;">
                    <i class="ph-fill ph-house-line" style="color: var(--accent-green); font-size: 2rem;"></i>
                    <span style="font-size: 2rem;">MeterVision</span>
                </div>
                <h2 style="margin-bottom: 0.5rem; font-weight: 600;">Welcome Back</h2>
                <p style="color: var(--text-muted); margin-bottom: 2rem;">Sign in to monitor your consumption</p>
                
                <form id="loginForm">
                    <div class="input-group">
                        <input type="text" id="username" class="input-field" placeholder="Username" required>
                    </div>
                    <div class="input-group">
                        <input type="password" id="password" class="input-field" placeholder="Password" required>
                    </div>
                    <button type="submit" class="btn-primary">Sign In</button>
                </form>
            </div>
        </div>
    `;

    document.getElementById('loginForm').addEventListener('submit', handleLogin);
}

function renderDashboard() {
    return `
        <div class="room-control-header">
            <div class="status-widget">
                 <i class="ph-fill ph-lightning"></i>
                 <div class="status-value">${state.flatMeters.length}</div>
                 <div class="status-label">Total Meters</div>
             </div>
            <div class="status-widget">
                <i class="ph-fill ph-buildings"></i>
                <div class="status-value">${new Set(state.flatMeters.map(m => m.place_name)).size}</div>
                <div class="status-label">Monitored Places</div>
            </div>
            <div class="status-widget">
                <i class="ph-fill ph-check-circle"></i>
                <div class="status-value">Active</div>
                <div class="status-label">System Status</div>
            </div>
        </div>

        <div class="dashboard-header">
            <div class="page-title">Meters Overview</div>
            <div class="filters">
                <button class="filter-btn active">All</button>
                <button class="filter-btn">Electricity</button>
                <button class="filter-btn">Gas</button>
            </div>
        </div>

        <div class="grid-container">
            ${state.flatMeters.map(m => renderMeterCard(m)).join('')}
            
            <!-- Add New Wrapper -->
            <div class="smart-card variant-light" style="justify-content: center; align-items: center; border: 2px dashed #ddd; box-shadow: none;" onclick="promptNewMeter()">
                <i class="ph ph-plus" style="font-size: 2rem; color: #ccc;"></i>
                <div style="color: #999; margin-top: 10px; font-weight: 500;">Add Device</div>
            </div>
        </div>
    `;
}

function renderMeterCard(meter) {
    // Generate a random-ish temp or last reading
    let mainValue = "---";
    let unit = meter.unit || "";
    let statusIcon = "ph-question";

    if (meter.readings && meter.readings.length > 0) {
        mainValue = meter.readings[0].value;
    }

    // Choose icon
    if (meter.meter_type === 'Gas') statusIcon = "ph-fire";
    else if (meter.meter_type === 'Electricity') statusIcon = "ph-lightning";
    else if (meter.meter_type === 'Heat') statusIcon = "ph-thermometer";

    return `
        <div class="smart-card" onclick="openMeterDetails(${meter.id})">
            <div class="card-header">
                <span>${meter.place_name || 'Unknown Place'}</span>
                <i class="ph-fill ${statusIcon}"></i>
            </div>
            <div class="card-temp">
                ${mainValue}<span style="font-size: 1rem; margin-left: 5px;">${unit}</span>
            </div>
            <div class="card-label">
                ${meter.serial_number}
            </div>
            <div class="card-meta">
                <div class="card-icons">
                    <i class="ph-fill ph-leaf"></i>
                    <i class="ph-fill ph-wifi-high"></i>
                </div>
                <!-- <i class="ph-fill ph-chart-bar" style="font-size: 1.5rem;"></i> -->
            </div>
        </div>
    `;
}

function renderModals() {
    return `
        <!-- Meter Detail Modal -->
        <div id="meterModal" class="overlay">
            <div class="modal-body">
                <div style="display:flex; justify-content:space-between; margin-bottom: 1.5rem;">
                    <h3 id="modalTitle" style="margin:0;">Meter Details</h3>
                    <i class="ph ph-x" style="font-size: 1.5rem; cursor: pointer;" onclick="closeModal('meterModal')"></i>
                </div>
                
                <div id="modalContent"></div>
                
                 <div style="margin-top: 2rem; text-align: right;">
                    <button class="btn-primary" style="width: auto; padding: 10px 20px;" onclick="document.getElementById('uploadInput').click()">
                        <i class="ph ph-camera"></i> New Reading
                    </button>
                    <input type="file" id="uploadInput" hidden accept="image/*" onchange="handleUpload(this)">
                </div>
            </div>
        </div>
    `;
}

/* --- LOGIC --- */

// --- Login ---
async function handleLogin(e) {
    e.preventDefault();
    const u = document.getElementById('username').value;
    const p = document.getElementById('password').value;

    // Simple FormData for OAuth2 endpoint
    const fd = new FormData();
    fd.append('username', u);
    fd.append('password', p);

    try {
        const res = await fetch('/token', { method: 'POST', body: fd });
        if (res.ok) {
            const data = await res.json();
            state.token = data.access_token;
            state.username = u;
            localStorage.setItem('access_token', state.token);
            initializeApp();
        } else {
            alert('Login failed');
        }
    } catch (err) {
        console.error(err);
        alert('Network error');
    }
}

window.logout = function () {
    state.token = null;
    localStorage.removeItem('access_token');
    render();
}

// --- Data Fetching ---
async function initializeApp() {
    // We want to flatten the hierarchy for the dashboard
    // Fetch all meters list endpoint (assuming it exists from previous code)
    try {
        // Fetch meters
        const metersRes = await fetchWithAuth('/meters_list/');
        let meters = await metersRes.json();

        // Enhance meters with Place names (need to fetch hierarchy or just fetch places)
        // For efficiency, let's fetch places map
        // Note: In a real app we might want a composite endpoint
        const placesRes = await fetchWithAuth('/places/');
        const places = await placesRes.json();
        const placeMap = {};
        places.forEach(p => placeMap[p.id] = p.name);

        // Enhance meters
        state.flatMeters = await Promise.all(meters.map(async m => {
            m.place_name = placeMap[m.place_id];
            try {
                const rRes = await fetchWithAuth(`/meters/${m.serial_number}/readings`);
                const readings = await rRes.json();
                m.readings = readings || [];
            } catch (e) {
                m.readings = [];
            }
            return m;
        }));

        render();
    } catch (e) {
        console.error("Init failed", e);
        if (state.token) render(); // Render empty dashboard
    }
}

async function fetchWithAuth(url, options = {}) {
    if (!options.headers) options.headers = {};
    options.headers['Authorization'] = `Bearer ${state.token}`;

    const res = await fetch(url, options);
    if (res.status === 401) {
        window.logout();
        throw new Error("Unauthorized");
    }
    return res;
}

// --- Meter Interaction ---
let currentMeterId = null;

window.openMeterDetails = function (id) {
    currentMeterId = id;
    const meter = state.flatMeters.find(m => m.id === id);
    if (!meter) return;

    const modal = document.getElementById('meterModal');
    const content = document.getElementById('modalContent');
    const title = document.getElementById('modalTitle');

    title.innerText = `${meter.place_name} - ${meter.meter_type}`;
    content.innerHTML = `
        <div style="background: #f4f6f8; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
             <strong>Serial:</strong> ${meter.serial_number} <br>
             <strong>Unit:</strong> ${meter.unit}
        </div>
        <h4>Reading History</h4>
        <div style="max-height: 300px; overflow-y: auto; border: 1px solid #eee; border-radius: 6px;">
             ${meter.readings && meter.readings.length > 0 ?
            meter.readings.map(r => `
                <div style="padding: 10px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center;">
                    <div style="display: flex; flex-direction: column;">
                        <span style="font-size: 0.85rem; color: #555;">${new Date(r.timestamp).toLocaleString()}</span>
                        <span style="font-size: 0.75rem; color: #888;">${r.status || 'Verified'}</span>
                    </div>
                    <strong>${r.value} <span style="font-size: 0.8rem; font-weight: normal; color: #666;">${meter.unit}</span></strong>
                </div>
            `).join('')
            : '<p style="padding: 20px; text-align: center; color:#888;">No readings found.</p>'}
        </div>
    `;

    modal.classList.add('open');
}

window.closeModal = function (id) {
    document.getElementById(id).classList.remove('open');
}

window.handleUpload = async function (input) {
    if (!input.files || !input.files[0]) return;
    const file = input.files[0];
    const meter = state.flatMeters.find(m => m.id === currentMeterId);

    // We can reuse the cropping logic later, for now let's just do direct upload or simulate
    // For modernization, let's keep it simple: direct upload
    const fd = new FormData();
    fd.append('file', file);

    // Show loading state
    const btn = document.querySelector('#meterModal .btn-primary');
    const oldText = btn.innerHTML;
    btn.innerHTML = 'Processing...';
    btn.disabled = true;

    try {
        const res = await fetchWithAuth(`/meters/${meter.serial_number}/reading`, {
            method: 'POST',
            body: fd
        });

        if (res.ok) {
            const reading = await res.json();
            alert(`Reading Success: ${reading.value}`);
            window.closeModal('meterModal');
            initializeApp(); // Refresh dashboard
        } else {
            const err = await res.json();
            alert("Error: " + err.detail);
        }
    } catch (e) {
        alert("Upload failed");
    } finally {
        btn.innerHTML = oldText;
        btn.disabled = false;
        input.value = ''; // Reset
    }
}

window.promptNewMeter = function () {
    window.location.href = '/static/installer.html';
}

// --- Init ---
if (state.token) {
    initializeApp();
} else {
    render();
}

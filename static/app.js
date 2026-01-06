const API_URL = "";
let state = {
    token: localStorage.getItem('access_token'),
    view: 'login', // login, projects, customers, buildings, places, meters, reading
    breadcrumbs: [], // Array of {label, id, view}
    data: {
        projects: [],
        customers: [],
        buildings: [],
        places: [],
        meters: [],
        currentProject: null,
        currentCustomer: null,
        currentBuilding: null,
        currentPlace: null,
        currentMeter: null,
        readings: []
    }
};

const app = document.getElementById('app');

function render() {
    if (!state.token) {
        renderLogin();
        return;
    }

    if (state.view === 'login') state.view = 'projects';

    switch (state.view) {
        case 'projects': renderProjects(); break;
        case 'customers': renderCustomers(); break;
        case 'buildings': renderBuildings(); break;
        case 'places': renderPlaces(); break;
        case 'meters': renderMeters(); break;
        case 'readings': renderReadings(); break;
        default: renderProjects();
    }
}

function renderLogin() {
    app.innerHTML = `
        <div class="auth-container">
            <div class="card">
                <h2>Login to MeterVision</h2>
                <form id="loginForm">
                    <input type="text" id="username" placeholder="Username" required>
                    <input type="password" id="password" placeholder="Password" required>
                    <button type="submit">Sign In</button>
                </form>
            </div>
        </div>
    `;

    document.getElementById('loginForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;

        try {
            const formData = new FormData();
            formData.append('username', username);
            formData.append('password', password);

            const res = await fetch(`${API_URL}/token`, { method: 'POST', body: formData });
            if (res.ok) {
                const data = await res.json();
                state.token = data.access_token;
                localStorage.setItem('access_token', state.token);
                state.view = 'projects';
                fetchProjects();
            } else {
                alert('Login failed');
            }
        } catch (err) {
            console.error(err);
            alert('Error logging in');
        }
    });
}

function logout() {
    state.token = null;
    localStorage.removeItem('access_token');
    state.view = 'login';
    render();
}

function renderNav(title) {
    const breadcrumbHtml = state.breadcrumbs.map((b, index) => {
        return `<span onclick="navigateTo(${index})">${b.label}</span>`;
    }).join(' > ');

    return `
        <nav>
            <div class="logo">MeterVision</div>
            <div style="display: flex; align-items: center; gap: 20px;">
                <button onclick="logout()" style="width: auto; margin:0; padding: 5px 15px;">Logout</button>
            </div>
        </nav>
        <div class="breadcrumb">
            ${breadcrumbHtml} ${breadcrumbHtml ? '> ' : ''} <strong>${title}</strong>
        </div>
    `;
}

function navigateTo(breadcrumbIndex) {
    const target = state.breadcrumbs[breadcrumbIndex];
    state.breadcrumbs = state.breadcrumbs.slice(0, breadcrumbIndex);
    state.view = target.view;
    // Helper to set current item based on breadcrumb target
    if (target.view === 'projects') {
        state.data.currentProject = state.data.projects.find(p => p.id === target.id);
    } else if (target.view === 'customers') {
        state.data.currentCustomer = state.data.customers.find(c => c.id === target.id);
    } else if (target.view === 'buildings') {
        state.data.currentBuilding = state.data.buildings.find(b => b.id === target.id);
    } else if (target.view === 'places') {
        state.data.currentPlace = state.data.places.find(p => p.id === target.id);
    }

    // Refresh data based on view
    if (target.view === 'projects') fetchProjects();
    else if (target.view === 'customers') { fetchCustomers(state.data.currentProject.id); }
    else if (target.view === 'buildings') { fetchBuildings(state.data.currentCustomer.id); }
    else if (target.view === 'places') { fetchPlaces(state.data.currentBuilding.id); }
    else if (target.view === 'meters') { fetchMeters(state.data.currentPlace.id); }
    else if (target.view === 'readings') { fetchReadings(state.data.currentMeter.serial_number); }
    render();
}

// --- API Helpers ---
async function apiCall(endpoint, method = 'GET', body = null) {
    const options = {
        method,
        headers: { 'Authorization': `Bearer ${state.token}` }
    };
    if (body) {
        if (body instanceof FormData) {
            options.body = body;
        } else {
            options.headers['Content-Type'] = 'application/json';
            options.body = JSON.stringify(body);
        }
    }
    const res = await fetch(`${API_URL}${endpoint}`, options);
    if (res.status === 401) { logout(); return null; }
    return res.json();
}

// --- Projects ---
async function fetchProjects() {
    state.data.projects = await apiCall('/projects/');
    state.breadcrumbs = [];
    render();
}

function renderProjects() {
    app.innerHTML = `
        ${renderNav('Projects')}
        <div class="grid">
            ${state.data.projects.map(p => `
                <div class="project-card" onclick="selectProject(${p.id})">
                    <h3>${p.name}</h3>
                    <p>${p.description || ''}</p>
                </div>
            `).join('')}
             <div class="project-card" style="border: 2px dashed #cbd5e1; display: flex; justify-content: center; align-items: center; color: #64748b;" onclick="createProject()">
                + New Project
            </div>
        </div>
    `;
}

async function createProject() {
    const name = prompt("Project Name:");
    if (!name) return;
    await apiCall('/projects/', 'POST', { name, description: "" });
    fetchProjects();
}

function selectProject(id) {
    const p = state.data.projects.find(x => x.id === id);
    state.data.currentProject = p;
    state.breadcrumbs.push({ label: p.name, view: 'projects', id: id });
    state.view = 'customers';
    fetchCustomers(id);
}

// --- Customers ---
async function fetchCustomers(projectId) {
    const allCustomers = await apiCall('/customers/');
    state.data.customers = allCustomers.filter(c => c.project_id === (projectId || state.data.currentProject.id));
    render();
}

function renderCustomers() {
    app.innerHTML = `
        ${renderNav('Customers')}
        <div class="grid">
            ${state.data.customers.map(c => `
                <div class="project-card" onclick="selectCustomer(${c.id})">
                    <h3>${c.name}</h3>
                    <p>${c.email || ''}</p>
                </div>
            `).join('')}
            <div class="project-card" style="border: 2px dashed #cbd5e1; display: flex; justify-content: center; align-items: center; color: #64748b;" onclick="createCustomer()">
                + New Customer
            </div>
        </div>
    `;
}

async function createCustomer() {
    const name = prompt("Customer Name:");
    if (!name) return;
    await apiCall('/customers/', 'POST', { name, project_id: state.data.currentProject.id });
    fetchCustomers(state.data.currentProject.id);
}

function selectCustomer(id) {
    const c = state.data.customers.find(x => x.id === id);
    state.data.currentCustomer = c;
    state.breadcrumbs.push({ label: c.name, view: 'customers', id: id });
    state.view = 'buildings';
    fetchBuildings(id);
}

// --- Buildings ---
async function fetchBuildings(customerId) {
    const all = await apiCall('/buildings/');
    state.data.buildings = all.filter(x => x.customer_id === customerId);
    render();
}

function renderBuildings() {
    app.innerHTML = `
        ${renderNav('Buildings')}
        <div class="grid">
            ${state.data.buildings.map(b => `
                <div class="project-card" onclick="selectBuilding(${b.id})">
                    <h3>${b.name}</h3>
                    <p>${b.address}</p>
                </div>
            `).join('')}
             <div class="project-card" style="border: 2px dashed #cbd5e1; display: flex; justify-content: center; align-items: center; color: #64748b;" onclick="createBuilding()">
                + New Building
            </div>
        </div>
    `;
}

async function createBuilding() {
    const name = prompt("Building Name:");
    const address = prompt("Address:");
    if (!name) return;
    await apiCall('/buildings/', 'POST', { name, address: address || "", customer_id: state.data.currentCustomer.id });
    fetchBuildings(state.data.currentCustomer.id);
}

function selectBuilding(id) {
    const b = state.data.buildings.find(x => x.id === id);
    state.data.currentBuilding = b;
    state.breadcrumbs.push({ label: b.name, view: 'buildings', id: id });
    state.view = 'places';
    fetchPlaces(id);
}

// --- Places ---
async function fetchPlaces(buildingId) {
    const all = await apiCall('/places/');
    state.data.places = all.filter(x => x.building_id === buildingId);
    render();
}

function renderPlaces() {
    app.innerHTML = `
        ${renderNav('Places')}
        <div class="grid">
            ${state.data.places.map(p => `
                <div class="project-card" onclick="selectPlace(${p.id})">
                    <h3>${p.name}</h3>
                    <p>${p.description || ''}</p>
                </div>
            `).join('')}
             <div class="project-card" style="border: 2px dashed #cbd5e1; display: flex; justify-content: center; align-items: center; color: #64748b;" onclick="createPlace()">
                + New Place
            </div>
        </div>
    `;
}

async function createPlace() {
    const name = prompt("Place Name:");
    if (!name) return;
    await apiCall('/places/', 'POST', { name, building_id: state.data.currentBuilding.id });
    fetchPlaces(state.data.currentBuilding.id);
}

function selectPlace(id) {
    const p = state.data.places.find(x => x.id === id);
    state.data.currentPlace = p;
    state.breadcrumbs.push({ label: p.name, view: 'places', id: id });
    state.view = 'meters';
    fetchMeters(id);
}

// --- Meters ---
async function fetchMeters(placeId) {
    try {
        const all = await apiCall('/meters_list/');
        state.data.meters = all.filter(x => x.place_id === placeId);
    } catch (e) {
        console.warn("Meters list endpoint missing or failed to fetch:", e);
        state.data.meters = [];
    }
    render();
}

function renderMeters() {
    app.innerHTML = `
        ${renderNav('Meters')}
        <div class="grid">
            ${state.data.meters.map(m => `
                <div class="project-card" onclick="selectMeter(${m.id})">
                    <h3>${m.serial_number}</h3>
                    <p>${m.meter_type} - ${m.unit}</p>
                </div>
            `).join('')}
             <div class="project-card" style="border: 2px dashed #cbd5e1; display: flex; justify-content: center; align-items: center; color: #64748b;" onclick="createMeter()">
                + New Meter
            </div>
        </div>
    `;
}

async function createMeter() {
    const serial = prompt("Serial Number:");
    const type = prompt("Type (Gas/Electricity/Heat):", "Gas");
    if (!serial) return;
    await apiCall('/meters/', 'POST', {
        serial_number: serial,
        meter_type: type,
        unit: 'm3',
        place_id: state.data.currentPlace.id
    });
    fetchMeters(state.data.currentPlace.id);
}

async function selectMeter(id) {
    // Fetch fresh meter data to get latest AOI config
    const tempM = state.data.meters.find(x => x.id === id);
    if (tempM) {
        try {
            const freshMeter = await apiCall(`/meters/${tempM.serial_number}`);
            state.data.currentMeter = freshMeter;
        } catch (e) {
            console.error("Failed to fetch fresh meter details", e);
            state.data.currentMeter = tempM;
        }
    } else {
        return;
    }

    state.breadcrumbs.push({ label: state.data.currentMeter.serial_number, view: 'meters', id: id });
    state.view = 'readings';
    fetchReadings(state.data.currentMeter.serial_number);
}

// --- Readings & Cropper ---

let cropperState = {
    image: null,
    startX: 0,
    startY: 0,
    endX: 0,
    endY: 0,
    isDragging: false,
    fileType: 'image/jpeg'
};

async function fetchReadings(serialNumber) {
    state.data.readings = await apiCall(`/meters/${serialNumber}/readings`);
    render();
}

function renderReadings() {
    const m = state.data.currentMeter;
    const readings = state.data.readings || [];

    app.innerHTML = `
        ${renderNav(`Readings for ${m.serial_number}`)}
        <div style="margin-bottom: 20px;">
            <div class="card" style="max-width: 600px; margin: 0 auto;">
                <h3>Upload New Reading</h3>
                <input type="file" id="readingFile" accept="image/*" onchange="handleFileSelect(this, '${m.serial_number}')">
                <p style="font-size: 0.8rem; color: #64748b; margin-top: 5px;">Select an image to open the editor.</p>
            </div>
        </div>

        <h3 style="margin-top: 2rem;">History</h3>
        <div class="grid">
            ${readings.map(r => `
                <div class="project-card" style="cursor: default;">
                    <h3>${r.value} ${m.unit}</h3>
                    <p>Status: <span class="reading-pill">${r.status}</span></p>
                    <p style="font-size: 0.8rem; color: #64748b;">${new Date(r.timestamp).toLocaleString()}</p>
                    <button class="btn-text" onclick="handleViewDetails(${r.id})" style="font-size: 0.8rem; color: var(--accent-color); margin-top: 0.5rem;">View Details</button>
                </div>
            `).join('')}
             ${readings.length === 0 ? '<p style="color: #64748b; font-style: italic;">No readings yet.</p>' : ''}
        </div>

        <!-- Cropper Modal -->
        <div id="cropModal" class="modal-overlay">
            <div class="modal-content">
                <h3>Define Area of Interest</h3>
                <div class="canvas-container" id="canvasContainer">
                    <canvas id="cropCanvas"></canvas>
                </div>
                <div style="margin-top: 1rem;">
                    <label class="block text-sm font-medium mb-1">Expected Reading (Calibration Hint):</label>
                    <input type="text" id="expectedValueInput" class="w-full p-2 rounded bg-slate-700 border border-slate-600 mb-4" placeholder="e.g. 12345.67">
                </div>
                <div class="modal-actions">
                    <button class="btn-secondary" onclick="closeModal()">Cancel</button>
                    <button onclick="confirmCrop('${m.serial_number}')">Upload Selection</button>
                </div>
            </div>
        </div>

        <!-- Reading Detail Modal -->
        <div id="readingModal" class="modal-overlay">
            <div class="modal-content" style="max-width: 800px; width: 90%;">
                <div class="flex justify-between items-center mb-4">
                    <h3>Reading Details</h3>
                    <button onclick="closeReadingModal()" style="background:none; border:none; font-size:1.5rem; cursor:pointer;">&times;</button>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <img id="detailImage" src="" alt="Meter Reading" style="width: 100%; border-radius: 8px; border: 1px solid #e2e8f0;">
                    </div>
                    <div>
                        <div class="mb-4">
                            <label class="block text-sm font-medium text-slate-500">Value</label>
                            <div class="text-3xl font-bold text-slate-800" id="detailValue"></div>
                        </div>
                        <div class="mb-4">
                            <label class="block text-sm font-medium text-slate-500">Status</label>
                            <span id="detailStatus" class="reading-pill"></span>
                        </div>
                        <div class="mb-4">
                            <label class="block text-sm font-medium text-slate-500">Timestamp</label>
                            <div id="detailTimestamp" class="text-slate-700"></div>
                        </div>
                         <div class="mb-4">
                            <label class="block text-sm font-medium text-slate-500">Serial Number</label>
                            <div class="text-slate-700">${m.serial_number}</div>
                        </div>
                    </div>
                </div>
                <div class="modal-actions mt-6">
                    <button class="btn-secondary" onclick="closeReadingModal()">Close</button>
                </div>
            </div>
        </div>
    `;
}

function handleFileSelect(input, serialNumber) {
    const file = input.files[0];
    if (!file) return;

    cropperState.fileType = file.type;
    const reader = new FileReader();
    reader.onload = function (e) {
        const img = new Image();
        img.onload = function () {
            cropperState.image = img;
            openModal();
            initCropper();
        };
        img.src = e.target.result;
    };
    reader.readAsDataURL(file);
}

function openModal() {
    document.getElementById('cropModal').style.display = 'flex';
}

function closeModal() {
    document.getElementById('cropModal').style.display = 'none';
    document.getElementById('readingFile').value = ''; // Reset input
}

function handleViewDetails(readingId) {
    const reading = state.data.readings.find(r => r.id === readingId);
    if (reading) {
        openReadingModal(reading);
    }
}

function openReadingModal(reading) {
    const modal = document.getElementById('readingModal');
    const imgPath = reading.raw_image_path ? '/' + reading.raw_image_path.replace('/home/ogema/MeterReading/', '') : '';

    document.getElementById('detailImage').src = imgPath;
    document.getElementById('detailValue').textContent = reading.value + ' ' + (state.data.currentMeter ? state.data.currentMeter.unit : '');
    document.getElementById('detailStatus').textContent = reading.status;
    document.getElementById('detailTimestamp').textContent = new Date(reading.timestamp).toLocaleString();

    modal.style.display = 'flex';
}

function closeReadingModal() {
    document.getElementById('readingModal').style.display = 'none';
}

function initCropper() {
    const canvas = document.getElementById('cropCanvas');
    const ctx = canvas.getContext('2d');
    const img = cropperState.image;

    // We draw specific resolution.
    canvas.width = img.width;
    canvas.height = img.height;

    // Initialize selection from saved AOI if available
    if (state.data.currentMeter && state.data.currentMeter.aoi_config) {
        try {
            const aoi = JSON.parse(state.data.currentMeter.aoi_config);
            cropperState.startX = aoi.x;
            cropperState.startY = aoi.y;
            cropperState.endX = aoi.x + aoi.w;
            cropperState.endY = aoi.y + aoi.h;
        } catch (e) {
            console.warn("Invalid AOI config", e);
            resetSelection(img);
        }
    } else {
        resetSelection(img);
    }

    function resetSelection(image) {
        cropperState.startX = 0;
        cropperState.startY = 0;
        cropperState.endX = image.width;
        cropperState.endY = image.height;
    }

    function draw() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(img, 0, 0);

        // Draw overlay dim
        ctx.fillStyle = 'rgba(0, 0, 0, 0.5)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // Clear rect for selection
        const x = Math.min(cropperState.startX, cropperState.endX);
        const y = Math.min(cropperState.startY, cropperState.endY);
        const w = Math.abs(cropperState.endX - cropperState.startX);
        const h = Math.abs(cropperState.endY - cropperState.startY);

        // Draw image inside selection cleanly
        ctx.drawImage(img, x, y, w, h, x, y, w, h);

        // Draw border
        ctx.strokeStyle = '#10b981';
        ctx.lineWidth = 4;
        ctx.strokeRect(x, y, w, h);
    }

    draw();

    // Event Listeners
    let isDown = false;

    // Helper to get coords
    function getCoords(e) {
        const rect = canvas.getBoundingClientRect();
        // Scale factor if CSS shrinks canvas
        const scaleX = canvas.width / rect.width;
        const scaleY = canvas.height / rect.height;
        return {
            x: (e.clientX - rect.left) * scaleX,
            y: (e.clientY - rect.top) * scaleY
        };
    }

    canvas.onmousedown = (e) => {
        isDown = true;
        const coords = getCoords(e);
        cropperState.startX = coords.x;
        cropperState.startY = coords.y;
        cropperState.endX = coords.x;
        cropperState.endY = coords.y;
        draw();
    };

    canvas.onmousemove = (e) => {
        if (!isDown) return;
        const coords = getCoords(e);
        cropperState.endX = coords.x;
        cropperState.endY = coords.y;
        draw();
    };

    canvas.onmouseup = () => { isDown = false; };
    canvas.onmouseout = () => { isDown = false; };
}

async function confirmCrop(serialNumber) {
    const canvas = document.getElementById('cropCanvas');
    const x = Math.min(cropperState.startX, cropperState.endX);
    const y = Math.min(cropperState.startY, cropperState.endY);
    const w = Math.abs(cropperState.endX - cropperState.startX);
    const h = Math.abs(cropperState.endY - cropperState.startY);

    if (w < 10 || h < 10) {
        alert("Selection too small!");
        return;
    }

    // Save AOI Config
    const aoiConfig = JSON.stringify({ x, y, w, h });
    try {
        await apiCall(`/meters/${serialNumber}`, 'PATCH', { aoi_config: aoiConfig });
        // Update local state
        if (state.data.currentMeter) state.data.currentMeter.aoi_config = aoiConfig;
    } catch (e) {
        console.warn("Failed to save AOI config", e);
    }

    // Create a generic canvas to extract blob
    const tempCanvas = document.createElement('canvas');
    tempCanvas.width = w;
    tempCanvas.height = h;
    const tCtx = tempCanvas.getContext('2d');
    tCtx.drawImage(cropperState.image, x, y, w, h, 0, 0, w, h);

    tempCanvas.toBlob(async (blob) => {
        const formData = new FormData();
        // Send as weird filename to ensure backend treats it as image
        formData.append('file', blob, `crop_${Date.now()}.jpg`);

        closeModal();
        app.innerHTML += `<div style="position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(255,255,255,0.7);display:flex;justify-content:center;align-items:center;z-index:1001;"><h3>Processing...</h3></div>`;

        try {
            const res = await fetch(`${API_URL}/meters/${serialNumber}/reading`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${state.token}` },
                body: formData
            });

            if (res.ok) {
                alert("Reading processed successfully!");
                fetchReadings(serialNumber);
            } else {
                const err = await res.json();
                alert("Error: " + (err.detail || "Upload failed"));
                render(); // Clear loading
            }
        } catch (e) {
            console.error(e);
            alert("Upload failed");
            render(); // Clear loading
        }
    }, 'image/jpeg', 0.95);
}

// Initial Kickoff
if (state.token) {
    fetchProjects();
} else {
    render();
}

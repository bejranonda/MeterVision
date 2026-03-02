const state = {
    token: localStorage.getItem('access_token'),
    user: null,
    currentView: 'dashboard',
    organizations: [],
    meters: [],
    logs: [],
    currentMeter: null, // For detail view
    lang: localStorage.getItem('app_lang') || 'de'
};

const translations = {
    en: {
        'menu.dashboard.title': 'Dashboard',
        'menu.dashboard.desc': 'Overview & statistics',
        'menu.organizations.title': 'Organizations',
        'menu.organizations.desc': 'Manage tenants',
        'menu.meters.title': 'Meters',
        'menu.meters.desc': 'View & manage meters',
        'menu.logs.title': 'Logs',
        'menu.logs.desc': 'System event history',
        'menu.settings.title': 'Settings',
        'menu.settings.desc': 'App configuration',
        'header.logout': 'Logout',
        'login.title': 'MeterVision',
        'login.subtitle': 'Sign In',
        'login.username': 'Username',
        'login.password': 'Password',
        'login.button': 'Login',
        'dashboard.active_meters': 'Active Meters',
        'dashboard.organizations': 'Organizations',
        'dashboard.readings_today': 'Readings Today',
        'dashboard.alerts': 'Alerts',
        'dashboard.recent_activity': 'Recent Activity',
        'dashboard.view_all': 'View All',
        'dashboard.table.time': 'Time',
        'dashboard.table.event': 'Event',
        'dashboard.table.details': 'Details',
        'dashboard.table.status': 'Status',
        'dashboard.table.loading': 'Loading activity...',
        'organizations.title': 'My Organizations',
        'meters.search': 'Search meters...',
        'meters.add_meter': 'Add Meter',
        'meter_detail.back': 'Back to Meters',
        'meter_detail.history': 'Reading History',
        'meter_detail.recent': 'Recent Readings',
        'meter_detail.table.date': 'Date',
        'meter_detail.table.value': 'Value',
        'meter_detail.table.image': 'Image',
        'meter_detail.details': 'Meter Details',
        'meter_detail.manual_upload': 'Manual Upload',
        'meter_detail.upload_image': 'Upload Image',
        'meter_detail.expected_value': 'Expected Value (Optional)',
        'meter_detail.submit': 'Submit Reading',
        'meter_detail.danger_zone': 'Danger Zone',
        'meter_detail.delete_meter': 'Delete Meter',
        'logs.title': 'System Logs',
        'logs.refresh': 'Refresh',
        'settings.title': 'App Settings',
        'settings.desc': 'Configuration options will appear here.',
        'modal.create_meter.serial': 'Serial Number',
        'modal.create_meter.org_id': 'Organization ID (Optional)',
        'modal.create_meter.org_id_placeholder': 'Leave empty for default',
        'modal.create_meter.org_id_help': 'Leave empty to use default "Undefined Organization"',
        'modal.create_meter.type': 'Type',
        'modal.create_meter.type_placeholder': 'Select or type custom type',
        'modal.create_meter.unit': 'Unit',
        'modal.cancel': 'Cancel',
        'modal.create_meter.submit': 'Create Meter'
    },
    de: {
        'menu.dashboard.title': 'Übersicht',
        'menu.dashboard.desc': 'Aktuellen Status und Statistiken anzeigen',
        'menu.organizations.title': 'Kunden / Organisationen',
        'menu.organizations.desc': 'Mandanten und Kunden verwalten',
        'menu.meters.title': 'Zählerverwaltung',
        'menu.meters.desc': 'Zähler und Ablesungen verwalten',
        'menu.logs.title': 'Systemprotokolle',
        'menu.logs.desc': 'Verlauf der Systemereignisse ansehen',
        'menu.settings.title': 'Einstellungen',
        'menu.settings.desc': 'App-Konfiguration',
        'header.logout': 'Abmelden',
        'login.title': 'MeterVision',
        'login.subtitle': 'Anmelden',
        'login.username': 'Benutzername*',
        'login.password': 'Passwort*',
        'login.button': 'Einloggen',
        'dashboard.active_meters': 'Aktive Zähler',
        'dashboard.organizations': 'Organisationen',
        'dashboard.readings_today': 'Ablesungen Heute',
        'dashboard.alerts': 'Warnungen',
        'dashboard.recent_activity': 'Letzte Aktivitäten',
        'dashboard.view_all': 'Alle ansehen',
        'dashboard.table.time': 'Zeit',
        'dashboard.table.event': 'Ereignis',
        'dashboard.table.details': 'Details',
        'dashboard.table.status': 'Status',
        'dashboard.table.loading': 'Aktivitäten werden geladen...',
        'organizations.title': 'Meine Organisationen',
        'meters.search': 'Suchen...',
        'meters.add_meter': 'Zähler hinzufügen',
        'meter_detail.back': 'Zurück zu Zählern',
        'meter_detail.history': 'Ablesehistorie',
        'meter_detail.recent': 'Letzte Ablesungen',
        'meter_detail.table.date': 'Datum',
        'meter_detail.table.value': 'Wert',
        'meter_detail.table.image': 'Bild',
        'meter_detail.details': 'Zählerdetails',
        'meter_detail.manual_upload': 'Manueller Upload',
        'meter_detail.upload_image': 'Bild hochladen',
        'meter_detail.expected_value': 'Erwarteter Wert (Optional)',
        'meter_detail.submit': 'Einreichen',
        'meter_detail.danger_zone': 'Gefahrenbereich',
        'meter_detail.delete_meter': 'Zähler löschen',
        'logs.title': 'Systemprotokolle',
        'logs.refresh': 'Aktualisieren',
        'settings.title': 'App-Einstellungen',
        'settings.desc': 'Konfigurationsoptionen werden hier angezeigt.',
        'modal.create_meter.serial': 'Seriennummer',
        'modal.create_meter.org_id': 'Organisations-ID (Optional)',
        'modal.create_meter.org_id_placeholder': 'Leer lassen für Standard',
        'modal.create_meter.org_id_help': 'Leer lassen, um die "Undefinierte Organisation" zu verwenden',
        'modal.create_meter.type': 'Typ',
        'modal.create_meter.type_placeholder': 'Wählen oder tippen Sie einen benutzerdefinierten Typ',
        'modal.create_meter.unit': 'Einheit',
        'modal.cancel': 'Abbrechen',
        'modal.create_meter.submit': 'Zähler erstellen'
    }
};

const API_BASE_URL = window.location.origin + '/meter-vision-api';

document.addEventListener('DOMContentLoaded', () => {
    if (state.token) {
        initializeApp();
    } else {
        renderLoginView();
    }
});

function navigateTo(view, params = null) {
    state.currentView = view;
    renderMainView(params);
    // Close sidebar on mobile on navigation
    document.getElementById('sidebar')?.classList.remove('open');
    document.getElementById('sidebar-overlay')?.classList.remove('active');
    applyTranslations();
}

function applyTranslations() {
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (translations[state.lang] && translations[state.lang][key]) {
            el.innerHTML = translations[state.lang][key];
        }
    });
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        if (translations[state.lang] && translations[state.lang][key]) {
            el.setAttribute('placeholder', translations[state.lang][key]);
        }
    });
}

function toggleLanguage() {
    state.lang = state.lang === 'de' ? 'en' : 'de';
    localStorage.setItem('app_lang', state.lang);

    // Update button text
    const langBtnText = document.getElementById('current-lang-text');
    if (langBtnText) {
        langBtnText.innerText = state.lang === 'de' ? 'EN' : 'DE'; // Show what it toggles TO
    }

    applyTranslations();
}

async function initializeApp() {
    try {
        await fetchUserInfo();
        renderAppLayout();
        await renderMainView();
    } catch (error) {
        console.error('Initialization failed:', error);
        // Only logout on actual auth failures, not UI rendering bugs
        if (error?.status === 401 || error?.message?.includes('token')) {
            logout();
        } else {
            // Show error UI instead of silently logging out
            const appElement = document.getElementById('app');
            if (appElement) {
                appElement.innerHTML = `
                    <div style="display:flex;align-items:center;justify-content:center;min-height:100vh;padding:2rem;">
                        <div class="card" style="max-width:500px;text-align:center;">
                            <h2 style="color:var(--error,#ef4444);margin-bottom:1rem;">Initialization Error</h2>
                            <p style="margin-bottom:1rem;">${error.message || 'An unexpected error occurred while loading the application.'}</p>
                            <button class="btn btn-primary" onclick="location.reload()">Reload</button>
                            <button class="btn btn-secondary" style="margin-left:0.5rem;" onclick="logout()">Logout</button>
                        </div>
                    </div>`;
            }
        }
    }
}

async function fetchUserInfo() {
    const payload = JSON.parse(atob(state.token.split('.')[1]));
    state.user = { username: payload.sub };
    // In a real app we'd fetch full profile from /users/me
}

function renderAppLayout() {
    const appElement = document.getElementById('app');
    const appLayoutTemplate = document.getElementById('app-layout-template');

    appElement.innerHTML = '';
    appElement.appendChild(appLayoutTemplate.content.cloneNode(true));

    // Event Listeners
    setupNavigation();
    setupMobileNav();
    setupModals();

    const userInfoElement = document.getElementById('user-info');
    if (state.user && userInfoElement) {
        userInfoElement.innerHTML = `
            <div style="text-align: right;">
                <div style="font-weight: 600; font-size: 0.9rem;">${state.user.username}</div>
                <div style="font-size: 0.75rem; color: var(--text-secondary);">Admin</div>
            </div>
            <div style="width: 32px; height: 32px; background: var(--bg-card); border: 2px solid var(--primary-color); color: var(--primary-color); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700;">
                ${state.user.username[0].toUpperCase()}
            </div>
        `;
    }

    const langBtnText = document.getElementById('current-lang-text');
    if (langBtnText) {
        langBtnText.innerText = state.lang === 'de' ? 'EN' : 'DE';
    }
    applyTranslations();
}

function setupNavigation() {
    document.querySelector('#main-nav').addEventListener('click', e => {
        const link = e.target.closest('a');
        if (link && link.dataset.view) {
            e.preventDefault();
            navigateTo(link.dataset.view);
        }
    });

    document.getElementById('logout-btn')?.addEventListener('click', logout);
    document.getElementById('lang-toggle-btn')?.addEventListener('click', toggleLanguage);
}

function setupMobileNav() {
    const btn = document.getElementById('mobile-menu-btn');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');

    if (btn && sidebar && overlay) {
        btn.addEventListener('click', () => {
            sidebar.classList.add('open');
            overlay.classList.add('active');
        });

        overlay.addEventListener('click', () => {
            sidebar.classList.remove('open');
            overlay.classList.remove('active');
        });
    }
}

function setupModals() {
    // Close modal on overlay click
    const modalOverlay = document.getElementById('global-modal');
    modalOverlay?.addEventListener('click', (e) => {
        if (e.target === modalOverlay) closeModal();
    });

    // Close button
    document.addEventListener('click', e => {
        if (e.target.closest('.close-modal') || e.target.closest('.modal-close-btn')) {
            closeModal();
        }
    });

    // Create Meter Modal Trigger (delegate because it might be re-rendered)
    document.addEventListener('click', e => {
        if (e.target.closest('#btn-create-meter')) {
            openCreateMeterModal();
        }
    });
}

function openModal(title, contentNode) {
    const overlay = document.getElementById('global-modal');
    const titleEl = document.getElementById('modal-title');
    const bodyEl = document.getElementById('modal-body');

    titleEl.textContent = title;
    bodyEl.innerHTML = '';
    bodyEl.appendChild(contentNode);

    overlay.classList.add('active');
}

function closeModal() {
    document.getElementById('global-modal').classList.remove('active');
}

async function renderMainView(params = null) {
    const viewContent = document.getElementById('view-content');
    const pageTitle = document.getElementById('app-header-title');

    // Update active nav
    document.querySelectorAll('#main-nav li').forEach(li => li.classList.remove('active'));
    // Handle 'meters' active state for meter-detail
    const activeView = state.currentView === 'meter-detail' ? 'meters' : state.currentView;
    document.querySelector(`#main-nav a[data-view="${activeView}"]`)?.closest('li')?.classList.add('active');

    if (pageTitle) {
        pageTitle.textContent = state.currentView.charAt(0).toUpperCase() + state.currentView.replace('-', ' ').slice(1);
    }

    switch (state.currentView) {
        case 'dashboard':
            renderDashboard(viewContent);
            break;
        case 'organizations':
            renderOrganizations(viewContent);
            break;
        case 'meters':
            renderMeters(viewContent);
            break;
        case 'meter-detail':
            pageTitle.textContent = params.serial_number;
            renderMeterDetail(viewContent, params);
            break;
        case 'logs':
            renderLogs(viewContent);
            break;
        case 'settings':
            renderSettings(viewContent);
            break;
        default:
            viewContent.innerHTML = '<h2>404 Not Found</h2>';
    }
}

async function renderDashboard(container) {
    const template = document.getElementById('dashboard-template');
    container.innerHTML = template.innerHTML;

    // Fetch stats (mocking some aggregations or using real data if available)
    try {
        const [metersRes, orgsRes] = await Promise.all([
            fetchWithAuth(`${API_BASE_URL}/meters_list/`),
            fetchWithAuth(`${API_BASE_URL}/api/organizations/my-organizations`)
        ]);

        if (metersRes.ok && orgsRes.ok) {
            const meters = await metersRes.json();
            const orgs = await orgsRes.json();

            document.getElementById('stat-active-meters').textContent = meters.length;
            document.getElementById('stat-organizations').textContent = orgs.length;

            // Fetch readings for each meter to get "Readings Today" and "Recent Activity"
            let allReadings = [];
            for (const meter of meters) {
                try {
                    const readingsRes = await fetchWithAuth(`${API_BASE_URL}/meters/${meter.serial_number}/readings`);
                    if (readingsRes.ok) {
                        const readings = await readingsRes.json();
                        allReadings = allReadings.concat(readings.map(r => ({ ...r, serial: meter.serial_number })));
                    }
                } catch (e) { /* ignore individual failures */ }
            }

            // Calculate "Readings Today"
            const today = new Date().toDateString();
            const readingsToday = allReadings.filter(r => new Date(r.timestamp).toDateString() === today);
            document.getElementById('stat-readings-today').textContent = readingsToday.length;

            // Recent Activity (last 5 readings)
            allReadings.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
            const recentActivity = allReadings.slice(0, 5);

            const activityTable = document.querySelector('#recent-activity-table tbody');
            if (activityTable) {
                if (recentActivity.length === 0) {
                    activityTable.innerHTML = '<tr><td colspan="4" class="text-muted" style="text-align: center;">No recent activity</td></tr>';
                } else {
                    activityTable.innerHTML = recentActivity.map(r => `
                        <tr>
                            <td>${new Date(r.timestamp).toLocaleString()}</td>
                            <td>Meter Reading</td>
                            <td>${r.serial}: <strong>${r.value}</strong></td>
                            <td><span class="badge badge-success">Verified</span></td>
                        </tr>
                    `).join('');
                }
            }
        }
    } catch (e) {
        console.error("Dashboard data load error", e);
    }
}

async function renderMeters(container) {
    const template = document.getElementById('meters-template');
    container.innerHTML = template.innerHTML;

    const grid = document.getElementById('meters-grid');
    grid.innerHTML = '<div class="text-muted">Loading meters...</div>';

    try {
        const response = await fetchWithAuth(`${API_BASE_URL}/meters_list/`);
        if (response.ok) {
            state.meters = await response.json();
            if (state.meters.length === 0) {
                grid.innerHTML = '<div class="text-muted">No meters found.</div>';
                return;
            }
            grid.innerHTML = state.meters.map(meter => createMeterCard(meter)).join('');

            // Add click listeners for cards
            grid.querySelectorAll('.meter-card').forEach(card => {
                card.addEventListener('click', () => {
                    navigateTo('meter-detail', { serial_number: card.dataset.serial });
                });
            });

            // Search filter
            document.getElementById('meter-search').addEventListener('input', (e) => {
                const term = e.target.value.toLowerCase();
                const filtered = state.meters.filter(m =>
                    m.serial_number.toLowerCase().includes(term) ||
                    (m.location && m.location.toLowerCase().includes(term))
                );
                grid.innerHTML = filtered.map(meter => createMeterCard(meter)).join('');
                // Re-bind click listeners
                grid.querySelectorAll('.meter-card').forEach(card => {
                    card.addEventListener('click', () => {
                        navigateTo('meter-detail', { serial_number: card.dataset.serial });
                    });
                });
            });

        } else {
            grid.innerHTML = '<div class="text-error">Failed to load meters.</div>';
        }
    } catch (error) {
        grid.innerHTML = `<div class="text-error">Error: ${error.message}</div>`;
    }
}

function createMeterCard(meter) {
    return `
        <div class="card meter-card" style="cursor: pointer;" data-serial="${meter.serial_number}">
            <div class="meter-preview">
                <i class="ph-duotone ph-gauge" style="font-size: 3rem;"></i>
            </div>
            <h3 class="card-title">${meter.serial_number}</h3>
            <p class="text-secondary text-sm" style="margin: 0.5rem 0;">${meter.meter_type} • ${meter.unit}</p>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 1rem;">
                <span class="text-sm bg-green-light" style="padding: 0.25rem 0.5rem; border-radius: 4px;">Active</span>
                <span class="text-muted text-sm">${meter.location || 'No Location'}</span>
            </div>
        </div>
    `;
}

async function renderMeterDetail(container, params) {
    const template = document.getElementById('meter-detail-template');
    container.innerHTML = template.innerHTML;

    try {
        const response = await fetchWithAuth(`${API_BASE_URL}/meters/${params.serial_number}`);
        if (!response.ok) throw new Error("Meter not found");
        const meter = await response.json();
        state.currentMeter = meter;

        // Populate Meta Info
        document.getElementById('meter-meta-info').innerHTML = `
            <table style="width: 100%;">
                <tr><td class="text-muted">Serial</td><td style="font-weight: 500;">${meter.serial_number}</td></tr>
                <tr><td class="text-muted">Type</td><td style="font-weight: 500;">${meter.meter_type}</td></tr>
                <tr><td class="text-muted">Unit</td><td style="font-weight: 500;">${meter.unit}</td></tr>
                <tr><td class="text-muted">Location</td><td style="font-weight: 500;">${meter.location || '-'}</td></tr>
                <tr><td class="text-muted">Org ID</td><td style="font-weight: 500;">${meter.organization_id}</td></tr>
            </table>
        `;

        // Handle Upload Form
        document.getElementById('upload-reading-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData();
            const fileInput = document.getElementById('reading-image');
            const expectedVal = document.getElementById('expected-value').value;

            if (fileInput.files.length > 0) {
                formData.append('file', fileInput.files[0]);
                if (expectedVal) formData.append('expected_value', expectedVal);

                try {
                    const res = await fetchWithAuth(`${API_BASE_URL}/meters/${meter.serial_number}/reading`, {
                        method: 'POST',
                        body: formData,
                        skipContentType: true // Let browser set boundary
                    });
                    if (res.ok) {
                        alert("Reading uploaded and processed!");
                        loadReadings(meter.serial_number); // Refresh
                        fileInput.value = ''; // Reset
                    } else {
                        alert("Upload failed.");
                    }
                } catch (err) {
                    console.error(err);
                    alert("Upload error.");
                }
            }
        });

        // Load Readings & Chart
        loadReadings(meter.serial_number);

        // Delete Meter Handler
        const deleteBtn = document.getElementById('delete-meter-btn');
        if (deleteBtn) {
            // Remove existing listener to prevent duplicates
            const newDeleteBtn = deleteBtn.cloneNode(true);
            deleteBtn.parentNode.replaceChild(newDeleteBtn, deleteBtn);

            newDeleteBtn.addEventListener('click', async () => {
                if (confirm(`Are you sure you want to delete meter ${meter.serial_number}? This action cannot be undone.`)) {
                    try {
                        const res = await fetchWithAuth(`${API_BASE_URL}/meters/${meter.id}`, {
                            method: 'DELETE'
                        });

                        if (res.ok) {
                            alert('Meter deleted successfully');
                            closeModal();
                            renderMetersList(); // Refresh list
                        } else {
                            const err = await res.json();
                            alert(`Failed to delete meter: ${err.detail || 'Unknown error'}`);
                        }
                    } catch (e) {
                        console.error("Delete error:", e);
                        alert("Error deleting meter");
                    }
                }
            });
        }

    } catch (e) {
        container.innerHTML = `<div class="text-error">${e.message}</div>`;
    }
}

async function loadReadings(serial) {
    try {
        const response = await fetchWithAuth(`${API_BASE_URL}/meters/${serial}/readings`);
        if (response.ok) {
            const readings = await response.json();
            renderReadingsTable(readings);
            renderReadingsChart(readings);
        }
    } catch (e) {
        console.error("Failed to load readings", e);
    }
}

function renderReadingsTable(readings) {
    const tbody = document.querySelector('#readings-table tbody');
    if (!tbody) return;

    tbody.innerHTML = readings.slice(0, 10).map(r => {
        // Handle both full paths (/home/ogema/...) and relative paths (/uploads/...)
        let imagePath = r.raw_image_path;
        if (imagePath.startsWith('/home/ogema/MeterReading/')) {
            imagePath = imagePath.replace('/home/ogema/MeterReading', '');
        }

        return `
            <tr>
                <td>${new Date(r.timestamp).toLocaleDateString()} ${new Date(r.timestamp).toLocaleTimeString()}</td>
                <td style="font-weight: 600;">${r.value}</td>
                <td><a href="${imagePath}" target="_blank" class="text-info">View</a></td>
            </tr>
        `;
    }).join('');
}

function renderReadingsChart(readings) {
    const ctx = document.getElementById('meter-history-chart');
    if (!ctx) return;

    // Filter last 30 days
    const recentReadings = readings.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp)); // ascending

    const dates = recentReadings.map(r => new Date(r.timestamp).toLocaleDateString());
    const values = recentReadings.map(r => r.value);

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [{
                label: 'Reading Value',
                data: values,
                borderColor: '#BDFF78',
                backgroundColor: 'rgba(189, 255, 120, 0.08)',
                tension: 0.4,
                fill: true,
                pointBackgroundColor: '#BDFF78',
                pointRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: { beginAtZero: false, grid: { color: 'rgba(0, 90, 68, 0.4)' }, ticks: { color: '#BDFF78' } },
                x: { grid: { display: false }, ticks: { color: 'rgba(189,255,120,0.6)' } }
            }
        }
    });
}

function openCreateMeterModal() {
    const template = document.getElementById('create-meter-modal-content');
    const formNode = template.content.cloneNode(true);

    // Attach event listener before appending
    const form = formNode.querySelector('form');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);

        const payload = Object.fromEntries(formData.entries());
        // For simple form -> JSON
        try {
            const res = await fetchWithAuth(`${API_BASE_URL}/meters/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (res.ok) {
                closeModal();
                if (state.currentView === 'meters') renderMeters(document.getElementById('view-content')); // refresh
            } else {
                alert("Failed to create meter");
            }
        } catch (err) {
            console.error(err);
            alert("Error creating meter");
        }
    });

    openModal('Create New Meter', formNode);
}

// ... (renderOrganizations, renderLogs, renderSettings - simplified for brevity but following pattern)
async function renderOrganizations(container) {
    const template = document.getElementById('organizations-template');
    container.innerHTML = template.innerHTML;
    // ... fetch logic similar to before
}

async function renderLogs(container) {
    const template = document.getElementById('log-viewer-template');
    container.innerHTML = template.innerHTML;

    const logContainer = document.getElementById('log-entries');
    logContainer.innerHTML = '<div class="text-muted" style="padding: 1rem;">Loading logs...</div>';

    const renderEntries = async () => {
        try {
            const response = await fetchWithAuth(`${API_BASE_URL}/api/logs/?limit=50`);
            if (response.ok) {
                const logs = await response.json();
                if (logs.length === 0) {
                    logContainer.innerHTML = '<div class="text-muted" style="padding: 1rem;">No logs found.</div>';
                    return;
                }

                // Sort logs by date descending (to be safe, though API usually does it)
                logs.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));

                logContainer.innerHTML = `
                    <table class="table">
                        <thead>
                            <tr>
                                <th>Time</th>
                                <th>Level</th>
                                <th>Message</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${logs.map(log => `
                                <tr>
                                    <td class="text-muted" style="white-space: nowrap;">${new Date(log.created_at).toLocaleString()}</td>
                                    <td><span class="status-badge status-${log.level.toLowerCase()}">${log.level}</span></td>
                                    <td>
                                        <div style="font-weight: 500;">${log.message}</div>
                                        ${log.details && Object.keys(log.details).length > 0 ?
                        `<pre style="font-size: 0.75rem; margin-top: 0.5rem; background: rgba(0,18,14,0.6); border: 1px solid var(--border-color); color: var(--primary-color); padding: 0.5rem; border-radius: 4px; overflow: auto; max-width: 400px;">${JSON.stringify(log.details, null, 2)}</pre>`
                        : ''}
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                `;
            } else {
                logContainer.innerHTML = '<div class="text-error" style="padding: 1rem;">Failed to load logs.</div>';
            }
        } catch (error) {
            logContainer.innerHTML = `<div class="text-error" style="padding: 1rem;">Error: ${error.message}</div>`;
        }
    };

    renderEntries();

    document.getElementById('refresh-logs').addEventListener('click', () => {
        logContainer.innerHTML = '<div class="text-muted" style="padding: 1rem;">Refreshing...</div>';
        renderEntries();
    });
}

function renderSettings(container) {
    const template = document.getElementById('settings-template');
    container.innerHTML = template.innerHTML;
}

// ... (Auth helpers: renderLoginView, handleLogin, logout, fetchWithAuth - same as before but customized if needed)

function renderLoginView() {
    const appElement = document.getElementById('app');
    const loginTemplate = document.getElementById('login-template');

    appElement.innerHTML = '';
    appElement.appendChild(loginTemplate.content.cloneNode(true));

    document.getElementById('login-form').addEventListener('submit', handleLogin);
    applyTranslations();
}

async function handleLogin(e) {
    e.preventDefault();
    const username = e.target.username.value;
    const password = e.target.password.value;
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);

    try {
        const response = await fetch(`${API_BASE_URL}/token`, { method: 'POST', body: formData });
        if (response.ok) {
            const data = await response.json();
            localStorage.setItem('access_token', data.access_token);
            state.token = data.access_token;
            initializeApp();
        } else {
            alert('Login Failed');
        }
    } catch (error) {
        console.error('Login error:', error);
        alert('An error occurred during login.');
    }
}

function logout() {
    localStorage.removeItem('access_token');
    state.token = null;
    state.user = null;
    renderLoginView();
}

async function fetchWithAuth(url, options = {}) {
    const headers = { ...options.headers, 'Authorization': `Bearer ${state.token}` };
    // Handle Custom skipContentType for manual multipart handling
    if (options.skipContentType) {
        delete options.skipContentType;
    } else if (!headers['Content-Type']) {
        // Default to JSON if not set and not skipped (like for FormData)
        // But fetch adds correct boundary for FormData only if Content-Type is NOT set manually
        // So for JSON we set it, for FormData we don't.
        // Actually, let's keep it simple: if body is string, set JSON.
        if (typeof options.body === 'string') {
            headers['Content-Type'] = 'application/json';
        }
    }

    const response = await fetch(url, { ...options, headers });
    if (response.status === 401) { logout(); throw new Error('Unauthorized'); }
    return response;
}

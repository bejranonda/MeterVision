const state = {
    token: localStorage.getItem('access_token'),
    user: null,
    currentView: 'dashboard',
    organizations: [],
    meters: [], // Added for meters
    logs: [],
};

const API_BASE_URL = window.location.origin;

document.addEventListener('DOMContentLoaded', () => {
    if (state.token) {
        initializeApp();
    } else {
        renderLoginView();
    }
});

function navigateTo(view) {
    state.currentView = view;
    renderMainView();
}

async function initializeApp() {
    try {
        await fetchUserInfo();
        renderAppLayout();
        await renderMainView();
    } catch (error) {
        console.error('Initialization failed:', error);
        logout();
    }
}

async function fetchUserInfo() {
    // A /users/me endpoint is standard for getting current user info
    // We'll assume one exists for this example.
    // If not, we might need to decode the JWT, but that's less secure.
    state.user = { username: 'Admin' }; // Placeholder
}

function renderAppLayout() {
    const appElement = document.getElementById('app');
    const appLayoutTemplate = document.getElementById('app-layout-template');
    
    // Always clear existing content in #app
    appElement.innerHTML = '';
    
    // Clone the template content and append it
    if (appLayoutTemplate && appLayoutTemplate.content) {
        appElement.appendChild(appLayoutTemplate.content.cloneNode(true));
    } else {
        console.error('App layout template or its content not found!');
        // Fallback or error handling if template is missing
        return; // Exit if template is not found
    }

    // Attach event listeners to the newly rendered elements
    document.querySelector('#main-nav').addEventListener('click', e => {
        if (e.target.tagName === 'A' && e.target.dataset.view) {
            e.preventDefault();
            navigateTo(e.target.dataset.view);
        }
    });

    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    } else {
        console.warn('Logout button not found in rendered layout.');
    }
    
    const userInfoElement = document.getElementById('user-info');
    // Only update if user info exists and element is found
    if (state.user && userInfoElement) {
        userInfoElement.textContent = `Welcome, ${state.user.username}`;
    }
}

async function renderMainView() {
    const viewContent = document.getElementById('view-content');
    if (!viewContent) {
        console.error('View content element not found!');
        return;
    }
    
    // Highlight active nav link
    document.querySelectorAll('#main-nav a').forEach(link => {
        link.parentElement.classList.toggle('active', link.dataset.view === state.currentView);
    });

    switch (state.currentView) {
        case 'dashboard':
            const dashboardTemplate = document.getElementById('dashboard-template');
            if (dashboardTemplate) {
                viewContent.innerHTML = dashboardTemplate.innerHTML;
            } else {
                viewContent.innerHTML = '<p>Dashboard template not found.</p>';
            }
            break;
        case 'organizations':
            const organizationsTemplate = document.getElementById('organizations-template');
            if (organizationsTemplate) {
                viewContent.innerHTML = organizationsTemplate.innerHTML;
                await renderOrganizationsView();
            } else {
                viewContent.innerHTML = '<p>Organizations template not found.</p>';
            }
            break;
        case 'meters': // New case for meters
            const metersTemplate = document.getElementById('meters-template');
            if (metersTemplate) {
                viewContent.innerHTML = metersTemplate.innerHTML;
                await renderMetersView();
            } else {
                viewContent.innerHTML = '<p>Meters template not found.</p>';
            }
            break;
        case 'logs':
            const logViewerTemplate = document.getElementById('log-viewer-template');
            if (logViewerTemplate) {
                viewContent.innerHTML = logViewerTemplate.innerHTML;
                await renderLogsView();
            } else {
                viewContent.innerHTML = '<p>Log viewer template not found.</p>';
            }
            break;
        default:
            viewContent.innerHTML = '<h2>Page Not Found</h2>';
            break;
    }
}

function renderLoginView() {
    const appElement = document.getElementById('app');
    const loginTemplate = document.getElementById('login-template');
    if (appElement && loginTemplate) {
        appElement.innerHTML = loginTemplate.innerHTML;
        const loginForm = document.getElementById('login-form');
        if (loginForm) {
            loginForm.addEventListener('submit', handleLogin);
        } else {
            console.warn('Login form not found in login template.');
        }
    } else {
        console.error('App element or login template not found.');
    }
}

async function handleLogin(e) {
    e.preventDefault();
    const username = e.target.username.value;
    const password = e.target.password.value;

    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);

    try {
        const response = await fetch(`${API_BASE_URL}/token`, {
            method: 'POST',
            body: formData,
        });

        if (response.ok) {
            const data = await response.json();
            state.token = data.access_token;
            localStorage.setItem('access_token', state.token);
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
    state.token = null;
    localStorage.removeItem('access_token');
    renderLoginView();
}

async function fetchWithAuth(url, options = {}) {
    const headers = {
        ...options.headers,
        'Authorization': `Bearer ${state.token}`,
    };
    const response = await fetch(url, { ...options, headers });
    if (response.status === 401) {
        logout();
        throw new Error('Unauthorized');
    }
    return response;
}

async function renderOrganizationsView() {
    try {
        const response = await fetchWithAuth(`${API_BASE_URL}/api/organizations/my-organizations`);
        if(response.ok) {
            state.organizations = await response.json();
            const orgList = document.getElementById('org-list');
            if (orgList) {
                orgList.innerHTML = state.organizations.map(org => `<li>${org.name}</li>`).join('');
            } else {
                console.warn('Organization list element not found.');
            }
        } else {
            document.getElementById('org-list').innerHTML = '<li>Could not fetch organizations.</li>';
        }
    } catch (error) {
        console.error('Failed to fetch organizations:', error);
    }
}

async function renderMetersView() {
    const metersListContainer = document.getElementById('meters-list');
    if (!metersListContainer) {
        console.error('Meters list container not found!');
        return;
    }
    metersListContainer.innerHTML = '<p>Loading meters...</p>';

    try {
        const response = await fetchWithAuth(`${API_BASE_URL}/meters_list/`);
        if (response.ok) {
            state.meters = await response.json();
            if (state.meters.length === 0) {
                metersListContainer.innerHTML = '<p>No meters found.</p>';
                return;
            }
            metersListContainer.innerHTML = `
                <table>
                    <thead>
                        <tr>
                            <th>Serial Number</th>
                            <th>Type</th>
                            <th>Unit</th>
                            <th>Location</th>
                            <th>Organization ID</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${state.meters.map(meter => `
                            <tr>
                                <td>${meter.serial_number}</td>
                                <td>${meter.meter_type}</td>
                                <td>${meter.unit}</td>
                                <td>${meter.location || 'N/A'}</td>
                                <td>${meter.organization_id}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
        } else {
            metersListContainer.innerHTML = '<p>Failed to load meters.</p>';
        }
    } catch (error) {
        console.error('Failed to fetch meters:', error);
        metersListContainer.innerHTML = '<p>An error occurred while fetching meters.</p>';
    }
}

async function renderLogsView() {
    const logEntriesContainer = document.getElementById('log-entries');
    if (!logEntriesContainer) {
        console.error('Log entries container not found!');
        return;
    }
    logEntriesContainer.innerHTML = '<p>Loading logs...</p>';

    try {
        const response = await fetchWithAuth(`${API_BASE_URL}/api/logs/`);
        if (response.ok) {
            state.logs = await response.json();
            if (state.logs.length === 0) {
                logEntriesContainer.innerHTML = '<p>No logs found.</p>';
                return;
            }
            logEntriesContainer.innerHTML = state.logs.map(log => `
                <div class="log-entry log-level-${log.level.toLowerCase()}">
                    <div class="log-header">
                        <span class="log-level">${log.level}</span>
                        <span class="log-timestamp">${new Date(log.created_at).toLocaleString()}</span>
                    </div>
                    <div class="log-message">${log.message}</div>
                    <div class="log-details">
                        <pre>${JSON.stringify(log.details, null, 2)}</pre>
                    </div>
                </div>
            `).join('');
        } else {
            logEntriesContainer.innerHTML = '<p>Failed to load logs.</p>';
        }
    } catch (error) {
        console.error('Failed to fetch logs:', error);
        logEntriesContainer.innerHTML = '<p>An error occurred while fetching logs.</p>';
    }
}

const state = {
    token: localStorage.getItem('access_token'),
    user: null,
    currentView: 'dashboard',
    organizations: [],
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
    
    // Clear existing content in #app
    appElement.innerHTML = '';
    
    // Clone the template content and append it
    if (appLayoutTemplate && appLayoutTemplate.content) {
        appElement.appendChild(appLayoutTemplate.content.cloneNode(true));
    } else {
        console.error('App layout template or its content not found!');
        // Fallback or error handling if template is missing
    }

    document.querySelector('#main-nav').addEventListener('click', e => {
        if (e.target.tagName === 'A' && e.target.dataset.view) {
            e.preventDefault();
            navigateTo(e.target.dataset.view);
        }
    });

    document.getElementById('logout-btn').addEventListener('click', logout);
    
    const userInfoElement = document.getElementById('user-info');
    userInfoElement.textContent = `Welcome, ${state.user.username}`;
}

async function renderMainView() {
    const viewContent = document.getElementById('view-content');
    
    // Highlight active nav link
    document.querySelectorAll('#main-nav a').forEach(link => {
        link.parentElement.classList.toggle('active', link.dataset.view === state.currentView);
    });

    switch (state.currentView) {
        case 'dashboard':
            viewContent.innerHTML = document.getElementById('dashboard-template').innerHTML;
            break;
        case 'organizations':
            viewContent.innerHTML = document.getElementById('organizations-template').innerHTML;
            await renderOrganizationsView();
            break;
        case 'logs':
            viewContent.innerHTML = document.getElementById('log-viewer-template').innerHTML;
            await renderLogsView();
            break;
    }
}

function renderLoginView() {
    const appElement = document.getElementById('app');
    appElement.innerHTML = document.getElementById('login-template').innerHTML;
    document.getElementById('login-form').addEventListener('submit', handleLogin);
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
            orgList.innerHTML = state.organizations.map(org => `<li>${org.name}</li>`).join('');
        } else {
            document.getElementById('org-list').innerHTML = '<li>Could not fetch organizations.</li>';
        }
    } catch (error) {
        console.error('Failed to fetch organizations:', error);
    }
}

async function renderLogsView() {
    const logEntriesContainer = document.getElementById('log-entries');
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

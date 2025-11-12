async function request(path, options = {}) {
    const config = {
        method: options.method || 'GET',
        headers: options.headers ? { ...options.headers } : {}
    };

    // --- MODIFIED: Add User ID header to all requests ---
    config.headers['X-User-ID'] = USER_ID;

    if (options.body) {
        config.body = options.body;
        if (!config.headers['Content-Type']) {
            config.headers['Content-Type'] = 'application/json';
        }
    }

    let response;
    try {
        response = await fetch(`${API_BASE_URL}${path}`, config);
    } catch (error) {
        beginBackendRecovery('Backend is waking up… please hold tight.');
        throw new Error('Backend is waking up… please hold tight.');
    }

    if (!response.ok) {
        if (response.status >= 500) {
            beginBackendRecovery('Backend issue detected… attempting to recover.');
        }
        const message = await response.text();
        throw new Error(message || `Request failed with status ${response.status}`);
    }
    markBackendOnline();

    if (response.status === 204) {
        return null;
    }

    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('application/json')) {
        return await response.json();
    }

    return null;
}
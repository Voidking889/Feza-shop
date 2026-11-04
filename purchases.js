(function () {
    const configuredBase = window.FEZA_API_BASE_URL;
    const apiBase = (configuredBase || (
        window.location.hostname === 'localhost' && window.location.port === '3000'
            ? 'http://127.0.0.1:8000'
            : window.location.origin
    )).replace(/\/+$/, '');

    async function request(path, options) {
        const response = await fetch(`${apiBase}${path}`, options);
        const body = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(body.detail || body.message || `Purchase service returned HTTP ${response.status}.`);
        }
        return body;
    }

    window.FezaPurchases = {
        create(order) {
            return request('/api/v1/orders', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(order)
            });
        },
        forCustomer(email) {
            return request(`/api/v1/orders?email=${encodeURIComponent(email)}`);
        },
        forSeller() {
            return request('/api/v1/seller/orders');
        }
    };
})();

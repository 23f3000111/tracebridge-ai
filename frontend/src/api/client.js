/* API Client for TraceBridge Backend */

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Upload a document with metadata
 */
export async function uploadDocument(file, deviceName, docType) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('device_name', deviceName);
    formData.append('doc_type', docType);

    const response = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        body: formData,
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Upload failed');
    }

    return response.json();
}

/**
 * List all documents
 */
export async function listDocuments() {
    const response = await fetch(`${API_BASE}/documents`);

    if (!response.ok) {
        throw new Error('Failed to fetch documents');
    }

    return response.json();
}

/**
 * Query documents with RAG
 */
export async function queryDocuments(query, filters = {}) {
    const response = await fetch(`${API_BASE}/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            query,
            device_name: filters.deviceName,
            doc_type: filters.docType,
            top_k: filters.topK || 5,
        }),
    });

    if (!response.ok) {
        throw new Error('Query failed');
    }

    return response.json();
}

/**
 * Generate gap report
 */
export async function generateGapReport(deviceName, focusArea, docIds = []) {
    const response = await fetch(`${API_BASE}/gap-report`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            device_name: deviceName,
            focus_area: focusArea,
            doc_ids: docIds,
        }),
    });

    if (!response.ok) {
        throw new Error('Gap report generation failed');
    }

    return response.json();
}

/**
 * Health check
 */
export async function healthCheck() {
    const response = await fetch(`${API_BASE}/health`);
    return response.json();
}

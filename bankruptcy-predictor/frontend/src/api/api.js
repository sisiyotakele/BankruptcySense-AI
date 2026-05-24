/**
 * api.js — Axios calls to the Flask backend.
 *
 * Base URL is read from the VITE_API_URL env variable.
 * In development, Vite proxies /api → http://localhost:5000,
 * so VITE_API_URL defaults to /api.
 * In production (Vercel), set VITE_API_URL to your Render backend URL.
 */

import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || '/api'

const client = axios.create({
    baseURL: BASE_URL,
    timeout: 30000,
    headers: { 'Content-Type': 'application/json' },
})

// ── response interceptor — normalise errors ───────────────────────────────────
client.interceptors.response.use(
    (res) => res,
    (err) => {
        const message =
            err.response?.data?.error ||
            err.message ||
            'An unexpected error occurred.'
        return Promise.reject(new Error(message))
    }
)

// ── API functions ─────────────────────────────────────────────────────────────

/** Liveness check */
export const checkHealth = () => client.get('/health').then((r) => r.data)

/** Single prediction */
export const predictSingle = (features) =>
    client.post('/predict', features).then((r) => r.data)

/** Batch prediction — accepts array of feature objects */
export const predictBatch = (records) =>
    client.post('/predict/batch', records).then((r) => r.data)

/** Fetch prediction history */
export const fetchHistory = (limit = 50) =>
    client.get(`/history?limit=${limit}`).then((r) => r.data)

/** Clear prediction history */
export const clearHistory = () =>
    client.delete('/history').then((r) => r.data)

/** Fetch expected feature names from backend */
export const fetchFeatures = () =>
    client.get('/features').then((r) => r.data)

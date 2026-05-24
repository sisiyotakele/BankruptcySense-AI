/**
 * HistoryTable.jsx
 * ----------------
 * Displays the last N predictions from the backend history endpoint.
 * Supports refresh and clear actions.
 */

import React, { useEffect, useState, useCallback } from 'react'
import { fetchHistory, clearHistory } from '../api/api'

const RISK_BADGE = {
    Low: 'bg-emerald-900 text-emerald-300',
    Medium: 'bg-yellow-900  text-yellow-300',
    High: 'bg-orange-900  text-orange-300',
    Critical: 'bg-red-900     text-red-300',
}

function formatDate(iso) {
    try {
        return new Date(iso).toLocaleString(undefined, {
            month: 'short', day: 'numeric',
            hour: '2-digit', minute: '2-digit',
        })
    } catch {
        return iso
    }
}

export default function HistoryTable() {
    const [entries, setEntries] = useState([])
    const [loading, setLoading] = useState(false)
    const [clearing, setClearing] = useState(false)
    const [error, setError] = useState('')

    const load = useCallback(async () => {
        setLoading(true)
        setError('')
        try {
            const data = await fetchHistory(50)
            setEntries(data)
        } catch (err) {
            setError(err.message)
        } finally {
            setLoading(false)
        }
    }, [])

    useEffect(() => { load() }, [load])

    const handleClear = async () => {
        if (!window.confirm('Clear all prediction history?')) return
        setClearing(true)
        try {
            await clearHistory()
            setEntries([])
        } catch (err) {
            setError(err.message)
        } finally {
            setClearing(false)
        }
    }

    return (
        <div className="space-y-4">
            {/* Toolbar */}
            <div className="flex items-center justify-between">
                <p className="text-sm text-gray-400">
                    {entries.length} recent prediction{entries.length !== 1 ? 's' : ''}
                </p>
                <div className="flex gap-2">
                    <button
                        onClick={load}
                        disabled={loading}
                        className="btn-secondary text-xs py-1.5 px-3"
                        aria-label="Refresh history"
                    >
                        {loading ? '…' : '↻ Refresh'}
                    </button>
                    {entries.length > 0 && (
                        <button
                            onClick={handleClear}
                            disabled={clearing}
                            className="text-xs py-1.5 px-3 rounded-xl bg-red-950 hover:bg-red-900 text-red-400
                         transition-colors focus:outline-none focus:ring-2 focus:ring-red-700
                         disabled:opacity-50"
                            aria-label="Clear history"
                        >
                            {clearing ? '…' : 'Clear'}
                        </button>
                    )}
                </div>
            </div>

            {/* Error */}
            {error && (
                <p role="alert" className="text-sm text-red-400 bg-red-950 border border-red-800 rounded-xl px-4 py-3">
                    {error}
                </p>
            )}

            {/* Empty state */}
            {!loading && entries.length === 0 && !error && (
                <div className="text-center py-12 text-gray-600">
                    <p className="text-4xl mb-3" aria-hidden="true">📋</p>
                    <p className="text-sm">No predictions yet. Run a prediction to see history here.</p>
                </div>
            )}

            {/* Table */}
            {entries.length > 0 && (
                <div className="overflow-x-auto rounded-xl border border-gray-800">
                    <table className="w-full text-sm" aria-label="Prediction history">
                        <thead>
                            <tr className="bg-gray-800 text-gray-400 text-xs uppercase tracking-wide">
                                <th className="px-4 py-3 text-left">Time</th>
                                <th className="px-4 py-3 text-left">Label</th>
                                <th className="px-4 py-3 text-left">Probability</th>
                                <th className="px-4 py-3 text-left">Risk</th>
                                <th className="px-4 py-3 text-left">Trusted</th>
                                <th className="px-4 py-3 text-left">ID</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-800">
                            {entries.map((entry) => {
                                const r = entry.result ?? {}
                                return (
                                    <tr key={entry.id} className="hover:bg-gray-800/50 transition-colors">
                                        <td className="px-4 py-2.5 text-gray-500 text-xs whitespace-nowrap">
                                            {formatDate(entry.timestamp)}
                                        </td>
                                        <td className={`px-4 py-2.5 font-semibold ${r.label === 'Bankrupt' ? 'text-red-400' : 'text-emerald-400'}`}>
                                            {r.label ?? '—'}
                                        </td>
                                        <td className="px-4 py-2.5 font-mono text-gray-300">
                                            {r.probability != null ? `${Math.round(r.probability * 100)}%` : '—'}
                                        </td>
                                        <td className="px-4 py-2.5">
                                            {r.risk_level ? (
                                                <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${RISK_BADGE[r.risk_level] ?? ''}`}>
                                                    {r.risk_level}
                                                </span>
                                            ) : '—'}
                                        </td>
                                        <td className="px-4 py-2.5">
                                            {r.trusted
                                                ? <span className="text-emerald-400">✓</span>
                                                : <span className="text-yellow-400">Low</span>
                                            }
                                        </td>
                                        <td className="px-4 py-2.5 font-mono text-gray-600 text-xs">
                                            {entry.id?.slice(0, 8)}…
                                        </td>
                                    </tr>
                                )
                            })}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    )
}

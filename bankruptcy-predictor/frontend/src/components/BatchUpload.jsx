/**
 * BatchUpload.jsx
 * ---------------
 * CSV upload component. Parses the CSV client-side, sends the records
 * to POST /predict/batch, and displays a summary + per-row results table.
 *
 * Expected CSV format:
 *   Header row with feature names (Attr1, Attr6, …)
 *   One company per row
 */

import React, { useState, useRef } from 'react'
import { predictBatch } from '../api/api'

function parseCSV(text) {
    const lines = text.trim().split(/\r?\n/)
    if (lines.length < 2) throw new Error('CSV must have a header row and at least one data row.')

    const headers = lines[0].split(',').map((h) => h.trim())
    const records = []

    for (let i = 1; i < lines.length; i++) {
        const cols = lines[i].split(',').map((c) => c.trim())
        if (cols.length !== headers.length) continue   // skip malformed rows
        const record = {}
        headers.forEach((h, j) => {
            const v = parseFloat(cols[j])
            if (!isNaN(v)) record[h] = v
        })
        if (Object.keys(record).length > 0) records.push(record)
    }

    if (records.length === 0) throw new Error('No valid data rows found in CSV.')
    return records
}

const RISK_BADGE = {
    Low: 'bg-emerald-900 text-emerald-300',
    Medium: 'bg-yellow-900  text-yellow-300',
    High: 'bg-orange-900  text-orange-300',
    Critical: 'bg-red-900     text-red-300',
}

export default function BatchUpload() {
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')
    const [summary, setSummary] = useState(null)
    const [results, setResults] = useState([])
    const [fileName, setFileName] = useState('')
    const fileRef = useRef(null)

    const handleFile = async (e) => {
        const file = e.target.files?.[0]
        if (!file) return

        setFileName(file.name)
        setError('')
        setSummary(null)
        setResults([])

        let records
        try {
            const text = await file.text()
            records = parseCSV(text)
        } catch (err) {
            setError(err.message)
            return
        }

        if (records.length > 500) {
            setError('Maximum 500 rows per batch. Please split your file.')
            return
        }

        setLoading(true)
        try {
            const data = await predictBatch(records)
            setSummary({
                total: data.total,
                bankrupt: data.bankrupt,
                safe: data.safe,
                errors: data.errors,
                summary: data.summary,
            })
            setResults(data.results)
        } catch (err) {
            setError(err.message)
        } finally {
            setLoading(false)
        }
    }

    const handleReset = () => {
        setSummary(null)
        setResults([])
        setError('')
        setFileName('')
        if (fileRef.current) fileRef.current.value = ''
    }

    return (
        <div className="space-y-5">
            {/* Upload area */}
            <div>
                <label
                    htmlFor="csv-upload"
                    className={`flex flex-col items-center justify-center w-full h-36 border-2 border-dashed
            rounded-2xl cursor-pointer transition-colors duration-150
            ${loading
                            ? 'border-gray-700 bg-gray-900 cursor-not-allowed'
                            : 'border-gray-700 bg-gray-900 hover:border-blue-500 hover:bg-gray-800'
                        }`}
                >
                    <svg className="w-8 h-8 text-gray-500 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                            d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
                    </svg>
                    <p className="text-sm text-gray-400">
                        {fileName
                            ? <span className="text-blue-400 font-medium">{fileName}</span>
                            : <><span className="text-blue-400 font-medium">Click to upload</span> or drag & drop</>
                        }
                    </p>
                    <p className="text-xs text-gray-600 mt-1">CSV with Attr1–Attr64 headers · max 500 rows</p>
                    <input
                        id="csv-upload"
                        ref={fileRef}
                        type="file"
                        accept=".csv,text/csv"
                        className="hidden"
                        onChange={handleFile}
                        disabled={loading}
                        aria-label="Upload CSV file"
                    />
                </label>
            </div>

            {/* Loading */}
            {loading && (
                <div className="flex items-center gap-3 text-sm text-gray-400">
                    <svg className="animate-spin h-4 w-4 text-blue-400" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                    </svg>
                    Running batch predictions…
                </div>
            )}

            {/* Error */}
            {error && (
                <p role="alert" className="text-sm text-red-400 bg-red-950 border border-red-800 rounded-xl px-4 py-3">
                    {error}
                </p>
            )}

            {/* Summary cards */}
            {summary && (
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    {[
                        { label: 'Total', value: summary.total, color: 'text-gray-200' },
                        { label: 'Safe', value: summary.safe, color: 'text-emerald-400' },
                        { label: 'Bankrupt', value: summary.bankrupt, color: 'text-red-400' },
                        { label: 'Bankrupt rate', value: `${(summary.summary.bankrupt_rate * 100).toFixed(1)}%`, color: 'text-orange-400' },
                    ].map(({ label, value, color }) => (
                        <div key={label} className="bg-gray-800 rounded-xl p-4 text-center">
                            <p className={`text-2xl font-bold ${color}`}>{value}</p>
                            <p className="text-xs text-gray-500 mt-1">{label}</p>
                        </div>
                    ))}
                </div>
            )}

            {/* Results table */}
            {results.length > 0 && (
                <div>
                    <div className="flex items-center justify-between mb-3">
                        <p className="text-sm text-gray-400">{results.length} results</p>
                        <button onClick={handleReset} className="btn-secondary text-xs py-1.5 px-3">
                            Clear
                        </button>
                    </div>
                    <div className="overflow-x-auto rounded-xl border border-gray-800">
                        <table className="w-full text-sm" aria-label="Batch prediction results">
                            <thead>
                                <tr className="bg-gray-800 text-gray-400 text-xs uppercase tracking-wide">
                                    <th className="px-4 py-3 text-left">#</th>
                                    <th className="px-4 py-3 text-left">Label</th>
                                    <th className="px-4 py-3 text-left">Probability</th>
                                    <th className="px-4 py-3 text-left">Risk</th>
                                    <th className="px-4 py-3 text-left">Trusted</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-800">
                                {results.map((r, i) => (
                                    <tr key={i} className="hover:bg-gray-800/50 transition-colors">
                                        <td className="px-4 py-2.5 text-gray-500 font-mono">{i + 1}</td>
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
                                            {r.error
                                                ? <span className="text-red-400 text-xs">{r.error}</span>
                                                : r.trusted
                                                    ? <span className="text-emerald-400">✓</span>
                                                    : <span className="text-yellow-400">Low</span>
                                            }
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    )
}

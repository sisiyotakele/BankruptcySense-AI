/**
 * PredictionForm.jsx
 * ------------------
 * Form for entering financial ratios and submitting a single prediction.
 * Shows the 20 most commonly used features with labels.
 * Users can also enter any Attr1–Attr64 value via the "Other features" section.
 */

import React, { useState } from 'react'

// The 20 most informative features with human-readable labels
const PRIMARY_FEATURES = [
    { key: 'Attr1', label: 'Net profit / Total assets' },
    { key: 'Attr5', label: 'Cash / Short-term liabilities' },
    { key: 'Attr6', label: 'Retained earnings / Total assets' },
    { key: 'Attr9', label: 'Sales / Total assets' },
    { key: 'Attr11', label: 'Gross profit / Short-term liabilities' },
    { key: 'Attr13', label: 'EBIT / Total assets' },
    { key: 'Attr15', label: 'Total liabilities / Total assets' },
    { key: 'Attr16', label: 'Working capital / Total assets' },
    { key: 'Attr18', label: 'Book value of equity / Total liabilities' },
    { key: 'Attr19', label: 'Revenue / Total assets' },
    { key: 'Attr21', label: 'Net profit / Sales' },
    { key: 'Attr22', label: 'Gross profit / Total assets' },
    { key: 'Attr23', label: 'Gross profit / Sales' },
    { key: 'Attr24', label: 'Working capital / Fixed assets' },
    { key: 'Attr25', label: 'Log(total assets)' },
    { key: 'Attr26', label: 'Total liabilities / Cash' },
    { key: 'Attr27', label: 'Profit on operating activities / Financial expenses' },
    { key: 'Attr29', label: 'Log(sales)' },
    { key: 'Attr34', label: 'Operating expenses / Short-term liabilities' },
    { key: 'Attr35', label: 'Total liabilities / (Operating profit + Depreciation)' },
]

const EMPTY_FORM = Object.fromEntries(PRIMARY_FEATURES.map((f) => [f.key, '']))

export default function PredictionForm({ onSubmit, loading }) {
    const [values, setValues] = useState(EMPTY_FORM)
    const [extraKey, setExtraKey] = useState('')
    const [extraVal, setExtraVal] = useState('')
    const [extras, setExtras] = useState({})
    const [formError, setFormError] = useState('')

    const handleChange = (key, val) => {
        setValues((prev) => ({ ...prev, [key]: val }))
        setFormError('')
    }

    const addExtra = () => {
        const k = extraKey.trim()
        const v = extraVal.trim()
        if (!k || !v) return
        if (!/^Attr([1-9]|[1-5][0-9]|6[0-4])$/.test(k) || k === 'Attr37') {
            setFormError('Extra key must be Attr1–Attr64 (excluding Attr37).')
            return
        }
        if (isNaN(Number(v))) {
            setFormError('Extra value must be a number.')
            return
        }
        setExtras((prev) => ({ ...prev, [k]: v }))
        setExtraKey('')
        setExtraVal('')
        setFormError('')
    }

    const removeExtra = (key) =>
        setExtras((prev) => { const n = { ...prev }; delete n[key]; return n })

    const handleSubmit = (e) => {
        e.preventDefault()
        setFormError('')

        // Collect all non-empty numeric values
        const payload = {}
        for (const [k, v] of Object.entries({ ...values, ...extras })) {
            if (v === '' || v === null || v === undefined) continue
            const num = Number(v)
            if (isNaN(num)) {
                setFormError(`"${k}" must be a number.`)
                return
            }
            payload[k] = num
        }

        if (Object.keys(payload).length === 0) {
            setFormError('Enter at least one financial ratio before predicting.')
            return
        }

        onSubmit(payload)
    }

    const handleReset = () => {
        setValues(EMPTY_FORM)
        setExtras({})
        setFormError('')
    }

    return (
        <form onSubmit={handleSubmit} noValidate>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {PRIMARY_FEATURES.map(({ key, label }) => (
                    <div key={key}>
                        <label className="label" htmlFor={key}>
                            <span className="text-blue-400 font-mono">{key}</span>
                            <span className="ml-1 normal-case text-gray-500">{label}</span>
                        </label>
                        <input
                            id={key}
                            type="number"
                            step="any"
                            placeholder="e.g. 0.12"
                            value={values[key]}
                            onChange={(e) => handleChange(key, e.target.value)}
                            className="input-field"
                            aria-label={`${key}: ${label}`}
                        />
                    </div>
                ))}
            </div>

            {/* Extra features */}
            <div className="mt-6">
                <p className="label">Add other features (optional)</p>
                <div className="flex gap-2 items-start">
                    <input
                        type="text"
                        placeholder="Attr47"
                        value={extraKey}
                        onChange={(e) => setExtraKey(e.target.value)}
                        className="input-field w-28"
                        aria-label="Extra feature name"
                    />
                    <input
                        type="number"
                        step="any"
                        placeholder="value"
                        value={extraVal}
                        onChange={(e) => setExtraVal(e.target.value)}
                        className="input-field w-32"
                        aria-label="Extra feature value"
                    />
                    <button
                        type="button"
                        onClick={addExtra}
                        className="btn-secondary text-sm whitespace-nowrap"
                    >
                        + Add
                    </button>
                </div>

                {Object.keys(extras).length > 0 && (
                    <div className="flex flex-wrap gap-2 mt-3">
                        {Object.entries(extras).map(([k, v]) => (
                            <span
                                key={k}
                                className="flex items-center gap-1 bg-gray-800 text-gray-300 text-xs px-2 py-1 rounded-lg"
                            >
                                <span className="font-mono text-blue-400">{k}</span>
                                <span>= {v}</span>
                                <button
                                    type="button"
                                    onClick={() => removeExtra(k)}
                                    className="ml-1 text-gray-500 hover:text-red-400 transition-colors"
                                    aria-label={`Remove ${k}`}
                                >
                                    ×
                                </button>
                            </span>
                        ))}
                    </div>
                )}
            </div>

            {formError && (
                <p role="alert" className="mt-3 text-sm text-red-400">
                    {formError}
                </p>
            )}

            <div className="flex gap-3 mt-6">
                <button type="submit" disabled={loading} className="btn-primary">
                    {loading ? (
                        <span className="flex items-center gap-2">
                            <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                            </svg>
                            Predicting…
                        </span>
                    ) : (
                        'Predict'
                    )}
                </button>
                <button type="button" onClick={handleReset} className="btn-secondary">
                    Reset
                </button>
            </div>
        </form>
    )
}

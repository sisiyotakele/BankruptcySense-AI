/**
 * ResultCard.jsx
 * --------------
 * Displays the prediction result: label, probability gauge,
 * risk level badge, confidence flag, and threshold info.
 */

import React from 'react'

const RISK_STYLES = {
    Low: { bar: 'bg-emerald-500', badge: 'bg-emerald-900 text-emerald-300', icon: '✓' },
    Medium: { bar: 'bg-yellow-500', badge: 'bg-yellow-900  text-yellow-300', icon: '⚠' },
    High: { bar: 'bg-orange-500', badge: 'bg-orange-900  text-orange-300', icon: '⚠' },
    Critical: { bar: 'bg-red-500', badge: 'bg-red-900     text-red-300', icon: '✕' },
}

const LABEL_STYLES = {
    Safe: 'text-emerald-400',
    Bankrupt: 'text-red-400',
}

export default function ResultCard({ result }) {
    if (!result) return null

    const {
        label,
        probability,
        risk_level,
        trusted,
        threshold,
        top_features = [],
    } = result

    const pct = Math.round((probability ?? 0) * 100)
    const riskStyle = RISK_STYLES[risk_level] ?? RISK_STYLES.Medium
    const labelStyle = LABEL_STYLES[label] ?? 'text-gray-300'

    return (
        <div className="card space-y-5" role="region" aria-label="Prediction result">

            {/* Header */}
            <div className="flex items-center justify-between flex-wrap gap-3">
                <div>
                    <p className="text-xs text-gray-500 uppercase tracking-widest mb-1">Prediction</p>
                    <p className={`text-3xl font-bold ${labelStyle}`}>{label}</p>
                </div>
                <span className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-semibold ${riskStyle.badge}`}>
                    <span aria-hidden="true">{riskStyle.icon}</span>
                    {risk_level} Risk
                </span>
            </div>

            {/* Probability gauge */}
            <div>
                <div className="flex justify-between text-xs text-gray-400 mb-1.5">
                    <span>Bankruptcy probability</span>
                    <span className="font-mono font-semibold text-gray-200">{pct}%</span>
                </div>
                <div className="w-full bg-gray-800 rounded-full h-3 overflow-hidden" role="progressbar"
                    aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}>
                    <div
                        className={`h-3 rounded-full transition-all duration-500 ${riskStyle.bar}`}
                        style={{ width: `${pct}%` }}
                    />
                </div>
            </div>

            {/* Threshold + confidence */}
            <div className="flex flex-wrap gap-4 text-sm">
                <div className="flex items-center gap-2">
                    <span className="text-gray-500">Decision threshold:</span>
                    <span className="font-mono text-gray-300">{threshold}</span>
                </div>
                <div className="flex items-center gap-2">
                    <span className="text-gray-500">Confidence:</span>
                    {trusted ? (
                        <span className="text-emerald-400 font-medium">High ✓</span>
                    ) : (
                        <span className="text-yellow-400 font-medium">Low — treat with caution</span>
                    )}
                </div>
            </div>

            {/* Top contributing features */}
            {top_features.length > 0 && (
                <div>
                    <p className="text-xs text-gray-500 uppercase tracking-widest mb-3">
                        Top contributing features
                    </p>
                    <div className="space-y-2">
                        {top_features.map(({ feature, value, importance }) => (
                            <div key={feature} className="flex items-center gap-3 text-sm">
                                <span className="font-mono text-blue-400 w-14 shrink-0">{feature}</span>
                                <div className="flex-1 bg-gray-800 rounded-full h-2 overflow-hidden">
                                    <div
                                        className="h-2 bg-blue-500 rounded-full"
                                        style={{ width: `${Math.round(importance * 100 * 10)}%`, maxWidth: '100%' }}
                                    />
                                </div>
                                <span className="text-gray-400 w-16 text-right font-mono">
                                    {(importance * 100).toFixed(1)}%
                                </span>
                                <span className="text-gray-500 w-16 text-right font-mono text-xs">
                                    val: {value}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    )
}

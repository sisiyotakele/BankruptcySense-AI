/**
 * ResultCard.jsx — Main prediction result with gauge, stats, and feature bars
 */
import React from 'react'
import RiskGauge from './RiskGauge'

const STAT_ITEMS = (r) => [
    {
        label: 'Probability', value: `${Math.round((r.probability ?? 0) * 100)}%`,
        color: 'text-gray-100'
    },
    { label: 'Threshold', value: r.threshold, color: 'text-blue-400' },
    {
        label: 'Confidence', value: r.trusted ? 'High ✓' : 'Low',
        color: r.trusted ? 'text-emerald-400' : 'text-yellow-400'
    },
    { label: 'Features used', value: r.top_features?.length ?? 0, color: 'text-purple-400' },
]

export default function ResultCard({ result }) {
    if (!result) return null
    const { label, probability = 0, risk_level, top_features = [] } = result

    return (
        <div className="card-glow animate-fade-in-up space-y-5">
            {/* Gauge */}
            <div className="flex justify-center py-2">
                <RiskGauge
                    probability={probability}
                    riskLevel={risk_level}
                    label={label}
                />
            </div>

            {/* Stats row */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {STAT_ITEMS(result).map(({ label: l, value, color }) => (
                    <div key={l} className="stat-card text-center">
                        <p className={`text-lg font-bold ${color}`}>{value}</p>
                        <p className="text-xs text-gray-500 mt-0.5">{l}</p>
                    </div>
                ))}
            </div>

            {/* Feature importance bars */}
            {top_features.length > 0 && (
                <div>
                    <p className="text-xs text-gray-500 uppercase tracking-widest mb-3">
                        Top contributing features
                    </p>
                    <div className="space-y-2.5">
                        {top_features.map(({ feature, value, importance }, i) => (
                            <div key={feature} className="space-y-1"
                                style={{ animation: `fadeInUp 0.3s ease-out ${i * 0.07}s both` }}>
                                <div className="flex justify-between text-xs">
                                    <span className="font-mono text-blue-400">{feature}</span>
                                    <div className="flex gap-3 text-gray-500">
                                        <span>val: <span className="text-gray-300">{value}</span></span>
                                        <span className="text-gray-300 font-medium">
                                            {(importance * 100).toFixed(1)}%
                                        </span>
                                    </div>
                                </div>
                                <div className="w-full bg-gray-800 rounded-full h-1.5 overflow-hidden">
                                    <div
                                        className="h-1.5 rounded-full bg-gradient-to-r from-blue-600 to-blue-400"
                                        style={{
                                            width: `${Math.min(importance * 100 * 8, 100)}%`,
                                            transition: `width 0.6s cubic-bezier(0.4,0,0.2,1) ${i * 0.07}s`,
                                        }}
                                    />
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    )
}

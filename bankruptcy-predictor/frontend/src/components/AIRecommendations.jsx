/**
 * AIRecommendations.jsx — AI-generated business recommendations panel
 */
import React, { useState } from 'react'

const URGENCY_STYLE = {
    'Monitor quarterly': 'text-emerald-400 bg-emerald-950 border-emerald-800',
    'Review within 30 days': 'text-yellow-400  bg-yellow-950  border-yellow-800',
    'Act within 2 weeks': 'text-orange-400  bg-orange-950  border-orange-800',
    'Immediate action required': 'text-red-400     bg-red-950     border-red-800',
}

const RISK_ICON = {
    Low: '✅',
    Medium: '⚠️',
    High: '🔶',
    Critical: '🚨',
}

export default function AIRecommendations({ recommendations }) {
    const [expanded, setExpanded] = useState(true)
    if (!recommendations) return null

    const {
        risk_level, probability_pct, summary,
        recommendations: tips = [],
        feature_advice = [],
        action_urgency,
    } = recommendations

    const urgencyStyle = URGENCY_STYLE[action_urgency] ?? URGENCY_STYLE['Review within 30 days']

    return (
        <div className="card-glow animate-fade-in-up-delay2 space-y-4">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <span className="text-xl" aria-hidden="true">🤖</span>
                    <h3 className="font-semibold text-gray-200">AI Recommendations</h3>
                </div>
                <button
                    onClick={() => setExpanded(e => !e)}
                    className="text-gray-500 hover:text-gray-300 transition-colors text-sm"
                    aria-label={expanded ? 'Collapse recommendations' : 'Expand recommendations'}
                >
                    {expanded ? '▲ Collapse' : '▼ Expand'}
                </button>
            </div>

            {/* Summary */}
            <div className="flex items-start gap-3 bg-gray-800/50 rounded-xl p-3">
                <span className="text-2xl mt-0.5" aria-hidden="true">{RISK_ICON[risk_level]}</span>
                <div>
                    <p className="text-sm text-gray-300">{summary}</p>
                    <span className={`inline-flex items-center mt-2 px-2.5 py-0.5 rounded-full text-xs font-semibold border ${urgencyStyle}`}>
                        ⏱ {action_urgency}
                    </span>
                </div>
            </div>

            {expanded && (
                <>
                    {/* Feature-specific advice */}
                    {feature_advice.length > 0 && (
                        <div>
                            <p className="text-xs text-gray-500 uppercase tracking-widest mb-2">
                                Based on your key risk drivers
                            </p>
                            <div className="space-y-2">
                                {feature_advice.map((advice, i) => (
                                    <div key={i}
                                        className="flex items-start gap-2 text-sm text-gray-300 bg-blue-950/30 border border-blue-900/30 rounded-lg px-3 py-2"
                                        style={{ animationDelay: `${i * 0.1}s` }}
                                    >
                                        <span className="text-blue-400 mt-0.5 shrink-0">→</span>
                                        {advice}
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* General recommendations */}
                    <div>
                        <p className="text-xs text-gray-500 uppercase tracking-widest mb-2">
                            Action plan
                        </p>
                        <ol className="space-y-2">
                            {tips.map((tip, i) => (
                                <li key={i}
                                    className="flex items-start gap-3 text-sm text-gray-300"
                                    style={{ animation: `fadeInUp 0.3s ease-out ${i * 0.08}s both` }}
                                >
                                    <span className="shrink-0 w-5 h-5 rounded-full bg-gray-800 border border-gray-700
                                   flex items-center justify-center text-xs text-gray-400 font-mono mt-0.5">
                                        {i + 1}
                                    </span>
                                    {tip}
                                </li>
                            ))}
                        </ol>
                    </div>
                </>
            )}
        </div>
    )
}

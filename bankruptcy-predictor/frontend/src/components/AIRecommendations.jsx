/**
 * AIRecommendations.jsx
 * ---------------------
 * Generates AI recommendations entirely on the frontend from the prediction
 * result. Works regardless of backend version — no dependency on backend
 * returning a recommendations field.
 */
import React, { useState } from 'react'

// ── Recommendation database ────────────────────────────────────────────────────
const TIPS = {
    Low: [
        'Business appears financially healthy. Maintain current liquidity ratios.',
        'Continue monitoring cash flow and debt-to-equity ratio quarterly.',
        'Consider reinvesting profits to strengthen retained earnings.',
        'Low bankruptcy risk — suitable for expansion or new credit lines.',
        'Schedule an annual financial health review to stay on track.',
    ],
    Medium: [
        'Monitor short-term liabilities closely — ensure coverage ratio stays above 1.5.',
        'Review operating expenses and identify areas to reduce overhead.',
        'Strengthen working capital by improving accounts receivable turnover.',
        'Consider refinancing short-term debt to longer terms to ease cash pressure.',
        'Build a 3–6 month cash reserve as a financial buffer.',
        'Engage a financial advisor for a mid-year review.',
    ],
    High: [
        '⚠ Immediate action required: review and reduce total liabilities.',
        'Prioritise improving net profit margin — target at least 5% within 2 quarters.',
        'Negotiate extended payment terms with suppliers to improve cash flow.',
        'Consider asset liquidation to reduce debt burden.',
        'Engage a financial advisor to restructure debt obligations.',
        'Suspend non-essential capital expenditure until ratios improve.',
        'Prepare a 90-day cash flow forecast and review weekly.',
    ],
    Critical: [
        '🚨 Critical risk — seek professional financial or legal counsel immediately.',
        'Explore debt restructuring or insolvency protection options.',
        'Prioritise paying secured creditors to avoid asset seizure.',
        'Conduct an emergency cash flow audit — identify all outflows within 30 days.',
        'Consider voluntary administration as a protective measure.',
        'Communicate proactively with lenders to negotiate forbearance agreements.',
        'Halt all non-essential spending and freeze new hiring immediately.',
    ],
}

const FEATURE_ADVICE = {
    Attr35: 'High debt-to-EBITDA ratio detected — focus on reducing total liabilities.',
    Attr39: 'Low profit on operating activities — review pricing and cost structure.',
    Attr21: 'Weak net profit margin — target operational efficiency improvements.',
    Attr1: 'Net profit/assets ratio is a key driver — improve asset utilisation.',
    Attr6: 'Retained earnings are low — reduce dividend payouts to build reserves.',
    Attr13: 'EBIT/assets ratio is critical — improve earnings before interest and tax.',
    Attr15: 'High total liabilities ratio — prioritise debt reduction.',
    Attr22: 'Gross profit/assets is low — review pricing strategy.',
    Attr27: 'Operating profit vs financial expenses is unfavourable — reduce interest burden.',
    Attr41: 'Working capital efficiency needs improvement — speed up receivables collection.',
    Attr42: 'Current ratio is concerning — reduce short-term obligations.',
    Attr46: 'Revenue growth is stagnant — explore new markets or product lines.',
    Attr25: 'Asset base is small — consider strategic asset acquisition.',
    Attr26: 'High liabilities relative to cash — improve cash generation.',
}

const URGENCY = {
    Low: { label: 'Monitor quarterly', style: 'text-emerald-400 bg-emerald-950 border-emerald-800' },
    Medium: { label: 'Review within 30 days', style: 'text-yellow-400  bg-yellow-950  border-yellow-800' },
    High: { label: 'Act within 2 weeks', style: 'text-orange-400  bg-orange-950  border-orange-800' },
    Critical: { label: 'Immediate action required', style: 'text-red-400     bg-red-950     border-red-800' },
}

const RISK_ICON = { Low: '✅', Medium: '⚠️', High: '🔶', Critical: '🚨' }
const RISK_COLOR = {
    Low: 'text-emerald-400',
    Medium: 'text-yellow-400',
    High: 'text-orange-400',
    Critical: 'text-red-400',
}

// ── Build recommendations from result ─────────────────────────────────────────
function buildRecommendations(result) {
    const risk = result.risk_level ?? 'Medium'
    const probability = result.probability ?? 0
    const pct = Math.round(probability * 100)
    const topFeatures = result.top_features ?? []

    const featureAdvice = topFeatures
        .slice(0, 3)
        .map(f => FEATURE_ADVICE[f.feature])
        .filter(Boolean)

    return {
        risk_level: risk,
        probability_pct: `${pct}%`,
        summary: `This business has a ${pct}% bankruptcy probability, indicating ${risk.toLowerCase()} financial risk.`,
        tips: TIPS[risk] ?? TIPS.Medium,
        feature_advice: featureAdvice,
        urgency: URGENCY[risk] ?? URGENCY.Medium,
    }
}

// ── Component ──────────────────────────────────────────────────────────────────
export default function AIRecommendations({ result }) {
    const [expanded, setExpanded] = useState(true)

    // Accept either a full result object or a pre-built recommendations object
    if (!result) return null

    const rec = result.risk_level !== undefined
        ? buildRecommendations(result)          // build from raw result
        : buildRecommendations({
            risk_level: result.risk_level,
            probability: 0,
            top_features: []
        })

    const { risk_level, summary, tips, feature_advice, urgency } = rec

    return (
        <div className="card-glow animate-fade-in-up-delay2 space-y-4">

            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <span className="text-xl" aria-hidden="true">🤖</span>
                    <h3 className="font-semibold text-gray-200">AI Recommendations</h3>
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${RISK_COLOR[risk_level]}`}>
                        {risk_level} Risk
                    </span>
                </div>
                <button
                    onClick={() => setExpanded(e => !e)}
                    className="text-gray-500 hover:text-gray-300 transition-colors text-sm px-2 py-1 rounded-lg hover:bg-gray-800"
                    aria-label={expanded ? 'Collapse' : 'Expand'}
                >
                    {expanded ? '▲' : '▼'}
                </button>
            </div>

            {/* Summary banner */}
            <div className="flex items-start gap-3 bg-gray-800/60 rounded-xl p-3.5 border border-gray-700/50">
                <span className="text-2xl mt-0.5 shrink-0" aria-hidden="true">
                    {RISK_ICON[risk_level]}
                </span>
                <div className="space-y-2">
                    <p className="text-sm text-gray-300 leading-relaxed">{summary}</p>
                    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border ${urgency.style}`}>
                        <span aria-hidden="true">⏱</span>
                        {urgency.label}
                    </span>
                </div>
            </div>

            {expanded && (
                <div className="space-y-4">

                    {/* Feature-specific advice */}
                    {feature_advice.length > 0 && (
                        <div>
                            <p className="text-xs text-gray-500 uppercase tracking-widest mb-2.5 flex items-center gap-1.5">
                                <span className="w-3 h-px bg-gray-700 inline-block" />
                                Based on your key risk drivers
                                <span className="w-3 h-px bg-gray-700 inline-block" />
                            </p>
                            <div className="space-y-2">
                                {feature_advice.map((advice, i) => (
                                    <div key={i}
                                        className="flex items-start gap-2.5 text-sm text-gray-300
                               bg-blue-950/30 border border-blue-900/30 rounded-xl px-3.5 py-2.5"
                                        style={{ animation: `fadeInUp 0.3s ease-out ${i * 0.08}s both` }}
                                    >
                                        <span className="text-blue-400 font-bold mt-0.5 shrink-0">→</span>
                                        <span>{advice}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Action plan */}
                    <div>
                        <p className="text-xs text-gray-500 uppercase tracking-widest mb-2.5 flex items-center gap-1.5">
                            <span className="w-3 h-px bg-gray-700 inline-block" />
                            Action plan
                            <span className="w-3 h-px bg-gray-700 inline-block" />
                        </p>
                        <ol className="space-y-2.5">
                            {tips.map((tip, i) => (
                                <li key={i}
                                    className="flex items-start gap-3 text-sm text-gray-300"
                                    style={{ animation: `fadeInUp 0.3s ease-out ${i * 0.06}s both` }}
                                >
                                    <span className="shrink-0 w-5 h-5 rounded-full bg-gray-800 border border-gray-700
                                   flex items-center justify-center text-xs text-gray-400 font-mono mt-0.5">
                                        {i + 1}
                                    </span>
                                    <span className="leading-relaxed">{tip}</span>
                                </li>
                            ))}
                        </ol>
                    </div>

                    {/* Disclaimer */}
                    <p className="text-xs text-gray-600 border-t border-gray-800 pt-3">
                        These recommendations are generated by AI based on financial risk indicators.
                        Always consult a qualified financial advisor before making business decisions.
                    </p>
                </div>
            )}
        </div>
    )
}

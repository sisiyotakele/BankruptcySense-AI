/**
 * RiskGauge.jsx — Animated semicircle gauge showing bankruptcy probability
 */
import React, { useEffect, useState } from 'react'

const RISK_COLOR = {
    Low: { stroke: '#10b981', text: 'text-emerald-400', glow: '#10b98133' },
    Medium: { stroke: '#f59e0b', text: 'text-yellow-400', glow: '#f59e0b33' },
    High: { stroke: '#f97316', text: 'text-orange-400', glow: '#f9731633' },
    Critical: { stroke: '#ef4444', text: 'text-red-400', glow: '#ef444433' },
}

export default function RiskGauge({ probability = 0, riskLevel = 'Low', label = 'Safe' }) {
    const [displayed, setDisplayed] = useState(0)

    useEffect(() => {
        let start = 0
        const target = Math.round(probability * 100)
        const step = Math.ceil(target / 30)
        const timer = setInterval(() => {
            start += step
            if (start >= target) { setDisplayed(target); clearInterval(timer) }
            else setDisplayed(start)
        }, 20)
        return () => clearInterval(timer)
    }, [probability])

    const colors = RISK_COLOR[riskLevel] ?? RISK_COLOR.Medium
    const r = 70
    const cx = 90
    const cy = 90
    const circumference = Math.PI * r          // semicircle
    const offset = circumference * (1 - probability)

    return (
        <div className="flex flex-col items-center">
            <div className="relative" style={{ width: 180, height: 100 }}>
                <svg width="180" height="100" viewBox="0 0 180 100" aria-label={`Risk gauge: ${displayed}%`}>
                    <defs>
                        <filter id="glow">
                            <feGaussianBlur stdDeviation="3" result="coloredBlur" />
                            <feMerge><feMergeNode in="coloredBlur" /><feMergeNode in="SourceGraphic" /></feMerge>
                        </filter>
                    </defs>
                    {/* Track */}
                    <path
                        d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`}
                        fill="none" stroke="#1f2937" strokeWidth="12" strokeLinecap="round"
                    />
                    {/* Progress */}
                    <path
                        d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`}
                        fill="none"
                        stroke={colors.stroke}
                        strokeWidth="12"
                        strokeLinecap="round"
                        strokeDasharray={circumference}
                        strokeDashoffset={offset}
                        filter="url(#glow)"
                        style={{ transition: 'stroke-dashoffset 0.8s cubic-bezier(0.4,0,0.2,1)' }}
                    />
                    {/* Tick marks */}
                    {[0, 25, 50, 75, 100].map((pct) => {
                        const angle = Math.PI * (pct / 100)
                        const tx = cx - r * Math.cos(angle)
                        const ty = cy - r * Math.sin(angle)
                        return (
                            <circle key={pct} cx={tx} cy={ty} r="2"
                                fill={pct <= displayed ? colors.stroke : '#374151'} />
                        )
                    })}
                </svg>
                {/* Center text */}
                <div className="absolute inset-0 flex flex-col items-center justify-end pb-1">
                    <span className={`text-3xl font-bold tabular-nums ${colors.text}`}>
                        {displayed}%
                    </span>
                </div>
            </div>

            {/* Label below gauge */}
            <div className="mt-2 text-center">
                <span className={`text-lg font-bold ${colors.text}`}>{label}</span>
                <div className={`inline-flex items-center gap-1.5 ml-2 px-2.5 py-0.5 rounded-full text-xs font-semibold border ${riskLevel === 'Low' ? 'risk-low' :
                        riskLevel === 'Medium' ? 'risk-medium' :
                            riskLevel === 'High' ? 'risk-high' : 'risk-critical'
                    }`}>
                    <span className="relative flex h-2 w-2">
                        <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${riskLevel === 'Low' ? 'bg-emerald-400' :
                                riskLevel === 'Medium' ? 'bg-yellow-400' :
                                    riskLevel === 'High' ? 'bg-orange-400' : 'bg-red-400'
                            }`} />
                        <span className={`relative inline-flex rounded-full h-2 w-2 ${riskLevel === 'Low' ? 'bg-emerald-500' :
                                riskLevel === 'Medium' ? 'bg-yellow-500' :
                                    riskLevel === 'High' ? 'bg-orange-500' : 'bg-red-500'
                            }`} />
                    </span>
                    {riskLevel} Risk
                </div>
            </div>
        </div>
    )
}

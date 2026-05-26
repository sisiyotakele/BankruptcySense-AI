/**
 * DashboardStats.jsx — Model performance stats shown on the landing page
 */
import React from 'react'
import { RadialBarChart, RadialBar, ResponsiveContainer, Tooltip } from 'recharts'

const METRICS = [
    { label: 'ROC-AUC', value: 91.2, target: 90, color: '#3b82f6', unit: '%' },
    { label: 'Recall', value: 79.3, target: 75, color: '#10b981', unit: '%' },
    { label: 'CV Std', value: 0.5, target: 5, color: '#8b5cf6', unit: '%', invert: true },
    { label: 'Features', value: 30, target: null, color: '#f59e0b', unit: '' },
]

function MetricCard({ label, value, target, color, unit, invert }) {
    const passes = target == null ? true : invert ? value < target : value >= target
    return (
        <div className="stat-card flex flex-col items-center text-center gap-1 py-5">
            <div className="relative w-16 h-16">
                <ResponsiveContainer width="100%" height="100%">
                    <RadialBarChart cx="50%" cy="50%" innerRadius="60%" outerRadius="100%"
                        data={[{ value: Math.min(value, 100), fill: color }]}
                        startAngle={90} endAngle={-270}>
                        <RadialBar dataKey="value" cornerRadius={4} background={{ fill: '#1f2937' }} />
                    </RadialBarChart>
                </ResponsiveContainer>
                <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-xs font-bold" style={{ color }}>
                        {value}{unit}
                    </span>
                </div>
            </div>
            <p className="text-xs text-gray-400 font-medium">{label}</p>
            {target != null && (
                <span className={`text-xs px-1.5 py-0.5 rounded-full font-medium ${passes ? 'bg-emerald-950 text-emerald-400' : 'bg-red-950 text-red-400'
                    }`}>
                    {passes ? '✓ Pass' : '✗ Fail'}
                </span>
            )}
        </div>
    )
}

export default function DashboardStats() {
    return (
        <div className="card">
            <div className="flex items-center gap-2 mb-4">
                <span className="text-lg" aria-hidden="true">📊</span>
                <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-widest">
                    Model Performance
                </h3>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {METRICS.map(m => <MetricCard key={m.label} {...m} />)}
            </div>
            <p className="text-xs text-gray-600 mt-3 text-center">
                Trained on Polish Bankruptcy Dataset · 5,910 companies · Random Forest
            </p>
        </div>
    )
}

/**
 * FeatureChart.jsx — Recharts horizontal bar chart of top-5 feature importances
 */
import React from 'react'
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid,
    Tooltip, ResponsiveContainer, Cell,
} from 'recharts'

const COLORS = ['#3b82f6', '#6366f1', '#8b5cf6', '#a78bfa', '#c4b5fd']

const CustomTooltip = ({ active, payload }) => {
    if (!active || !payload?.length) return null
    const { feature, importance, value } = payload[0].payload
    return (
        <div className="bg-gray-800 border border-gray-700 rounded-xl px-3 py-2 text-sm shadow-xl">
            <p className="font-mono text-blue-400 font-semibold mb-1">{feature}</p>
            <p className="text-gray-300">Importance: <span className="text-white font-medium">{(importance * 100).toFixed(2)}%</span></p>
            <p className="text-gray-300">Scaled value: <span className="text-white">{value}</span></p>
        </div>
    )
}

export default function FeatureChart({ features = [] }) {
    if (!features.length) return null
    const data = features.map(f => ({
        ...f, pct: parseFloat((f.importance * 100).toFixed(2)),
    }))

    return (
        <div className="card animate-fade-in-up-delay">
            <p className="text-xs text-gray-500 uppercase tracking-widest mb-4">
                Feature importance breakdown
            </p>
            <ResponsiveContainer width="100%" height={190}>
                <BarChart data={data} layout="vertical"
                    margin={{ top: 0, right: 28, left: 8, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" horizontal={false} />
                    <XAxis type="number" domain={[0, 'dataMax']}
                        tickFormatter={v => `${v}%`}
                        tick={{ fill: '#6b7280', fontSize: 11 }}
                        axisLine={false} tickLine={false} />
                    <YAxis type="category" dataKey="feature" width={52}
                        tick={{ fill: '#60a5fa', fontSize: 12, fontFamily: 'monospace' }}
                        axisLine={false} tickLine={false} />
                    <Tooltip content={<CustomTooltip />}
                        cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
                    <Bar dataKey="pct" radius={[0, 4, 4, 0]} maxBarSize={18}>
                        {data.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                    </Bar>
                </BarChart>
            </ResponsiveContainer>
        </div>
    )
}

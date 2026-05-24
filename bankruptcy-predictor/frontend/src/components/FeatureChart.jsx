/**
 * FeatureChart.jsx
 * ----------------
 * Horizontal bar chart of the top-5 feature importances
 * for the most recent prediction. Uses Recharts.
 */

import React from 'react'
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Cell,
} from 'recharts'

const BAR_COLORS = ['#3b82f6', '#6366f1', '#8b5cf6', '#a78bfa', '#c4b5fd']

const CustomTooltip = ({ active, payload }) => {
    if (!active || !payload?.length) return null
    const { feature, importance, value } = payload[0].payload
    return (
        <div className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm shadow-xl">
            <p className="font-mono text-blue-400 font-semibold">{feature}</p>
            <p className="text-gray-300">Importance: <span className="text-white">{(importance * 100).toFixed(2)}%</span></p>
            <p className="text-gray-300">Scaled value: <span className="text-white">{value}</span></p>
        </div>
    )
}

export default function FeatureChart({ features = [] }) {
    if (!features.length) return null

    const data = features.map((f) => ({
        feature: f.feature,
        importance: f.importance,
        value: f.value,
        pct: parseFloat((f.importance * 100).toFixed(2)),
    }))

    return (
        <div className="card">
            <p className="text-xs text-gray-500 uppercase tracking-widest mb-4">
                Feature importance (top 5)
            </p>
            <ResponsiveContainer width="100%" height={200}>
                <BarChart
                    data={data}
                    layout="vertical"
                    margin={{ top: 0, right: 24, left: 8, bottom: 0 }}
                >
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" horizontal={false} />
                    <XAxis
                        type="number"
                        domain={[0, 'dataMax']}
                        tickFormatter={(v) => `${v}%`}
                        tick={{ fill: '#9ca3af', fontSize: 11 }}
                        axisLine={false}
                        tickLine={false}
                    />
                    <YAxis
                        type="category"
                        dataKey="feature"
                        tick={{ fill: '#60a5fa', fontSize: 12, fontFamily: 'monospace' }}
                        axisLine={false}
                        tickLine={false}
                        width={52}
                    />
                    <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.04)' }} />
                    <Bar dataKey="pct" radius={[0, 4, 4, 0]} maxBarSize={20}>
                        {data.map((_, i) => (
                            <Cell key={i} fill={BAR_COLORS[i % BAR_COLORS.length]} />
                        ))}
                    </Bar>
                </BarChart>
            </ResponsiveContainer>
        </div>
    )
}

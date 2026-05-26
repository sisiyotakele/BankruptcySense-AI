/**
 * App.jsx — BankruptcySense AI main application
 * Dark dashboard with animated gauge, AI recommendations, and batch upload
 */
import React, { useState, useEffect } from 'react'
import { predictSingle, checkHealth } from './api/api'
import PredictionForm from './components/PredictionForm'
import ResultCard from './components/ResultCard'
import FeatureChart from './components/FeatureChart'
import BatchUpload from './components/BatchUpload'
import HistoryTable from './components/HistoryTable'
import AIRecommendations from './components/AIRecommendations'
import DashboardStats from './components/DashboardStats'

const TABS = [
    { id: 'predict', label: '🔍 Predict', },
    { id: 'batch', label: '📂 Batch', },
    { id: 'history', label: '📋 History', },
]

export default function App() {
    const [tab, setTab] = useState('predict')
    const [loading, setLoading] = useState(false)
    const [result, setResult] = useState(null)
    const [apiError, setApiError] = useState('')
    const [apiStatus, setApiStatus] = useState('checking')

    useEffect(() => {
        checkHealth()
            .then(() => setApiStatus('ok'))
            .catch(() => setApiStatus('error'))
    }, [])

    const handlePredict = async (features) => {
        setLoading(true); setApiError(''); setResult(null)
        try {
            const data = await predictSingle(features)
            setResult(data)
        } catch (err) {
            setApiError(err.message)
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="min-h-screen bg-gray-950 flex flex-col">

            {/* ── Header ── */}
            <header className="sticky top-0 z-20 border-b border-gray-800 bg-gray-950/90 backdrop-blur-md">
                <div className="max-w-6xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                        <div className="w-7 h-7 rounded-lg bg-blue-600 flex items-center justify-center text-sm font-bold">
                            B
                        </div>
                        <span className="font-bold text-gray-100 tracking-tight">BankruptcySense</span>
                        <span className="hidden sm:inline text-xs text-gray-600 font-medium px-1.5 py-0.5 bg-gray-800 rounded">AI</span>
                    </div>
                    <div className="flex items-center gap-3">
                        <div className="flex items-center gap-1.5 text-xs">
                            <span className={`w-2 h-2 rounded-full ${apiStatus === 'ok' ? 'bg-emerald-500' :
                                    apiStatus === 'error' ? 'bg-red-500' :
                                        'bg-yellow-500 animate-pulse'
                                }`} aria-hidden="true" />
                            <span className="text-gray-500 hidden sm:inline">
                                {apiStatus === 'ok' ? 'API online' : apiStatus === 'error' ? 'API offline' : 'Connecting…'}
                            </span>
                        </div>
                    </div>
                </div>
            </header>

            {/* ── Hero ── */}
            <div className="bg-gradient-to-b from-blue-950/20 to-transparent border-b border-gray-800/50">
                <div className="max-w-6xl mx-auto px-4 sm:px-6 py-10">
                    <div className="max-w-2xl">
                        <div className="inline-flex items-center gap-2 text-xs text-blue-400 bg-blue-950/50 border border-blue-900/50 rounded-full px-3 py-1 mb-4">
                            <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />
                            Powered by Random Forest · ROC-AUC 0.912
                        </div>
                        <h1 className="text-3xl sm:text-4xl font-bold text-gray-100 mb-3 leading-tight">
                            Bankruptcy Risk<br />
                            <span className="text-blue-400">Prediction System</span>
                        </h1>
                        <p className="text-gray-400 text-sm sm:text-base max-w-lg">
                            Enter a company's financial ratios to instantly assess bankruptcy risk,
                            get AI-powered recommendations, and understand the key risk drivers.
                        </p>
                    </div>
                </div>
            </div>

            {/* ── Main ── */}
            <main className="flex-1 max-w-6xl mx-auto w-full px-4 sm:px-6 py-8 space-y-6">

                {/* Model stats dashboard */}
                <DashboardStats />

                {/* Tab bar */}
                <div className="flex gap-1 bg-gray-900 border border-gray-800 rounded-xl p-1 w-fit"
                    role="tablist">
                    {TABS.map(({ id, label }) => (
                        <button key={id} role="tab" aria-selected={tab === id}
                            onClick={() => setTab(id)}
                            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-150
                focus:outline-none focus:ring-2 focus:ring-blue-500
                ${tab === id
                                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-900/30'
                                    : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800'
                                }`}>
                            {label}
                        </button>
                    ))}
                </div>

                {/* ── Predict tab ── */}
                {tab === 'predict' && (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

                        {/* Left: form */}
                        <div className="card">
                            <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-5">
                                Financial Ratios Input
                            </h2>
                            <PredictionForm onSubmit={handlePredict} loading={loading} />
                        </div>

                        {/* Right: results */}
                        <div className="space-y-4">
                            {apiError && (
                                <div role="alert"
                                    className="bg-red-950 border border-red-800 rounded-2xl px-5 py-4 text-sm text-red-400 animate-fade-in-up">
                                    <span className="font-semibold">Error: </span>{apiError}
                                </div>
                            )}

                            {!result && !apiError && !loading && (
                                <div className="card flex flex-col items-center justify-center py-20 text-center">
                                    <div className="w-16 h-16 rounded-2xl bg-gray-800 flex items-center justify-center text-3xl mb-4">
                                        📊
                                    </div>
                                    <p className="text-gray-500 text-sm max-w-xs">
                                        Fill in the financial ratios on the left and click{' '}
                                        <strong className="text-gray-400">Predict</strong> to see the risk analysis.
                                    </p>
                                </div>
                            )}

                            {loading && (
                                <div className="card flex flex-col items-center justify-center py-20">
                                    <div className="relative w-12 h-12 mb-4">
                                        <div className="absolute inset-0 rounded-full border-2 border-blue-900" />
                                        <div className="absolute inset-0 rounded-full border-2 border-blue-500 border-t-transparent animate-spin" />
                                    </div>
                                    <p className="text-gray-500 text-sm">Analysing financial data…</p>
                                </div>
                            )}

                            {result && !loading && (
                                <>
                                    <ResultCard result={result} />
                                    <FeatureChart features={result.top_features ?? []} />
                                    <AIRecommendations recommendations={result.recommendations} />
                                </>
                            )}
                        </div>
                    </div>
                )}

                {/* ── Batch tab ── */}
                {tab === 'batch' && (
                    <div className="card">
                        <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-5">
                            Batch CSV Upload
                        </h2>
                        <BatchUpload />
                    </div>
                )}

                {/* ── History tab ── */}
                {tab === 'history' && (
                    <div className="card">
                        <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-5">
                            Prediction History
                        </h2>
                        <HistoryTable />
                    </div>
                )}
            </main>

            {/* ── Footer ── */}
            <footer className="border-t border-gray-800 py-6 text-center text-xs text-gray-700">
                BankruptcySense AI · Random Forest · Polish Bankruptcy Dataset ·
                ROC-AUC 0.912 · Recall 79.3%
            </footer>
        </div>
    )
}

/**
 * App.jsx — Main React application
 *
 * Layout:
 *   Header (logo + status badge)
 *   Tab bar: Predict | Batch | History
 *   Tab panels
 */

import React, { useState, useEffect } from 'react'
import { predictSingle, checkHealth } from './api/api'
import PredictionForm from './components/PredictionForm'
import ResultCard from './components/ResultCard'
import FeatureChart from './components/FeatureChart'
import BatchUpload from './components/BatchUpload'
import HistoryTable from './components/HistoryTable'

const TABS = ['Predict', 'Batch', 'History']

export default function App() {
    const [activeTab, setActiveTab] = useState('Predict')
    const [loading, setLoading] = useState(false)
    const [result, setResult] = useState(null)
    const [apiError, setApiError] = useState('')
    const [apiStatus, setApiStatus] = useState('checking') // 'ok' | 'error' | 'checking'

    // Check backend health on mount
    useEffect(() => {
        checkHealth()
            .then(() => setApiStatus('ok'))
            .catch(() => setApiStatus('error'))
    }, [])

    const handlePredict = async (features) => {
        setLoading(true)
        setApiError('')
        setResult(null)
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
        <div className="min-h-screen bg-gray-950">
            {/* ── Header ── */}
            <header className="border-b border-gray-800 bg-gray-900/80 backdrop-blur sticky top-0 z-10">
                <div className="max-w-5xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                        <span className="text-blue-500 text-xl" aria-hidden="true">⬡</span>
                        <span className="font-bold text-gray-100 tracking-tight">BankruptcySense</span>
                        <span className="text-gray-600 text-sm hidden sm:inline">AI</span>
                    </div>

                    {/* API status badge */}
                    <div className="flex items-center gap-1.5 text-xs">
                        <span
                            className={`w-2 h-2 rounded-full ${apiStatus === 'ok' ? 'bg-emerald-500' :
                                    apiStatus === 'error' ? 'bg-red-500' :
                                        'bg-yellow-500 animate-pulse'
                                }`}
                            aria-hidden="true"
                        />
                        <span className="text-gray-500">
                            {apiStatus === 'ok' ? 'API online' :
                                apiStatus === 'error' ? 'API offline' :
                                    'Connecting…'}
                        </span>
                    </div>
                </div>
            </header>

            {/* ── Main ── */}
            <main className="max-w-5xl mx-auto px-4 sm:px-6 py-8">

                {/* Hero */}
                <div className="mb-8">
                    <h1 className="text-2xl sm:text-3xl font-bold text-gray-100 mb-2">
                        Bankruptcy Prediction
                    </h1>
                    <p className="text-gray-500 text-sm sm:text-base max-w-xl">
                        Enter a company's financial ratios to predict bankruptcy risk using
                        a Random Forest model trained on the Polish Bankruptcy Dataset.
                    </p>
                </div>

                {/* Tab bar */}
                <div className="flex gap-1 mb-6 bg-gray-900 border border-gray-800 rounded-xl p-1 w-fit"
                    role="tablist" aria-label="Main navigation">
                    {TABS.map((tab) => (
                        <button
                            key={tab}
                            role="tab"
                            aria-selected={activeTab === tab}
                            onClick={() => setActiveTab(tab)}
                            className={`px-5 py-2 rounded-lg text-sm font-medium transition-colors duration-150
                focus:outline-none focus:ring-2 focus:ring-blue-500
                ${activeTab === tab
                                    ? 'bg-blue-600 text-white shadow'
                                    : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800'
                                }`}
                        >
                            {tab}
                        </button>
                    ))}
                </div>

                {/* ── Predict tab ── */}
                {activeTab === 'Predict' && (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {/* Left: form */}
                        <div className="card">
                            <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-widest mb-5">
                                Financial Ratios
                            </h2>
                            <PredictionForm onSubmit={handlePredict} loading={loading} />
                        </div>

                        {/* Right: result + chart */}
                        <div className="space-y-4">
                            {apiError && (
                                <div
                                    role="alert"
                                    className="bg-red-950 border border-red-800 rounded-2xl px-5 py-4 text-sm text-red-400"
                                >
                                    <span className="font-semibold">Error: </span>{apiError}
                                </div>
                            )}

                            {!result && !apiError && !loading && (
                                <div className="card flex flex-col items-center justify-center py-16 text-center">
                                    <span className="text-5xl mb-4" aria-hidden="true">📊</span>
                                    <p className="text-gray-500 text-sm">
                                        Fill in the financial ratios and click <strong className="text-gray-400">Predict</strong> to see results.
                                    </p>
                                </div>
                            )}

                            {loading && (
                                <div className="card flex flex-col items-center justify-center py-16">
                                    <svg className="animate-spin h-8 w-8 text-blue-500 mb-3" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                                    </svg>
                                    <p className="text-gray-500 text-sm">Running prediction…</p>
                                </div>
                            )}

                            {result && !loading && (
                                <>
                                    <ResultCard result={result} />
                                    <FeatureChart features={result.top_features ?? []} />
                                </>
                            )}
                        </div>
                    </div>
                )}

                {/* ── Batch tab ── */}
                {activeTab === 'Batch' && (
                    <div className="card">
                        <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-widest mb-5">
                            Batch CSV Upload
                        </h2>
                        <BatchUpload />
                    </div>
                )}

                {/* ── History tab ── */}
                {activeTab === 'History' && (
                    <div className="card">
                        <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-widest mb-5">
                            Prediction History
                        </h2>
                        <HistoryTable />
                    </div>
                )}
            </main>

            {/* ── Footer ── */}
            <footer className="border-t border-gray-800 mt-16 py-6 text-center text-xs text-gray-600">
                BankruptcySense AI · Random Forest · Polish Bankruptcy Dataset ·{' '}
                <span className="text-gray-700">ROC-AUC 0.91</span>
            </footer>
        </div>
    )
}

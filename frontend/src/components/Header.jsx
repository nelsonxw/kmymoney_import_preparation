import React from 'react'

export default function Header({
  showConfig,
  setShowConfig,
  transactionsCount,
  onExport,
  loading
}) {
  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 bg-indigo-600 rounded-lg flex items-center justify-center text-white font-bold text-lg">
            K
          </div>
          <div>
            <h1 className="text-lg font-bold text-slate-900 leading-tight">
              KMyMoney Transaction Categorizer
            </h1>
            <p className="text-xs text-slate-500">
              AI-First Matching + Google Gemini Flash Free Tier
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => setShowConfig(!showConfig)}
            className="text-xs px-3 py-1.5 font-medium rounded-md border border-slate-300 hover:bg-slate-100 transition"
          >
            ⚙️ Settings & Files
          </button>
          {transactionsCount > 0 && (
            <button
              onClick={onExport}
              disabled={loading}
              className="text-xs px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-medium rounded-md shadow-xs transition flex items-center space-x-1 disabled:opacity-50"
            >
              <span>Export Categorized CSV</span>
            </button>
          )}
        </div>
      </div>
    </header>
  )
}

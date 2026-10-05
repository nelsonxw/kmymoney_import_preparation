import React from 'react'

export default function ProgressBar({ loading, progress, progressMsg }) {
  if (!loading) return null

  return (
    <div className="p-5 bg-gradient-to-r from-indigo-50 via-white to-indigo-50 border-2 border-indigo-300 rounded-xl shadow-xs space-y-3 transition-all duration-300">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center text-white">
            <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
            </svg>
          </div>
          <div>
            <h4 className="text-sm font-bold text-slate-900">
              Running AI Auto-Categorization
            </h4>
            <p className="text-xs text-indigo-700 font-medium">
              {progressMsg || 'Processing transactions with Gemini 3.8 Flash...'}
            </p>
          </div>
        </div>
        <div className="text-right">
          <span className="text-2xl font-black text-indigo-600 font-mono">
            {progress}%
          </span>
          <span className="block text-[10px] text-slate-400 font-medium uppercase tracking-wider">
            Completion
          </span>
        </div>
      </div>

      {/* Progress track */}
      <div className="w-full bg-slate-200 rounded-full h-3 overflow-hidden p-0.5">
        <div
          className="bg-gradient-to-r from-indigo-500 via-indigo-600 to-emerald-500 h-2 rounded-full transition-all duration-300 ease-out shadow-xs"
          style={{ width: `${Math.max(progress, 3)}%` }}
        ></div>
      </div>

      <div className="flex justify-between items-center text-[11px] text-slate-500 pt-1">
        <span>Matching against 300+ Payees & 168 Master Categories with Amount Patterns</span>
        <span className="font-semibold text-indigo-600">
          {progress === 100 ? '✓ Ready!' : 'Please keep this window open'}
        </span>
      </div>
    </div>
  )
}

import React from 'react'

export default function AlertBanners({
  error,
  setError,
  successMsg,
  setSuccessMsg,
  onRetry,
  onNewImport,
  loading
}) {
  return (
    <div className="space-y-4">
      {/* AI Error / Capacity Spike Warning */}
      {error && (
        <div className="p-5 bg-amber-50 border-2 border-amber-300 rounded-xl text-amber-900 text-sm shadow-sm space-y-3">
          <div className="flex items-start justify-between">
            <div className="flex items-start space-x-3">
              <span className="text-2xl leading-none">⚠️</span>
              <div>
                <h3 className="font-bold text-amber-950 text-base">
                  AI Auto-Categorization Warning
                </h3>
                <p className="mt-1 text-xs text-amber-900 leading-relaxed font-mono bg-white/70 p-2.5 rounded border border-amber-200">
                  {error}
                </p>
              </div>
            </div>
            <button
              onClick={() => setError(null)}
              className="text-amber-600 hover:text-amber-800 font-bold px-2 py-1 text-sm rounded hover:bg-amber-100"
            >
              ✕ Dismiss
            </button>
          </div>
          <div className="flex items-center justify-between pt-1 border-t border-amber-200/60 text-xs text-amber-800">
            <span>OpenRouter servers may be experiencing temporary traffic spikes. Please wait a minute and try again.</span>
            <button
              onClick={onRetry}
              disabled={loading}
              className="px-3 py-1.5 bg-amber-600 hover:bg-amber-700 text-white font-semibold rounded-md shadow-2xs transition disabled:opacity-50 text-xs shrink-0 ml-4"
            >
              {loading ? 'Retrying...' : '↻ Try Again Now'}
            </button>
          </div>
        </div>
      )}

      {/* Success Notification */}
      {successMsg && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-lg text-emerald-800 text-sm flex items-start justify-between">
          <div className="flex items-center space-x-4">
            <div>
              <span className="font-semibold">Success: </span>
              {successMsg}
            </div>
            {onNewImport && (
              <button
                onClick={onNewImport}
                className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-md text-xs shrink-0"
              >
                + Start New Import
              </button>
            )}
          </div>
          <button onClick={() => setSuccessMsg(null)} className="text-emerald-500 font-bold ml-4">
            ✕
          </button>
        </div>
      )}
    </div>
  )
}

import React from 'react'

export default function UploadSection({
  transactionsCount,
  uploadInfo,
  onUploadTransactions,
  dateCol,
  setDateCol,
  descCol,
  setDescCol,
  amountCol,
  setAmountCol,
  onMapColumns,
  onProcessTransactions,
  loading,
  progress
}) {
  if (transactionsCount > 0) return null

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-8 shadow-xs text-center space-y-4">
      <div className="w-12 h-12 bg-indigo-50 text-indigo-600 rounded-full flex items-center justify-center mx-auto text-xl">
        📂
      </div>
      <div>
        <h2 className="text-lg font-semibold text-slate-900">
          Upload Bank or Credit Card CSV
        </h2>
        <p className="text-sm text-slate-500 max-w-md mx-auto mt-1">
          Select any CSV exported from Chase, Amex, Bank of America, or credit union.
          Delimiter and columns will be detected automatically.
        </p>
      </div>

      <div className="max-w-sm mx-auto">
        <input
          type="file"
          accept=".csv"
          onChange={(e) => onUploadTransactions(e.target.files[0])}
          className="block w-full text-sm text-slate-500 file:mr-4 file:py-2.5 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-indigo-600 file:text-white hover:file:bg-indigo-700 cursor-pointer"
        />
      </div>

      {/* Column mapping preview if uploaded */}
      {uploadInfo && (
        <div className="mt-6 pt-6 border-t border-slate-200 text-left max-w-2xl mx-auto space-y-4">
          <div className="font-semibold text-sm text-slate-800">
            Detected Column Mapping for: <span className="text-indigo-600">{uploadInfo.filename}</span>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs text-slate-500 mb-1">Date Column</label>
              <select
                value={dateCol}
                onChange={(e) => setDateCol(e.target.value)}
                className="w-full text-xs p-2 border border-slate-300 rounded-md bg-white"
              >
                {uploadInfo.headers.map(h => (
                  <option key={h} value={h}>{h}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs text-slate-500 mb-1">Description Column</label>
              <select
                value={descCol}
                onChange={(e) => setDescCol(e.target.value)}
                className="w-full text-xs p-2 border border-slate-300 rounded-md bg-white"
              >
                {uploadInfo.headers.map(h => (
                  <option key={h} value={h}>{h}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs text-slate-500 mb-1">Amount Column</label>
              <select
                value={amountCol}
                onChange={(e) => setAmountCol(e.target.value)}
                className="w-full text-xs p-2 border border-slate-300 rounded-md bg-white"
              >
                {uploadInfo.headers.map(h => (
                  <option key={h} value={h}>{h}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex justify-end space-x-3 pt-2">
            <button
              onClick={onMapColumns}
              className="text-xs px-3 py-1.5 border border-slate-300 rounded-md hover:bg-slate-50"
            >
              Save Mapping
            </button>
            <button
              onClick={onProcessTransactions}
              disabled={loading}
              className="text-xs px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-md shadow-xs disabled:opacity-60 transition flex items-center space-x-2"
            >
              {loading ? (
                <>
                  <svg className="animate-spin h-3.5 w-3.5 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
                  </svg>
                  <span>Running AI ({progress}%)...</span>
                </>
              ) : (
                <span>Run Auto-Categorization</span>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

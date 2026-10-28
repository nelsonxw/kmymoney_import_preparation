import React from 'react'

export default function ConfigModal({
  showConfig,
  setShowConfig,
  config,
  apiKey,
  setApiKey,
  onSaveConfig,
  onLoadReferenceFiles
}) {
  if (!showConfig) return null

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-6">
      <div className="flex justify-between items-center border-b border-slate-100 pb-3">
        <h2 className="text-base font-semibold text-slate-900">
          Configuration & Reference Files
        </h2>
        <button
          onClick={() => setShowConfig(false)}
          className="text-slate-400 hover:text-slate-600 text-sm"
        >
          Close ✕
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* OpenRouter API Key */}
        <div className="space-y-2">
          <label className="block text-xs font-semibold text-slate-700 uppercase">
            OpenRouter API Key
          </label>
          <div className="flex space-x-2">
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder={config?.openrouter_api_key_configured ? '•••••••••••••••• (Configured)' : 'Enter OpenRouter API key'}
              className="flex-1 text-sm px-3 py-2 border border-slate-300 rounded-md focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
            />
            <button
              onClick={onSaveConfig}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-md"
            >
              Save
            </button>
          </div>
          <p className="text-xs text-slate-500">
            Used for unresolved payees & categories. Create a key at openrouter.ai/keys.
          </p>
        </div>

        {/* Status summary */}
        <div className="bg-slate-50 p-4 rounded-lg border border-slate-200 text-xs space-y-1">
          <div className="font-semibold text-slate-700 mb-1">Active Reference Status:</div>
          <div className="flex justify-between">
            <span>Transaction History:</span>
            <span className="font-medium text-slate-900">
              {config?.history_loaded ? `✓ ${config.total_payees} Payees` : '❌ Not Loaded'}
            </span>
          </div>
          <div className="flex justify-between">
            <span>Master Category List:</span>
            <span className="font-medium text-slate-900">
              {config?.master_list_loaded ? `✓ ${config.total_categories} Categories` : '❌ Not Loaded'}
            </span>
          </div>
          <div className="flex justify-between">
            <span>OpenRouter Status:</span>
            <span className={`font-medium ${config?.openrouter_api_key_configured ? 'text-emerald-600' : 'text-amber-600'}`}>
              {config?.openrouter_api_key_configured ? '✓ Ready' : '⚠ API Key Missing'}
            </span>
          </div>
        </div>
      </div>

      {/* Reference File uploaders */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2 border-t border-slate-100">
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">
            Reload Transaction History CSV (KMyMoney export)
          </label>
          <input
            type="file"
            accept=".csv"
            onChange={(e) => onLoadReferenceFiles(e.target.files[0], null)}
            className="block w-full text-xs text-slate-500 file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">
            Reload Category & Payee list CSV
          </label>
          <input
            type="file"
            accept=".csv"
            onChange={(e) => onLoadReferenceFiles(null, e.target.files[0])}
            className="block w-full text-xs text-slate-500 file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"
          />
        </div>
      </div>
    </div>
  )
}

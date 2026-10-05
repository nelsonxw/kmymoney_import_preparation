import React from 'react'

export default function StatCards({ config, totalActive, tbdCount }) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs">
        <div className="text-xs text-slate-500 font-medium">Master Payees</div>
        <div className="text-2xl font-bold text-slate-900 mt-1">
          {config?.total_payees || 0}
        </div>
        <div className="text-xs text-slate-400 mt-0.5">Loaded for matching</div>
      </div>

      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs">
        <div className="text-xs text-slate-500 font-medium">KMyMoney Categories</div>
        <div className="text-2xl font-bold text-slate-900 mt-1">
          {config?.total_categories || 0}
        </div>
        <div className="text-xs text-slate-400 mt-0.5">Strict allowed set</div>
      </div>

      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs">
        <div className="text-xs text-slate-500 font-medium">Active Batch</div>
        <div className="text-2xl font-bold text-slate-900 mt-1">
          {totalActive}
        </div>
        <div className="text-xs text-slate-400 mt-0.5">Transactions loaded</div>
      </div>

      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs">
        <div className="text-xs text-slate-500 font-medium">Needs Attention (TBD)</div>
        <div className={`text-2xl font-bold mt-1 ${tbdCount > 0 ? 'text-amber-600' : 'text-emerald-600'}`}>
          {tbdCount}
        </div>
        <div className="text-xs text-slate-400 mt-0.5">Zero tolerance for export</div>
      </div>
    </div>
  )
}

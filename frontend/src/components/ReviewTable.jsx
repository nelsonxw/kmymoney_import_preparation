import React from 'react'

export default function ReviewTable({
  transactions,
  filteredTransactions,
  filter,
  setFilter,
  searchTerm,
  setSearchTerm,
  sortColumn,
  sortDirection,
  onSort,
  onUpdateTransaction,
  onExport,
  loading,
  counts
}) {
  const { tbdCount, newPayeeCount, newCategoryCount, conflictCount } = counts

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      {/* Filter Pills & Actions Bar */}
      <div className="p-4 border-b border-slate-200 flex flex-wrap gap-3 items-center justify-between bg-slate-50/50">
        <div className="flex flex-wrap gap-2 items-center">
          <button
            onClick={() => setFilter('all')}
            className={`text-xs px-3 py-1.5 rounded-full font-medium transition ${
              filter === 'all'
                ? 'bg-indigo-600 text-white'
                : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-100'
            }`}
          >
            All ({transactions.length})
          </button>

          <button
            onClick={() => setFilter('attention')}
            className={`text-xs px-3 py-1.5 rounded-full font-medium transition ${
              filter === 'attention'
                ? 'bg-amber-600 text-white'
                : 'bg-white text-amber-700 border border-amber-200 hover:bg-amber-50'
            }`}
          >
            Needs Attention ({tbdCount})
          </button>

          <button
            onClick={() => setFilter('new-payee')}
            className={`text-xs px-3 py-1.5 rounded-full font-medium transition ${
              filter === 'new-payee'
                ? 'bg-red-600 text-white'
                : 'bg-white text-red-700 border border-red-200 hover:bg-red-50'
            }`}
          >
            New Payees ({newPayeeCount})
          </button>

          <button
            onClick={() => setFilter('new-category')}
            className={`text-xs px-3 py-1.5 rounded-full font-medium transition ${
              filter === 'new-category'
                ? 'bg-red-600 text-white'
                : 'bg-white text-red-700 border border-red-200 hover:bg-red-50'
            }`}
          >
            New Categories ({newCategoryCount})
          </button>

          {conflictCount > 0 && (
            <button
              onClick={() => setFilter('conflict')}
              className={`text-xs px-3 py-1.5 rounded-full font-medium transition ${
                filter === 'conflict'
                  ? 'bg-orange-600 text-white'
                  : 'bg-white text-orange-700 border border-orange-200 hover:bg-orange-50'
              }`}
            >
              Conflicts ({conflictCount})
            </button>
          )}
        </div>

        <div className="flex items-center space-x-3">
          <input
            type="text"
            placeholder="Search description, payee..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="text-xs px-3 py-1.5 border border-slate-300 rounded-lg w-52 focus:outline-hidden focus:ring-1 focus:ring-indigo-500 bg-white"
          />
          <button
            onClick={onExport}
            disabled={loading}
            className="text-xs px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-md shadow-xs disabled:opacity-50"
          >
            Export CSV
          </button>
        </div>
      </div>

      {/* Validation Notice if TBD exists */}
      {tbdCount > 0 && (
        <div className="px-4 py-2.5 bg-amber-50 border-b border-amber-200 text-amber-900 text-xs flex items-center justify-between">
          <span>
            ⚠️ <strong>{tbdCount} transaction(s)</strong> have Category set to <strong>TBD</strong>.
            KMyMoney export requires all categories to be resolved.
          </span>
          <button
            onClick={() => setFilter('attention')}
            className="underline font-semibold ml-2 hover:text-amber-700"
          >
            View TBD items
          </button>
        </div>
      )}

      {/* Table */}
      <div className="overflow-x-auto max-h-[600px] overflow-y-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead className="bg-slate-100 text-slate-700 sticky top-0 z-10 shadow-2xs font-semibold">
            <tr>
              <th
                className="px-4 py-3 cursor-pointer hover:bg-slate-200"
                onClick={() => onSort('date')}
              >
                Date {sortColumn === 'date' && (sortDirection === 'asc' ? '↑' : '↓')}
              </th>
              <th className="px-4 py-3 min-w-[200px]">
                Original Description
              </th>
              <th
                className="px-4 py-3 cursor-pointer hover:bg-slate-200 text-right"
                onClick={() => onSort('amount')}
              >
                Amount {sortColumn === 'amount' && (sortDirection === 'asc' ? '↑' : '↓')}
              </th>
              <th className="px-4 py-3 min-w-[220px]">
                Payee (Editable Autocomplete)
              </th>
              <th className="px-4 py-3 min-w-[240px]">
                Category (Editable Dropdown)
              </th>
              <th className="px-4 py-3">Status</th>
            </tr>
          </thead>

          <tbody className="divide-y divide-slate-200">
            {filteredTransactions.map((tx) => {
              const isNewPayee = tx.payee_is_new
              const isNewCategory = tx.category_is_new
              const isTbd = !tx.category || tx.category.trim().toUpperCase() === 'TBD'
              const hasConflict = tx.has_conflict

              return (
                <tr key={tx.index} className="hover:bg-slate-50 transition">
                  <td className="px-4 py-2.5 whitespace-nowrap text-slate-600 font-mono">
                    {tx.date}
                  </td>

                  <td className="px-4 py-2.5 text-slate-700 font-mono text-[11px] max-w-xs truncate" title={tx.description}>
                    {tx.description}
                  </td>

                  <td className="px-4 py-2.5 text-right font-mono font-medium text-slate-900">
                    {tx.amount}
                  </td>

                  {/* Payee Cell with Red Highlighting for New */}
                  <td className="px-4 py-2">
                    <div className="space-y-1">
                      <input
                        type="text"
                        list="all-payees-datalist"
                        value={tx.payee || ''}
                        onChange={(e) => onUpdateTransaction(tx.index, e.target.value, undefined)}
                        className={`w-full px-2.5 py-1 text-xs rounded-md border font-medium ${
                          isNewPayee
                            ? 'border-red-400 bg-red-50 text-red-900 focus:ring-red-500'
                            : 'border-slate-300 bg-white text-slate-800 focus:ring-indigo-500'
                        }`}
                      />
                      {isNewPayee && (
                        <span className="inline-block text-[10px] font-semibold text-red-600 tracking-wide uppercase">
                          ● New Payee
                        </span>
                      )}
                    </div>
                  </td>

                  {/* Category Cell with Red Highlighting for New and Amber for TBD */}
                  <td className="px-4 py-2">
                    <div className="space-y-1">
                      <input
                        type="text"
                        list="all-categories-datalist"
                        value={tx.category || ''}
                        onChange={(e) => onUpdateTransaction(tx.index, undefined, e.target.value)}
                        className={`w-full px-2.5 py-1 text-xs rounded-md border font-medium ${
                          isTbd
                            ? 'border-amber-400 bg-amber-50 text-amber-900 focus:ring-amber-500'
                            : isNewCategory
                            ? 'border-red-400 bg-red-50 text-red-900 focus:ring-red-500'
                            : 'border-slate-300 bg-white text-slate-800 focus:ring-indigo-500'
                        }`}
                      />
                      {isTbd && (
                        <span className="inline-block text-[10px] font-semibold text-amber-700 uppercase">
                          ⚠ Action Required (TBD)
                        </span>
                      )}
                      {isNewCategory && !isTbd && (
                        <span className="inline-block text-[10px] font-semibold text-red-600 uppercase">
                          ● New Category
                        </span>
                      )}
                      {/* If Payee has multiple historical categories, show clickable options */}
                      {hasConflict && tx.conflict_options?.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-1">
                          <span className="text-[10px] text-slate-500">History:</span>
                          {tx.conflict_options.slice(0, 3).map((opt, i) => (
                            <button
                              key={i}
                              type="button"
                              onClick={() => onUpdateTransaction(tx.index, undefined, opt)}
                              className="text-[10px] px-1.5 py-0.5 bg-indigo-50 text-indigo-700 hover:bg-indigo-100 rounded border border-indigo-200"
                              title={`Click to set category to ${opt}`}
                            >
                              {opt}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  </td>

                  {/* Status Column */}
                  <td className="px-4 py-2 whitespace-nowrap">
                    {hasConflict && (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-orange-100 text-orange-800">
                        Conflict
                      </span>
                    )}
                    {!hasConflict && tx.confidence === 'high' && (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-100 text-emerald-800">
                        Matched
                      </span>
                    )}
                    {!hasConflict && tx.confidence === 'medium' && (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-blue-100 text-blue-800">
                        AI Suggested
                      </span>
                    )}
                    {!hasConflict && tx.confidence === 'low' && !isTbd && (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-slate-100 text-slate-600">
                        Low Conf
                      </span>
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

import { useState, useEffect, useMemo } from 'react'
import Header from './components/Header'
import AlertBanners from './components/AlertBanners'
import ProgressBar from './components/ProgressBar'
import StatCards from './components/StatCards'
import ConfigModal from './components/ConfigModal'
import UploadSection from './components/UploadSection'
import ReviewTable from './components/ReviewTable'

const API_BASE = 'http://127.0.0.1:8000/api'

function App() {
  const [config, setConfig] = useState(null)
  const [uploadInfo, setUploadInfo] = useState(null)
  const [transactions, setTransactions] = useState([])
  const [filter, setFilter] = useState('all')
  const [searchTerm, setSearchTerm] = useState('')
  const [sortColumn, setSortColumn] = useState('date')
  const [sortDirection, setSortDirection] = useState('desc')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [successMsg, setSuccessMsg] = useState(null)
  const [showConfig, setShowConfig] = useState(false)
  const [apiKey, setApiKey] = useState('')

  // AI Progress completion state
  const [progress, setProgress] = useState(0)
  const [progressMsg, setProgressMsg] = useState('')

  // Column mapping state
  const [dateCol, setDateCol] = useState('')
  const [descCol, setDescCol] = useState('')
  const [amountCol, setAmountCol] = useState('')

  useEffect(() => {
    fetchConfig()
  }, [])

  const fetchConfig = async () => {
    try {
      const res = await fetch(`${API_BASE}/config`)
      const data = await res.json()
      setConfig(data)
    } catch {
      setError('Cannot connect to backend server. Make sure it is running on http://127.0.0.1:8000')
    }
  }

  const handleSaveConfig = async () => {
    try {
      const formData = new FormData()
      if (apiKey) formData.append('gemini_api_key', apiKey)
      const res = await fetch(`${API_BASE}/config`, {
        method: 'POST',
        body: formData
      })
      if (res.ok) {
        setSuccessMsg('Configuration saved successfully!')
        setApiKey('')
        fetchConfig()
      }
    } catch {
      setError('Failed to save configuration')
    }
  }

  const handleLoadReferenceFiles = async (historyFile, masterListFile) => {
    const formData = new FormData()
    if (historyFile) formData.append('history_file', historyFile)
    if (masterListFile) formData.append('master_list_file', masterListFile)

    try {
      const res = await fetch(`${API_BASE}/reference-files/load`, {
        method: 'POST',
        body: formData
      })
      const data = await res.json()
      if (res.ok) {
        setSuccessMsg(`Reference files reloaded: ${data.total_payees} payees, ${data.total_categories} categories`)
        fetchConfig()
      } else {
        setError(data.detail || 'Failed to load reference files')
      }
    } catch {
      setError('Error uploading reference files')
    }
  }

  const handleUploadTransactions = async (file) => {
    if (!file) return
    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await fetch(`${API_BASE}/transactions/upload`, {
        method: 'POST',
        body: formData
      })
      const data = await res.json()
      if (res.ok) {
        setUploadInfo(data)
        setDateCol(data.date_col || '')
        setDescCol(data.description_col || '')
        setAmountCol(data.amount_col || '')
        setTransactions([])
        setSuccessMsg(`Loaded ${data.total_rows} transactions from ${data.filename}`)
      } else {
        setError(data.detail || 'Failed to upload transaction CSV')
      }
    } catch {
      setError('Error uploading transaction file')
    }
  }

  const handleMapColumns = async () => {
    try {
      const res = await fetch(`${API_BASE}/transactions/map-columns`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          date_col: dateCol,
          description_col: descCol,
          amount_col: amountCol
        })
      })
      if (res.ok) {
        setSuccessMsg('Column mappings saved!')
      }
    } catch {
      setError('Failed to update column mappings')
    }
  }

  const handleProcessTransactions = async () => {
    setLoading(true)
    setError(null)
    setSuccessMsg(null)
    setProgress(5)
    setProgressMsg('Initializing Master Payees & Categories...')

    try {
      const res = await fetch(`${API_BASE}/transactions/process`, {
        method: 'POST'
      })

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}))
        throw new Error(errData.detail || `Server error (${res.status})`)
      }

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          const trimmed = line.trim()
          if (trimmed.startsWith('data: ')) {
            try {
              const event = JSON.parse(trimmed.slice(6))
              if (event.type === 'progress') {
                setProgress(event.percent)
                if (event.message) setProgressMsg(event.message)
              } else if (event.type === 'complete') {
                setProgress(100)
                setProgressMsg('Completed!')
                setTransactions(event.transactions || [])
                setSuccessMsg(`Categorized ${event.total_processed} transactions! Review results below.`)
              } else if (event.type === 'error') {
                throw new Error(event.detail)
              }
            } catch (e) {
              if (e.message && !e.message.includes('JSON')) {
                throw e
              }
            }
          }
        }
      }
    } catch (err) {
      setError(err.message || 'Failed to process transactions')
    } finally {
      setLoading(false)
      setTimeout(() => {
        setProgress(0)
        setProgressMsg('')
      }, 1500)
    }
  }

  const handleUpdateTransaction = async (index, newPayee, newCategory) => {
    try {
      const res = await fetch(`${API_BASE}/transactions/update`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          index,
          payee: newPayee !== undefined ? newPayee : null,
          category: newCategory !== undefined ? newCategory : null
        })
      })
      if (res.ok) {
        const data = await res.json()
        setTransactions(prev =>
          prev.map((tx, i) => (i === index ? data.transaction : tx))
        )
      }
    } catch {
      setError('Failed to update transaction')
    }
  }

  const handleExport = async () => {
    try {
      const res = await fetch(`${API_BASE}/transactions/export`, {
        method: 'POST'
      })

      if (!res.ok) {
        const err = await res.json()
        setError(err.detail || 'Export validation failed')
        return
      }

      const blob = await res.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `categorized_${uploadInfo?.filename || 'transactions.csv'}`
      document.body.appendChild(a)
      a.click()
      a.remove()
      window.URL.revokeObjectURL(url)

      setSuccessMsg('Export successful! Master Category and Payee list has been updated.')
      fetchConfig()
    } catch {
      setError('Export failed')
    }
  }

  // Derived counts
  const counts = useMemo(() => ({
    tbdCount: transactions.filter(tx => !tx.category || tx.category.toUpperCase() === 'TBD').length,
    newPayeeCount: transactions.filter(tx => tx.payee_is_new).length,
    newCategoryCount: transactions.filter(tx => tx.category_is_new).length,
    conflictCount: transactions.filter(tx => tx.has_conflict).length
  }), [transactions])

  // Filter & sort logic
  const filteredTransactions = useMemo(() => {
    return transactions
      .filter(tx => {
        if (filter === 'attention') return !tx.category || tx.category.toUpperCase() === 'TBD' || tx.confidence === 'low'
        if (filter === 'new-payee') return tx.payee_is_new
        if (filter === 'new-category') return tx.category_is_new
        if (filter === 'conflict') return tx.has_conflict
        return true
      })
      .filter(tx => {
        if (!searchTerm) return true
        const term = searchTerm.toLowerCase()
        return (
          tx.description?.toLowerCase().includes(term) ||
          tx.payee?.toLowerCase().includes(term) ||
          tx.category?.toLowerCase().includes(term) ||
          tx.date?.toLowerCase().includes(term)
        )
      })
      .sort((a, b) => {
        let aVal = a[sortColumn]
        let bVal = b[sortColumn]
        if (sortColumn === 'amount') {
          aVal = parseFloat(aVal) || 0
          bVal = parseFloat(bVal) || 0
        }
        if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1
        if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1
        return 0
      })
  }, [transactions, filter, searchTerm, sortColumn, sortDirection])

  const handleSort = (column) => {
    if (sortColumn === column) {
      setSortDirection(prev => prev === 'asc' ? 'desc' : 'asc')
    } else {
      setSortColumn(column)
      setSortDirection('asc')
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800">
      {/* HTML5 Datalists for autocompletes */}
      <datalist id="all-payees-datalist">
        {config?.all_payees?.map((p, i) => (
          <option key={i} value={p} />
        ))}
      </datalist>

      <datalist id="all-categories-datalist">
        <option value="TBD" />
        {config?.all_categories?.map((c, i) => (
          <option key={i} value={c} />
        ))}
      </datalist>

      {/* Top Header */}
      <Header
        showConfig={showConfig}
        setShowConfig={setShowConfig}
        transactionsCount={transactions.length}
        onExport={handleExport}
        loading={loading}
      />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Alerts */}
        <AlertBanners
          error={error}
          setError={setError}
          successMsg={successMsg}
          setSuccessMsg={setSuccessMsg}
          onRetry={handleProcessTransactions}
          loading={loading}
        />

        {/* Real-time AI Progress Bar */}
        <ProgressBar
          loading={loading}
          progress={progress}
          progressMsg={progressMsg}
        />

        {/* Configuration Modal */}
        <ConfigModal
          showConfig={showConfig}
          setShowConfig={setShowConfig}
          config={config}
          apiKey={apiKey}
          setApiKey={setApiKey}
          onSaveConfig={handleSaveConfig}
          onLoadReferenceFiles={handleLoadReferenceFiles}
        />

        {/* Status Metrics Cards */}
        <StatCards
          config={config}
          totalActive={transactions.length || uploadInfo?.total_rows || 0}
          tbdCount={counts.tbdCount}
        />

        {/* Step 1: Upload Bank CSV */}
        <UploadSection
          transactionsCount={transactions.length}
          uploadInfo={uploadInfo}
          onUploadTransactions={handleUploadTransactions}
          dateCol={dateCol}
          setDateCol={setDateCol}
          descCol={descCol}
          setDescCol={setDescCol}
          amountCol={amountCol}
          setAmountCol={setAmountCol}
          onMapColumns={handleMapColumns}
          onProcessTransactions={handleProcessTransactions}
          loading={loading}
          progress={progress}
        />

        {/* Step 2: Review Table */}
        {transactions.length > 0 && (
          <ReviewTable
            transactions={transactions}
            filteredTransactions={filteredTransactions}
            filter={filter}
            setFilter={setFilter}
            searchTerm={searchTerm}
            setSearchTerm={setSearchTerm}
            sortColumn={sortColumn}
            sortDirection={sortDirection}
            onSort={handleSort}
            onUpdateTransaction={handleUpdateTransaction}
            onExport={handleExport}
            loading={loading}
            counts={counts}
          />
        )}
      </main>
    </div>
  )
}

export default App

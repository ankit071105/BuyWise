'use client'
import { useEffect, useState } from 'react'
import { History, Trash2, Search } from 'lucide-react'
import { historyApi } from '@/lib/api'
import { format } from 'date-fns'
import toast from 'react-hot-toast'

export default function HistoryPage() {
  const [history, setHistory] = useState<any[]>([])
  const [filter, setFilter] = useState('')

  useEffect(() => {
    historyApi.get().then(r => setHistory(r.data)).catch(() => {})
  }, [])

  async function clear() {
    await historyApi.clear()
    setHistory([])
    toast.success('History cleared')
  }

  const filtered = history.filter(h => h.query.toLowerCase().includes(filter.toLowerCase()))

  return (
    <div className="space-y-5">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="font-display text-2xl font-bold text-navy-700 flex items-center gap-2">
            <History className="text-cyan-500 w-6 h-6" /> Search History
          </h1>
          <p className="text-navy-400 text-sm mt-0.5">{history.length} searches recorded</p>
        </div>
        {history.length > 0 && (
          <button onClick={clear} className="flex items-center gap-1.5 text-xs text-red-400 hover:text-red-600">
            <Trash2 size={13} /> Clear All
          </button>
        )}
      </div>

      <div className="relative">
        <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-navy-400" />
        <input
          value={filter} onChange={e => setFilter(e.target.value)}
          placeholder="Filter history..."
          className="w-full pl-9 pr-4 py-2.5 rounded-xl border border-cyan-200 bg-white text-sm text-navy-700 focus:outline-none focus:ring-2 focus:ring-cyan-300"
        />
      </div>

      {filtered.length === 0 ? (
        <div className="bw-card p-12 text-center">
          <History className="text-cyan-300 w-10 h-10 mx-auto mb-3" />
          <p className="text-navy-500 font-medium">No history yet</p>
          <p className="text-navy-400 text-sm mt-1">Start searching for products from the dashboard</p>
        </div>
      ) : (
        <div className="bw-card divide-y divide-cyan-50">
          {filtered.map((h: any) => (
            <div key={h.id} className="flex items-center gap-3 px-5 py-3.5 hover:bg-cyan-50 transition-colors">
              <Search size={14} className="text-navy-300 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm text-navy-700 font-medium truncate">{h.query}</p>
                {h.product_id && (
                  <p className="text-xs text-cyan-500">Product ID: {h.product_id}</p>
                )}
              </div>
              <span className="text-xs text-navy-400 flex-shrink-0">
                {(() => { try { return format(new Date(h.searched_at), 'dd MMM, hh:mm a') } catch { return h.searched_at } })()}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

'use client'
import { useState } from 'react'
import { Search, Link2, Loader2, Sparkles } from 'lucide-react'
import { productsApi } from '@/lib/api'
import toast from 'react-hot-toast'

interface Props {
  onResult: (result: any) => void
}

export default function ProductSearch({ onResult }: Props) {
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [mode, setMode] = useState<'url' | 'search'>('url')

  const isUrl = (s: string) => s.startsWith('http://') || s.startsWith('https://')

  async function handleAnalyze() {
    if (!input.trim()) return toast.error('Enter a product URL or name')
    setLoading(true)
    try {
      const payload = isUrl(input) ? { url: input } : { query: input }
      const res = await productsApi.analyze(payload)
      onResult(res.data)
      toast.success('Analysis complete!')
    } catch (e: any) {
      toast.error(e.response?.data?.detail || 'Analysis failed. Check your GROQ_API_KEY.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bw-card p-6">
      <div className="flex items-center gap-2 mb-4">
        <Sparkles className="text-cyan-500 w-5 h-5" />
        <h2 className="font-display font-semibold text-navy-700">Analyze a Product</h2>
      </div>

      {/* Mode toggle */}
      <div className="flex gap-2 mb-4">
        {[{ key: 'url', label: 'Paste URL', Icon: Link2 }, { key: 'search', label: 'Search by Name', Icon: Search }].map(({ key, label, Icon }) => (
          <button key={key} onClick={() => setMode(key as any)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
              mode === key ? 'bg-cyan-500 text-white shadow-score' : 'bg-cyan-50 text-cyan-600 hover:bg-cyan-100'
            }`}>
            <Icon size={14} /> {label}
          </button>
        ))}
      </div>

      <div className="flex gap-3">
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleAnalyze()}
          placeholder={mode === 'url'
            ? 'Paste Amazon/Flipkart product URL...'
            : 'Search e.g. "Nike Air Max 270"'}
          className="flex-1 px-4 py-3 rounded-xl border border-cyan-200 bg-cyan-50 text-navy-700 placeholder-navy-400 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-300 focus:bg-white transition-all"
        />
        <button
          onClick={handleAnalyze}
          disabled={loading}
          className="px-5 py-3 bg-cyan-500 hover:bg-cyan-600 text-white rounded-xl text-sm font-semibold shadow-score bw-btn disabled:opacity-60 flex items-center gap-2">
          {loading ? <Loader2 size={16} className="animate-spin" /> : <Sparkles size={16} />}
          {loading ? 'Analyzing...' : 'Analyze'}
        </button>
      </div>

      <p className="text-xs text-navy-400 mt-3">
        Supports: Amazon India, Flipkart · Analysis uses AI agents + price prediction
      </p>
    </div>
  )
}

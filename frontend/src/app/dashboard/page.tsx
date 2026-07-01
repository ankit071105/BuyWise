'use client'
import { useState, useEffect } from 'react'
import { Package, TrendingDown, Bell, Sparkles, ArrowLeftRight, Loader2, ExternalLink, Trophy, Wand2, AlertCircle } from 'lucide-react'
import ProductSearch from '@/components/ui/ProductSearch'
import AnalysisResult from '@/components/ui/AnalysisResult'
import { productsApi, historyApi, api } from '@/lib/api'
import { useAuthStore } from '@/lib/store'
import BuyScore from '@/components/ui/BuyScore'
import Link from 'next/link'

export default function DashboardPage() {
  const { user, initFromStorage } = useAuthStore()
  const [result, setResult] = useState<any>(null)
  const [tracked, setTracked] = useState<any[]>([])
  const [searchHistory, setSearchHistory] = useState<any[]>([])

  const [compareMode, setCompareMode] = useState(false)
  const [autoCompareUrl, setAutoCompareUrl] = useState('')
  const [compareResult, setCompareResult] = useState<any>(null)
  const [compareLoading, setCompareLoading] = useState(false)

  useEffect(() => {
    initFromStorage()
    productsApi.getTracked().then(r => setTracked(r.data)).catch(() => {})
    historyApi.get().then(r => setSearchHistory(r.data.slice(0, 5))).catch(() => {})
  }, [])

  async function handleAutoCompare() {
    if (!autoCompareUrl) return
    setCompareLoading(true)
    setCompareResult(null)
    try {
      const res = await api.post('/api/products/compare', { url: autoCompareUrl })
      setCompareResult(res.data)
    } catch (e: any) {
      setCompareResult({ error: e.response?.data?.detail || 'Compare failed' })
    } finally {
      setCompareLoading(false)
    }
  }

  const matchQualityConfig: any = {
    excellent: { color: 'emerald', text: 'Excellent match', icon: '✓' },
    good:      { color: 'cyan',    text: 'Good match',      icon: '✓' },
    moderate:  { color: 'amber',   text: 'Moderate match',  icon: '~' },
    weak:      { color: 'red',     text: 'Weak match',      icon: '?' },
    no_similar_products: { color: 'red', text: 'No similar products found', icon: '⚠' },
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-bold text-navy-700">
          Hey {user?.name?.split(' ')[0] || 'there'} 👋
        </h1>
        <p className="text-navy-400 text-sm mt-0.5">Track prices and buy smarter with AI.</p>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Tracked Products', value: tracked.length, icon: Package, color: 'text-cyan-500', bg: 'bg-cyan-50' },
          { label: 'Searches', value: searchHistory.length, icon: Sparkles, color: 'text-violet-500', bg: 'bg-violet-50' },
          { label: 'Best Deals Found', value: tracked.filter(t => t.recommendation === 'buy').length, icon: TrendingDown, color: 'text-emerald-500', bg: 'bg-emerald-50' },
          { label: 'Active Alerts', value: '—', icon: Bell, color: 'text-amber-500', bg: 'bg-amber-50' },
        ].map(({ label, value, icon: Icon, color, bg }) => (
          <div key={label} className="bw-card p-4">
            <div className={`w-8 h-8 rounded-lg ${bg} flex items-center justify-center mb-2`}>
              <Icon className={`w-4 h-4 ${color}`} />
            </div>
            <p className="font-display text-2xl font-bold text-navy-700">{value}</p>
            <p className="text-xs text-navy-400 mt-0.5">{label}</p>
          </div>
        ))}
      </div>

      {/* Mode toggle */}
      <div className="flex gap-2">
        <button onClick={() => { setCompareMode(false); setCompareResult(null) }}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all ${
            !compareMode ? 'bg-cyan-500 text-white shadow-score' : 'bg-white border border-cyan-200 text-cyan-600 hover:bg-cyan-50'
          }`}>
          <Sparkles size={15} /> Analyze Product
        </button>
        <button onClick={() => { setCompareMode(true); setResult(null) }}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all ${
            compareMode ? 'bg-cyan-500 text-white shadow-score' : 'bg-white border border-cyan-200 text-cyan-600 hover:bg-cyan-50'
          }`}>
          <ArrowLeftRight size={15} /> Auto-Compare
        </button>
      </div>

      {!compareMode && (
        <>
          <ProductSearch onResult={setResult} />
          {result && <AnalysisResult result={result} />}
        </>
      )}

      {compareMode && (
        <div className="bw-card p-6 space-y-4">
          <div className="flex items-center gap-2 mb-1">
            <Wand2 className="text-cyan-500 w-5 h-5" />
            <h2 className="font-display font-semibold text-navy-700">Smart Cross-Platform Price Match</h2>
          </div>
          <p className="text-xs text-navy-400">
            Paste any URL. We scrape source + search Amazon, Flipkart, Myntra, Snapdeal → filter for TRUE similar products only (uses similarity scoring).
          </p>

          <div className="flex gap-3">
            <input
              value={autoCompareUrl}
              onChange={e => setAutoCompareUrl(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleAutoCompare()}
              placeholder="Paste any product URL..."
              className="flex-1 px-4 py-3 rounded-xl border border-cyan-200 bg-cyan-50 text-navy-700 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-300 focus:bg-white transition-all"
            />
            <button onClick={handleAutoCompare} disabled={compareLoading || !autoCompareUrl}
              className="px-5 py-3 bg-cyan-500 hover:bg-cyan-600 text-white rounded-xl text-sm font-semibold shadow-score bw-btn disabled:opacity-60 flex items-center gap-2">
              {compareLoading ? <Loader2 size={16} className="animate-spin" /> : <Wand2 size={16} />}
              {compareLoading ? 'Searching...' : 'Find Best Price'}
            </button>
          </div>

          {compareLoading && (
            <div className="text-center py-6 text-navy-400 text-sm">
              🔎 Scraping source · searching 4 platforms · filtering by similarity...
              <p className="text-xs mt-1">This can take 20-30 seconds</p>
            </div>
          )}

          {compareResult && compareResult.success && (
            <div className="mt-2 space-y-3">
              {/* Match quality banner */}
              {compareResult.match_quality && (() => {
                const cfg = matchQualityConfig[compareResult.match_quality] || matchQualityConfig.weak
                return (
                  <div className={`flex items-center gap-3 bg-${cfg.color}-50 border border-${cfg.color}-200 rounded-xl px-4 py-3`}>
                    <AlertCircle className={`text-${cfg.color}-500 w-5 h-5 flex-shrink-0`} />
                    <div>
                      <p className={`font-semibold text-${cfg.color}-700 text-sm`}>
                        Match Quality: {cfg.text}
                      </p>
                      <p className={`text-xs text-${cfg.color}-600`}>
                        {compareResult.match_quality === 'excellent' && 'Products appear to be near-identical across platforms'}
                        {compareResult.match_quality === 'good' && 'Products are very similar with minor variations'}
                        {compareResult.match_quality === 'moderate' && 'Products are similar but may have differences — verify before buying'}
                        {compareResult.match_quality === 'weak' && 'Products are only loosely related — treat as reference only'}
                        {compareResult.match_quality === 'no_similar_products' && 'This product appears to be unique to its platform'}
                      </p>
                    </div>
                  </div>
                )
              })()}

              {compareResult.recommendation && compareResult.best_platform && (
                <div className="flex items-center gap-3 bg-emerald-50 border border-emerald-200 rounded-xl px-4 py-3">
                  <Trophy className="text-emerald-500 w-5 h-5 flex-shrink-0" />
                  <div>
                    <p className="font-semibold text-emerald-700 text-sm">{compareResult.recommendation}</p>
                    {compareResult.search_keywords && (
                      <p className="text-xs text-emerald-600">Searched: "{compareResult.search_keywords}"</p>
                    )}
                  </div>
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {compareResult.options?.map((o: any, idx: number) => (
                  <div key={idx}
                    className={`rounded-xl border p-4 ${
                      o.is_best
                        ? 'border-emerald-300 bg-emerald-50'
                        : o.is_source
                        ? 'border-cyan-300 bg-cyan-50'
                        : 'border-cyan-100 bg-white'
                    }`}>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold uppercase tracking-wide text-cyan-600 bg-cyan-100 px-2 py-0.5 rounded-md">
                          {o.platform}
                        </span>
                        {o.is_source && (
                          <span className="text-xs text-navy-400">Your source</span>
                        )}
                        {o.similarity_score !== undefined && !o.is_source && (
                          <span className={`text-xs px-1.5 py-0.5 rounded ${
                            o.similarity_score >= 0.6 ? 'bg-emerald-100 text-emerald-700' :
                            o.similarity_score >= 0.4 ? 'bg-cyan-100 text-cyan-700' :
                            'bg-amber-100 text-amber-700'
                          }`}>
                            {Math.round(o.similarity_score * 100)}% match
                          </span>
                        )}
                      </div>
                      {o.is_best && (
                        <span className="text-xs font-bold text-emerald-600 bg-emerald-100 px-2 py-0.5 rounded-full">
                          🏆 Best
                        </span>
                      )}
                    </div>

                    {o.image_url && (
                      <img src={o.image_url} alt={o.name} className="w-full h-24 object-contain mb-2 rounded-lg bg-white" />
                    )}

                    <p className="text-sm font-medium text-navy-700 line-clamp-2 mb-2">{o.name}</p>

                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-xl font-bold text-navy-700">
                        ₹{o.current_price?.toLocaleString('en-IN') || 'N/A'}
                      </span>
                      {o.original_price && o.original_price > o.current_price && (
                        <span className="text-xs text-navy-400 line-through">
                          ₹{o.original_price?.toLocaleString('en-IN')}
                        </span>
                      )}
                      {o.savings > 0 && (
                        <span className="text-xs text-emerald-600 font-semibold">
                          Save ₹{o.savings?.toLocaleString('en-IN')} ({o.savings_pct}%)
                        </span>
                      )}
                    </div>

                    {o.rating && (
                      <p className="text-xs text-amber-600 mt-1">★ {o.rating}</p>
                    )}
                    {o.url && (
                      <a href={o.url} target="_blank" rel="noopener noreferrer"
                        className="mt-2 flex items-center gap-1 text-xs text-cyan-500 hover:underline">
                        <ExternalLink size={11} /> View on {o.platform}
                      </a>
                    )}
                  </div>
                ))}
              </div>

              {compareResult.options?.length === 1 && (
                <div className="text-center py-4 text-sm text-navy-400 bg-amber-50 border border-amber-200 rounded-xl">
                  ⚠️ No similar products found on other platforms. This item appears to be unique.
                </div>
              )}
            </div>
          )}

          {compareResult?.error && (
            <div className="bg-red-50 border border-red-200 rounded-xl p-3">
              <p className="text-red-600 text-sm">{compareResult.error}</p>
            </div>
          )}
        </div>
      )}

      {tracked.length > 0 && (
        <div className="bw-card p-5">
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-display font-semibold text-navy-700 text-sm">Tracked Products</h3>
            <Link href="/dashboard/track" className="text-xs text-cyan-500 hover:underline">See all</Link>
          </div>
          <div className="space-y-3">
            {tracked.slice(0, 3).map((t: any) => (
              <div key={t.tracked_id} className="flex items-center gap-3 p-3 rounded-xl bg-cyan-50 border border-cyan-100">
                {t.product.image_url && (
                  <img src={t.product.image_url} alt={t.product.name} className="w-10 h-10 rounded-lg object-cover" />
                )}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-navy-700 truncate">{t.product.name}</p>
                  <p className="text-xs text-navy-400">₹{t.product.current_price?.toLocaleString('en-IN')}</p>
                </div>
                {t.buy_score && <BuyScore score={t.buy_score} size="sm" showLabel={false} />}
              </div>
            ))}
          </div>
        </div>
      )}

      {searchHistory.length > 0 && (
        <div className="bw-card p-5">
          <h3 className="font-display font-semibold text-navy-700 text-sm mb-3">Recent Searches</h3>
          <div className="flex flex-wrap gap-2">
            {searchHistory.map((h: any) => (
              <span key={h.id} className="px-3 py-1.5 bg-cyan-50 border border-cyan-100 rounded-full text-xs text-cyan-700 font-medium truncate max-w-xs">
                {h.query}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
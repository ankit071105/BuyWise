'use client'
import { useEffect, useState } from 'react'
import { Package, Trash2, ExternalLink } from 'lucide-react'
import { productsApi } from '@/lib/api'
import BuyScore from '@/components/ui/BuyScore'
import PriceChart from '@/components/charts/PriceChart'
import toast from 'react-hot-toast'

export default function TrackPage() {
  const [tracked, setTracked] = useState<any[]>([])
  const [expanded, setExpanded] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    productsApi.getTracked()
      .then(r => setTracked(r.data))
      .catch(() => toast.error('Failed to load tracked products'))
      .finally(() => setLoading(false))
  }, [])

  async function untrack(id: number) {
    await productsApi.untrack(id)
    setTracked(prev => prev.filter(t => t.tracked_id !== id))
    toast.success('Removed from tracking')
  }

  if (loading) return <div className="text-center py-20 text-navy-400">Loading tracked products...</div>

  return (
    <div className="space-y-5">
      <div>
        <h1 className="font-display text-2xl font-bold text-navy-700 flex items-center gap-2">
          <Package className="text-cyan-500 w-6 h-6" /> Tracked Products
        </h1>
        <p className="text-navy-400 text-sm mt-0.5">{tracked.length} products being monitored</p>
      </div>

      {tracked.length === 0 ? (
        <div className="bw-card p-12 text-center">
          <Package className="text-cyan-300 w-10 h-10 mx-auto mb-3" />
          <p className="text-navy-500 font-medium">No tracked products yet</p>
          <p className="text-navy-400 text-sm mt-1">Analyze a product from the dashboard and click "Track This"</p>
        </div>
      ) : (
        tracked.map((t: any) => (
          <div key={t.tracked_id} className="bw-card p-5">
            <div className="flex items-start gap-4">
              {t.product.image_url && (
                <img src={t.product.image_url} className="w-16 h-16 rounded-xl object-cover border border-cyan-100" alt="" />
              )}
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <span className="text-xs font-semibold uppercase text-cyan-500 bg-cyan-50 px-2 py-0.5 rounded-md">
                      {t.product.platform}
                    </span>
                    <p className="font-semibold text-navy-700 mt-1 text-sm line-clamp-1">{t.product.name}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-lg font-bold text-navy-700">
                        ₹{t.product.current_price?.toLocaleString('en-IN') || 'N/A'}
                      </span>
                      {t.target_price && (
                        <span className="text-xs text-amber-600 bg-amber-50 px-2 py-0.5 rounded-full">
                          Target: ₹{t.target_price.toLocaleString('en-IN')}
                        </span>
                      )}
                    </div>
                  </div>
                  {t.buy_score && (
                    <BuyScore score={t.buy_score} size="sm" recommendation={t.recommendation} />
                  )}
                </div>

                {t.reasoning && (
                  <p className="text-xs text-navy-400 mt-2 line-clamp-2 italic">"{t.reasoning}"</p>
                )}

                <div className="flex gap-2 mt-3">
                  <button onClick={() => setExpanded(expanded === t.tracked_id ? null : t.tracked_id)}
                    className="text-xs text-cyan-500 hover:underline">
                    {expanded === t.tracked_id ? 'Hide' : 'Show'} price chart
                  </button>
                  <a href={t.product.url} target="_blank" rel="noopener noreferrer"
                    className="text-xs text-navy-400 hover:text-cyan-500 flex items-center gap-0.5">
                    <ExternalLink size={11} /> View
                  </a>
                  <button onClick={() => untrack(t.tracked_id)}
                    className="text-xs text-red-400 hover:text-red-600 flex items-center gap-0.5 ml-auto">
                    <Trash2 size={11} /> Remove
                  </button>
                </div>
              </div>
            </div>

            {expanded === t.tracked_id && t.price_history?.length > 0 && (
              <div className="mt-4 pt-4 border-t border-cyan-100">
                <PriceChart data={t.price_history} currentPrice={t.product.current_price} />
              </div>
            )}
          </div>
        ))
      )}
    </div>
  )
}

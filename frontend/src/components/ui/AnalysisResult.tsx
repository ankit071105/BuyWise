'use client'
import { useState } from 'react'
import { ExternalLink, Bell, CheckCircle, AlertTriangle, TrendingDown, TrendingUp, Minus, ShieldAlert, Ruler } from 'lucide-react'
import BuyScore from './BuyScore'
import PriceChart from '@/components/charts/PriceChart'
import SmartFeatures from './SmartFeatures'
import { productsApi, alertsApi } from '@/lib/api'
import toast from 'react-hot-toast'

interface Props { result: any }

export default function AnalysisResult({ result }: Props) {
  const [tracking, setTracking] = useState(false)
  const [targetPrice, setTargetPrice] = useState('')

  const product = result?.product || {}
  const buyScore = result?.buy_score || {}
  const prediction = result?.price_prediction || {}
  const reviewSummary = result?.review_summary || {}
  const reasoning = result?.llm_reasoning || ''
  const priceHistory = result?.price_history || []
  const productId = result?.product_id
  const festival = result?.festival || {}

  const TrendIcon = prediction.trend === 'falling' ? TrendingDown : prediction.trend === 'rising' ? TrendingUp : Minus
  const trendColor = prediction.trend === 'falling' ? 'text-emerald-500' : prediction.trend === 'rising' ? 'text-red-400' : 'text-navy-400'

  async function handleTrack() {
    if (!productId) return toast.error('Save the product first')
    try {
      await productsApi.track(productId, targetPrice ? parseFloat(targetPrice) : undefined)
      toast.success('Added to tracked products!')
      setTracking(false)
    } catch { toast.error('Tracking failed') }
  }

  async function handleAlert() {
    if (!productId) return toast.error('Analyze a product first')
    try {
      await alertsApi.create({ product_id: productId, alert_type: 'price_drop', channel: 'email' })
      toast.success('Price drop alert set!')
    } catch { toast.error('Alert creation failed') }
  }

  if (!result?.success) return null

  return (
    <div className="space-y-4 mt-6">
      {/* Festival banner */}
      {(festival.active || festival.upcoming) && (
        <div className="bw-card p-4 border-l-4 border-amber-400 bg-amber-50">
          <div className="flex items-center gap-3">
            <span className="text-2xl">🎉</span>
            <div>
              {festival.active ? (
                <>
                  <p className="text-sm font-bold text-amber-700">{festival.active.name} is LIVE</p>
                  <p className="text-xs text-amber-600">Great time to buy — sales are active right now</p>
                </>
              ) : (
                <>
                  <p className="text-sm font-bold text-amber-700">
                    {festival.upcoming.name} in {festival.upcoming.days_away} days
                  </p>
                  <p className="text-xs text-amber-600">Consider waiting for the sale for better prices</p>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Product header */}
      <div className="bw-card p-5 flex gap-4">
        {product.image_url && (
          <img src={product.image_url} alt={product.name} className="w-24 h-24 rounded-xl object-cover border border-cyan-100" />
        )}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <div>
              <span className="text-xs font-semibold uppercase tracking-wide text-cyan-500 bg-cyan-50 px-2 py-0.5 rounded-md">
                {product.platform}
              </span>
              <h2 className="font-display font-semibold text-navy-700 mt-1 text-base leading-snug line-clamp-2">
                {product.name}
              </h2>
            </div>
            {buyScore.score !== undefined && (
              <BuyScore score={buyScore.score} recommendation={buyScore.recommendation_label} size="md" />
            )}
          </div>

          <div className="flex items-center gap-3 mt-2 flex-wrap">
            <span className="text-2xl font-bold text-navy-700">
              ₹{product.current_price?.toLocaleString('en-IN') || 'N/A'}
            </span>
            {product.original_price && product.original_price > product.current_price && (
              <span className="text-sm text-navy-400 line-through">
                ₹{product.original_price.toLocaleString('en-IN')}
              </span>
            )}
            {product.rating && (
              <span className="text-xs text-amber-600 bg-amber-50 px-2 py-0.5 rounded-md font-medium">
                ★ {product.rating}
              </span>
            )}
            {product.url && (
              <a href={product.url} target="_blank" rel="noopener noreferrer"
                className="text-cyan-500 hover:text-cyan-600 flex items-center gap-1 text-xs">
                <ExternalLink size={13} /> View
              </a>
            )}
          </div>
        </div>
      </div>

      {/* AI Reasoning */}
      {reasoning && (
        <div className="bw-card p-5 border-l-4 border-cyan-400">
          <p className="text-xs font-bold text-cyan-500 uppercase tracking-wide mb-1.5">BuyWise AI Says</p>
          <p className="text-navy-700 text-sm leading-relaxed">{reasoning}</p>
        </div>
      )}

      {/* Score breakdown + Price info */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bw-card p-5">
          <p className="text-xs font-bold text-navy-500 uppercase tracking-wide mb-4">Score Breakdown</p>
          {[
            { label: 'Price Position', score: buyScore.price_score, desc: '40% weight' },
            { label: 'Review Quality', score: buyScore.review_score, desc: '35% weight' },
            { label: 'Buy Timing', score: buyScore.timing_score, desc: '25% weight' },
          ].map(({ label, score, desc }) => score !== undefined && (
            <div key={label} className="mb-3">
              <div className="flex justify-between text-sm mb-1">
                <span className="text-navy-600 font-medium">{label}</span>
                <span className="text-navy-400 text-xs">{score?.toFixed(1)}/10 · {desc}</span>
              </div>
              <div className="h-2 bg-cyan-50 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-cyan-400 to-cyan-600 transition-all duration-700"
                  style={{ width: `${(score / 10) * 100}%` }}
                />
              </div>
            </div>
          ))}
        </div>

        <div className="bw-card p-5">
          <p className="text-xs font-bold text-navy-500 uppercase tracking-wide mb-4">Price Intelligence</p>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-navy-500">Historical Low</span>
              <span className="font-semibold text-emerald-600">
                ₹{prediction.historical_min?.toLocaleString('en-IN') || 'N/A'}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-navy-500">Historical Avg</span>
              <span className="font-semibold text-navy-700">
                ₹{prediction.historical_avg?.toLocaleString('en-IN') || 'N/A'}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-navy-500">Predicted Low</span>
              <span className="font-semibold text-cyan-600">
                ₹{buyScore.predicted_low_price?.toLocaleString('en-IN') || 'N/A'}
                {buyScore.predicted_low_days && <span className="text-xs text-navy-400 ml-1">in ~{buyScore.predicted_low_days}d</span>}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-navy-500">Price Trend</span>
              <span className={`flex items-center gap-1 font-semibold text-sm ${trendColor}`}>
                <TrendIcon size={14} />
                {prediction.trend || 'unknown'}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-navy-500">Volatility</span>
              <span className="text-sm text-navy-600">{prediction.price_volatility || 0}%</span>
            </div>
          </div>
        </div>
      </div>

      {/* Price History Chart */}
      {priceHistory.length > 0 && (
        <div className="bw-card p-5">
          <p className="text-xs font-bold text-navy-500 uppercase tracking-wide mb-4">Price History</p>
          <PriceChart
            data={priceHistory}
            currentPrice={product.current_price}
            predictedLow={buyScore.predicted_low_price}
          />
        </div>
      )}

      {/* Review insights */}
      <div className="bw-card p-5">
        <p className="text-xs font-bold text-navy-500 uppercase tracking-wide mb-4">Review Intelligence</p>
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-cyan-50 rounded-xl p-3">
            <p className="text-xs text-navy-400 mb-0.5">Genuine Reviews</p>
            <p className="font-bold text-navy-700">{reviewSummary.valid_count || 0}</p>
          </div>
          <div className={`rounded-xl p-3 ${reviewSummary.fake_count > 0 ? 'bg-red-50' : 'bg-emerald-50'}`}>
            <p className="text-xs text-navy-400 mb-0.5 flex items-center gap-1">
              <ShieldAlert size={11} /> Suspicious
            </p>
            <p className={`font-bold ${reviewSummary.fake_count > 0 ? 'text-red-600' : 'text-emerald-600'}`}>
              {reviewSummary.fake_count || 0} ({reviewSummary.fake_percentage || 0}%)
            </p>
          </div>
          <div className="bg-cyan-50 rounded-xl p-3">
            <p className="text-xs text-navy-400 mb-0.5">Sentiment</p>
            <p className="font-bold text-navy-700">{reviewSummary.sentiment_label || 'N/A'}</p>
          </div>
          {reviewSummary.dominant_fit && (
            <div className="bg-amber-50 rounded-xl p-3">
              <p className="text-xs text-navy-400 mb-0.5 flex items-center gap-1">
                <Ruler size={11} /> Size Fit
              </p>
              <p className="font-bold text-amber-700 capitalize">{reviewSummary.dominant_fit}</p>
            </div>
          )}
        </div>
      </div>

      {/* Actions */}
      <div className="bw-card p-5 flex flex-wrap gap-3 items-center">
        <div className="flex gap-2 flex-1">
          <input
            type="number"
            placeholder="Target price ₹ (optional)"
            value={targetPrice}
            onChange={e => setTargetPrice(e.target.value)}
            className="px-3 py-2 rounded-xl border border-cyan-200 bg-cyan-50 text-sm text-navy-700 focus:outline-none focus:ring-2 focus:ring-cyan-300 w-48"
          />
          <button onClick={handleTrack}
            className="flex items-center gap-2 px-4 py-2 bg-cyan-500 text-white rounded-xl text-sm font-semibold hover:bg-cyan-600 shadow-score bw-btn">
            <CheckCircle size={15} /> Track This
          </button>
        </div>
        <button onClick={handleAlert}
          className="flex items-center gap-2 px-4 py-2 bg-white border border-cyan-200 text-cyan-600 rounded-xl text-sm font-semibold hover:bg-cyan-50 bw-btn">
          <Bell size={15} /> Set Alert
        </button>
      </div>

      {/* SMART FEATURES — Price manipulation, Regret, TCO, Sustainability, Alternatives */}
      <SmartFeatures smart={result?.smart_features} />
    </div>
  )
}
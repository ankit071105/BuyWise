'use client'
import { AlertTriangle, ShieldCheck, IndianRupee, Leaf, Sparkles, ExternalLink, TrendingDown, Package, Info } from 'lucide-react'

interface Props { smart: any }

export default function SmartFeatures({ smart }: Props) {
  if (!smart) return null

  const priceManip = smart.price_manipulation
  const regret = smart.regret_analysis
  const tco = smart.total_cost_of_ownership
  const sust = smart.sustainability
  const alts = smart.alternatives

  return (
    <div className="space-y-4 mt-4">
      {/* Header */}
      <div className="flex items-center gap-2">
        <Sparkles className="text-cyan-500 w-5 h-5" />
        <h3 className="font-display font-bold text-navy-700 text-base">
          BuyWise Smart Insights
        </h3>
        <span className="text-xs bg-cyan-100 text-cyan-700 px-2 py-0.5 rounded-full font-semibold">
          Only on BuyWise
        </span>
      </div>

      {/* Price Manipulation Detector */}
      {priceManip && priceManip.claimed_discount_pct > 0 && (
        <div className={`bw-card p-5 border-l-4 ${
          priceManip.manipulation_detected ? 'border-red-400' : 'border-emerald-400'
        }`}>
          <div className="flex items-start gap-3">
            <div className={`w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 ${
              priceManip.manipulation_detected ? 'bg-red-50' : 'bg-emerald-50'
            }`}>
              {priceManip.manipulation_detected
                ? <AlertTriangle className="text-red-500 w-5 h-5" />
                : <ShieldCheck className="text-emerald-500 w-5 h-5" />
              }
            </div>
            <div className="flex-1">
              <p className="text-xs font-bold uppercase tracking-wide text-navy-500 mb-1">
                Price Manipulation Check
              </p>
              <p className={`font-semibold text-sm mb-2 ${
                priceManip.manipulation_detected ? 'text-red-600' : 'text-emerald-600'
              }`}>
                {priceManip.verdict}
              </p>
              <div className="grid grid-cols-3 gap-3 mt-3">
                <div className="bg-cyan-50 rounded-lg p-2">
                  <p className="text-xs text-navy-400">Claimed Discount</p>
                  <p className="font-bold text-navy-700">{priceManip.claimed_discount_pct}%</p>
                </div>
                <div className={`rounded-lg p-2 ${priceManip.real_discount_pct !== null ? 'bg-cyan-50' : 'bg-navy-50'}`}>
                  <p className="text-xs text-navy-400">Real Discount</p>
                  <p className="font-bold text-navy-700">
                    {priceManip.real_discount_pct !== null ? `${priceManip.real_discount_pct}%` : 'Need history'}
                  </p>
                </div>
                <div className="bg-amber-50 rounded-lg p-2">
                  <p className="text-xs text-navy-400">Suspicion Score</p>
                  <p className="font-bold text-amber-700">{priceManip.manipulation_score}/100</p>
                </div>
              </div>
              {priceManip.warnings?.length > 0 && (
                <ul className="mt-3 space-y-1">
                  {priceManip.warnings.map((w: string, i: number) => (
                    <li key={i} className="text-xs text-red-600 flex items-start gap-1.5">
                      <span>•</span> {w}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Regret Predictor */}
      {regret && regret.regret_score !== null && (
        <div className={`bw-card p-5 border-l-4 ${
          regret.regret_risk === 'high' ? 'border-red-400' :
          regret.regret_risk === 'moderate' ? 'border-amber-400' : 'border-emerald-400'
        }`}>
          <div className="flex items-start gap-3">
            <div className={`w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 ${
              regret.regret_risk === 'high' ? 'bg-red-50' :
              regret.regret_risk === 'moderate' ? 'bg-amber-50' : 'bg-emerald-50'
            }`}>
              <TrendingDown className={
                regret.regret_risk === 'high' ? 'text-red-500 w-5 h-5' :
                regret.regret_risk === 'moderate' ? 'text-amber-500 w-5 h-5' : 'text-emerald-500 w-5 h-5'
              } />
            </div>
            <div className="flex-1">
              <p className="text-xs font-bold uppercase tracking-wide text-navy-500 mb-1">
                Regret Risk Predictor
              </p>
              <div className="flex items-center gap-3 mb-2">
                <p className="font-bold text-2xl text-navy-700">{regret.regret_score}/10</p>
                <span className={`text-xs font-semibold px-2 py-1 rounded-full capitalize ${
                  regret.regret_risk === 'high' ? 'bg-red-100 text-red-700' :
                  regret.regret_risk === 'moderate' ? 'bg-amber-100 text-amber-700' :
                  'bg-emerald-100 text-emerald-700'
                }`}>
                  {regret.regret_risk.replace('_', ' ')} risk
                </span>
              </div>
              <p className="text-sm text-navy-600 mb-2">{regret.verdict}</p>
              {regret.top_regret_reasons?.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mt-2">
                  {regret.top_regret_reasons.map((r: string, i: number) => (
                    <span key={i} className="text-xs bg-red-50 text-red-600 px-2 py-1 rounded-md">
                      {r}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Total Cost of Ownership */}
      {tco && tco.true_cost_upfront && (
        <div className="bw-card p-5 border-l-4 border-cyan-400">
          <div className="flex items-start gap-3">
            <div className="w-9 h-9 rounded-xl bg-cyan-50 flex items-center justify-center flex-shrink-0">
              <IndianRupee className="text-cyan-500 w-5 h-5" />
            </div>
            <div className="flex-1">
              <p className="text-xs font-bold uppercase tracking-wide text-navy-500 mb-1">
                True Cost of Ownership
              </p>
              <p className="text-sm text-navy-600 mb-3">{tco.verdict}</p>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                <div className="bg-cyan-50 rounded-lg p-2.5">
                  <p className="text-xs text-navy-400">Listed</p>
                  <p className="font-bold text-navy-700 text-sm">₹{tco.listed_price?.toLocaleString('en-IN')}</p>
                </div>
                <div className="bg-cyan-50 rounded-lg p-2.5">
                  <p className="text-xs text-navy-400">True Upfront</p>
                  <p className="font-bold text-cyan-700 text-sm">₹{tco.true_cost_upfront?.toLocaleString('en-IN')}</p>
                </div>
                {tco.true_cost_with_emi > tco.true_cost_upfront && (
                  <div className="bg-amber-50 rounded-lg p-2.5">
                    <p className="text-xs text-navy-400">With EMI</p>
                    <p className="font-bold text-amber-700 text-sm">₹{tco.true_cost_with_emi?.toLocaleString('en-IN')}</p>
                  </div>
                )}
                <div className="bg-emerald-50 rounded-lg p-2.5">
                  <p className="text-xs text-navy-400">Per Year</p>
                  <p className="font-bold text-emerald-700 text-sm">₹{tco.cost_per_year?.toLocaleString('en-IN')}</p>
                </div>
              </div>
              {tco.breakdown && (
                <details className="mt-3 text-xs">
                  <summary className="cursor-pointer text-cyan-600 font-medium">Cost breakdown</summary>
                  <div className="mt-2 space-y-1 pl-3 text-navy-500">
                    {Object.entries(tco.breakdown).map(([k, v]: any) => (
                      <div key={k} className="flex justify-between">
                        <span className="capitalize">{k.replace(/_/g, ' ')}</span>
                        <span>₹{Number(v).toLocaleString('en-IN')}</span>
                      </div>
                    ))}
                  </div>
                </details>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Sustainability */}
      {sust && sust.sustainability_score !== null && (
        <div className="bw-card p-5 border-l-4 border-emerald-400">
          <div className="flex items-start gap-3">
            <div className="w-9 h-9 rounded-xl bg-emerald-50 flex items-center justify-center flex-shrink-0">
              <Leaf className="text-emerald-500 w-5 h-5" />
            </div>
            <div className="flex-1">
              <p className="text-xs font-bold uppercase tracking-wide text-navy-500 mb-1">
                Sustainability Score
              </p>
              <div className="flex items-center gap-3 mb-2">
                <p className="font-bold text-2xl text-navy-700">{sust.sustainability_score}/10</p>
                <span className="text-sm font-semibold text-emerald-600">{sust.label}</span>
              </div>
              <div className="grid grid-cols-3 gap-2 mt-2">
                <div className="bg-emerald-50 rounded-lg p-2">
                  <p className="text-xs text-navy-400">Brand ESG</p>
                  <p className="font-semibold text-navy-700 text-sm">
                    {sust.brand_esg_score}/10
                    {sust.brand_detected && <span className="text-xs text-navy-400 block">{sust.brand_detected}</span>}
                  </p>
                </div>
                <div className="bg-emerald-50 rounded-lg p-2">
                  <p className="text-xs text-navy-400">Platform</p>
                  <p className="font-semibold text-navy-700 text-sm">{sust.platform_packaging_score}/10</p>
                </div>
                <div className="bg-emerald-50 rounded-lg p-2">
                  <p className="text-xs text-navy-400">Category</p>
                  <p className="font-semibold text-navy-700 text-sm">{sust.product_category_score}/10</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Alternative Products (only shown when Buy Score low) */}
      {alts?.triggered && alts.alternatives?.length > 0 && (
        <div className="bw-card p-5 border-l-4 border-violet-400">
          <div className="flex items-start gap-3">
            <div className="w-9 h-9 rounded-xl bg-violet-50 flex items-center justify-center flex-shrink-0">
              <Package className="text-violet-500 w-5 h-5" />
            </div>
            <div className="flex-1">
              <p className="text-xs font-bold uppercase tracking-wide text-navy-500 mb-1">
                Better Alternatives Suggested
              </p>
              <p className="text-sm text-navy-600 mb-3">
                {alts.verdict || `Since Buy Score is low, here are better options:`}
              </p>
              <div className="space-y-2">
                {alts.alternatives.map((a: any, i: number) => (
                  <a key={i} href={a.url} target="_blank" rel="noopener noreferrer"
                    className="flex items-center gap-3 p-2 rounded-xl bg-violet-50 hover:bg-violet-100 transition-colors group">
                    {a.image_url && (
                      <img src={a.image_url} className="w-10 h-10 rounded-lg object-cover" alt="" />
                    )}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-navy-700 truncate">{a.name}</p>
                      <div className="flex gap-2 items-center">
                        <span className="text-xs font-bold text-violet-700">
                          ₹{a.current_price?.toLocaleString('en-IN')}
                        </span>
                        <span className="text-xs uppercase text-navy-400">{a.platform}</span>
                        {a.rating && <span className="text-xs text-amber-600">★ {a.rating}</span>}
                      </div>
                    </div>
                    <ExternalLink size={13} className="text-violet-500 group-hover:translate-x-0.5 transition-transform" />
                  </a>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

'use client'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'
import { format } from 'date-fns'

interface PricePoint { price: number; date: string }

interface PriceChartProps {
  data: PricePoint[]
  currentPrice?: number
  predictedLow?: number
}

function CustomTooltip({ active, payload, label }: any) {
  if (active && payload?.length) {
    return (
      <div className="bg-white border border-cyan-100 rounded-xl shadow-hover px-4 py-3 text-sm">
        <p className="text-navy-400 text-xs mb-1">{label}</p>
        <p className="font-bold text-navy-700">₹{payload[0].value.toLocaleString('en-IN')}</p>
      </div>
    )
  }
  return null
}

export default function PriceChart({ data, currentPrice, predictedLow }: PriceChartProps) {
  if (!data?.length) {
    return (
      <div className="h-48 flex items-center justify-center text-navy-400 text-sm">
        No price history yet. Check back after the next scrape.
      </div>
    )
  }

  const chartData = data.map(d => ({
    price: d.price,
    date: (() => { try { return format(new Date(d.date), 'dd MMM') } catch { return d.date } })()
  }))

  const allPrices = data.map(d => d.price)
  const minPrice = Math.min(...allPrices)
  const maxPrice = Math.max(...allPrices)
  const padding = (maxPrice - minPrice) * 0.1 || 100
  const yMin = Math.floor(minPrice - padding)
  const yMax = Math.ceil(maxPrice + padding)

  return (
    <div className="w-full h-56">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData} margin={{ top: 8, right: 8, left: 8, bottom: 0 }}>
          <defs>
            <linearGradient id="priceGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor="#0891B2" stopOpacity={0.2} />
              <stop offset="95%" stopColor="#0891B2" stopOpacity={0.01} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#E0F7FA" vertical={false} />
          <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#94A3B8' }} axisLine={false} tickLine={false} />
          <YAxis
            tickFormatter={(v) => `₹${(v/1000).toFixed(0)}k`}
            tick={{ fontSize: 11, fill: '#94A3B8' }}
            axisLine={false} tickLine={false}
            domain={[yMin, yMax]}
          />
          <Tooltip content={<CustomTooltip />} />
          {predictedLow && (
            <ReferenceLine
              y={predictedLow} stroke="#059669" strokeDasharray="4 3" strokeWidth={1.5}
              label={{ value: `Predicted Low ₹${predictedLow.toLocaleString('en-IN')}`, position: 'insideTopRight', fontSize: 10, fill: '#059669' }}
            />
          )}
          {currentPrice && (
            <ReferenceLine
              y={currentPrice} stroke="#0891B2" strokeDasharray="4 3" strokeWidth={1.5}
              label={{ value: 'Current', position: 'insideBottomRight', fontSize: 10, fill: '#0891B2' }}
            />
          )}
          <Area type="monotone" dataKey="price" stroke="#0891B2" strokeWidth={2.5}
            fill="url(#priceGrad)" dot={false} activeDot={{ r: 5, fill: '#0891B2', strokeWidth: 0 }} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}

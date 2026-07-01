'use client'
import clsx from 'clsx'

interface BuyScoreProps {
  score: number
  size?: 'sm' | 'md' | 'lg'
  showLabel?: boolean
  recommendation?: string
}

function getScoreStyle(score: number) {
  if (score >= 7.5) return { color: '#059669', bg: '#ECFDF5', label: 'Great Buy', cls: 'score-great' }
  if (score >= 5.5) return { color: '#0891B2', bg: '#ECFEFF', label: 'Consider', cls: 'score-consider' }
  if (score >= 4.0) return { color: '#D97706', bg: '#FFFBEB', label: 'Wait', cls: 'score-wait' }
  return { color: '#DC2626', bg: '#FEF2F2', label: 'Avoid', cls: 'score-avoid' }
}

export default function BuyScore({ score, size = 'md', showLabel = true, recommendation }: BuyScoreProps) {
  const style = getScoreStyle(score)
  const radius = size === 'lg' ? 52 : size === 'md' ? 40 : 28
  const stroke = size === 'lg' ? 7 : 5
  const circ = 2 * Math.PI * radius
  const dash = (score / 10) * circ
  const svgSize = (radius + stroke + 4) * 2
  const textSize = size === 'lg' ? 'text-3xl' : size === 'md' ? 'text-xl' : 'text-base'

  return (
    <div className="flex flex-col items-center gap-1.5">
      <div className="relative flex items-center justify-center">
        <svg width={svgSize} height={svgSize} viewBox={`0 0 ${svgSize} ${svgSize}`}>
          {/* Track */}
          <circle
            cx={svgSize / 2} cy={svgSize / 2} r={radius}
            fill="none" stroke="#E0F7FA" strokeWidth={stroke}
          />
          {/* Progress */}
          <circle
            cx={svgSize / 2} cy={svgSize / 2} r={radius}
            fill="none" stroke={style.color} strokeWidth={stroke}
            strokeDasharray={`${dash} ${circ}`}
            strokeLinecap="round"
            transform={`rotate(-90 ${svgSize / 2} ${svgSize / 2})`}
            style={{ transition: 'stroke-dasharray 0.6s ease' }}
          />
        </svg>
        <div className="absolute flex flex-col items-center">
          <span className={clsx('font-display font-bold leading-none', textSize)} style={{ color: style.color }}>
            {score.toFixed(1)}
          </span>
          {size !== 'sm' && <span className="text-xs text-navy-400 font-medium mt-0.5">/10</span>}
        </div>
      </div>
      {showLabel && (
        <span className={clsx('text-xs font-semibold px-2.5 py-1 rounded-full', style.cls)}>
          {recommendation || style.label}
        </span>
      )}
    </div>
  )
}

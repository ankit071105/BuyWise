'use client'
import { useEffect, useState } from 'react'
import { Bell, Trash2, CheckCircle, Clock } from 'lucide-react'
import { alertsApi } from '@/lib/api'
import toast from 'react-hot-toast'

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<any[]>([])

  useEffect(() => {
    alertsApi.get().then(r => setAlerts(r.data)).catch(() => {})
  }, [])

  async function deleteAlert(id: number) {
    await alertsApi.delete(id)
    setAlerts(prev => prev.filter(a => a.id !== id))
    toast.success('Alert removed')
  }

  return (
    <div className="space-y-5">
      <div>
        <h1 className="font-display text-2xl font-bold text-navy-700 flex items-center gap-2">
          <Bell className="text-cyan-500 w-6 h-6" /> Alerts
        </h1>
        <p className="text-navy-400 text-sm mt-0.5">
          You'll be notified via email or Telegram when conditions are met.
          {/* ⚠️ NOTE: Telegram notifications require TELEGRAM_BOT_TOKEN in backend .env */}
        </p>
      </div>

      {/* Telegram setup notice */}
      <div className="bw-card p-4 border-l-4 border-cyan-400 bg-cyan-50">
        <p className="text-sm font-semibold text-navy-700 mb-1">Set up Telegram Notifications</p>
        <p className="text-xs text-navy-500">
          Add your Telegram username in Settings and add <code className="bg-cyan-100 px-1 py-0.5 rounded text-xs">TELEGRAM_BOT_TOKEN</code> to backend .env for real-time price drop alerts.
        </p>
      </div>

      {alerts.length === 0 ? (
        <div className="bw-card p-12 text-center">
          <Bell className="text-cyan-300 w-10 h-10 mx-auto mb-3" />
          <p className="text-navy-500 font-medium">No alerts set</p>
          <p className="text-navy-400 text-sm mt-1">Analyze a product and click "Set Alert" to get notified on price drops</p>
        </div>
      ) : (
        <div className="bw-card divide-y divide-cyan-50">
          {alerts.map((a: any) => (
            <div key={a.id} className="flex items-center gap-4 px-5 py-4">
              <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${a.is_triggered ? 'bg-emerald-50' : 'bg-amber-50'}`}>
                {a.is_triggered
                  ? <CheckCircle size={16} className="text-emerald-500" />
                  : <Clock size={16} className="text-amber-500" />}
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-navy-700 capitalize">
                  {a.alert_type.replace('_', ' ')} · Product #{a.product_id}
                </p>
                <div className="flex gap-2 mt-0.5">
                  {a.threshold && <span className="text-xs text-navy-400">Target: ₹{a.threshold.toLocaleString('en-IN')}</span>}
                  <span className="text-xs text-cyan-500 capitalize">{a.channel}</span>
                  <span className={`text-xs font-medium ${a.is_triggered ? 'text-emerald-600' : 'text-amber-600'}`}>
                    {a.is_triggered ? 'Triggered' : 'Watching'}
                  </span>
                </div>
              </div>
              <button onClick={() => deleteAlert(a.id)} className="text-red-400 hover:text-red-600 transition-colors">
                <Trash2 size={15} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

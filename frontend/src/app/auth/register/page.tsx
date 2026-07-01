'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Zap } from 'lucide-react'
import { authApi } from '@/lib/api'
import { useAuthStore } from '@/lib/store'
import toast from 'react-hot-toast'

export default function RegisterPage() {
  const [form, setForm] = useState({ name: '', email: '', password: '' })
  const [loading, setLoading] = useState(false)
  const router = useRouter()
  const { setAuth } = useAuthStore()

  async function handleRegister(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    try {
      const res = await authApi.register(form)
      setAuth(res.data.user, res.data.access_token)
      toast.success('Account created! Welcome to BuyWise 🎉')
      router.push('/dashboard')
    } catch (e: any) {
      toast.error(e.response?.data?.detail || 'Registration failed')
    } finally { setLoading(false) }
  }

  return (
    <div className="min-h-screen bg-surface-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 mb-4">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-400 to-cyan-600 flex items-center justify-center shadow-score">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <span className="font-display font-bold text-navy-700 text-2xl">BuyWise</span>
          </div>
          <h1 className="font-display text-2xl font-bold text-navy-700">Create your account</h1>
          <p className="text-navy-400 text-sm mt-1">Start shopping smarter — it's free</p>
        </div>

        <div className="bw-card p-8">
          <form onSubmit={handleRegister} className="space-y-4">
            {[
              { key: 'name', label: 'Full Name', type: 'text', placeholder: 'Ankit Kumar' },
              { key: 'email', label: 'Email', type: 'email', placeholder: 'you@example.com' },
              { key: 'password', label: 'Password', type: 'password', placeholder: '8+ characters' },
            ].map(({ key, label, type, placeholder }) => (
              <div key={key}>
                <label className="block text-sm font-medium text-navy-600 mb-1.5">{label}</label>
                <input type={type} value={(form as any)[key]} required
                  onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))}
                  className="w-full px-4 py-3 rounded-xl border border-cyan-200 bg-cyan-50 text-navy-700 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-300 focus:bg-white transition-all"
                  placeholder={placeholder} />
              </div>
            ))}
            <button type="submit" disabled={loading}
              className="w-full py-3 bg-cyan-500 hover:bg-cyan-600 text-white font-semibold rounded-xl shadow-score bw-btn disabled:opacity-60 text-sm mt-2">
              {loading ? 'Creating account...' : 'Create Account'}
            </button>
          </form>
          <p className="text-center text-sm text-navy-400 mt-5">
            Already have an account?{' '}
            <Link href="/auth/login" className="text-cyan-600 font-semibold hover:underline">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  )
}

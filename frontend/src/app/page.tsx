import Link from 'next/link'
import { Zap, TrendingDown, ShieldCheck, Ruler, Bell, Bot, ArrowRight } from 'lucide-react'

const FEATURES = [
  { icon: TrendingDown, title: 'Price History & Prediction', desc: 'See lowest ever price + AI-predicted price drop date using ML models' },
  { icon: ShieldCheck, title: 'Fake Review Detection', desc: 'Burst-pattern analysis flags suspicious reviews so you only trust genuine ones' },
  { icon: Ruler, title: 'Fit/Size Intelligence', desc: 'For footwear: automatically detects if a product runs small, large, or true to size' },
  { icon: Zap, title: 'Buy Score™ (0–10)', desc: 'AI synthesizes price position, review quality, and timing into one actionable score' },
  { icon: Bell, title: 'Festival Sale Alerts', desc: 'Know before Big Billion Days, Diwali, Republic Day — India-specific sale timing engine' },
  { icon: Bot, title: 'AI Shopping Assistant', desc: 'Chat with BuyWise AI to decode scores, compare products, or decide when to buy' },
]

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-surface-100">
      {/* Nav */}
      <nav className="sticky top-0 z-50 bg-white/80 backdrop-blur-sm border-b border-cyan-100 px-8 py-4 flex justify-between items-center">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-400 to-cyan-600 flex items-center justify-center">
            <Zap className="w-4 h-4 text-white" />
          </div>
          <span className="font-display font-bold text-navy-700 text-lg">BuyWise</span>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/auth/login" className="text-sm text-navy-500 hover:text-cyan-600 font-medium transition-colors">
            Login
          </Link>
          <Link href="/auth/register"
            className="text-sm bg-cyan-500 hover:bg-cyan-600 text-white font-semibold px-4 py-2 rounded-xl shadow-score transition-all">
            Get Started Free
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="max-w-4xl mx-auto px-8 pt-24 pb-16 text-center">
        <div className="inline-flex items-center gap-2 bg-cyan-100 text-cyan-600 text-xs font-semibold px-3 py-1.5 rounded-full mb-6">
          <Zap size={12} /> AI-Powered · Amazon & Flipkart · Made for India
        </div>
        <h1 className="font-display text-5xl font-bold text-navy-700 leading-tight mb-5">
          Stop Overpaying.<br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-500 to-cyan-700">
            Buy at the Right Price.
          </span>
        </h1>
        <p className="text-navy-500 text-lg max-w-2xl mx-auto mb-8 leading-relaxed">
          BuyWise tracks prices, detects fake reviews, predicts the best time to buy, and gives every product a single AI-powered Buy Score — so you never second-guess a purchase.
        </p>
        <div className="flex gap-3 justify-center">
          <Link href="/auth/register"
            className="flex items-center gap-2 bg-cyan-500 hover:bg-cyan-600 text-white font-semibold px-6 py-3.5 rounded-xl shadow-score transition-all">
            Start Tracking Free <ArrowRight size={16} />
          </Link>
          <Link href="/auth/login"
            className="flex items-center gap-2 bg-white border border-cyan-200 text-navy-600 font-semibold px-6 py-3.5 rounded-xl hover:bg-cyan-50 transition-all">
            Sign In
          </Link>
        </div>
        <p className="text-xs text-navy-400 mt-4">No credit card required · Free forever for personal use</p>
      </section>

      {/* Features */}
      <section className="max-w-5xl mx-auto px-8 pb-20">
        <h2 className="font-display text-2xl font-bold text-navy-700 text-center mb-10">
          Everything you need to shop smarter
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {FEATURES.map(({ icon: Icon, title, desc }) => (
            <div key={title} className="bw-card p-5 hover:shadow-hover transition-all group">
              <div className="w-10 h-10 rounded-xl bg-cyan-50 flex items-center justify-center mb-3 group-hover:bg-cyan-100 transition-colors">
                <Icon className="text-cyan-500 w-5 h-5" />
              </div>
              <h3 className="font-display font-semibold text-navy-700 mb-1.5 text-sm">{title}</h3>
              <p className="text-navy-400 text-sm leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>
      </section>

      {}
      <footer className="border-t border-cyan-100 py-6 text-center">
        <p className="text-xs text-navy-400">
          © 2024 BuyWise. All rights reserved. <br />
          {/* ⚠️ CHANGE THIS: Add your name */}
          Made by Ankit
        </p>
      </footer>
    </main>
  )
}

'use client'
import { useState, useEffect, useRef } from 'react'
import { Send, Bot, User, Trash2, Loader2 } from 'lucide-react'
import { chatApi } from '@/lib/api'
import toast from 'react-hot-toast'
import { format } from 'date-fns'

interface Message { id?: number; message: string; response: string; created_at?: string }

const QUICK_PROMPTS = [
  'What does the Buy Score mean?',
  'How do I track a product?',
  'How is fake review detection done?',
  'What is the Fit Signal feature?',
  'When is the best time to buy shoes in India?',
]

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    chatApi.getHistory().then(r => setMessages(r.data)).catch(() => {})
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  async function sendMessage(text?: string) {
    const msg = text || input.trim()
    if (!msg) return
    setInput('')
    setLoading(true)

    const tempMsg: Message = { message: msg, response: '' }
    setMessages(prev => [...prev, tempMsg])

    try {
      const res = await chatApi.send(msg)
      setMessages(prev => prev.map((m, i) =>
        i === prev.length - 1 ? { ...m, response: res.data.response } : m
      ))
    } catch { toast.error('Chat failed. Check GROQ_API_KEY.') }
    finally { setLoading(false) }
  }

  async function clearHistory() {
    await chatApi.clearHistory()
    setMessages([])
    toast.success('Chat history cleared')
  }

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      {/* Header */}
      <div className="flex justify-between items-center mb-4">
        <div>
          <h1 className="font-display text-2xl font-bold text-navy-700 flex items-center gap-2">
            <Bot className="text-cyan-500 w-6 h-6" /> AI Shopping Assistant
          </h1>
          <p className="text-navy-400 text-sm mt-0.5">Ask anything about prices, products, or how BuyWise works</p>
        </div>
        {messages.length > 0 && (
          <button onClick={clearHistory} className="flex items-center gap-1.5 text-xs text-red-400 hover:text-red-600 transition-colors">
            <Trash2 size={13} /> Clear
          </button>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 pr-1">
        {messages.length === 0 && (
          <div className="text-center py-12">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-cyan-400 to-cyan-600 flex items-center justify-center mx-auto mb-4 shadow-score">
              <Bot className="text-white w-7 h-7" />
            </div>
            <h3 className="font-display font-semibold text-navy-700 mb-1">BuyWise AI Assistant</h3>
            <p className="text-navy-400 text-sm mb-6">Ask about products, prices, or how BuyWise works</p>
            <div className="flex flex-wrap gap-2 justify-center max-w-lg mx-auto">
              {QUICK_PROMPTS.map(p => (
                <button key={p} onClick={() => sendMessage(p)}
                  className="px-3 py-2 bg-cyan-50 border border-cyan-200 rounded-xl text-xs text-cyan-700 hover:bg-cyan-100 transition-colors text-left">
                  {p}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className="space-y-3">
            {/* User message */}
            <div className="flex justify-end">
              <div className="flex items-start gap-2 max-w-[75%]">
                <div className="bg-cyan-500 text-white px-4 py-3 rounded-2xl rounded-tr-sm text-sm leading-relaxed">
                  {msg.message}
                </div>
                <div className="w-7 h-7 rounded-full bg-cyan-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <User size={14} className="text-cyan-600" />
                </div>
              </div>
            </div>
            {/* Bot response */}
            {(msg.response || (i === messages.length - 1 && loading)) && (
              <div className="flex items-start gap-2 max-w-[75%]">
                <div className="w-7 h-7 rounded-full bg-gradient-to-br from-cyan-400 to-cyan-600 flex items-center justify-center flex-shrink-0 mt-0.5 shadow-score">
                  <Bot size={14} className="text-white" />
                </div>
                <div className="bw-card px-4 py-3 text-sm text-navy-700 leading-relaxed">
                  {msg.response || <Loader2 size={14} className="animate-spin text-cyan-400" />}
                </div>
              </div>
            )}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="mt-4 flex gap-3">
        <input
          type="text" value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && !e.shiftKey && sendMessage()}
          placeholder="Ask BuyWise anything..."
          className="flex-1 px-4 py-3 rounded-xl border border-cyan-200 bg-white text-navy-700 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-300 transition-all"
        />
        <button onClick={() => sendMessage()} disabled={loading || !input.trim()}
          className="px-4 py-3 bg-cyan-500 hover:bg-cyan-600 text-white rounded-xl shadow-score bw-btn disabled:opacity-60">
          {loading ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
        </button>
      </div>
    </div>
  )
}

import { create } from 'zustand'

interface User { id: number; email: string; name: string; telegram_id?: string }

interface AuthStore {
  user: User | null
  token: string | null
  setAuth: (user: User, token: string) => void
  logout: () => void
  initFromStorage: () => void
}

export const useAuthStore = create<AuthStore>((set) => ({
  user: null,
  token: null,
  setAuth: (user, token) => {
    localStorage.setItem('buywise_token', token)
    localStorage.setItem('buywise_user', JSON.stringify(user))
    set({ user, token })
  },
  logout: () => {
    localStorage.removeItem('buywise_token')
    localStorage.removeItem('buywise_user')
    set({ user: null, token: null })
  },
  initFromStorage: () => {
    if (typeof window === 'undefined') return
    const token = localStorage.getItem('buywise_token')
    const userStr = localStorage.getItem('buywise_user')
    if (token && userStr) {
      try {
        const user = JSON.parse(userStr)
        set({ user, token })
      } catch {}
    }
  },
}))

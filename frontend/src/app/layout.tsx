import type { Metadata } from 'next'
import './globals.css'
import { Toaster } from 'react-hot-toast'

export const metadata: Metadata = {
  title: 'BuyWise — AI-Powered Smart Shopping',
  description: 'Track prices, analyze reviews, and get AI-powered Buy Scores for Amazon, Flipkart & Myntra',
  icons: { icon: '/favicon.ico' }
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        {children}
        <Toaster
          position="top-right"
          toastOptions={{
            style: {
              background: '#fff',
              color: '#1E293B',
              border: '1px solid #CBEFF3',
              borderRadius: '12px',
              boxShadow: '0 4px 20px rgba(8,145,178,0.1)',
            },
          }}
        />
      </body>
    </html>
  )
}

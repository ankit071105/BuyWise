/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // BuyWise brand palette
        cyan: {
          50:  '#F0FBFC',
          100: '#CBEFF3',
          200: '#A4E2EA',
          300: '#6DD0DC',
          400: '#2BB8CB',
          500: '#0891B2',
          600: '#0772A1',
          700: '#065A86',
          800: '#084367',
          900: '#0A3554',
        },
        navy: {
          900: '#0A1628',
          800: '#0F2040',
          700: '#1E293B',
          600: '#334155',
          500: '#475569',
        },
        surface: {
          50:  '#F8FFFE',
          100: '#F0FBFC',
          200: '#E0F7FA',
        },
        score: {
          great:    '#059669',   // green  ≥7.5
          consider: '#0891B2',   // cyan   5.5-7.4
          wait:     '#D97706',   // amber  4.0-5.4
          avoid:    '#DC2626',   // red    <4.0
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Sora', 'Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      boxShadow: {
        card:   '0 2px 12px 0 rgba(8,145,178,0.08)',
        hover:  '0 8px 32px 0 rgba(8,145,178,0.15)',
        score:  '0 4px 20px 0 rgba(8,145,178,0.2)',
      },
      borderRadius: {
        xl: '1rem',
        '2xl': '1.25rem',
      }
    },
  },
  plugins: [],
}
